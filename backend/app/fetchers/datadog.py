from typing import List, Dict, Any, Optional
import logging
import json

from app.fetchers.base import BaseFetcher
from app.schemas import APIDocumentationCreate, HTTPMethod

logger = logging.getLogger(__name__)


class DatadogFetcher(BaseFetcher):
    """Fetcher for Datadog API documentation"""
    
    def __init__(self, provider_id: int, api_key: Optional[str] = None, app_key: Optional[str] = None, **kwargs):
        super().__init__(
            provider_id=provider_id,
            base_url="https://api.datadoghq.com",
            **kwargs
        )
        self.api_key = api_key
        self.app_key = app_key
        self.openapi_urls = [
            "https://docs.datadoghq.com/api/latest/spec/v1/datadog-api-spec-v1.json",
            "https://docs.datadoghq.com/api/latest/spec/v2/datadog-api-spec-v2.json"
        ]
    
    def get_provider_name(self) -> str:
        return "datadog"
    
    async def fetch_documentation(self) -> List[APIDocumentationCreate]:
        """Fetch Datadog API documentation"""
        docs = []
        
        try:
            logger.info("Fetching Datadog API documentation...")
            
            # Fetch both v1 and v2 API specifications
            for openapi_url in self.openapi_urls:
                try:
                    logger.info(f"Fetching from {openapi_url}")
                    openapi_spec = await self.make_request(openapi_url)
                    
                    if openapi_spec:
                        # Parse OpenAPI spec using base class method
                        api_docs = self.parse_openapi_spec(openapi_spec)
                        
                        # Determine API version from URL
                        api_version = "v2" if "v2" in openapi_url else "v1"
                        
                        # Apply Datadog-specific processing
                        api_docs = self._enhance_datadog_docs(api_docs, api_version)
                        
                        docs.extend(api_docs)
                        
                    await self.rate_limit_delay(0.5)  # Be nice to Datadog's servers
                    
                except Exception as e:
                    logger.error(f"Failed to fetch from {openapi_url}: {str(e)}")
                    continue
                
            logger.info(f"Successfully fetched {len(docs)} Datadog API endpoints")
            
        except Exception as e:
            logger.error(f"Failed to fetch Datadog documentation: {str(e)}")
            raise
        
        return docs
    
    def _enhance_datadog_docs(self, docs: List[APIDocumentationCreate], api_version: str) -> List[APIDocumentationCreate]:
        """Enhance documentation with Datadog-specific information"""
        enhanced_docs = []
        
        for doc in docs:
            # Set API version
            doc.version = api_version
            
            # Add Datadog-specific tags
            if not doc.tags:
                doc.tags = []
            
            doc.tags.append(f"API-{api_version}")
            
            # Categorize by endpoint path
            if '/metrics' in doc.endpoint_path:
                doc.tags.append('Metrics')
            elif '/events' in doc.endpoint_path:
                doc.tags.append('Events')
            elif '/logs' in doc.endpoint_path:
                doc.tags.append('Logs')
            elif '/monitors' in doc.endpoint_path:
                doc.tags.append('Monitors')
            elif '/dashboards' in doc.endpoint_path:
                doc.tags.append('Dashboards')
            elif '/users' in doc.endpoint_path:
                doc.tags.append('Users')
            elif '/organizations' in doc.endpoint_path:
                doc.tags.append('Organizations')
            elif '/hosts' in doc.endpoint_path:
                doc.tags.append('Infrastructure')
            elif '/traces' in doc.endpoint_path or '/apm' in doc.endpoint_path:
                doc.tags.append('APM')
            elif '/synthetics' in doc.endpoint_path:
                doc.tags.append('Synthetics')
            elif '/security' in doc.endpoint_path:
                doc.tags.append('Security')
            elif '/rum' in doc.endpoint_path:
                doc.tags.append('RUM')
            elif '/incidents' in doc.endpoint_path:
                doc.tags.append('Incidents')
            elif '/slo' in doc.endpoint_path:
                doc.tags.append('SLO')
            elif '/service' in doc.endpoint_path:
                doc.tags.append('Service Management')
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
            
            # Mark v1 endpoints as potentially deprecated
            if api_version == "v1" and not doc.deprecated:
                # Check if there might be a v2 equivalent
                if any(category in doc.tags for category in ['Metrics', 'Logs', 'Events']):
                    doc.content = f"{doc.content}\n\n**Note:** Consider using the v2 API if available, as v1 endpoints may be deprecated in the future."
            
            enhanced_docs.append(doc)
        
        return enhanced_docs
    
    def _get_authentication_info(self) -> str:
        """Get authentication information for Datadog API"""
        return """**Authentication:**
This endpoint requires authentication using:
- **DD-API-KEY**: Your Datadog API key (required)
- **DD-APPLICATION-KEY**: Your Datadog application key (required for most endpoints)

API keys can be created in your Datadog account under Organization Settings > API Keys.
Application keys can be created under Organization Settings > Application Keys.

Include these as headers in your requests:
```
DD-API-KEY: <your-api-key>
DD-APPLICATION-KEY: <your-app-key>
```"""
    
    def _get_rate_limit_info(self) -> str:
        """Get rate limiting information for Datadog API"""
        return """**Rate Limiting:**
Datadog APIs are rate limited per organization:
- Default limit: 1000 requests per hour per organization
- Some endpoints have specific limits (e.g., metrics submission: 500,000 requests per hour)
- Rate limit headers are included in responses
- Exceeding limits returns HTTP 429 (Too Many Requests)

Monitor your usage in the Datadog UI under Organization Settings > Usage."""
    
    def _get_datadog_examples(self, endpoint_path: str, method: str) -> Dict[str, Any]:
        """Generate Datadog-specific examples"""
        examples = {}
        
        try:
            # Add common examples based on endpoint type
            if '/metrics' in endpoint_path and method.upper() == 'POST':
                examples['submit_metrics'] = {
                    "summary": "Submit metrics to Datadog",
                    "value": {
                        "series": [
                            {
                                "metric": "system.load.1",
                                "points": [[1636629071, 0.7]],
                                "tags": ["environment:test"],
                                "host": "test.example.com"
                            }
                        ]
                    }
                }
            elif '/events' in endpoint_path and method.upper() == 'POST':
                examples['create_event'] = {
                    "summary": "Create an event",
                    "value": {
                        "title": "Something big happened!",
                        "text": "And let me tell you all about it here!",
                        "date_happened": 1636629071,
                        "priority": "normal",
                        "tags": ["environment:test"],
                        "alert_type": "info"
                    }
                }
            elif '/monitors' in endpoint_path and method.upper() == 'POST':
                examples['create_monitor'] = {
                    "summary": "Create a monitor",
                    "value": {
                        "type": "metric alert",
                        "query": "avg(last_1m):avg:system.load.1{host:web01} > 0.5",
                        "name": "Bytes received on host0",
                        "message": "We may need to add web hosts if this is consistently high.",
                        "tags": ["app:webserver", "frontend"]
                    }
                }
        
        except Exception as e:
            logger.error(f"Error generating Datadog examples: {str(e)}")
        
        return examples 