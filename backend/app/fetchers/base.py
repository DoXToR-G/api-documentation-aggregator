from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
import asyncio
import logging
from datetime import datetime

from app.schemas import APIDocumentationCreate, HTTPMethod

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Base class for API documentation fetchers"""
    
    def __init__(self, provider_id: int, base_url: str, **kwargs):
        self.provider_id = provider_id
        self.base_url = base_url
        self.session = None
        self.config = kwargs
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    @abstractmethod
    async def fetch_documentation(self) -> List[APIDocumentationCreate]:
        """Fetch all API documentation from the provider"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name"""
        pass
    
    async def make_request(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            if not self.session:
                raise RuntimeError("Fetcher must be used as async context manager")
            
            response = await self.session.get(url, headers=headers, **kwargs)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                return {"content": response.text, "content_type": content_type}
                
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {str(e)}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {str(e)}")
            raise
    
    def parse_openapi_spec(self, spec: Dict[str, Any]) -> List[APIDocumentationCreate]:
        """Parse OpenAPI/Swagger specification"""
        docs = []
        
        try:
            paths = spec.get('paths', {})
            base_info = spec.get('info', {})
            servers = spec.get('servers', [])
            
            for path, path_info in paths.items():
                for method, method_info in path_info.items():
                    if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                        continue
                    
                    # Extract documentation information
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
                    request_body = None
                    if 'requestBody' in method_info:
                        request_body = method_info['requestBody']
                    
                    # Extract responses
                    responses = method_info.get('responses', {})
                    
                    # Extract examples
                    examples = {}
                    if 'examples' in method_info:
                        examples = method_info['examples']
                    
                    # Extract tags
                    tags = method_info.get('tags', [])
                    
                    # Check if deprecated
                    deprecated = method_info.get('deprecated', False)
                    
                    doc = APIDocumentationCreate(
                        provider_id=self.provider_id,
                        endpoint_path=path,
                        http_method=HTTPMethod(method.upper()),
                        title=title,
                        description=description,
                        content=self._generate_content(method_info),
                        parameters={'parameters': parameters} if parameters else None,
                        request_body=request_body,
                        responses=responses,
                        examples=examples,
                        tags=tags,
                        version=base_info.get('version'),
                        deprecated=deprecated
                    )
                    
                    docs.append(doc)
        
        except Exception as e:
            logger.error(f"Error parsing OpenAPI spec: {str(e)}")
            raise
        
        return docs
    
    def _generate_content(self, method_info: Dict[str, Any]) -> str:
        """Generate readable content from method information"""
        content_parts = []
        
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
        
        if method_info.get('responses'):
            content_parts.append("**Responses:**")
            for code, response in method_info['responses'].items():
                resp_desc = f"- `{code}`: {response.get('description', 'No description')}"
                content_parts.append(resp_desc)
        
        return "\n\n".join(content_parts)
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean HTML content and convert to readable text"""
        try:
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning HTML content: {str(e)}")
            return html_content
    
    async def rate_limit_delay(self, delay_seconds: float = 1.0):
        """Add delay between requests to respect rate limits"""
        await asyncio.sleep(delay_seconds) 