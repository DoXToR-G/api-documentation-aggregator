from fastapi import APIRouter
from app.api.v1 import providers, documentation, search, analytics, agent, jira_agent

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(documentation.router, prefix="/documentation", tags=["documentation"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(jira_agent.router, prefix="/jira", tags=["jira-agent"]) 