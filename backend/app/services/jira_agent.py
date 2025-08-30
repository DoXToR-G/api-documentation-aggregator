"""
Specialized Jira API Documentation Agent
Acts as an intelligent documentation helper for Jira Cloud REST API
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


class JiraAgent:
    """Specialized agent for Jira Cloud API documentation"""
    
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found, agent will use mock responses")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
    
    async def help_with_jira(self, user_request: str) -> Dict[str, Any]:
        """
        Help users with Jira API operations
        
        Args:
            user_request: User's question about Jira API
            
        Returns:
            Structured response with Jira-specific guidance
        """
        
        # Search for relevant Jira documentation
        jira_docs = await self._search_jira_docs(user_request)
        
        # Generate response based on documentation
        if self.client:
            response = await self._generate_ai_response(user_request, jira_docs)
        else:
            response = self._generate_jira_response(user_request, jira_docs)
        
        return response
    
    async def _search_jira_docs(self, query: str) -> List[Dict]:
        """Search specifically for Jira documentation"""
        try:
            # Create search request focused on Jira
            # Don't add "jira" prefix as it may interfere with specific searches
            search_request = SearchRequest(
                query=query,  # Use original query for better matching
                limit=10,  # Get more results for better context
                provider_ids=[2]  # Jira Cloud provider ID - this already filters to Jira
            )
            
            # Perform search
            search_response = await search_documentation(search_request)
            
            # Convert to simplified format
            docs = []
            for result in search_response.results:
                docs.append({
                    "title": result.title,
                    "description": result.description,
                    "endpoint": result.endpoint_path,
                    "method": result.http_method.value,
                    "content": getattr(result, 'content', ''),
                    "score": result.score
                })
            
            return docs
            
        except Exception as e:
            logger.error(f"Error searching Jira documentation: {e}")
            return []
    
    async def _generate_ai_response(self, user_request: str, docs: List[Dict]) -> Dict[str, Any]:
        """Generate AI response using OpenAI with Jira focus"""
        
        # Prepare Jira-specific context
        context = self._prepare_jira_context(docs)
        
        system_prompt = """You are a Jira Cloud REST API documentation expert. 
Your job is to help developers use the Jira API effectively.

Given a user's question about Jira and relevant API documentation, provide:

1. **Endpoint**: The exact Jira REST API endpoint
2. **Method**: HTTP method (GET, POST, PUT, DELETE)
3. **Description**: Clear explanation of what this does in Jira
4. **Authentication**: Jira authentication requirements
5. **cURL Example**: Complete working cURL command for Jira Cloud
6. **Python Example**: Complete Python code using requests library
7. **Common Issues**: Jira-specific troubleshooting tips
8. **Related Operations**: Other Jira operations the user might need

Format as JSON with these keys:
- endpoint, method, description, authentication
- curl_example, python_example  
- common_issues (array), related_operations (array)

Focus specifically on Jira Cloud REST API v3. Include Jira-specific details like:
- Project keys, issue types, fields
- Jira permissions and user management
- Atlassian account IDs vs usernames
- JQL (Jira Query Language) where relevant"""

        user_prompt = f"""
User Question: {user_request}

Available Jira API Documentation:
{context}

