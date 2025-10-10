"""
Celery Tasks for Maintenance Operations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.db.database import SessionLocal
from app.db.models import FetchLog, SearchQuery

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.maintenance_tasks.cleanup_old_fetch_logs')
def cleanup_old_fetch_logs(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old fetch logs to prevent database bloat

    Args:
        days_to_keep: Number of days to keep fetch logs (default: 30)
    """
    logger.info(f"Starting cleanup of fetch logs older than {days_to_keep} days")

    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Delete old fetch logs
        deleted_count = db.query(FetchLog).filter(
            FetchLog.completed_at < cutoff_date
        ).delete()

        db.commit()

        result = {
            'status': 'success',
            'deleted_logs': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }

        logger.info(f"Cleanup complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in cleanup_old_fetch_logs: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


@celery_app.task(name='app.tasks.maintenance_tasks.cleanup_old_search_queries')
def cleanup_old_search_queries(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old search queries to prevent database bloat

    Args:
        days_to_keep: Number of days to keep search queries (default: 90)
    """
    logger.info(f"Starting cleanup of search queries older than {days_to_keep} days")

    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Delete old search queries
        deleted_count = db.query(SearchQuery).filter(
            SearchQuery.created_at < cutoff_date
        ).delete()

        db.commit()

        result = {
            'status': 'success',
            'deleted_queries': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }

        logger.info(f"Cleanup complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in cleanup_old_search_queries: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


@celery_app.task(name='app.tasks.maintenance_tasks.optimize_vector_store')
def optimize_vector_store() -> Dict[str, Any]:
    """
    Optimize vector store by rebuilding indexes or cleaning up orphaned entries
    """
    logger.info("Starting vector store optimization")

    try:
        from app.vector_store.chroma_client import ChromaDBClient
        from app.db.database import SessionLocal
        from app.db.models import APIDocumentation

        vector_store = ChromaDBClient()
        db = SessionLocal()

        try:
            # Get vector store stats before optimization
            stats_before = vector_store.get_collection_stats()

            # Get all document IDs from database
            db_doc_ids = set(f"doc_{doc.id}" for doc in db.query(APIDocumentation.id).all())

            # Get all IDs from vector store
            collection = vector_store.collection
            vector_doc_ids = set(collection.get()['ids'])

            # Find orphaned vector store entries (in vector store but not in DB)
            orphaned_ids = vector_doc_ids - db_doc_ids

            if orphaned_ids:
                logger.info(f"Found {len(orphaned_ids)} orphaned vector store entries")
                # Delete orphaned entries
                collection.delete(ids=list(orphaned_ids))

            # Get stats after optimization
            stats_after = vector_store.get_collection_stats()

            result = {
                'status': 'success',
                'orphaned_entries_removed': len(orphaned_ids),
                'stats_before': stats_before,
                'stats_after': stats_after
            }

            logger.info(f"Vector store optimization complete: {result}")
            return result

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in optimize_vector_store: {str(e)}")
        raise
