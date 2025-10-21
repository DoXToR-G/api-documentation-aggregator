from fastapi import APIRouter
from app.api.v1 import search, agent, ai_settings, doc_sources, logs
# Removed: providers, documentation, analytics, jira_agent, fetcher
# These are no longer needed as AI handles documentation access via MCP

# Main API router
api_router = APIRouter()

# Include sub-routers - Simplified for AI-powered documentation
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(ai_settings.router, tags=["ai-settings"])
api_router.include_router(doc_sources.router, tags=["documentation-sources"])
api_router.include_router(logs.router, tags=["logs"]) 