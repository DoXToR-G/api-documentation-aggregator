"""
True MCP Server Implementation for API Documentation Service
Follows MCP Protocol: Discovery → Request → Response

MCP Primitives:
1. Resources - Atlassian/Datadog documentation as readable resources
2. Tools - Search and query operations
3. Prompts - Templates to guide AI model interactions
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    ResourceTemplate,
    Tool,
    Prompt,
    TextContent,
    ImageContent,
    EmbeddedResource
)

logger = logging.getLogger(__name__)


class APIDocumentationMCPServer:
    """
    MCP Server exposing API documentation as resources, tools, and prompts

    Flow:
    1. Discovery: Client lists available resources, tools, prompts
    2. Request: Client/AI requests specific resource or calls tool
    3. Response: Server returns documentation data or tool results
    """

    def __init__(self):
        self.server = Server("api-documentation-server")
        self.setup_mcp_primitives()

    def setup_mcp_primitives(self):
        """Setup MCP resources, tools, and prompts"""

        # ===== RESOURCES =====
        # Resources represent readable data (documentation)

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """
            List available documentation resources
            OpenAI can discover what documentation is available
            """
            from app.db.database import SessionLocal
            from app.db.models import APIProvider

            db = SessionLocal()
            try:
                providers = db.query(APIProvider).filter(APIProvider.is_active == True).all()

                resources = []
                for provider in providers:
                    # Each provider is a resource
                    resources.append(Resource(
                        uri=f"docs://{provider.name}/overview",
                        name=f"{provider.display_name} API Documentation",
                        description=f"Complete API documentation for {provider.display_name}. Contains {provider.endpoint_count if hasattr(provider, 'endpoint_count') else 'multiple'} endpoints.",
                        mimeType="application/json"
                    ))

                    # Provider endpoints as resource template
                    resources.append(Resource(
                        uri=f"docs://{provider.name}/endpoints",
                        name=f"{provider.display_name} Endpoints",
                        description=f"List of all API endpoints for {provider.display_name}",
                        mimeType="application/json"
                    ))

                return resources

            finally:
                db.close()

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """
            Read a specific documentation resource
            When OpenAI requests a resource, return its content
            """
            from app.db.database import SessionLocal
            from app.db.models import APIProvider, APIDocumentation

            db = SessionLocal()
            try:
                # Parse URI: docs://<provider>/overview or docs://<provider>/endpoints
                parts = uri.replace("docs://", "").split("/")
                provider_name = parts[0]
                resource_type = parts[1] if len(parts) > 1 else "overview"

                provider = db.query(APIProvider).filter(APIProvider.name == provider_name).first()
                if not provider:
                    return json.dumps({"error": f"Provider {provider_name} not found"})

                if resource_type == "overview":
                    # Return provider overview
                    return json.dumps({
                        "provider": provider.display_name,
                        "name": provider.name,
                        "base_url": provider.base_url,
                        "total_endpoints": db.query(APIDocumentation).filter(
                            APIDocumentation.provider_id == provider.id
                        ).count(),
                        "description": f"API documentation for {provider.display_name}",
                        "available_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                    })

                elif resource_type == "endpoints":
                    # Return all endpoints for this provider
                    endpoints = db.query(APIDocumentation).filter(
                        APIDocumentation.provider_id == provider.id
                    ).limit(100).all()  # Limit for performance

                    return json.dumps({
                        "provider": provider.display_name,
                        "endpoints": [
                            {
                                "id": ep.id,
                                "title": ep.title,
                                "path": ep.endpoint_path,
                                "method": ep.http_method,
                                "description": ep.description[:200] if ep.description else None
                            }
                            for ep in endpoints
                        ],
                        "total": len(endpoints)
                    })

                return json.dumps({"error": "Unknown resource type"})

            finally:
                db.close()

        # ===== TOOLS =====
        # Tools represent actions the AI can perform

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """
            List available tools for AI to use
            OpenAI discovers these and can call them
            """
            return [
                Tool(
                    name="search_documentation",
                    description=(
                        "Search API documentation across all providers. "
                        "Use this when user asks about specific APIs, endpoints, or operations. "
                        "Supports natural language queries. "
                        "Returns relevant endpoints with descriptions and examples."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (natural language or keywords)"
                            },
                            "provider": {
                                "type": "string",
                                "enum": ["atlassian", "kubernetes", "datadog", "all"],
                                "description": "Filter by provider (default: all)"
                            },
                            "http_method": {
                                "type": "string",
                                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "all"],
                                "description": "Filter by HTTP method (default: all)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results to return (default: 5)",
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_endpoint_details",
                    description=(
                        "Get detailed information about a specific API endpoint. "
                        "Use when user wants complete details about an endpoint, "
                        "including parameters, request/response schemas, and examples."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "endpoint_id": {
                                "type": "integer",
                                "description": "ID of the endpoint from search results"
                            }
                        },
                        "required": ["endpoint_id"]
                    }
                ),
                Tool(
                    name="list_providers",
                    description=(
                        "List all available API documentation providers. "
                        "Use when user asks what APIs are available or wants to see all providers."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """
            Execute a tool call from AI
            This is where OpenAI searches documentation
            """
            try:
                if name == "search_documentation":
                    result = await self.search_documentation(**arguments)
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]

                elif name == "get_endpoint_details":
                    result = await self.get_endpoint_details(**arguments)
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]

                elif name == "list_providers":
                    result = await self.list_providers()
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]

                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": f"Unknown tool: {name}"})
                    )]

            except Exception as e:
                logger.error(f"Tool execution error: {str(e)}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]

        # ===== PROMPTS =====
        # Prompts guide the AI on how to use the documentation

        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """
            List available prompt templates
            These guide OpenAI on how to interact with documentation
            """
            return [
                Prompt(
                    name="search_and_explain",
                    description="Search documentation and provide a detailed explanation",
                    arguments=[
                        {
                            "name": "user_question",
                            "description": "The user's question about the API",
                            "required": True
                        }
                    ]
                ),
                Prompt(
                    name="generate_code_example",
                    description="Generate code example for an API endpoint",
                    arguments=[
                        {
                            "name": "endpoint_name",
                            "description": "Name or description of the endpoint",
                            "required": True
                        },
                        {
                            "name": "language",
                            "description": "Programming language (python, javascript, curl)",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="compare_endpoints",
                    description="Compare multiple API endpoints",
                    arguments=[
                        {
                            "name": "endpoint_ids",
                            "description": "Comma-separated endpoint IDs",
                            "required": True
                        }
                    ]
                )
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> str:
            """
            Get a specific prompt template filled with arguments
            """
            if name == "search_and_explain":
                user_question = arguments.get("user_question", "")
                return f"""You are an expert API documentation assistant.

