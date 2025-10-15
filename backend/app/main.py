from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import uvicorn
import json
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.db.database import get_db, engine
from app.db.models import Base
from app.api.routes import api_router
from app.services.ai_agent_openai_mcp import AIAgentWithOpenAIMCP
from app.vector_store.chroma_client import ChromaDBClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request models
class AIQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    openai_api_key: Optional[str] = None
    enable_web_search: Optional[bool] = None


# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize services
ai_agent_service = AIAgentWithOpenAIMCP()
vector_store = ChromaDBClient()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="MCP-Based API Documentation Aggregator with AI Agent",
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

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Initialize AI agent on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Load settings from database
        from app.services.settings_service import settings_service
        db = next(get_db())
        settings_service.load_settings_to_config(db)
        logger.info("Settings loaded from database")

        # Initialize AI agent
        await ai_agent_service.initialize()
        logger.info("AI Agent with OpenAI+MCP initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI Agent: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": "MCP-Based API Documentation Aggregator - AI-powered documentation service",
        "docs_url": "/docs",
        "status": "running",
        "features": [
            "MCP (Model Context Protocol) integration",
            "AI-powered search and assistance",
            "Vector-based semantic search",
            "Intelligent API documentation",
            "Real-time chat interface"
        ]
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))

        # Test vector store
        vector_stats = vector_store.get_collection_stats()

        return {
            "status": "healthy",
            "database": "connected",
            "vector_store": "connected",
            "vector_store_stats": vector_stats,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/ai/query")
async def ai_query(request: AIQueryRequest):
    """Process user query with AI agent"""
    try:
        response = await ai_agent_service.process_user_query(
            query=request.query,
            context=request.context,
            session_id=request.session_id
        )
        return response
    except Exception as e:
        logger.error(f"AI query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")


@app.get("/ai/conversation/{session_id}")
async def get_conversation_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return")
):
    """Get conversation history for a session"""
    try:
        history = ai_agent_service.get_conversation_history(
            session_id=session_id,
            limit=limit
        )
        return {
            "session_id": session_id,
            "history": history,
            "total_messages": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@app.get("/ai/session/{session_id}/context")
async def get_session_context(session_id: str):
    """Get session context and insights"""
    try:
        context = ai_agent_service.get_session_context(session_id)
        return {
            "session_id": session_id,
            "context": context
        }
    except Exception as e:
        logger.error(f"Failed to get session context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve context: {str(e)}")


@app.get("/ai/status")
async def get_ai_agent_status():
    """Get AI agent status and statistics"""
    try:
        status = ai_agent_service.get_agent_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get AI agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.delete("/ai/conversation/{session_id}")
async def clear_conversation_history(session_id: str):
    """Clear conversation history for a session"""
    try:
        ai_agent_service.clear_conversation_history(session_id=session_id)
        return {"message": f"Conversation history cleared for session {session_id}"}
    except Exception as e:
        logger.error(f"Failed to clear conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")


@app.websocket("/ws/ai")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time AI interactions"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message
            if message.get("type") == "query":
                query = message.get("query", "")
                context = message.get("context", {})
                session_id = message.get("session_id")
                
                # Process with AI agent
                response = await ai_agent_service.process_user_query(
                    query=query,
                    context=context,
                    session_id=session_id
                )
                
                # Send response back
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "data": response
                }))
            
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Unknown message type"
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except:
            pass


@app.get("/vector-store/stats")
async def get_vector_store_stats():
    """Get vector store statistics"""
    try:
        stats = vector_store.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get vector store stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/api/v1/settings/update")
async def update_settings(request: SettingsUpdateRequest):
    """
    Update application settings (OpenAI API key, web search toggle)
    Settings are stored in memory for the current session
    """
    try:
        updated_settings = {}

        # Update OpenAI API key
        if request.openai_api_key is not None:
            settings.openai_api_key = request.openai_api_key
            updated_settings["openai_api_key"] = "***" if request.openai_api_key else None
            logger.info("OpenAI API key updated")

        # Update web search setting
        if request.enable_web_search is not None:
            settings.enable_web_search = request.enable_web_search
            updated_settings["enable_web_search"] = request.enable_web_search
            logger.info(f"Web search {'enabled' if request.enable_web_search else 'disabled'}")

        return {
            "status": "success",
            "message": "Settings updated successfully",
            "updated_settings": updated_settings
        }

    except Exception as e:
        logger.error(f"Failed to update settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@app.get("/api/v1/settings")
async def get_settings():
    """Get current application settings (masked sensitive data)"""
    try:
        return {
            "openai_api_key_configured": bool(settings.openai_api_key),
            "enable_web_search": settings.enable_web_search,
            "web_search_provider": settings.web_search_provider,
            "web_search_max_results": settings.web_search_max_results
        }
    except Exception as e:
        logger.error(f"Failed to get settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 