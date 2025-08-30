from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import httpx
import os

from app.core.config import settings
from app.db.database import get_db, engine
from app.db.models import Base

# Database tables will be created by startup event
# Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API Documentation Aggregator - Minimal Testing Version",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only basic API routes
from app.api.v1 import providers, documentation, agent, search, jira_agent

app.include_router(providers.router, prefix="/api/v1/providers", tags=["providers"])
app.include_router(documentation.router, prefix="/api/v1/documentation", tags=["documentation"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(jira_agent.router, prefix="/api/v1/jira", tags=["jira-agent"])


@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": "API Documentation Aggregator - Minimal Testing Version",
        "docs_url": "/docs",
        "status": "running",
        "mode": "minimal"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "mode": "minimal",
            "services": {
                "database": "✅ Connected",
                "elasticsearch": await get_elasticsearch_status(),
                "celery": "⚠️ Not configured (minimal mode)"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


async def get_elasticsearch_status():
    """Check Elasticsearch connection status"""
    try:
        elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{elasticsearch_url}/_cluster/health', timeout=5.0)
            if response.status_code == 200:
                health = response.json()
                return f"✅ Connected ({health['status']})"
            else:
                return "❌ Connection failed"
    except Exception as e:
        return f"❌ Not available ({str(e)[:50]}...)" if len(str(e)) > 50 else f"❌ Not available ({str(e)})"


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 