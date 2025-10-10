"""
API endpoints for documentation fetching
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.db.database import get_db
from app.services.fetcher_service import FetcherService
from app.vector_store.chroma_client import ChromaDBClient
from app.db.models import APIProvider, FetchLog
from app.tasks.fetch_tasks import fetch_provider_documentation, fetch_all_providers

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sync/all", response_model=Dict[str, Any])
async def sync_all_providers(
    background_tasks: BackgroundTasks,
    use_celery: bool = True,
    db: Session = Depends(get_db)
):
    """
    Trigger documentation sync for all active providers

    Args:
        use_celery: If True, run as Celery task. If False, run in background
    """
    try:
        if use_celery:
            # Use Celery for scheduled task
            result = fetch_all_providers.delay()
            return {
                "status": "queued",
                "task_id": result.id,
                "message": "Documentation sync queued for all providers"
            }
        else:
            # Run in background task (non-blocking)
            vector_store = ChromaDBClient()
            fetcher_service = FetcherService(db=db, vector_store=vector_store)

            background_tasks.add_task(fetcher_service.fetch_all_providers)

            return {
                "status": "started",
                "message": "Documentation sync started for all providers"
            }

    except Exception as e:
        logger.error(f"Failed to start sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/provider/{provider_name}", response_model=Dict[str, Any])
async def sync_provider(
    provider_name: str,
    background_tasks: BackgroundTasks,
    use_celery: bool = True,
    db: Session = Depends(get_db)
):
    """
    Trigger documentation sync for a specific provider

    Args:
        provider_name: Name of the provider (e.g., 'atlassian', 'datadog', 'kubernetes')
        use_celery: If True, run as Celery task. If False, run in background
    """
    try:
        # Check if provider exists and is active
        provider = db.query(APIProvider).filter(
            APIProvider.name == provider_name,
            APIProvider.is_active == True
        ).first()

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_name}' not found or inactive"
            )

        if use_celery:
            # Use Celery for scheduled task
            result = fetch_provider_documentation.delay(provider_name)
            return {
                "status": "queued",
                "task_id": result.id,
                "provider": provider_name,
                "message": f"Documentation sync queued for {provider_name}"
            }
        else:
            # Run in background task (non-blocking)
            vector_store = ChromaDBClient()
            fetcher_service = FetcherService(db=db, vector_store=vector_store)

            background_tasks.add_task(fetcher_service.sync_provider_by_name, provider_name)

            return {
                "status": "started",
                "provider": provider_name,
                "message": f"Documentation sync started for {provider_name}"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start sync for {provider_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/provider/id/{provider_id}", response_model=Dict[str, Any])
async def sync_provider_by_id(
    provider_id: int,
    background_tasks: BackgroundTasks,
    use_celery: bool = False,
    db: Session = Depends(get_db)
):
    """
    Trigger documentation sync for a specific provider by ID

    Args:
        provider_id: ID of the provider
        use_celery: If True, run as Celery task. If False, run in background
    """
    try:
        # Check if provider exists and is active
        provider = db.query(APIProvider).filter(
            APIProvider.id == provider_id,
            APIProvider.is_active == True
        ).first()

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"Provider with ID {provider_id} not found or inactive"
            )

        if use_celery:
            # Use Celery for scheduled task
            from app.tasks.fetch_tasks import fetch_provider_by_id_task
            result = fetch_provider_by_id_task.delay(provider_id)
            return {
                "status": "queued",
                "task_id": result.id,
                "provider_id": provider_id,
                "provider_name": provider.name,
                "message": f"Documentation sync queued for {provider.name}"
            }
        else:
            # Run in background task (non-blocking)
            vector_store = ChromaDBClient()
            fetcher_service = FetcherService(db=db, vector_store=vector_store)

            background_tasks.add_task(fetcher_service.sync_provider_by_id, provider_id)

            return {
                "status": "started",
                "provider_id": provider_id,
                "provider_name": provider.name,
                "message": f"Documentation sync started for {provider.name}"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start sync for provider ID {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/logs", response_model=Dict[str, Any])
async def get_fetch_logs(
    provider_id: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get recent fetch logs

    Args:
        provider_id: Filter by provider ID (optional)
        limit: Number of logs to return
    """
    try:
        query = db.query(FetchLog)

        if provider_id:
            query = query.filter(FetchLog.provider_id == provider_id)

        logs = query.order_by(FetchLog.started_at.desc()).limit(limit).all()

        return {
            "logs": [
                {
                    "id": log.id,
                    "provider_id": log.provider_id,
                    "provider_name": log.provider.name if log.provider else None,
                    "status": log.status,
                    "started_at": log.started_at.isoformat() if log.started_at else None,
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "total_endpoints": log.total_endpoints,
                    "new_endpoints": log.new_endpoints,
                    "updated_endpoints": log.updated_endpoints,
                    "error_count": log.error_count,
                    "error_message": log.error_message
                }
                for log in logs
            ],
            "count": len(logs)
        }

    except Exception as e:
        logger.error(f"Failed to get fetch logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/latest/{provider_name}", response_model=Dict[str, Any])
async def get_latest_fetch_status(
    provider_name: str,
    db: Session = Depends(get_db)
):
    """
    Get latest fetch status for a specific provider
    """
    try:
        provider = db.query(APIProvider).filter(
            APIProvider.name == provider_name
        ).first()

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_name}' not found"
            )

        latest_log = db.query(FetchLog).filter(
            FetchLog.provider_id == provider.id
        ).order_by(FetchLog.started_at.desc()).first()

        if not latest_log:
            return {
                "provider": provider_name,
                "status": "never_fetched",
                "message": "No fetch logs found for this provider"
            }

        return {
            "provider": provider_name,
            "status": latest_log.status,
            "started_at": latest_log.started_at.isoformat() if latest_log.started_at else None,
            "completed_at": latest_log.completed_at.isoformat() if latest_log.completed_at else None,
            "total_endpoints": latest_log.total_endpoints,
            "new_endpoints": latest_log.new_endpoints,
            "updated_endpoints": latest_log.updated_endpoints,
            "error_count": latest_log.error_count,
            "error_message": latest_log.error_message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest fetch status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
