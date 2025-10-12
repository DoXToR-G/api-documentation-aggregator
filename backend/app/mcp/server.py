"""
MCP Server Implementation for API Documentation Service
Handles tool definitions, context management, and agent interactions
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, TextContent, ImageContent, EmbeddedResource,
    LoggingLevel, Text, Position, Range, Location
)

logger = logging.getLogger(__name__)


@dataclass
class APIDocContext:
    """Context for API documentation operations"""
    provider_id: Optional[int] = None
    endpoint_path: Optional[str] = None
    method: Optional[str] = None
    user_query: Optional[str] = None
    search_filters: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class APIDocMCPServer:
    """MCP Server for API Documentation Service"""
    
    def __init__(self):
        self.server = Server("api-doc-mcp-server")
        self.contexts: Dict[str, APIDocContext] = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP tool handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Dict[str, Any]]:
            """List available tools"""
            return [
                {
                    "name": "search_api_docs",
                    "description": "Search API documentation using semantic search",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "provider_ids": {"type": "array", "items": {"type": "integer"}},
                            "methods": {"type": "array", "items": {"type": "string"}},
                            "limit": {"type": "integer", "default": 10}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_api_endpoint",
                    "description": "Get detailed information about a specific API endpoint",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "endpoint_id": {"type": "integer"},
                            "provider_id": {"type": "integer"},
                            "path": {"type": "string"},
                            "method": {"type": "string"}
                        },
                        "required": ["endpoint_id"]
                    }
                },
                {
                    "name": "analyze_api_usage",
                    "description": "Analyze API usage patterns and provide insights",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "provider_id": {"type": "integer"},
                            "time_range": {"type": "string", "enum": ["1d", "7d", "30d", "90d"]},
                            "metrics": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                {
                    "name": "suggest_api_improvements",
                    "description": "Suggest improvements for API documentation based on usage patterns",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "provider_id": {"type": "integer"},
                            "endpoint_id": {"type": "integer"},
                            "feedback_type": {"type": "string", "enum": ["clarity", "examples", "structure"]}
                        }
                    }
                }
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
            """Handle tool calls"""
            try:
                if name == "search_api_docs":
                    return await self.search_api_docs(**arguments)
                elif name == "get_api_endpoint":
                    return await self.get_api_endpoint(**arguments)
                elif name == "analyze_api_usage":
                    return await self.analyze_api_usage(**arguments)
                elif name == "suggest_api_improvements":
                    return await self.suggest_api_improvements(**arguments)
                else:
                    return {"error": f"Unknown tool: {name}"}
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return {"error": str(e)}
    
    async def search_api_docs(
        self,
        query: str,
        provider_ids: Optional[List[int]] = None,
        methods: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search API documentation using database search"""
        try:
            from app.db.database import SessionLocal
            from app.db.models import APIDocumentation, APIProvider
            from sqlalchemy import or_

            db = SessionLocal()

            try:
                # Build query
                db_query = db.query(APIDocumentation).join(APIProvider)

                # Apply filters
                if provider_ids:
                    db_query = db_query.filter(APIDocumentation.provider_id.in_(provider_ids))

                if methods:
                    db_query = db_query.filter(APIDocumentation.http_method.in_(methods))

                # Text search on title, description, and endpoint path
                if query:
                    # Split query into words for better matching
                    words = [w.strip() for w in query.split() if len(w.strip()) > 2]

                    if words:
                        # Create OR conditions for each word
                        search_conditions = []
                        for word in words:
                            search_term = f"%{word}%"
                            search_conditions.append(
                                or_(
                                    APIDocumentation.title.ilike(search_term),
                                    APIDocumentation.description.ilike(search_term),
                                    APIDocumentation.endpoint_path.ilike(search_term)
                                )
                            )
                        # Match if ANY word matches
                        db_query = db_query.filter(or_(*search_conditions))
                    else:
                        # If no words after filtering, search with full query
                        search_term = f"%{query}%"
                        db_query = db_query.filter(
                            or_(
                                APIDocumentation.title.ilike(search_term),
                                APIDocumentation.description.ilike(search_term),
                                APIDocumentation.endpoint_path.ilike(search_term)
                            )
                        )

                # Get results
                results = db_query.limit(limit).all()

                # Format results
                formatted_results = []
                for doc in results:
                    formatted_results.append({
                        "id": doc.id,
                        "title": doc.title,
                        "description": doc.description[:200] + "..." if doc.description and len(doc.description) > 200 else doc.description,
                        "provider": doc.provider.display_name,
                        "endpoint": doc.endpoint_path,
                        "method": doc.http_method,
                        "relevance_score": 0.85
                    })

                return {
                    "results": formatted_results,
                    "total": len(formatted_results),
                    "query": query,
                    "filters": {
                        "provider_ids": provider_ids,
                        "methods": methods
                    }
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error searching API docs: {str(e)}")
            return {
                "error": f"Search failed: {str(e)}",
                "results": [],
                "total": 0
            }
    
    async def get_api_endpoint(
        self, 
        endpoint_id: int,
        provider_id: Optional[int] = None,
        path: Optional[str] = None,
        method: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed information about a specific API endpoint"""
        # TODO: Implement endpoint retrieval
        return {
            "id": endpoint_id,
            "title": "Sample API Endpoint",
            "description": "Detailed description of the endpoint",
            "provider": "Sample Provider",
            "endpoint": "/api/v1/sample",
            "method": "GET",
            "parameters": [],
            "responses": {},
            "examples": []
        }
    
    async def analyze_api_usage(
        self,
        provider_id: Optional[int] = None,
        time_range: str = "7d",
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze API usage patterns and provide insights"""
        # TODO: Implement usage analytics
        return {
            "provider_id": provider_id,
            "time_range": time_range,
            "metrics": metrics or ["requests", "errors", "response_time"],
            "data": {
                "total_requests": 1000,
                "error_rate": 0.02,
                "avg_response_time": 150
            }
        }
    
    async def suggest_api_improvements(
        self,
        provider_id: Optional[int] = None,
        endpoint_id: Optional[int] = None,
        feedback_type: str = "clarity"
    ) -> Dict[str, Any]:
        """Suggest improvements for API documentation"""
        # TODO: Implement improvement suggestions
        return {
            "provider_id": provider_id,
            "endpoint_id": endpoint_id,
            "feedback_type": feedback_type,
            "suggestions": [
                "Add more code examples",
                "Improve parameter descriptions",
                "Include common use cases"
            ]
        }


async def main():
    """Main MCP server entry point"""
    server = APIDocMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="api-doc-mcp-server",
                server_version="1.0.0",
                capabilities=server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
