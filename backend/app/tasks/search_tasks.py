from datetime import datetime
from sqlalchemy.orm import Session
import logging
import asyncio

from app.tasks.celery import celery
from app.db.database import SessionLocal
from app.db.models import APIProvider, APIDocumentation
from app.search.elasticsearch_client import bulk_index_documentation, create_index, health_check

logger = logging.getLogger(__name__)


@celery.task
def reindex_all_documentation():
    """Reindex all documentation in Elasticsearch"""
    db = SessionLocal()
    
    try:
        # Check if Elasticsearch is healthy
        if not asyncio.run(health_check()):
            logger.error("Elasticsearch is not healthy, skipping reindex")
            return {"error": "Elasticsearch is not healthy"}
        
        # Create index if it doesn't exist
        asyncio.run(create_index())
        
        # Get all documentation
        docs = db.query(APIDocumentation).all()
        
        if not docs:
            return {"message": "No documentation to reindex"}
        
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
        
        logger.info(f"Reindexed {indexed_count}/{len(docs)} documents")
        
        return {
            "message": f"Successfully reindexed {indexed_count} documents",
            "total_docs": len(docs),
            "indexed_docs": indexed_count
        }
        
    except Exception as e:
        logger.error(f"Error reindexing documentation: {str(e)}")
        return {"error": str(e)}
        
    finally:
        db.close()


@celery.task
def reindex_provider_documentation(provider_id: int):
    """Reindex documentation for a specific provider"""
    db = SessionLocal()
    
    try:
        # Get provider
        provider = db.query(APIProvider).filter(APIProvider.id == provider_id).first()
        if not provider:
            return {"error": f"Provider {provider_id} not found"}
        
        # Check if Elasticsearch is healthy
        if not asyncio.run(health_check()):
            logger.error("Elasticsearch is not healthy, skipping reindex")
            return {"error": "Elasticsearch is not healthy"}
        
        # Get all documentation for provider
        docs = db.query(APIDocumentation).filter(
            APIDocumentation.provider_id == provider_id
        ).all()
        
        if not docs:
            return {"message": f"No documentation found for provider {provider.display_name}"}
        
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
        
        logger.info(f"Reindexed {indexed_count} documents for provider {provider.display_name}")
        
        return {
            "message": f"Successfully reindexed {indexed_count} documents for {provider.display_name}",
            "provider": provider.display_name,
            "total_docs": len(docs),
            "indexed_docs": indexed_count
        }
        
    except Exception as e:
        logger.error(f"Error reindexing provider documentation: {str(e)}")
        return {"error": str(e)}
        
    finally:
        db.close()


@celery.task
def initialize_search_index():
    """Initialize Elasticsearch index with proper mappings"""
    try:
        # Check if Elasticsearch is healthy
        if not asyncio.run(health_check()):
            logger.error("Elasticsearch is not healthy")
            return {"error": "Elasticsearch is not healthy"}
        
        # Create index
        result = asyncio.run(create_index())
        
        if result:
            logger.info("Successfully initialized search index")
            return {"message": "Search index initialized successfully"}
        else:
            return {"error": "Failed to create search index"}
            
    except Exception as e:
        logger.error(f"Error initializing search index: {str(e)}")
        return {"error": str(e)} 