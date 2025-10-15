"""
AI Agent using OpenAI + MCP
Proper MCP protocol: OpenAI discovers MCP tools and uses them for search
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.openai_mcp_client import OpenAIMCPClient, get_openai_mcp_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIAgentWithOpenAIMCP:
    """
    AI Agent that uses OpenAI with MCP protocol

    Flow:
    1. User asks a question
    2. OpenAI+MCP Client handles everything:
       - OpenAI understands the question
       - OpenAI decides which MCP tool to call
       - OpenAI calls MCP tool to search documentation
       - OpenAI generates natural language response
    3. Return response to user
    """

    def __init__(self):
        self.openai_mcp_client: Optional[OpenAIMCPClient] = None
        self.session_conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.agent_id = str(uuid.uuid4())

    async def initialize(self) -> bool:
        """Initialize OpenAI+MCP client"""
        try:
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured - AI agent will not work")
                return False

            self.openai_mcp_client = await get_openai_mcp_client()
            logger.info("AI Agent initialized with OpenAI + MCP")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {str(e)}")
            return False

    async def process_user_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user query using OpenAI + MCP

        This is the main entry point. OpenAI handles:
        - Understanding the question
        - Deciding what to search
        - Calling MCP tools
        - Generating the response
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())

            # Initialize session if new
            if session_id not in self.session_conversations:
                self.session_conversations[session_id] = []

            # Get conversation history
            conversation_history = self.session_conversations[session_id]

            # Ensure OpenAI is configured; if not, try to initialize on-demand
            if not self.openai_mcp_client:
                if getattr(settings, 'openai_api_key', None):
                    try:
                        init_ok = await self.initialize()
                        logger.info(f"On-demand AI initialization result: {init_ok}")
                    except Exception as init_err:
                        logger.error(f"On-demand AI initialization failed: {str(init_err)}")
                # If still not initialized, return fallback
                if not self.openai_mcp_client:
                    return await self._fallback_response(query, session_id)

            # Add user message to history
            conversation_history.append({
                "role": "user",
                "content": query
            })

            # Let OpenAI + MCP handle everything
            logger.info(f"Processing query with OpenAI+MCP: {query}")
            response = await self.openai_mcp_client.chat(
                messages=conversation_history,
                temperature=0.7,
                max_tokens=3000
            )

            # Add assistant response to history
            conversation_history.append({
                "role": "assistant",
                "content": response["content"]
            })

            # Trim history if too long (keep last 20 messages)
            if len(conversation_history) > 20:
                # Keep system prompt + last 18 messages
                self.session_conversations[session_id] = [conversation_history[0]] + conversation_history[-18:]

            logger.info(f"OpenAI used {len(response.get('tools_used', []))} MCP tools")
            logger.info(f"Token usage: {response.get('usage', {}).get('total_tokens', 0)} tokens")

            return {
                "query": query,
                "response": response["content"],
                "session_id": session_id,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "tools_used": response.get("tools_used", []),
                    "tokens": response.get("usage", {}),
                    "finish_reason": response.get("finish_reason"),
                    "model": self.openai_mcp_client.model if self.openai_mcp_client else None
                }
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "error": str(e),
                "query": query,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _fallback_response(self, query: str, session_id: str) -> Dict[str, Any]:
        """Fallback response when OpenAI is not configured"""
        return {
            "query": query,
            "response": (
                "I'm sorry, but I'm not configured with OpenAI access yet. "
                "To enable AI-powered responses:\n\n"
                "1. Set your OPENAI_API_KEY environment variable\n"
                "2. Restart the backend service\n\n"
                "For now, you can use the search API directly at /api/v1/search"
            ),
            "session_id": session_id,
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "fallback": True
        }

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        conversation = self.session_conversations.get(session_id, [])
        return conversation[-limit:]

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        conversation = self.session_conversations.get(session_id, [])
        return {
            "session_id": session_id,
            "message_count": len(conversation),
            "created_at": datetime.utcnow().isoformat() if conversation else None
        }

    def clear_conversation_history(self, session_id: Optional[str] = None):
        """Clear conversation history"""
        if session_id:
            if session_id in self.session_conversations:
                del self.session_conversations[session_id]
        else:
            self.session_conversations.clear()

    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and statistics"""
        return {
            "agent_id": self.agent_id,
            "openai_configured": self.openai_mcp_client is not None,
            "mcp_connected": self.openai_mcp_client is not None,
            "total_sessions": len(self.session_conversations),
            "total_messages": sum(len(conv) for conv in self.session_conversations.values()),
            "uptime": datetime.utcnow().isoformat(),
            "model": self.openai_mcp_client.model if self.openai_mcp_client else None
        }
