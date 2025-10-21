"""
True MCP Server Implementation for API Documentation Service
Follows MCP Protocol: Discovery → Request → Response

MCP Primitives:
1. Resources - Atlassian/Datadog documentation as readable resources
2. Tools - Search and query operations (including dynamic OpenAPI loading)
3. Prompts - Templates to guide AI model interactions

New Features:
- In-memory OpenAPI cache for dynamic "bring your own OpenAPI URL" at chat time
- No DB persistence required for dynamically loaded providers
"""

import asyncio
import json
import logging
import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

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


@dataclass
class CachedEndpoint:
    """Represents a cached OpenAPI endpoint in memory"""
    id: str  # Unique ID: provider:path:method
    provider: str
    path: str
    method: str
    title: str
    description: Optional[str]
    parameters: Optional[List[Dict[str, Any]]]
    request_body: Optional[Dict[str, Any]]
    responses: Optional[Dict[str, Any]]
    examples: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    deprecated: bool
    content: str  # Human-readable formatted content

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


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

        # In-memory OpenAPI cache: provider_name -> list of endpoints
        self.openapi_cache: Dict[str, List[CachedEndpoint]] = {}

        # Track OpenAPI URLs for each provider
        self.openapi_urls: Dict[str, str] = {}

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

                # Add dynamically loaded providers from cache
                for provider_name in self.openapi_cache.keys():
                    # Skip if already in DB providers
                    if not any(p.name == provider_name for p in providers):
                        resources.append(Resource(
                            uri=f"docs://{provider_name}/overview",
                            name=f"{provider_name} API Documentation (Dynamic)",
                            description=f"Dynamically loaded OpenAPI documentation for {provider_name}",
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

                # Check if provider is in dynamic cache
                if provider_name in self.openapi_cache:
                    endpoints = self.openapi_cache[provider_name]

                    if resource_type == "overview":
                        return json.dumps({
                            "provider": provider_name,
                            "name": provider_name,
                            "total_endpoints": len(endpoints),
                            "description": f"Dynamically loaded OpenAPI documentation for {provider_name}",
                            "source": "in-memory cache",
                            "openapi_url": self.openapi_urls.get(provider_name, "unknown")
                        })
                    elif resource_type == "endpoints":
                        return json.dumps({
                            "provider": provider_name,
                            "endpoints": [
                                {
                                    "id": ep.id,
                                    "title": ep.title,
                                    "path": ep.path,
                                    "method": ep.method,
                                    "description": ep.description[:200] if ep.description else None
                                }
                                for ep in endpoints[:100]  # Limit for performance
                            ],
                            "total": len(endpoints),
                            "source": "in-memory cache"
                        })

                # Fall back to DB provider
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
                        "available_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                        "source": "database"
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
                        "total": len(endpoints),
                        "source": "database"
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
                    name="load_openapi",
                    description=(
                        "Load and cache OpenAPI documentation from a URL at runtime. "
                        "Use this to dynamically load API documentation without database persistence. "
                        "The documentation will be cached in memory and available for searching. "
                        "Supports OpenAPI 2.0 (Swagger) and OpenAPI 3.0 specifications."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "description": "Name/identifier for this API provider (e.g., 'stripe', 'github')"
                            },
                            "url": {
                                "type": "string",
                                "description": "URL to the OpenAPI/Swagger specification (JSON format)"
                            }
                        },
                        "required": ["provider", "url"]
                    }
                ),
                Tool(
                    name="search_openapi",
                    description=(
                        "Search cached OpenAPI endpoints loaded via load_openapi. "
                        "Performs semantic search across endpoint paths, titles, descriptions, and tags. "
                        "Use this after loading OpenAPI documentation to find specific endpoints."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "description": "Provider name to search within"
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query (natural language or keywords)"
                            },
                            "http_method": {
                                "type": "string",
                                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "all"],
                                "description": "Filter by HTTP method (optional, default: all)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results to return (default: 10)",
                                "minimum": 1,
                                "maximum": 50
                            }
                        },
                        "required": ["provider", "query"]
                    }
                ),
                Tool(
                    name="get_openapi_endpoint_details",
                    description=(
                        "Get full details for a specific cached OpenAPI endpoint. "
                        "Use the endpoint ID from search_openapi results. "
                        "Returns complete information including parameters, request/response schemas, and examples."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "description": "Provider name"
                            },
                            "id": {
                                "type": "string",
                                "description": "Endpoint ID from search results (format: provider:path:method)"
                            }
                        },
                        "required": ["provider", "id"]
                    }
                ),
                Tool(
                    name="search_documentation",
                    description=(
                        "Search API documentation across all providers (database-persisted only). "
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
                        "Get detailed information about a specific API endpoint (database-persisted). "
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
                        "List all available API documentation providers (both database and cached). "
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
                if name == "load_openapi":
                    result = await self.load_openapi(**arguments)
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]

                elif name == "search_openapi":
                    result = await self.search_openapi(**arguments)
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]

                elif name == "get_openapi_endpoint_details":
                    result = await self.get_openapi_endpoint_details(**arguments)
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]

                elif name == "search_documentation":
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
                ),
                Prompt(
                    name="load_and_explore",
                    description="Load OpenAPI documentation from a URL and explore available endpoints",
                    arguments=[
                        {
                            "name": "provider_name",
                            "description": "Name for the API provider",
                            "required": True
                        },
                        {
                            "name": "openapi_url",
                            "description": "URL to the OpenAPI specification",
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

            elif name == "load_and_explore":
                provider_name = arguments.get("provider_name", "")
                openapi_url = arguments.get("openapi_url", "")
                return f"""Load and explore OpenAPI documentation dynamically.

Provider: {provider_name}
OpenAPI URL: {openapi_url}

Steps:
1. Use load_openapi tool to download and cache the OpenAPI specification
2. Once loaded, use search_openapi to explore available endpoints
3. Provide a summary of:
   - Total number of endpoints
   - Main endpoint categories/tags
   - Most common HTTP methods
   - Interesting or notable endpoints
4. Be ready to answer questions about specific endpoints using get_openapi_endpoint_details

This enables "bring your own OpenAPI URL" functionality without database persistence."""

            return "Unknown prompt"

    # ===== NEW MCP TOOL IMPLEMENTATIONS =====

    async def load_openapi(self, provider: str, url: str) -> Dict[str, Any]:
        """
        Load and cache OpenAPI specification from a URL
        Stores parsed endpoints in memory without database persistence
        """
        try:
            logger.info(f"Loading OpenAPI spec for {provider} from {url}")

            # Download OpenAPI spec
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                spec = response.json()

            # Parse OpenAPI spec
            endpoints = self._parse_openapi_spec(provider, spec)

            # Store in cache
            self.openapi_cache[provider] = endpoints
            self.openapi_urls[provider] = url

            logger.info(f"Successfully loaded {len(endpoints)} endpoints for {provider}")

            return {
                "status": "success",
                "provider": provider,
                "url": url,
                "total_endpoints": len(endpoints),
                "message": f"Loaded and cached {len(endpoints)} endpoints from {provider}",
                "sample_endpoints": [
                    {
                        "id": ep.id,
                        "method": ep.method,
                        "path": ep.path,
                        "title": ep.title
                    }
                    for ep in endpoints[:5]  # Show first 5
                ]
            }

        except httpx.HTTPError as e:
            error_msg = f"Failed to fetch OpenAPI spec from {url}: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "provider": provider,
                "url": url,
                "error": error_msg
            }
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in OpenAPI spec: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "provider": provider,
                "url": url,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error loading OpenAPI spec: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "provider": provider,
                "url": url,
                "error": error_msg
            }

    async def search_openapi(
        self,
        provider: str,
        query: str,
        http_method: str = "all",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search cached OpenAPI endpoints
        """
        try:
            # Check if provider is loaded
            if provider not in self.openapi_cache:
                return {
                    "status": "error",
                    "provider": provider,
                    "query": query,
                    "error": f"Provider '{provider}' not loaded. Use load_openapi first.",
                    "suggestion": f"Call load_openapi with provider='{provider}' and a valid OpenAPI URL"
                }

            endpoints = self.openapi_cache[provider]

            # Filter by HTTP method if specified
            if http_method and http_method != "all":
                endpoints = [ep for ep in endpoints if ep.method.upper() == http_method.upper()]

            # Search
            query_lower = query.lower()
            scored_results = []

            for ep in endpoints:
                score = 0

                # Exact matches get highest score
                if query_lower in ep.path.lower():
                    score += 10
                if query_lower in ep.title.lower():
                    score += 10

                # Partial matches
                query_words = query_lower.split()
                for word in query_words:
                    if len(word) < 3:
                        continue

                    if word in ep.path.lower():
                        score += 3
                    if word in ep.title.lower():
                        score += 3
                    if ep.description and word in ep.description.lower():
                        score += 2
                    if ep.tags and any(word in tag.lower() for tag in ep.tags):
                        score += 2

                if score > 0:
                    scored_results.append((score, ep))

            # Sort by score and limit
            scored_results.sort(key=lambda x: x[0], reverse=True)
            top_results = scored_results[:limit]

            return {
                "status": "success",
                "provider": provider,
                "query": query,
                "http_method": http_method,
                "total_found": len(scored_results),
                "showing": len(top_results),
                "results": [
                    {
                        "id": ep.id,
                        "method": ep.method,
                        "path": ep.path,
                        "title": ep.title,
                        "description": ep.description[:200] if ep.description else None,
                        "tags": ep.tags,
                        "deprecated": ep.deprecated,
                        "relevance_score": score / 10.0
                    }
                    for score, ep in top_results
                ]
            }

        except Exception as e:
            logger.error(f"Error searching OpenAPI cache: {str(e)}")
            return {
                "status": "error",
                "provider": provider,
                "query": query,
                "error": str(e)
            }

    async def get_openapi_endpoint_details(
        self,
        provider: str,
        id: str
    ) -> Dict[str, Any]:
        """
        Get full details for a cached OpenAPI endpoint
        """
        try:
            # Check if provider is loaded
            if provider not in self.openapi_cache:
                return {
                    "status": "error",
                    "provider": provider,
                    "id": id,
                    "error": f"Provider '{provider}' not loaded. Use load_openapi first."
                }

            endpoints = self.openapi_cache[provider]

            # Find endpoint by ID
            endpoint = next((ep for ep in endpoints if ep.id == id), None)

            if not endpoint:
                return {
                    "status": "error",
                    "provider": provider,
                    "id": id,
                    "error": f"Endpoint with ID '{id}' not found in provider '{provider}'"
                }

            return {
                "status": "success",
                "provider": provider,
                "endpoint": endpoint.to_dict()
            }

        except Exception as e:
            logger.error(f"Error getting endpoint details: {str(e)}")
            return {
                "status": "error",
                "provider": provider,
                "id": id,
                "error": str(e)
            }

    def _parse_openapi_spec(self, provider: str, spec: Dict[str, Any]) -> List[CachedEndpoint]:
        """
        Parse OpenAPI/Swagger specification into CachedEndpoint objects
        """
        endpoints = []

        try:
            paths = spec.get('paths', {})
            base_info = spec.get('info', {})

            logger.info(f"Parsing OpenAPI spec with {len(paths)} paths")

            for path, path_info in paths.items():
                for method, method_info in path_info.items():
                    # Skip non-method properties
                    if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                        continue

                    # Skip if method_info is not a dict
                    if not isinstance(method_info, dict):
                        continue

                    try:
                        # Generate unique ID
                        endpoint_id = f"{provider}:{path}:{method.upper()}"

                        # Extract information
                        title = method_info.get('summary', f"{method.upper()} {path}")
                        description = method_info.get('description', '')

                        # Extract parameters
                        parameters = []
                        if 'parameters' in method_info:
                            for param in method_info['parameters']:
                                parameters.append({
                                    'name': param.get('name'),
                                    'in': param.get('in'),
                                    'description': param.get('description'),
                                    'required': param.get('required', False),
                                    'schema': param.get('schema', {})
                                })

                        # Extract request body
                        request_body = method_info.get('requestBody')

                        # Extract responses
                        responses = method_info.get('responses', {})

                        # Extract examples
                        examples = method_info.get('examples', {})

                        # Extract tags
                        tags = method_info.get('tags', [])

                        # Check if deprecated
                        deprecated = method_info.get('deprecated', False)

                        # Generate human-readable content
                        content = self._generate_endpoint_content(method_info, path, method.upper())

                        endpoint = CachedEndpoint(
                            id=endpoint_id,
                            provider=provider,
                            path=path,
                            method=method.upper(),
                            title=title,
                            description=description,
                            parameters=parameters if parameters else None,
                            request_body=request_body,
                            responses=responses,
                            examples=examples,
                            tags=tags,
                            deprecated=deprecated,
                            content=content
                        )

                        endpoints.append(endpoint)

                    except Exception as e:
                        logger.error(f"Error parsing endpoint {method.upper()} {path}: {str(e)}")
                        continue

            logger.info(f"Successfully parsed {len(endpoints)} endpoints")

        except Exception as e:
            logger.error(f"Error parsing OpenAPI spec: {str(e)}")
            raise

        return endpoints

    def _generate_endpoint_content(
        self,
        method_info: Dict[str, Any],
        path: str,
        method: str
    ) -> str:
        """
        Generate human-readable content for an endpoint
        """
        content_parts = []

        content_parts.append(f"**Endpoint:** {method} {path}")

        if method_info.get('summary'):
            content_parts.append(f"**Summary:** {method_info['summary']}")

        if method_info.get('description'):
            content_parts.append(f"**Description:** {method_info['description']}")

        if method_info.get('parameters'):
            content_parts.append("**Parameters:**")
            for param in method_info['parameters']:
                param_desc = f"- `{param.get('name')}` ({param.get('in')})"
                if param.get('required'):
                    param_desc += " *required*"
                if param.get('description'):
                    param_desc += f": {param['description']}"
                content_parts.append(param_desc)

        if method_info.get('requestBody'):
            content_parts.append("**Request Body:**")
            req_body = method_info['requestBody']
            if 'description' in req_body:
                content_parts.append(req_body['description'])
            if 'content' in req_body:
                content_types = list(req_body['content'].keys())
                content_parts.append(f"Content-Types: {', '.join(content_types)}")

        if method_info.get('responses'):
            content_parts.append("**Responses:**")
            for code, response in method_info['responses'].items():
                resp_desc = f"- `{code}`: {response.get('description', 'No description')}"
                content_parts.append(resp_desc)

        if method_info.get('deprecated'):
            content_parts.append("⚠️ **DEPRECATED** - This endpoint is deprecated and may be removed in future versions.")

        return "\n\n".join(content_parts)

    # ===== EXISTING TOOL IMPLEMENTATIONS =====

    async def search_documentation(
        self,
        query: str,
        provider: str = "all",
        http_method: str = "all",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search API documentation (database-persisted providers)
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
                "source": "database",
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
        """Get complete details for a specific endpoint (database-persisted)"""
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
                "documentation_url": doc.documentation_url,
                "source": "database"
            }

        finally:
            db.close()

    async def list_providers(self) -> Dict[str, Any]:
        """List all available API providers (both database and cached)"""
        from app.db.database import SessionLocal
        from app.db.models import APIProvider, APIDocumentation

        db = SessionLocal()
        try:
            providers = db.query(APIProvider).filter(APIProvider.is_active == True).all()

            result = {
                "total_providers": len(providers) + len(self.openapi_cache),
                "providers": []
            }

            # Add database providers
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
                    "is_active": provider.is_active,
                    "source": "database"
                })

            # Add cached providers
            for provider_name, endpoints in self.openapi_cache.items():
                # Skip if already in DB
                if any(p.name == provider_name for p in providers):
                    continue

                result["providers"].append({
                    "name": provider_name,
                    "display_name": provider_name.title(),
                    "endpoint_count": len(endpoints),
                    "is_active": True,
                    "source": "in-memory cache",
                    "openapi_url": self.openapi_urls.get(provider_name, "unknown")
                })

            return result

        finally:
            db.close()


async def main():
    """Start MCP server"""
    server = APIDocumentationMCPServer()

    logger.info("Starting API Documentation MCP Server...")
    logger.info("Exposing: Resources (docs), Tools (search + dynamic OpenAPI loading), Prompts (templates)")

    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="api-documentation-server",
                server_version="2.1.0",
                capabilities=server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
