from celery import Celery
from celery.schedules import crontab
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery instance
celery = Celery(
    "api_docs_fetcher",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.fetch_tasks",
        "app.tasks.search_tasks"
    ]
)

# Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks
celery.conf.beat_schedule = {
    # Fetch Atlassian docs daily
    'fetch-atlassian-docs': {
        'task': 'app.tasks.fetch_tasks.fetch_provider_documentation',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': ('atlassian',),
    },
    # Fetch Datadog docs twice daily
    'fetch-datadog-docs': {
        'task': 'app.tasks.fetch_tasks.fetch_provider_documentation',
        'schedule': crontab(hour='2,14', minute=30),  # 2:30 AM and 2:30 PM
        'args': ('datadog',),
    },
    # Fetch Kubernetes docs daily
    'fetch-kubernetes-docs': {
        'task': 'app.tasks.fetch_tasks.fetch_provider_documentation',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
        'args': ('kubernetes',),
    },
    # Reindex search documents weekly
    'reindex-search': {
        'task': 'app.tasks.search_tasks.reindex_all_documentation',
        'schedule': crontab(day_of_week=0, hour=1, minute=0),  # Sunday 1 AM
    },
    # Clean up old fetch logs monthly
    'cleanup-old-logs': {
        'task': 'app.tasks.fetch_tasks.cleanup_old_fetch_logs',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # 1st of month
    },
} 