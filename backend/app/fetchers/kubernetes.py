from typing import List, Dict, Any, Optional
import logging
import re

from app.fetchers.base import BaseFetcher
from app.schemas import APIDocumentationCreate, HTTPMethod

logger = logging.getLogger(__name__)


class KubernetesFetcher(BaseFetcher):
    """Fetcher for Kubernetes API documentation"""
    
    def __init__(self, provider_id: int, **kwargs):
        super().__init__(
            provider_id=provider_id,
            base_url="https://kubernetes.io",
            **kwargs
        )
        # Latest stable Kubernetes API version
        self.api_version = "v1.28"  # Update as needed
        self.openapi_url = f"https://raw.githubusercontent.com/kubernetes/kubernetes/release-{self.api_version}/api/openapi-spec/swagger.json"
    
    def get_provider_name(self) -> str:
        return "kubernetes"
    
    async def fetch_documentation(self) -> List[APIDocumentationCreate]:
        """Fetch Kubernetes API documentation"""
        docs = []
        
        try:
            logger.info(f"Fetching Kubernetes API documentation for {self.api_version}...")
            
            # Fetch OpenAPI specification from GitHub
            openapi_spec = await self.make_request(self.openapi_url)
            
            if openapi_spec:
                # Parse OpenAPI spec using base class method
                docs = self.parse_openapi_spec(openapi_spec)
                
                # Apply Kubernetes-specific processing
                docs = self._enhance_kubernetes_docs(docs)
                
                logger.info(f"Successfully fetched {len(docs)} Kubernetes API endpoints")
            
        except Exception as e:
            logger.error(f"Failed to fetch Kubernetes documentation: {str(e)}")
            # Fallback: try to fetch from alternative sources
            docs = await self._fetch_fallback_docs()
        
        return docs
    
    async def _fetch_fallback_docs(self) -> List[APIDocumentationCreate]:
        """Fallback method to fetch Kubernetes docs from alternative sources"""
        docs = []
        
        try:
            # Try the official Kubernetes API reference
            fallback_urls = [
                "https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json",
                "https://raw.githubusercontent.com/kubernetes/kubernetes/main/api/openapi-spec/swagger.json"
            ]
            
            for url in fallback_urls:
                try:
                    logger.info(f"Trying fallback URL: {url}")
                    openapi_spec = await self.make_request(url)
                    
                    if openapi_spec:
                        docs = self.parse_openapi_spec(openapi_spec)
                        docs = self._enhance_kubernetes_docs(docs)
                        break
                        
                except Exception as e:
                    logger.warning(f"Fallback URL failed: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"All fallback methods failed: {str(e)}")
        
        return docs
    
    def _enhance_kubernetes_docs(self, docs: List[APIDocumentationCreate]) -> List[APIDocumentationCreate]:
        """Enhance documentation with Kubernetes-specific information"""
        enhanced_docs = []
        
        for doc in docs:
            # Set API version
            doc.version = self.api_version
            
            # Add Kubernetes-specific tags
            if not doc.tags:
                doc.tags = []
            
            # Categorize by API group and resource type
            endpoint_path = doc.endpoint_path.lower()
            
            # Core API resources
            if '/api/v1/' in endpoint_path:
                doc.tags.append('Core API')
                
                if '/pods' in endpoint_path:
                    doc.tags.extend(['Workloads', 'Pods'])
                elif '/services' in endpoint_path:
                    doc.tags.extend(['Services', 'Networking'])
                elif '/configmaps' in endpoint_path:
                    doc.tags.extend(['Config', 'ConfigMaps'])
                elif '/secrets' in endpoint_path:
                    doc.tags.extend(['Config', 'Secrets'])
                elif '/namespaces' in endpoint_path:
                    doc.tags.extend(['Cluster', 'Namespaces'])
                elif '/nodes' in endpoint_path:
                    doc.tags.extend(['Cluster', 'Nodes'])
                elif '/persistentvolumes' in endpoint_path:
                    doc.tags.extend(['Storage', 'PersistentVolumes'])
                elif '/persistentvolumeclaims' in endpoint_path:
                    doc.tags.extend(['Storage', 'PersistentVolumeClaims'])
                elif '/events' in endpoint_path:
                    doc.tags.extend(['Cluster', 'Events'])
            
            # Apps API resources
            elif '/apis/apps/' in endpoint_path:
                doc.tags.append('Apps API')
                
                if '/deployments' in endpoint_path:
                    doc.tags.extend(['Workloads', 'Deployments'])
                elif '/replicasets' in endpoint_path:
                    doc.tags.extend(['Workloads', 'ReplicaSets'])
                elif '/daemonsets' in endpoint_path:
                    doc.tags.extend(['Workloads', 'DaemonSets'])
                elif '/statefulsets' in endpoint_path:
                    doc.tags.extend(['Workloads', 'StatefulSets'])
            
            # Extensions/Networking
            elif '/apis/networking.k8s.io/' in endpoint_path:
                doc.tags.extend(['Networking API', 'Networking'])
                
                if '/ingresses' in endpoint_path:
                    doc.tags.append('Ingresses')
                elif '/networkpolicies' in endpoint_path:
                    doc.tags.append('NetworkPolicies')
            
            # RBAC
            elif '/apis/rbac.authorization.k8s.io/' in endpoint_path:
                doc.tags.extend(['RBAC API', 'Authorization'])
                
                if '/roles' in endpoint_path:
                    doc.tags.append('Roles')
                elif '/rolebindings' in endpoint_path:
                    doc.tags.append('RoleBindings')
                elif '/clusterroles' in endpoint_path:
                    doc.tags.append('ClusterRoles')
                elif '/clusterrolebindings' in endpoint_path:
                    doc.tags.append('ClusterRoleBindings')
            
            # Batch API
            elif '/apis/batch/' in endpoint_path:
                doc.tags.extend(['Batch API', 'Workloads'])
                
                if '/jobs' in endpoint_path:
                    doc.tags.append('Jobs')
                elif '/cronjobs' in endpoint_path:
                    doc.tags.append('CronJobs')
            
            # Autoscaling
            elif '/apis/autoscaling/' in endpoint_path:
                doc.tags.extend(['Autoscaling API', 'Scaling'])
                
                if '/horizontalpodautoscalers' in endpoint_path:
                    doc.tags.append('HorizontalPodAutoscalers')
            
            # Storage
            elif '/apis/storage.k8s.io/' in endpoint_path:
                doc.tags.extend(['Storage API', 'Storage'])
                
                if '/storageclasses' in endpoint_path:
                    doc.tags.append('StorageClasses')
            
            # Custom Resource Definitions
            elif '/apis/apiextensions.k8s.io/' in endpoint_path:
                doc.tags.extend(['API Extensions', 'CRDs'])
                
                if '/customresourcedefinitions' in endpoint_path:
                    doc.tags.append('CustomResourceDefinitions')
            
            # Metrics
            elif '/apis/metrics.k8s.io/' in endpoint_path:
                doc.tags.extend(['Metrics API', 'Monitoring'])
            
            # Add general category if no specific category found
            if len(doc.tags) <= 1:  # Only has version tag
                doc.tags.append('General')
            
            # Add authentication information to content
            if doc.content:
                auth_info = self._get_authentication_info()
                doc.content = f"{doc.content}\n\n{auth_info}"
            
            # Add RBAC information
            if doc.content:
                rbac_info = self._get_rbac_info(doc.endpoint_path, doc.http_method.value)
                if rbac_info:
                    doc.content = f"{doc.content}\n\n{rbac_info}"
            
            enhanced_docs.append(doc)
        
        return enhanced_docs
    
    def _get_authentication_info(self) -> str:
        """Get authentication information for Kubernetes API"""
        return """**Authentication:**
Kubernetes API requires authentication. Common methods:
- **Service Account Tokens**: Default for in-cluster access
- **Client Certificates**: For external access with mutual TLS
- **Bearer Tokens**: For service accounts or external identity providers
- **Basic Auth**: Legacy method (not recommended)
- **OIDC**: Integration with external identity providers

For kubectl users, authentication is handled by kubeconfig file.
For applications, use service account tokens or client certificates."""
    
    def _get_rbac_info(self, endpoint_path: str, method: str) -> Optional[str]:
        """Get RBAC information for specific endpoint"""
        # Map HTTP methods to RBAC verbs
        verb_mapping = {
            'GET': 'get' if '/{name}' in endpoint_path else 'list',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'patch',
            'DELETE': 'delete'
        }
        
        verb = verb_mapping.get(method.upper(), method.lower())
        
        # Extract resource type from path
        resource = None
        if '/pods' in endpoint_path:
            resource = 'pods'
        elif '/services' in endpoint_path:
            resource = 'services'
        elif '/deployments' in endpoint_path:
            resource = 'deployments'
        elif '/configmaps' in endpoint_path:
            resource = 'configmaps'
        elif '/secrets' in endpoint_path:
            resource = 'secrets'
        # Add more as needed
        
        if resource:
            return f"""**RBAC Requirements:**
To use this endpoint, you need RBAC permissions:
- **Verb**: {verb}
- **Resource**: {resource}
- **API Group**: {self._get_api_group(endpoint_path)}

Example ClusterRole:
```yaml
rules:
- apiGroups: ["{self._get_api_group(endpoint_path)}"]
  resources: ["{resource}"]
  verbs: ["{verb}"]
```"""
        
        return None
    
    def _get_api_group(self, endpoint_path: str) -> str:
        """Get API group from endpoint path"""
        if '/api/v1/' in endpoint_path:
            return ""  # Core API group
        elif '/apis/apps/' in endpoint_path:
            return "apps"
        elif '/apis/networking.k8s.io/' in endpoint_path:
            return "networking.k8s.io"
        elif '/apis/rbac.authorization.k8s.io/' in endpoint_path:
            return "rbac.authorization.k8s.io"
        elif '/apis/batch/' in endpoint_path:
            return "batch"
        elif '/apis/autoscaling/' in endpoint_path:
            return "autoscaling"
        elif '/apis/storage.k8s.io/' in endpoint_path:
            return "storage.k8s.io"
        elif '/apis/apiextensions.k8s.io/' in endpoint_path:
            return "apiextensions.k8s.io"
        else:
            return "unknown" 