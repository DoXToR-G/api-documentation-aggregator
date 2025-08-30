from celery import current_task
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List
import logging
import asyncio

from app.tasks.celery import celery
from app.db.database import SessionLocal
from app.db.models import APIProvider, APIDocumentation, FetchLog
from app.fetchers.atlassian import AtlassianFetcher
from app.fetchers.datadog import DatadogFetcher
from app.fetchers.kubernetes import KubernetesFetcher
from app.search.elasticsearch_client import bulk_index_documentation
from app.core.config import settings

logger = logging.getLogger(__name__)


async def fetch_docs_async(fetcher):
    """Async wrapper for fetching documentation"""
    async with fetcher:
        return await fetcher.fetch_documentation()


@celery.task(bind=True)
def fetch_provider_documentation(self, provider_name: str):
    """Fetch documentation for a specific provider"""
    db = SessionLocal()
    
    try:
        # Get provider from database
        provider = db.query(APIProvider).filter(APIProvider.name == provider_name).first()
        if not provider:
            logger.error(f"Provider {provider_name} not found")
            return {"error": f"Provider {provider_name} not found"}
        
        if not provider.is_active:
            logger.info(f"Provider {provider_name} is not active, skipping")
            return {"message": f"Provider {provider_name} is not active"}
        
        # Create fetch log
        fetch_log = FetchLog(
            provider_id=provider.id,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(fetch_log)
        db.commit()
        
        try:
            # Get appropriate fetcher
            fetcher = get_fetcher(provider_name, provider.id)
            
            if not fetcher:
                raise ValueError(f"No fetcher available for provider {provider_name}")
            
            # Fetch documentation
            logger.info(f"Starting documentation fetch for {provider_name}")
            
            docs = asyncio.run(fetch_docs_async(fetcher))
            
            # Process and store documentation
            result = process_fetched_docs(db, provider.id, docs)
            
            # Update fetch log with success
            fetch_log.status = "success"
            fetch_log.completed_at = datetime.utcnow()
            fetch_log.total_endpoints = result["total"]
            fetch_log.new_endpoints = result["new"]
            fetch_log.updated_endpoints = result["updated"]
            fetch_log.error_count = 0
            
            db.commit()
            
            # Index in Elasticsearch
            index_result = index_documentation_in_search(db, provider.id)
            
            logger.info(f"Successfully fetched {result['total']} docs for {provider_name}")
            
            return {
                "provider": provider_name,
                "status": "success",
                "total_docs": result["total"],
                "new_docs": result["new"],
                "updated_docs": result["updated"],
                "indexed_docs": index_result
            }
            
        except Exception as e:
            logger.error(f"Error fetching docs for {provider_name}: {str(e)}")
            
            # Update fetch log with error
            fetch_log.status = "error"
            fetch_log.completed_at = datetime.utcnow()
            fetch_log.error_message = str(e)
            fetch_log.error_details = {"task_id": self.request.id}
            
            db.commit()
            
            return {
                "provider": provider_name,
                "status": "error",
                "error": str(e)
            }
            
    except Exception as e:
        logger.error(f"Critical error in fetch task: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()


def get_fetcher(provider_name: str, provider_id: int):
    """Get appropriate fetcher for provider"""
    if provider_name == "atlassian":
        return AtlassianFetcher(
            provider_id=provider_id,
            api_token=settings.atlassian_api_token
        )
    elif provider_name == "datadog":
        return DatadogFetcher(
            provider_id=provider_id,
            api_key=settings.datadog_api_key,
            app_key=settings.datadog_app_key
        )
    elif provider_name == "kubernetes":
        return KubernetesFetcher(provider_id=provider_id)
    else:
        return None


def process_fetched_docs(db: Session, provider_id: int, docs: List) -> dict:
    """Process and store fetched documentation"""
    new_count = 0
    updated_count = 0
    
    for doc_data in docs:
        try:
            # Check if endpoint already exists
            existing = db.query(APIDocumentation).filter(
                APIDocumentation.provider_id == provider_id,
                APIDocumentation.endpoint_path == doc_data.endpoint_path,
                APIDocumentation.http_method == doc_data.http_method.value
            ).first()
            
            if existing:
                # Update existing documentation
                for field, value in doc_data.dict(exclude_unset=True).items():
                    if field != "provider_id":  # Don't change provider_id
                        setattr(existing, field, value)
                
                existing.last_fetched = datetime.utcnow()
                updated_count += 1
                
            else:
                # Create new documentation
                doc = APIDocumentation(**doc_data.dict())
                doc.last_fetched = datetime.utcnow()
                db.add(doc)
                new_count += 1
            
        except Exception as e:
            logger.error(f"Error processing doc {doc_data.title}: {str(e)}")
            continue
    
    db.commit()
    
    return {
        "total": len(docs),
        "new": new_count,
        "updated": updated_count
    }


def index_documentation_in_search(db: Session, provider_id: int) -> int:
    """Index documentation in Elasticsearch"""
    try:
        # Get all documentation for provider
        docs = db.query(APIDocumentation).filter(
            APIDocumentation.provider_id == provider_id
        ).all()
        
        # Prepare documents for indexing
        index_docs = []
        for doc in docs:
            doc_dict = {
                "id": doc.id,
                "title": doc.title,
                "description": doc.description,
                "endpoint_path": doc.endpoint_path,
                "http_method": doc.http_method,
                "content": doc.content,
                "tags": doc.tags or [],
                "version": doc.version,
                "deprecated": doc.deprecated,
                "provider_id": doc.provider_id,
                "provider": {
                    "id": doc.provider.id,
                    "name": doc.provider.name,
                    "display_name": doc.provider.display_name,
                    "base_url": doc.provider.base_url,
                    "documentation_url": doc.provider.documentation_url,
                    "icon_url": doc.provider.icon_url,
                    "description": doc.provider.description,
                    "is_active": doc.provider.is_active,
                    "created_at": doc.provider.created_at.isoformat() if doc.provider.created_at else None
                },
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "last_fetched": doc.last_fetched.isoformat() if doc.last_fetched else None
            }
            index_docs.append(doc_dict)
        
        # Bulk index documents
        indexed_count = asyncio.run(bulk_index_documentation(index_docs))
        
        logger.info(f"Indexed {indexed_count} documents for provider {provider_id}")
        return indexed_count
        
    except Exception as e:
        logger.error(f"Error indexing documentation: {str(e)}")
        return 0


@celery.task
def fetch_all_providers():
    """Fetch documentation for all active providers"""
    db = SessionLocal()
    
    try:
        active_providers = db.query(APIProvider).filter(APIProvider.is_active == True).all()
        
        results = []
        for provider in active_providers:
            result = fetch_provider_documentation.delay(provider.name)
            results.append({
                "provider": provider.name,
                "task_id": result.id
            })
        
        return {
            "message": f"Started fetch tasks for {len(active_providers)} providers",
            "tasks": results
        }
        
    finally:
        db.close()


@celery.task
def cleanup_old_fetch_logs(days: int = 30):
    """Clean up old fetch logs"""
    db = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = db.query(FetchLog).filter(
            FetchLog.started_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old fetch logs")
        
        return {
            "message": f"Cleaned up {deleted_count} fetch logs older than {days} days"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up fetch logs: {str(e)}")
        return {"error": str(e)}
        
    finally:
        db.close() 