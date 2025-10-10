"""
Mock AI Agent Service for fast testing without OpenAI dependency
"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class APIAgent:
    """Mock AI documentation agent for testing"""

    def __init__(self):
        logger.info("Mock AI Agent initialized (no OpenAI dependency)")
    
    async def analyze_request(self, user_request: str, provider_name: str = None) -> Dict[str, Any]:
        """Mock analyze request - returns simple responses"""
        return self._generate_mock_response(user_request, provider_name)

    def _generate_mock_response(self, user_request: str, provider_name: str = None) -> Dict[str, Any]:
        """Generate mock response based on keywords"""

        query_lower = user_request.lower()

        if "jira" in query_lower or "issue" in query_lower:
            return {
                "endpoint": "POST /rest/api/3/issue",
                "method": "POST",
                "description": "Create a new issue in Jira",
                "curl_example": '''curl -X POST \\
  -H "Authorization: Basic YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "fields": {
      "project": {"key": "TEST"},
      "summary": "New issue",
      "description": "Issue description",
      "issuetype": {"name": "Task"}
    }
  }' \\
  https://your-domain.atlassian.net/rest/api/3/issue''',
                "python_example": '''import requests
import base64

# Encode credentials
credentials = base64.b64encode(b"email:api_token").decode()

headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

data = {
    "fields": {
        "project": {"key": "TEST"},
        "summary": "New issue",
        "description": "Issue description", 
        "issuetype": {"name": "Task"}
    }
}

response = requests.post(
    "https://your-domain.atlassian.net/rest/api/3/issue",
    headers=headers,
    json=data
)

print(response.json())''',
                "troubleshooting": [
                    "Check API token permissions",
                    "Verify project key exists",
                    "Ensure issue type is valid",
                    "Check domain URL format"
                ],
                "related_operations": [
                    "Update issue",
                    "Add comment to issue",
                    "Assign issue to user",
                    "Get issue details"
                ],
                "agent_type": "mock",
                "confidence": "medium"
            }

        # Kubernetes
        if "kubernetes" in query_lower or "pod" in query_lower:
            return {
                "endpoint": "GET /api/v1/namespaces/{namespace}/pods",
                "method": "GET",
                "description": "List pods in a namespace",
                "response": "To list Kubernetes pods, use the GET /api/v1/namespaces/{namespace}/pods endpoint.",
                "agent_type": "mock",
                "confidence": "medium"
            }

        # Generic response
        return {
            "endpoint": "API endpoint",
            "method": "GET",
            "description": f"Mock response for: {user_request}",
            "response": f"I can help with API documentation! Your query: '{user_request}'",
            "agent_type": "mock",
            "confidence": "low"
        }


# Global agent instance
agent = APIAgent()


async def get_agent_response(user_request: str, provider_name: str = None, db: Session = None) -> Dict[str, Any]:
    """Mock get agent response"""
    return await agent.analyze_request(user_request, provider_name)