from typing import List, Dict, Any, Optional
import logging
import re

from app.fetchers.base import BaseFetcher
from app.schemas import APIDocumentationCreate, HTTPMethod

logger = logging.getLogger(__name__)


class AtlassianFetcher(BaseFetcher):
    """Fetcher for Atlassian (Jira) API documentation"""
    
    def __init__(self, provider_id: int, api_token: Optional[str] = None, **kwargs):
        super().__init__(
            provider_id=provider_id,
            base_url="https://developer.atlassian.com",
            **kwargs
        )
        self.api_token = api_token
        self.openapi_url = "https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json"
    
    def get_provider_name(self) -> str:
        return "atlassian"
    
    async def fetch_documentation(self) -> List[APIDocumentationCreate]:
        """Fetch Atlassian API documentation"""
        docs = []
        
        try:
            logger.info("Fetching Atlassian API documentation...")
            
            # Fetch OpenAPI specification
            openapi_spec = await self.make_request(self.openapi_url)
            
            if openapi_spec:
                # Parse OpenAPI spec using base class method
                docs = self.parse_openapi_spec(openapi_spec)
                
                # Apply Atlassian-specific processing
                docs = self._enhance_atlassian_docs(docs)
                
                logger.info(f"Successfully fetched {len(docs)} Atlassian API endpoints")
            
        except Exception as e:
            logger.error(f"Failed to fetch Atlassian documentation: {str(e)}")
            raise
        
        return docs
    
    def _enhance_atlassian_docs(self, docs: List[APIDocumentationCreate]) -> List[APIDocumentationCreate]:
        """Enhance documentation with Atlassian-specific information"""
        enhanced_docs = []
        
        for doc in docs:
            # Add Atlassian-specific tags
            if not doc.tags:
                doc.tags = []
            
            # Categorize by endpoint path
            if '/rest/api/3/issue' in doc.endpoint_path:
                doc.tags.append('Issues')
            elif '/rest/api/3/project' in doc.endpoint_path:
                doc.tags.append('Projects')
            elif '/rest/api/3/user' in doc.endpoint_path:
                doc.tags.append('Users')
            elif '/rest/api/3/search' in doc.endpoint_path:
                doc.tags.append('Search')
            elif '/rest/api/3/workflow' in doc.endpoint_path:
                doc.tags.append('Workflows')
            elif '/rest/api/3/filter' in doc.endpoint_path:
                doc.tags.append('Filters')
            elif '/rest/api/3/dashboard' in doc.endpoint_path:
                doc.tags.append('Dashboards')
            elif '/rest/api/3/permission' in doc.endpoint_path:
                doc.tags.append('Permissions')
            elif '/rest/api/3/field' in doc.endpoint_path:
                doc.tags.append('Fields')
            elif '/rest/api/3/component' in doc.endpoint_path:
                doc.tags.append('Components')
            elif '/rest/api/3/version' in doc.endpoint_path:
                doc.tags.append('Versions')
            else:
                doc.tags.append('General')
            
            # Add authentication information to content
            if doc.content:
                auth_info = self._get_authentication_info()
                doc.content = f"{doc.content}\n\n{auth_info}"
            
            # Add rate limiting information
            if doc.content:
                rate_limit_info = self._get_rate_limit_info()
                doc.content = f"{doc.content}\n\n{rate_limit_info}"
            
            enhanced_docs.append(doc)
        
        return enhanced_docs
    
    def _get_authentication_info(self) -> str:
        """Get authentication information for Atlassian API"""
        return """**Authentication:**
This endpoint requires authentication. You can use:
- Basic authentication with email and API token
- OAuth 2.0 (3LO) for apps
- JWT for Connect apps

For basic authentication, use your Atlassian account email as the username and an API token as the password.
API tokens can be created at: https://id.atlassian.com/manage-profile/security/api-tokens"""
    
    def _get_rate_limit_info(self) -> str:
        """Get rate limiting information for Atlassian API"""
        return """**Rate Limiting:**
Atlassian Cloud REST APIs are rate limited. The rate limit is per user, not per app.
- Standard rate limit: 10 requests per second per user
- Some endpoints have lower limits
- Rate limit information is included in response headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset"""
    
    async def fetch_additional_examples(self, endpoint_path: str, method: str) -> Dict[str, Any]:
        """Fetch additional examples from Atlassian documentation pages"""
        try:
            # This would require scraping the actual documentation pages
            # For now, return empty examples
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch additional examples: {str(e)}")
            return {}
    
    def _clean_atlassian_description(self, description: str) -> str:
        """Clean and enhance Atlassian API descriptions"""
        if not description:
            return description
        
        # Remove HTML tags if present
        description = self.clean_html_content(description)
        
        # Clean up common Atlassian documentation patterns
        description = re.sub(r'\*\*Permissions required:\*\*[^*]*\*\*', '', description)
        description = re.sub(r'Permissions required:[^.]*\.', '', description)
        
        # Clean up extra whitespace
        description = ' '.join(description.split())
        
        return description 