"""
MCP Client Implementation for API Documentation Service
Handles communication with MCP server and tool execution
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client for API Documentation Service"""
    
    def __init__(self, server_name: str = "api-doc-mcp-server"):
        self.server_name = server_name
        self.available_tools: List[Dict[str, Any]] = []
        self.connection_status = "disconnected"
    
    async def connect(self) -> bool:
        """Connect to MCP server"""
        try:
            # In a real implementation, this would connect to the MCP server
            # For now, we'll simulate the connection
            self.connection_status = "connected"
            logger.info(f"Connected to MCP server: {self.server_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            self.connection_status = "failed"
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server"""
        try:
            # Simulate tool listing
            self.available_tools = [
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
            
            logger.info(f"Retrieved {len(self.available_tools)} tools from MCP server")
            return self.available_tools
            
        except Exception as e:
            logger.error(f"Failed to list tools: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool"""
        try:
            # Validate tool exists
            tool = next((t for t in self.available_tools if t["name"] == tool_name), None)
            if not tool:
                return {"error": f"Tool '{tool_name}' not found"}
            
            # Validate arguments against schema
            validation_result = self._validate_arguments(arguments, tool["inputSchema"])
            if not validation_result["valid"]:
                return {"error": f"Invalid arguments: {validation_result['errors']}"}
            
            # Execute tool (simulated for now)
            result = await self._execute_tool(tool_name, arguments)
            
            logger.info(f"Successfully executed tool '{tool_name}'")
            return result
            
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}': {str(e)}")
            return {"error": str(e)}
    
    def _validate_arguments(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate arguments against tool schema"""
        errors = []
        
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in arguments:
                errors.append(f"Missing required field: {field}")
        
        # Check field types
        properties = schema.get("properties", {})
        for field, value in arguments.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "integer" and not isinstance(value, int):
                    errors.append(f"Field '{field}' must be an integer")
                elif expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field '{field}' must be a string")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Field '{field}' must be an array")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the specified tool with arguments"""
        # Simulate tool execution
        if tool_name == "search_api_docs":
            return await self._execute_search_tool(arguments)
        elif tool_name == "get_api_endpoint":
            return await self._execute_endpoint_tool(arguments)
        elif tool_name == "analyze_api_usage":
            return await self._execute_analytics_tool(arguments)
        elif tool_name == "suggest_api_improvements":
            return await self._execute_improvements_tool(arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def _execute_search_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search API docs tool with real database search"""
        query = arguments.get("query", "")
        provider_ids = arguments.get("provider_ids", [])
        methods = arguments.get("methods", [])
        limit = arguments.get("limit", 10)

        logger.info(f"Searching database for query: '{query}', providers: {provider_ids}, methods: {methods}")

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
                    # "how to create issue" -> ["how", "to", "create", "issue"]
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
                                    APIDocumentation.endpoint_path.ilike(search_term),
                                    APIDocumentation.content.ilike(search_term)
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
                                APIDocumentation.endpoint_path.ilike(search_term),
                                APIDocumentation.content.ilike(search_term)
                            )
                        )

                # Get results (no limit yet, we'll rank them first)
                results_list = db_query.all()

                logger.info(f"Found {len(results_list)} results in database")

                # Calculate relevance scores for ranking
                scored_results = []
                for doc in results_list:
                    score = 0
                    title_lower = (doc.title or "").lower()
                    desc_lower = (doc.description or "").lower()

                    # Count word matches (if we split query into words)
                    if query and words:
                        for word in words:
                            word_lower = word.lower()
                            # Title matches are worth more
                            if word_lower in title_lower:
                                score += 10
                            # Description matches worth less
                            if word_lower in desc_lower:
                                score += 2
                            # Endpoint path matches
                            if doc.endpoint_path and word_lower in doc.endpoint_path.lower():
                                score += 5

                    scored_results.append((score, doc))

                # Sort by relevance score (highest first), then apply limit
                scored_results.sort(key=lambda x: x[0], reverse=True)
                top_results = scored_results[:limit]

                # Format results
                formatted_results = []
                for score, doc in top_results:
                    formatted_results.append({
                        "id": doc.id,
                        "title": doc.title,
                        "description": (doc.description[:250] + "...") if doc.description and len(doc.description) > 250 else doc.description,
                        "provider": doc.provider.display_name,
                        "endpoint": doc.endpoint_path,
                        "method": doc.http_method,
                        "relevance_score": score / 10.0 if score > 0 else 0.5,
                        "tags": doc.tags if doc.tags else []
                    })

                return {
                    "results": formatted_results,
                    "total": len(formatted_results),
                    "query": query,
                    "filters": {
                        "provider_ids": provider_ids,
                        "methods": methods,
                        "limit": limit
                    }
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Database search error: {str(e)}")
            return {
                "error": f"Search failed: {str(e)}",
                "results": [],
                "total": 0,
                "query": query
            }
    
    async def _execute_endpoint_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get API endpoint tool"""
        endpoint_id = arguments.get("endpoint_id")
        provider_id = arguments.get("provider_id")
        
        return {
            "id": endpoint_id,
            "title": f"API Endpoint {endpoint_id}",
            "description": "Detailed description of the endpoint",
            "provider": f"Provider {provider_id}" if provider_id else "Unknown Provider",
            "endpoint": f"/api/v1/endpoint/{endpoint_id}",
            "method": "GET",
            "parameters": [],
            "responses": {},
            "examples": []
        }
    
    async def _execute_analytics_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analytics tool"""
        provider_id = arguments.get("provider_id")
        time_range = arguments.get("time_range", "7d")
        metrics = arguments.get("metrics", ["requests", "errors", "response_time"])
        
        return {
            "provider_id": provider_id,
            "time_range": time_range,
            "metrics": metrics,
            "data": {
                "total_requests": 1000,
                "error_rate": 0.02,
                "avg_response_time": 150
            }
        }
    
    async def _execute_improvements_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute improvements tool"""
        provider_id = arguments.get("provider_id")
        endpoint_id = arguments.get("endpoint_id")
        feedback_type = arguments.get("feedback_type", "clarity")
        
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
    
    def get_connection_status(self) -> str:
        """Get current connection status"""
        return self.connection_status
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        self.connection_status = "disconnected"
        logger.info("Disconnected from MCP server")
