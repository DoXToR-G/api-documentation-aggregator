from fastapi import APIRouter
from app.api.v1 import providers, documentation, search, analytics, agent, jira_agent, fetcher
# Temporarily disable auth until PyJWT is properly installed
# from app.api.v1 import auth

# Main API router
api_router = APIRouter()

# Include sub-routers
# api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(documentation.router, prefix="/documentation", tags=["documentation"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(jira_agent.router, prefix="/jira", tags=["jira-agent"])
api_router.include_router(fetcher.router, prefix="/fetcher", tags=["fetcher"]) 