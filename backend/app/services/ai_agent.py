"""
AI Agent Service for generating intelligent API documentation responses
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.search.elasticsearch_client import search_documentation
from app.schemas import SearchRequest
from app.db.models import APIProvider

logger = logging.getLogger(__name__)


class APIAgent:
    """Intelligent API documentation agent"""
    
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found, agent will use mock responses")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
    
    async def analyze_request(self, user_request: str, provider_name: str = None) -> Dict[str, Any]:
        """
        Analyze user request and generate comprehensive API documentation response
        
        Args:
            user_request: User's natural language request
            provider_name: Optional specific API provider to focus on
            
        Returns:
            Dict containing structured response with examples and troubleshooting
        """
        
        # Search for relevant documentation
        relevant_docs = await self._search_relevant_docs(user_request, provider_name)
        
        # Generate AI response if OpenAI is available
        if self.client:
            response = await self._generate_ai_response(user_request, relevant_docs, provider_name)
        else:
            response = self._generate_mock_response(user_request, relevant_docs, provider_name)
        
        return response
    
    async def _search_relevant_docs(self, query: str, provider_name: str = None) -> List[Dict]:
        """Search for relevant documentation using Elasticsearch"""
        try:
            # Create search request
            search_request = SearchRequest(
                query=query,
                limit=5,  # Get top 5 most relevant results
                provider_ids=None  # We'll filter by provider name if specified
            )
            
            # Perform search
            search_response = await search_documentation(search_request)
            
            # Filter by provider if specified
            relevant_results = []
            for result in search_response.results:
                if provider_name and result.provider.name.lower() != provider_name.lower():
                    continue
                
                relevant_results.append({
                    "title": result.title,
                    "description": result.description,
                    "endpoint": result.endpoint_path,
                    "method": result.http_method.value,
                    "provider": result.provider.name,
                    "score": result.score
                })
            
            return relevant_results
            
        except Exception as e:
            logger.error(f"Error searching documentation: {e}")
            return []
    
    async def _generate_ai_response(self, user_request: str, docs: List[Dict], provider_name: str = None) -> Dict[str, Any]:
        """Generate AI response using OpenAI"""
        
        # Prepare context from documentation
        context = self._prepare_context(docs, provider_name)
        
        # Create system prompt
        system_prompt = """You are an expert API documentation assistant. Given a user's request and relevant API documentation, provide a comprehensive response with:

1. **Endpoint**: The exact API endpoint to use
2. **Method**: HTTP method (GET, POST, PUT, DELETE, etc.)
3. **cURL Example**: Complete working cURL command
4. **Python Example**: Complete Python code using requests library
5. **Troubleshooting**: Common issues and solutions
6. **Related**: Related operations the user might need

Format your response as JSON with these exact keys:
- endpoint
- method  
- description
- curl_example
- python_example
- troubleshooting (array of strings)
- related_operations (array of strings)

Be precise, practical, and include real working examples."""

        user_prompt = f"""
User Request: {user_request}

Available API Documentation:
{context}

Provider Focus: {provider_name or "Any"}

Generate a comprehensive response following the JSON format specified.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent responses
                max_tokens=2000
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            
            # Remove code block markers if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            result = json.loads(content)
            
            # Add metadata
            result["agent_type"] = "ai_generated"
            result["confidence"] = "high" if docs else "low"
            result["sources"] = len(docs)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_mock_response(user_request, docs, provider_name)
    
    def _generate_mock_response(self, user_request: str, docs: List[Dict], provider_name: str = None) -> Dict[str, Any]:
        """Generate mock response when OpenAI is not available"""
        
        # Try to find the most relevant doc
        best_doc = docs[0] if docs else None
        
        if best_doc and "jira" in user_request.lower():
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
                "agent_type": "mock_generated",
                "confidence": "medium",
                "sources": len(docs)
            }
        
        # Generic response for other requests
        return {
            "endpoint": f"{best_doc['method'] + ' ' + best_doc['endpoint'] if best_doc else 'API endpoint not found'}",
            "method": best_doc['method'] if best_doc else "GET",
            "description": f"API operation for: {user_request}",
            "curl_example": "# API documentation needed - please add documentation for this provider",
            "python_example": "# API documentation needed - please add documentation for this provider",
            "troubleshooting": [
                "Check API documentation",
                "Verify authentication",
                "Check API endpoint URL"
            ],
            "related_operations": [
                "Check API documentation",
                "View available endpoints"
            ],
            "agent_type": "mock_generated",
            "confidence": "low",
            "sources": len(docs)
        }
    
    def _prepare_context(self, docs: List[Dict], provider_name: str = None) -> str:
        """Prepare documentation context for AI prompt"""
        if not docs:
            return "No relevant documentation found."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"""
Document {i}:
- Title: {doc['title']}
- Description: {doc['description']}
- Endpoint: {doc['method']} {doc['endpoint']}
- Provider: {doc['provider']}
- Relevance Score: {doc['score']:.2f}
""")
        
        return "\n".join(context_parts)


# Global agent instance
agent = APIAgent()


async def get_agent_response(user_request: str, provider_name: str = None, db: Session = None) -> Dict[str, Any]:
    """
    Main function to get agent response for user request
    
    Args:
        user_request: User's natural language request
        provider_name: Optional API provider name
        db: Database session (for future use)
        
    Returns:
        Structured agent response
    """
    return await agent.analyze_request(user_request, provider_name)