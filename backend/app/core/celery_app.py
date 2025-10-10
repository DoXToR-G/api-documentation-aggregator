"""
Celery Application Configuration
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "api_docs_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.fetch_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks configuration
celery_app.conf.beat_schedule = {
    'fetch-all-providers-daily': {
        'task': 'app.tasks.fetch_tasks.fetch_all_providers_task',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM UTC daily
        'options': {'queue': 'default'}
    },
    'fetch-atlassian-hourly': {
        'task': 'app.tasks.fetch_tasks.fetch_provider_task',
        'schedule': crontab(minute=0),  # Run every hour
        'args': ('atlassian',),
        'options': {'queue': 'default'}
    },
    'fetch-datadog-6hours': {
        'task': 'app.tasks.fetch_tasks.fetch_provider_task',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'args': ('datadog',),
        'options': {'queue': 'default'}
    },
    'fetch-kubernetes-weekly': {
        'task': 'app.tasks.fetch_tasks.fetch_provider_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Monday at 3 AM
        'args': ('kubernetes',),
        'options': {'queue': 'default'}
    },
    'cleanup-old-fetch-logs': {
        'task': 'app.tasks.maintenance_tasks.cleanup_old_fetch_logs',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4 AM
        'options': {'queue': 'maintenance'}
    }
}

# Task routing
celery_app.conf.task_routes = {
    'app.tasks.fetch_tasks.*': {'queue': 'default'},
    'app.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
}
