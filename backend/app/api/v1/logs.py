"""
API endpoints for system logs
Provides access to bot activity logs for admin monitoring
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from collections import deque

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory log storage (circular buffer)
# In production, you'd use a proper logging system or database
LOG_BUFFER_SIZE = 1000
log_buffer = deque(maxlen=LOG_BUFFER_SIZE)


class LogHandler(logging.Handler):
    """Custom logging handler that stores logs in memory"""

    def emit(self, record):
        try:
            log_entry = {
                "id": str(record.created),
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "source": record.name,
                "details": {
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                } if hasattr(record, 'module') else None
            }
            log_buffer.append(log_entry)
        except Exception:
            self.handleError(record)


# Install the custom log handler
def install_log_handler():
    """Install custom log handler to capture logs"""
    handler = LogHandler()
    handler.setLevel(logging.INFO)

    # Add to root logger to capture all logs
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    # Also add to specific loggers we want to monitor
    for logger_name in ['app', 'app.services.ai_agent', 'app.mcp.server_redesign', 'uvicorn']:
        specific_logger = logging.getLogger(logger_name)
        specific_logger.addHandler(handler)


@router.get("/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    source: Optional[str] = None,
    since: Optional[datetime] = None
):
    """
    Get system logs

    Parameters:
    - limit: Maximum number of logs to return (1-1000)
    - level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - source: Filter by source logger name
    - since: Only return logs after this timestamp
    """
    try:
        logs = list(log_buffer)

        # Apply filters
        if level:
            logs = [log for log in logs if log['level'] == level]

        if source:
            logs = [log for log in logs if source.lower() in log['source'].lower()]

        if since:
            since_iso = since.isoformat()
            logs = [log for log in logs if log['timestamp'] >= since_iso]

        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x['timestamp'], reverse=True)

        # Apply limit
        logs = logs[:limit]

        return {
            "logs": logs,
            "total": len(logs),
            "buffer_size": len(log_buffer),
            "buffer_max": LOG_BUFFER_SIZE
        }

    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        return {
            "logs": [],
            "total": 0,
            "error": str(e)
        }


@router.delete("/logs")
async def clear_logs():
    """Clear all logs from the buffer"""
    try:
        log_buffer.clear()
        logger.info("Log buffer cleared by admin")
        return {
            "message": "Logs cleared successfully",
            "buffer_size": len(log_buffer)
        }
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}")
        return {
            "error": str(e)
        }


@router.get("/logs/stats")
async def get_log_stats():
    """Get statistics about logs"""
    try:
        logs = list(log_buffer)

        # Count by level
        level_counts = {}
        for log in logs:
            level = log['level']
            level_counts[level] = level_counts.get(level, 0) + 1

        # Count by source
        source_counts = {}
        for log in logs:
            source = log['source']
            source_counts[source] = source_counts.get(source, 0) + 1

        # Recent activity (last hour)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        recent_logs = [log for log in logs if log['timestamp'] >= one_hour_ago]

        return {
            "total_logs": len(logs),
            "buffer_usage": f"{len(logs)}/{LOG_BUFFER_SIZE}",
            "level_counts": level_counts,
            "source_counts": source_counts,
            "recent_activity": {
                "last_hour": len(recent_logs),
                "errors_last_hour": len([log for log in recent_logs if log['level'] == 'ERROR'])
            }
        }

    except Exception as e:
        logger.error(f"Error getting log stats: {str(e)}")
        return {
            "error": str(e)
        }


# Install log handler when module is imported
install_log_handler()

# Log that the logs API is ready
logger.info("Logs API initialized - log collection started")
