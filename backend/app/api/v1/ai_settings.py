"""
API endpoints for AI settings management
Admin panel can configure OpenAI settings dynamically
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.openai_mcp_client import _openai_mcp_client

logger = logging.getLogger(__name__)

router = APIRouter()


class AISettingsModel(BaseModel):
    """AI settings that can be updated from admin panel"""
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    system_prompt: Optional[str] = None
    enable_web_search: Optional[bool] = None


class APIKeyValidationResponse(BaseModel):
    """Response for API key validation"""
    valid: bool
    message: str
    model: Optional[str] = None
    organization: Optional[str] = None


@router.get("/ai/settings")
async def get_ai_settings():
    """Get current AI settings (masked API key)"""
    try:
        return {
            "openai_api_key_configured": bool(settings.openai_api_key),
            "openai_api_key_preview": f"{settings.openai_api_key[:10]}..." if settings.openai_api_key else None,
            "openai_model": settings.openai_model,
            "enable_web_search": settings.enable_web_search,
            "use_openai_agent": settings.use_openai_agent,
            "system_prompt": get_current_system_prompt()
        }
    except Exception as e:
        logger.error(f"Failed to get AI settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/settings")
async def update_ai_settings(ai_settings: AISettingsModel):
    """
    Update AI settings dynamically
    Admin panel uses this to configure OpenAI without restart
    """
    try:
        global _openai_mcp_client
        updated_fields = []

        # Update OpenAI API key
        if ai_settings.openai_api_key is not None:
            settings.openai_api_key = ai_settings.openai_api_key
            updated_fields.append("openai_api_key")

            # Reinitialize OpenAI client with new key
            if _openai_mcp_client:
                _openai_mcp_client.openai_client = AsyncOpenAI(api_key=ai_settings.openai_api_key)
                logger.info("OpenAI client reinitialized with new API key")

        # Update model
        if ai_settings.openai_model is not None:
            settings.openai_model = ai_settings.openai_model
            updated_fields.append("openai_model")

            if _openai_mcp_client:
                _openai_mcp_client.model = ai_settings.openai_model
                logger.info(f"OpenAI model updated to: {ai_settings.openai_model}")

        # Update system prompt
        if ai_settings.system_prompt is not None:
            update_system_prompt(ai_settings.system_prompt)
            updated_fields.append("system_prompt")

        # Update web search
        if ai_settings.enable_web_search is not None:
            settings.enable_web_search = ai_settings.enable_web_search
            updated_fields.append("enable_web_search")

        return {
            "status": "success",
            "message": f"Updated: {', '.join(updated_fields)}",
            "updated_fields": updated_fields
        }

    except Exception as e:
        logger.error(f"Failed to update AI settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class APIKeyRequest(BaseModel):
    """Request model for API key validation"""
    api_key: str


@router.post("/ai/validate-key", response_model=APIKeyValidationResponse)
async def validate_openai_key(request: APIKeyRequest):
    """
    Validate OpenAI API key
    Returns green/red status for admin panel
    """
    api_key = request.api_key
    try:
        # Try to make a simple API call
        test_client = AsyncOpenAI(api_key=api_key)

        # Test with a minimal completion request
        response = await test_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )

        return APIKeyValidationResponse(
            valid=True,
            message="API key is valid and working",
            model="gpt-4o-mini",
            organization=None  # OpenAI doesn't provide org in response
        )

    except Exception as e:
        error_message = str(e)

        if "invalid_api_key" in error_message.lower() or "incorrect api key" in error_message.lower():
            return APIKeyValidationResponse(
                valid=False,
                message="Invalid API key format or key doesn't exist"
            )
        elif "insufficient_quota" in error_message.lower():
            return APIKeyValidationResponse(
                valid=False,
                message="API key is valid but has insufficient quota/credits"
            )
        elif "rate_limit" in error_message.lower():
            return APIKeyValidationResponse(
                valid=True,  # Key is valid, just rate limited
                message="API key is valid (rate limit reached during test)"
            )
        else:
            return APIKeyValidationResponse(
                valid=False,
                message=f"Validation failed: {error_message[:100]}"
            )


@router.get("/ai/models")
async def get_available_models():
    """Get list of available OpenAI models"""
    return {
        "models": [
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "description": "Most capable model, best for complex tasks",
                "context_window": 128000,
                "cost_per_1m_tokens": {"input": 2.50, "output": 10.00}
            },
            {
                "id": "gpt-4o-mini",
                "name": "GPT-4o Mini",
                "description": "Fast and affordable, great for most tasks",
                "context_window": 128000,
                "cost_per_1m_tokens": {"input": 0.15, "output": 0.60}
            },
            {
                "id": "gpt-4-turbo",
                "name": "GPT-4 Turbo",
                "description": "Previous generation, still very capable",
                "context_window": 128000,
                "cost_per_1m_tokens": {"input": 10.00, "output": 30.00}
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Fastest and cheapest, good for simple tasks",
                "context_window": 16385,
                "cost_per_1m_tokens": {"input": 0.50, "output": 1.50}
            }
        ],
        "recommended": "gpt-4o-mini"
    }


def get_current_system_prompt() -> str:
    """Get current system prompt (would be stored in DB in production)"""
    # For now, return the default from openai_mcp_client
    return """You are an expert API documentation assistant specializing in Atlassian (Jira), Kubernetes, and Datadog APIs.

You have access to MCP tools that let you search and retrieve API documentation. Always use these tools to provide accurate, up-to-date information.

Available documentation:
- Atlassian/Jira Cloud REST API v3 (598 endpoints)
- Kubernetes API (1,062 endpoints)
- Datadog API (coming soon)

When answering questions:
1. Use search_documentation to find relevant endpoints
2. Use get_endpoint_details for complete information
3. Provide clear, practical answers with:
   - HTTP method and endpoint path
   - Required authentication
   - Request parameters/body
   - Expected response
   - Code example (Python, cURL, or JavaScript)

Be conversational but precise. Focus on helping developers use the APIs effectively."""


def update_system_prompt(new_prompt: str):
    """Update system prompt (would save to DB in production)"""
    # For now, update the client instance
    global _openai_mcp_client
    if _openai_mcp_client:
        _openai_mcp_client.system_prompt = new_prompt
        logger.info("System prompt updated")
