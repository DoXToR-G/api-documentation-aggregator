"""
OpenAI Client integrated with MCP
OpenAI discovers and uses MCP tools for searching documentation
"""

from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import logging
import json
from app.core.config import settings
from app.mcp.server_redesign import APIDocumentationMCPServer

logger = logging.getLogger(__name__)


class OpenAIMCPClient:
    """
    OpenAI client that uses MCP for documentation access

    Flow:
    1. Initialize OpenAI + MCP server
    2. Discovery: Get available MCP tools
    3. Convert MCP tools to OpenAI function format
    4. When OpenAI calls a function → execute MCP tool
    5. Return results to OpenAI
    """

    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = getattr(settings, 'openai_model', 'gpt-4o-mini')
        self.mcp_server = APIDocumentationMCPServer()

        # System prompt for Atlassian/API documentation expert
        self.system_prompt = """You are an expert API documentation assistant specializing in Atlassian (Jira), Kubernetes, Datadog, and any OpenAPI-documented APIs.

You have access to MCP tools that let you search and retrieve API documentation. Always use these tools to provide accurate, up-to-date information.

Available documentation sources:
1. **Database-persisted providers** (use search_documentation):
   - Atlassian/Jira Cloud REST API v3 (598 endpoints)
   - Kubernetes API (1,062 endpoints)
   - Datadog API (if configured)

2. **Dynamic OpenAPI loading** (use load_openapi):
   - You can load ANY OpenAPI specification from a URL at runtime
   - The documentation will be cached in memory during the session
   - No database persistence needed - perfect for ad-hoc exploration

Available MCP tools:
- **load_openapi(provider, url)**: Load OpenAPI spec from a URL and cache it in memory
- **search_openapi(provider, query, http_method?, limit?)**: Search loaded OpenAPI endpoints
- **get_openapi_endpoint_details(provider, id)**: Get full details for a cached endpoint
- **search_documentation(query, provider?, http_method?, limit?)**: Search database-persisted docs
- **get_endpoint_details(endpoint_id)**: Get details for database-persisted endpoint
- **list_providers()**: List all available providers (both database and cached)

Workflow for dynamic OpenAPI loading:
1. If user provides an OpenAPI URL, use load_openapi first
2. Then use search_openapi to explore the loaded documentation
3. Use get_openapi_endpoint_details for specific endpoint information

When answering questions:
1. Determine if you need to load new documentation or use existing providers
2. Use appropriate search tools (search_openapi for cached, search_documentation for database)
3. Get detailed information when needed
4. Provide clear, practical answers with:
   - HTTP method and endpoint path
   - Required authentication
   - Request parameters/body
   - Expected response
   - Code example (Python, cURL, or JavaScript)

Be conversational but precise. Focus on helping developers use the APIs effectively.
When users mention "bring your own OpenAPI URL" or provide a URL to an OpenAPI spec, use load_openapi to dynamically load it."""

    async def initialize(self) -> bool:
        """Initialize and verify MCP connection"""
        try:
            # Get available MCP tools
            tools = await self.mcp_server.server._tool_manager.list_tools()
            logger.info(f"MCP tools available: {len(tools)}")

            # Get available MCP resources
            # resources = await self.mcp_server.server._resource_manager.list_resources()
            # logger.info(f"MCP resources available: {len(resources)}")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {str(e)}")
            return False

    async def get_mcp_tools_as_openai_functions(self) -> List[Dict[str, Any]]:
        """
        Convert MCP tools to OpenAI function format

        MCP Tool → OpenAI Function
        """
        try:
            # Get tools from MCP server
            mcp_tools = await self.mcp_server.server._tool_manager.list_tools()

            openai_functions = []
            for tool in mcp_tools:
                openai_functions.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            return openai_functions

        except Exception as e:
            logger.error(f"Error converting MCP tools: {str(e)}")
            return []

    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute MCP tool and return results

        This is called when OpenAI requests a function call
        """
        try:
            logger.info(f"Executing MCP tool: {tool_name} with args: {arguments}")

            # Call MCP tool
            results = await self.mcp_server.server._tool_manager.call_tool(
                tool_name,
                arguments
            )

            # Extract text content from MCP response
            if results and len(results) > 0:
                return results[0].text

            return json.dumps({"error": "No results from MCP tool"})

        except Exception as e:
            logger.error(f"MCP tool execution error: {str(e)}")
            return json.dumps({"error": str(e)})

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 3000
    ) -> Dict[str, Any]:
        """
        Send chat request to OpenAI with MCP tools

        Flow:
        1. Add system prompt if not present
        2. Get MCP tools as OpenAI functions
        3. Send to OpenAI
        4. If OpenAI calls a function:
           - Execute MCP tool
           - Send results back to OpenAI
           - Get final response
        5. Return response
        """
        try:
            # Ensure system prompt is first
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {
                    "role": "system",
                    "content": self.system_prompt
                })

            # Get MCP tools as OpenAI functions
            functions = await self.get_mcp_tools_as_openai_functions()
            logger.info(f"Using {len(functions)} MCP tools as OpenAI functions")

            # First OpenAI call
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=functions if functions else None,
                tool_choice="auto" if functions else None,
                temperature=temperature,
                max_tokens=max_tokens
            )

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # Track tokens
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            # Check if OpenAI wants to call a tool
            if finish_reason == "tool_calls" and message.tool_calls:
                logger.info(f"OpenAI requesting {len(message.tool_calls)} tool calls")

                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })

                # Execute each tool call
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"Executing: {function_name}({function_args})")

                    # Execute MCP tool
                    tool_result = await self.execute_mcp_tool(function_name, function_args)

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": tool_result
                    })

                # Second OpenAI call with tool results
                logger.info("Sending tool results back to OpenAI for final response")
                final_response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                final_message = final_response.choices[0].message

                # Update usage
                usage["prompt_tokens"] += final_response.usage.prompt_tokens
                usage["completion_tokens"] += final_response.usage.completion_tokens
                usage["total_tokens"] += final_response.usage.total_tokens

                return {
                    "content": final_message.content,
                    "role": "assistant",
                    "usage": usage,
                    "tools_used": [tc.function.name for tc in message.tool_calls],
                    "finish_reason": final_response.choices[0].finish_reason
                }

            # No tool calls, return direct response
            return {
                "content": message.content,
                "role": "assistant",
                "usage": usage,
                "tools_used": [],
                "finish_reason": finish_reason
            }

        except Exception as e:
            logger.error(f"OpenAI chat error: {str(e)}")
            raise

    async def process_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query using OpenAI + MCP

        High-level method for simple queries
        """
        messages = conversation_history or []
        messages.append({
            "role": "user",
            "content": query
        })

        response = await self.chat(messages)

        return {
            "query": query,
            "answer": response["content"],
            "usage": response["usage"],
            "tools_used": response["tools_used"]
        }


# Global instance
_openai_mcp_client = None


async def get_openai_mcp_client() -> OpenAIMCPClient:
    """Get or create OpenAI MCP client instance"""
    global _openai_mcp_client

    if _openai_mcp_client is None:
        _openai_mcp_client = OpenAIMCPClient()
        await _openai_mcp_client.initialize()

    return _openai_mcp_client