Provide a comprehensive Jira API response in JSON format.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Very low for consistent API documentation
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
            result["agent_type"] = "jira_ai_generated"
            result["confidence"] = "high" if docs else "medium"
            result["jira_docs_found"] = len(docs)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_jira_response(user_request, docs)
    
    def _generate_jira_response(self, user_request: str, docs: List[Dict]) -> Dict[str, Any]:
        """Generate Jira-specific mock response when OpenAI is not available"""
        
        # If we have search results, determine if this is a broad query or category query
        if docs:
            request_lower = user_request.lower()
            
            # Detect category queries (single word categories)
            category_keywords = ['issues', 'projects', 'comments', 'dashboards', 'users', 'groups', 'workflows', 'search', 'apps', 'fields']
            is_category_query = any(keyword in request_lower for keyword in category_keywords) and len(request_lower.split()) <= 2
            
            # Detect broad operation queries
            broad_query_keywords = ['create', 'update', 'delete', 'get', 'list', 'manage']
            is_broad_query = any(keyword in request_lower for keyword in broad_query_keywords) and len(request_lower.split()) <= 3
            
            if is_category_query and len(docs) > 1:
                # For category queries, group operations by type
                category = next((keyword for keyword in category_keywords if keyword in request_lower), 'operations')
                
                # Group operations by HTTP method and type
                operations_by_type = {}
                for doc in docs[:20]:  # Limit to top 20 results
                    title = doc['title']
                    method = doc['method']
                    endpoint = doc['endpoint']
                    
                    # Categorize operations
                    if 'create' in title.lower() or method == 'POST':
                        op_type = 'Create Operations'
                    elif 'update' in title.lower() or 'edit' in title.lower() or method in ['PUT', 'PATCH']:
                        op_type = 'Update Operations'
                    elif 'delete' in title.lower() or 'remove' in title.lower() or method == 'DELETE':
                        op_type = 'Delete Operations'
                    elif 'get' in title.lower() or 'search' in title.lower() or 'list' in title.lower() or method == 'GET':
                        op_type = 'Get/Search Operations'
                    else:
                        op_type = 'Other Operations'
                    
                    if op_type not in operations_by_type:
                        operations_by_type[op_type] = []
                    
                    operations_by_type[op_type].append({
                        'title': title,
                        'method': method,
                        'endpoint': endpoint,
                        'description': doc['description'][:100] + '...' if len(doc['description']) > 100 else doc['description']
                    })
                
                # Build organized response
                primary_doc = docs[0]
                
                # Create formatted operations list
                formatted_operations = []
                for op_type, operations in operations_by_type.items():
                    formatted_operations.append(f"\n=== {op_type} ===")
                    for op in operations[:5]:  # Limit to 5 per type
                        formatted_operations.append(f"• {op['method']} {op['endpoint']} - {op['title']}")
                
                return {
                    "endpoint": f"{category.title()} Category Operations",
                    "method": "Various",
                    "description": f"Complete {category} operations available in Jira API. Found {len(docs)} related endpoints organized by operation type. Click on any related operation below for specific examples.",
                    "authentication": "Basic Auth (email:api_token) or OAuth 2.0",
                    "curl_example": f'''# {category.title()} Operations Available:
# Example: {primary_doc['title']}

curl -X {primary_doc['method']} \\
  -H "Authorization: Basic $(echo -n 'your-email@domain.com:your-api-token' | base64)" \\
  -H "Content-Type: application/json" \\
  https://your-domain.atlassian.net{primary_doc['endpoint']}

# See organized operations below - click any operation for specific examples''',
                    "python_example": f'''# {category.title()} Operations Available
# Example: {primary_doc['title']}

import requests
import base64

# Jira Cloud authentication
email = "your-email@domain.com"
api_token = "your-api-token"
jira_url = "https://your-domain.atlassian.net"

credentials = base64.b64encode(f"{{email}}:{{api_token}}".encode()).decode()
headers = {{
    "Authorization": f"Basic {{credentials}}",
    "Content-Type": "application/json"
}}

# Example: {primary_doc['title']}
response = requests.{primary_doc['method'].lower()}(
    f"{{jira_url}}{primary_doc['endpoint']}",
    headers=headers
)

print(f"Response: {{response.status_code}} - {{response.json()}}")

# Check organized operations below for more {category} examples''',
                    "common_issues": [
                        f"Choose the specific {category} operation for your use case",
                        "Check API token from Atlassian Account Settings > Security > API tokens",
                        "Verify your Jira Cloud URL format (subdomain.atlassian.net)", 
                        "Ensure you have proper permissions for the specific operation",
                        "Review the endpoint documentation for required parameters"
                    ],
                    "related_operations": [f"{doc['method']} {doc['endpoint']} - {doc['title']}" for doc in docs[:15]],
                    "agent_type": "jira_category_explorer",
                    "confidence": "high",
                    "jira_docs_found": len(docs)
                }
            elif is_broad_query and len(docs) > 1:
                # For broad queries, provide overview with multiple options
                primary_doc = docs[0]
                operation_type = next((keyword for keyword in broad_query_keywords if keyword in request_lower), 'operation')
                
                # Group related operations by method
                method_groups = {}
                for doc in docs[:8]:  # Limit to top 8 results
                    method = doc['method']
                    if method not in method_groups:
                        method_groups[method] = []
                    method_groups[method].append(f"{doc['title']} - {doc['endpoint']}")
                
                # Build overview description
                overview_desc = f"Multiple {operation_type} operations available in Jira API. "
                overview_desc += f"Found {len(docs)} related endpoints. "
                overview_desc += "Select from the related operations below for specific examples."
                
                return {
                    "endpoint": f"Multiple {operation_type.upper()} operations",
                    "method": "Various",
                    "description": overview_desc,
                    "authentication": "Basic Auth (email:api_token) or OAuth 2.0",
                    "curl_example": f'''# Multiple {operation_type} operations available:
# {primary_doc['title']} - {primary_doc['method']} {primary_doc['endpoint']}

curl -X {primary_doc['method']} \\
  -H "Authorization: Basic $(echo -n 'your-email@domain.com:your-api-token' | base64)" \\
  -H "Content-Type: application/json" \\
  https://your-domain.atlassian.net{primary_doc['endpoint']}

# See related operations below for more {operation_type} options''',
                    "python_example": f'''# Multiple {operation_type} operations available
# Example: {primary_doc['title']}

import requests
import base64

# Jira Cloud authentication
email = "your-email@domain.com"
api_token = "your-api-token"
jira_url = "https://your-domain.atlassian.net"

credentials = base64.b64encode(f"{{email}}:{{api_token}}".encode()).decode()
headers = {{
    "Authorization": f"Basic {{credentials}}",
    "Content-Type": "application/json"
}}

# Example: {primary_doc['title']}
response = requests.{primary_doc['method'].lower()}(
    f"{{jira_url}}{primary_doc['endpoint']}",
    headers=headers
)

print(f"Response: {{response.status_code}} - {{response.json()}}")

# Check related operations below for more {operation_type} examples''',
                    "common_issues": [
                        f"Choose the right {operation_type} operation for your use case",
                        "Check API token from Atlassian Account Settings > Security > API tokens",
                        "Verify your Jira Cloud URL format (subdomain.atlassian.net)", 
                        "Ensure you have proper permissions for the specific operation",
                        "Check the endpoint path and HTTP method for each operation"
                    ],
                    "related_operations": [f"{doc['method']} {doc['endpoint']} - {doc['title']}" for doc in docs[:10]],
                    "agent_type": "jira_multi_search",
                    "confidence": "high",
                    "jira_docs_found": len(docs)
                }
            else:
                # For specific queries, return single best match
                best_doc = docs[0]
                return {
                    "endpoint": f"{best_doc['method']} {best_doc['endpoint']}",
                    "method": best_doc['method'],
                    "description": best_doc['description'],
                    "authentication": "Basic Auth (email:api_token) or OAuth 2.0",
                    "curl_example": f'''curl -X {best_doc['method']} \\
  -H "Authorization: Basic $(echo -n 'your-email@domain.com:your-api-token' | base64)" \\
  -H "Content-Type: application/json" \\
  https://your-domain.atlassian.net{best_doc['endpoint']}''',
                    "python_example": f'''import requests
import base64

# Jira Cloud authentication
email = "your-email@domain.com"
api_token = "your-api-token"  # From Atlassian Account Settings
jira_url = "https://your-domain.atlassian.net"

credentials = base64.b64encode(f"{{email}}:{{api_token}}".encode()).decode()
headers = {{
    "Authorization": f"Basic {{credentials}}",
    "Content-Type": "application/json"
}}

# API call
response = requests.{best_doc['method'].lower()}(
    f"{{jira_url}}{best_doc['endpoint']}",
    headers=headers
)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print(f"Error: {{response.status_code}} - {{response.text}}")''',
                    "common_issues": [
                        "Check API token from Atlassian Account Settings > Security > API tokens",
                        "Verify your Jira Cloud URL format (subdomain.atlassian.net)", 
                        "Ensure you have proper permissions for this operation",
                        "Check the endpoint path and parameters are correct",
                        "Verify the HTTP method is supported"
                    ],
                    "related_operations": [f"{doc['method']} {doc['endpoint']} - {doc['title']}" for doc in docs[1:6]],
                    "agent_type": "jira_search_generated",
                    "confidence": "high",
                    "jira_docs_found": len(docs)
                }
        
        # Fallback to hardcoded responses when no search results
        request_lower = user_request.lower()
        
        # Create issue
        if any(word in request_lower for word in ["create", "new", "add"]) and "issue" in request_lower:
            return {
                "endpoint": "POST /rest/api/3/issue",
                "method": "POST",
                "description": "Creates a new issue in a Jira project",
                "authentication": "Basic Auth (email:api_token) or Bearer token",
                "curl_example": '''curl -X POST \\
  -H "Authorization: Basic $(echo -n 'your-email@domain.com:your-api-token' | base64)" \\
  -H "Content-Type: application/json" \\
  -d '{
    "fields": {
      "project": {"key": "PROJ"},
      "summary": "Issue summary",
      "description": "Issue description",
      "issuetype": {"name": "Task"},
      "assignee": {"accountId": "5b10a2844c20165700ede21g"}
    }
  }' \\
  https://your-domain.atlassian.net/rest/api/3/issue''',
                "python_example": '''import requests
import base64

# Jira Cloud credentials
email = "your-email@domain.com"
api_token = "your-api-token"
jira_url = "https://your-domain.atlassian.net"

# Encode credentials
credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()

headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

issue_data = {
    "fields": {
        "project": {"key": "PROJ"},
        "summary": "New issue from API",
        "description": "Issue created via REST API",
        "issuetype": {"name": "Task"}
    }
}

response = requests.post(
    f"{jira_url}/rest/api/3/issue",
    headers=headers,
    json=issue_data
)

if response.status_code == 201:
    issue = response.json()
    print(f"Created issue: {issue['key']}")
else:
    print(f"Error: {response.status_code} - {response.text}")''',
                "common_issues": [
                    "Invalid project key - verify project exists and you have access",
                    "Missing required fields - check project's issue type configuration",
                    "Authentication failed - verify email and API token",
                    "Permission denied - ensure you can create issues in the project",
                    "Invalid assignee accountId - use Jira user's accountId, not username"
                ],
                "related_operations": [
                    "Update issue - PUT /rest/api/3/issue/{issueIdOrKey}",
                    "Add comment - POST /rest/api/3/issue/{issueIdOrKey}/comment",
                    "Assign issue - PUT /rest/api/3/issue/{issueIdOrKey}/assignee",
                    "Get issue - GET /rest/api/3/issue/{issueIdOrKey}",
                    "Search issues - GET /rest/api/3/search"
                ],
                "agent_type": "jira_mock_generated",
                "confidence": "high",
                "jira_docs_found": len(docs)
            }
        
        # Get/Search issues
        elif any(word in request_lower for word in ["get", "find", "search", "list"]) and "issue" in request_lower:
            return {
                "endpoint": "GET /rest/api/3/search",
                "method": "GET", 
                "description": "Search for issues using JQL (Jira Query Language)",
                "authentication": "Basic Auth (email:api_token) or Bearer token",
                "curl_example": '''curl -X GET \\
  -H "Authorization: Basic $(echo -n 'your-email@domain.com:your-api-token' | base64)" \\
  "https://your-domain.atlassian.net/rest/api/3/search?jql=project=PROJ AND assignee=currentUser()"''',
                "python_example": '''import requests
import base64

# Jira Cloud credentials  
email = "your-email@domain.com"
api_token = "your-api-token"
jira_url = "https://your-domain.atlassian.net"

credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()

headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

# JQL query examples
jql_queries = [
    "project = PROJ",  # All issues in project
    "assignee = currentUser()",  # My issues
    "status = 'To Do'",  # Open issues
    "created >= -7d",  # Created in last 7 days
    "project = PROJ AND status != Done"  # Active issues
]

for jql in jql_queries:
    response = requests.get(
        f"{jira_url}/rest/api/3/search",
        headers=headers,
        params={"jql": jql, "maxResults": 50}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['total']} issues for: {jql}")
        for issue in data['issues']:
            print(f"  {issue['key']}: {issue['fields']['summary']}")
    else:
        print(f"Error: {response.status_code}")''',
                "common_issues": [
                    "Invalid JQL syntax - check Jira Query Language documentation",
                    "Permission denied - ensure you can view the project/issues",
                    "Field not found - verify custom field names and IDs",
                    "Too many results - add pagination or limit with maxResults",
                    "Invalid project key - check project exists and is accessible"
                ],
                "related_operations": [
                    "Get specific issue - GET /rest/api/3/issue/{issueIdOrKey}",
                    "Get issue transitions - GET /rest/api/3/issue/{issueIdOrKey}/transitions",
                    "Get issue comments - GET /rest/api/3/issue/{issueIdOrKey}/comment",
                    "Get project issues - GET /rest/api/3/search?jql=project=KEY",
                    "Advanced search with fields - POST /rest/api/3/search"
                ],
                "agent_type": "jira_mock_generated",
                "confidence": "high",
                "jira_docs_found": len(docs)
            }
        
        # Update issue
        elif any(word in request_lower for word in ["update", "edit", "modify"]) and "issue" in request_lower:
            return {
                "endpoint": "PUT /rest/api/3/issue/{issueIdOrKey}",
                "method": "PUT",
                "description": "Updates an existing Jira issue",
                "authentication": "Basic Auth (email:api_token) or Bearer token",
                "curl_example": '''curl -X PUT \\
  -H "Authorization: Basic $(echo -n 'your-email@domain.com:your-api-token' | base64)" \\
  -H "Content-Type: application/json" \\
  -d '{
    "fields": {
      "summary": "Updated issue summary",
      "description": "Updated description",
      "priority": {"name": "High"}
    }
  }' \\
  https://your-domain.atlassian.net/rest/api/3/issue/PROJ-123''',
                "python_example": '''import requests
import base64

# Jira Cloud setup
email = "your-email@domain.com"
api_token = "your-api-token"
jira_url = "https://your-domain.atlassian.net"
issue_key = "PROJ-123"

credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()

headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

# Fields to update
update_data = {
    "fields": {
        "summary": "Updated issue title",
        "description": "Updated issue description",
        "priority": {"name": "High"},
        "labels": ["api-update", "automated"]
    }
}

response = requests.put(
    f"{jira_url}/rest/api/3/issue/{issue_key}",
    headers=headers,
    json=update_data
)

if response.status_code == 204:
    print(f"Successfully updated issue {issue_key}")
else:
    print(f"Error: {response.status_code} - {response.text}")''',
                "common_issues": [
                    "Issue not found - verify issue key exists",
                    "Field update failed - check field permissions and valid values",
                    "Permission denied - ensure you can edit this issue",
                    "Invalid field values - verify priority/status names are correct",
                    "Required field missing - some fields may be required for updates"
                ],
                "related_operations": [
                    "Get issue details - GET /rest/api/3/issue/{issueIdOrKey}",
                    "Transition issue - POST /rest/api/3/issue/{issueIdOrKey}/transitions",
                    "Add comment - POST /rest/api/3/issue/{issueIdOrKey}/comment",
                    "Assign issue - PUT /rest/api/3/issue/{issueIdOrKey}/assignee",
                    "Delete issue - DELETE /rest/api/3/issue/{issueIdOrKey}"
                ],
                "agent_type": "jira_mock_generated",
                "confidence": "high", 
                "jira_docs_found": len(docs)
            }
        
        # Default general response
        return {
            "endpoint": "Jira Cloud REST API v3",
            "method": "Various",
            "description": f"Jira API help for: {user_request}",
            "authentication": "Basic Auth using email and API token, or Bearer token",
            "curl_example": '''# Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens
curl -X GET \\
  -H "Authorization: Basic $(echo -n 'email@domain.com:api-token' | base64)" \\
  https://your-domain.atlassian.net/rest/api/3/myself''',
            "python_example": '''import requests
import base64

# Jira Cloud authentication
email = "your-email@domain.com" 
api_token = "your-api-token"  # From Atlassian Account Settings
jira_url = "https://your-domain.atlassian.net"

credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
headers = {"Authorization": f"Basic {credentials}"}

# Test connection
response = requests.get(f"{jira_url}/rest/api/3/myself", headers=headers)
print(f"Connected as: {response.json()['displayName']}")''',
            "common_issues": [
                "Get API token from Atlassian Account Settings > Security > API tokens",
                "Use email address (not username) for authentication",
                "Ensure your Jira Cloud URL is correct (subdomain.atlassian.net)",
                "Check user permissions for the operation you're trying to perform",
                "Verify the issue key or project key format (PROJECT-123)"
            ],
            "related_operations": [
                "Issue operations - create, update, delete, search issues",
                "Project management - get projects, components, versions",
                "User management - get users, groups, permissions",
                "Workflow operations - transitions, statuses",
                "Comments and attachments - add/get comments, upload files"
            ],
            "agent_type": "jira_mock_generated",
            "confidence": "medium",
            "jira_docs_found": len(docs)
        }
    
    def _prepare_jira_context(self, docs: List[Dict]) -> str:
        """Prepare Jira-specific documentation context"""
        if not docs:
            return "No specific Jira documentation found. Using general Jira Cloud REST API knowledge."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"""
Jira API Documentation {i}:
- Operation: {doc['title']}
- Description: {doc['description']}
- Endpoint: {doc['method']} {doc['endpoint']}
- Relevance: {doc['score']:.2f}
- Content: {doc['content'][:500]}{'...' if len(doc['content']) > 500 else ''}
""")
        
        return "\n".join(context_parts)


# Global Jira agent instance
jira_agent = JiraAgent()


async def get_jira_help(user_request: str, db: Session = None) -> Dict[str, Any]:
    """
    Get Jira API help for user request
    
    Args:
        user_request: User's question about Jira API
        db: Database session (for future use)
        
    Returns:
        Structured Jira API response
    """
    return await jira_agent.help_with_jira(user_request)