User Question: {user_question}

Instructions:
1. Use the search_documentation tool to find relevant endpoints
2. Analyze the results carefully
3. Provide a clear, detailed explanation including:
   - Which endpoint(s) to use
   - HTTP method and path
   - Required parameters
   - Authentication requirements
   - Example request body (if applicable)
   - Expected response
4. Include a code example if helpful

Be concise but thorough. Focus on practical, actionable information."""

            elif name == "generate_code_example":
                endpoint_name = arguments.get("endpoint_name", "")
                language = arguments.get("language", "python")
                return f"""Generate a code example for: {endpoint_name}

Language: {language}

1. First, use search_documentation to find the endpoint
2. Then use get_endpoint_details for complete information
3. Generate a working code example including:
   - Authentication setup
   - Request construction
   - Error handling
   - Response parsing
4. Add comments explaining each part"""

            elif name == "compare_endpoints":
                endpoint_ids = arguments.get("endpoint_ids", "")
                return f"""Compare these endpoints: {endpoint_ids}

1. Get details for each endpoint using get_endpoint_details
2. Create a comparison table showing:
   - Endpoint path and method
   - Purpose and use case
   - Required parameters
   - Response format
   - Key differences
3. Recommend which to use in different scenarios"""

            return "Unknown prompt"

    # ===== TOOL IMPLEMENTATIONS =====

    async def search_documentation(
        self,
        query: str,
        provider: str = "all",
        http_method: str = "all",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search API documentation
        This is called by OpenAI through MCP
        """
        from app.db.database import SessionLocal
        from app.db.models import APIDocumentation, APIProvider
        from sqlalchemy import or_

        db = SessionLocal()
        try:
            # Build query
            db_query = db.query(APIDocumentation).join(APIProvider)

            # Filter by provider
            if provider != "all":
                db_query = db_query.filter(APIProvider.name == provider)

            # Filter by HTTP method
            if http_method != "all":
                db_query = db_query.filter(APIDocumentation.http_method == http_method.upper())

            # Search in title, description, endpoint path
            words = [w.strip() for w in query.split() if len(w.strip()) > 2]
            if words:
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
                db_query = db_query.filter(or_(*search_conditions))

            # Get results
            results = db_query.limit(limit).all()

            # Calculate relevance scores
            scored_results = []
            for doc in results:
                score = 0
                query_lower = query.lower()
                title_lower = (doc.title or "").lower()
                desc_lower = (doc.description or "").lower()

                # Title exact match
                if query_lower in title_lower:
                    score += 10
                # Description match
                if query_lower in desc_lower:
                    score += 5
                # Word matches
                for word in words:
                    if word.lower() in title_lower:
                        score += 3
                    if word.lower() in desc_lower:
                        score += 1

                scored_results.append((score or 1, doc))

            # Sort by score
            scored_results.sort(key=lambda x: x[0], reverse=True)

            # Format results
            return {
                "query": query,
                "provider": provider,
                "http_method": http_method,
                "total_found": len(scored_results),
                "results": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "description": doc.description[:300] if doc.description else None,
                        "provider": doc.provider.display_name,
                        "endpoint_path": doc.endpoint_path,
                        "http_method": doc.http_method,
                        "relevance_score": score / 10.0,
                        "summary": f"{doc.http_method} {doc.endpoint_path} - {doc.title}"
                    }
                    for score, doc in scored_results
                ]
            }

        finally:
            db.close()

    async def get_endpoint_details(self, endpoint_id: int) -> Dict[str, Any]:
        """Get complete details for a specific endpoint"""
        from app.db.database import SessionLocal
        from app.db.models import APIDocumentation

        db = SessionLocal()
        try:
            doc = db.query(APIDocumentation).filter(APIDocumentation.id == endpoint_id).first()
            if not doc:
                return {"error": f"Endpoint {endpoint_id} not found"}

            return {
                "id": doc.id,
                "title": doc.title,
                "description": doc.description,
                "provider": doc.provider.display_name,
                "endpoint_path": doc.endpoint_path,
                "http_method": doc.http_method,
                "request_body": doc.request_body,
                "response_schema": doc.response_schema,
                "parameters": doc.parameters,
                "content": doc.content,
                "tags": doc.tags,
                "version": doc.version,
                "full_url": f"{doc.provider.base_url}{doc.endpoint_path}",
                "documentation_url": doc.documentation_url
            }

        finally:
            db.close()

    async def list_providers(self) -> Dict[str, Any]:
        """List all available API providers"""
        from app.db.database import SessionLocal
        from app.db.models import APIProvider, APIDocumentation

        db = SessionLocal()
        try:
            providers = db.query(APIProvider).filter(APIProvider.is_active == True).all()

            result = {
                "total_providers": len(providers),
                "providers": []
            }

            for provider in providers:
                endpoint_count = db.query(APIDocumentation).filter(
                    APIDocumentation.provider_id == provider.id
                ).count()

                result["providers"].append({
                    "id": provider.id,
                    "name": provider.name,
                    "display_name": provider.display_name,
                    "base_url": provider.base_url,
                    "endpoint_count": endpoint_count,
                    "is_active": provider.is_active
                })

            return result

        finally:
            db.close()


async def main():
    """Start MCP server"""
    server = APIDocumentationMCPServer()

    logger.info("Starting API Documentation MCP Server...")
    logger.info("Exposing: Resources (docs), Tools (search), Prompts (templates)")

    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="api-documentation-server",
                server_version="2.0.0",
                capabilities=server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
