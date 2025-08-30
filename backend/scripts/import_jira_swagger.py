"""
Import complete Jira Cloud REST API documentation from official Swagger/OpenAPI specification
Source: https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import json
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import APIProvider, APIDocumentation
from typing import Dict, List, Any
import re

def clean_description(text: str) -> str:
    """Clean and normalize description text"""
    if not text:
        return ""
    
    # Remove excessive whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove markdown-style links and formatting
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Limit length for database storage
    if len(text) > 500:
        text = text[:497] + "..."
    
    return text

def extract_tags_from_path(path: str, operation_id: str = "") -> List[str]:
    """Extract meaningful tags from API path and operation"""
    tags = []
    
    # Extract resource types from path
    path_parts = [part for part in path.split('/') if part and not part.startswith('{')]
    
    # Common Jira resources
    jira_resources = {
        'issue': ['issue', 'issues', 'jira-issues'],
        'project': ['project', 'projects', 'project-management'],
        'user': ['user', 'users', 'user-management'],
        'group': ['group', 'groups', 'group-management'],
        'dashboard': ['dashboard', 'dashboards', 'dashboard-management'],
        'filter': ['filter', 'filters', 'jql', 'search'],
        'workflow': ['workflow', 'workflows', 'transitions'],
        'permission': ['permission', 'permissions', 'security'],
        'comment': ['comment', 'comments'],
        'attachment': ['attachment', 'attachments', 'files'],
        'worklog': ['worklog', 'worklogs', 'time-tracking'],
        'component': ['component', 'components'],
        'version': ['version', 'versions'],
        'priority': ['priority', 'priorities'],
        'status': ['status', 'statuses'],
        'field': ['field', 'fields', 'custom-fields'],
        'screen': ['screen', 'screens'],
        'webhook': ['webhook', 'webhooks', 'notifications']
    }
    
    # Add tags based on path components
    for part in path_parts:
        part_lower = part.lower()
        for resource, resource_tags in jira_resources.items():
            if resource in part_lower or part_lower in resource:
                tags.extend(resource_tags)
                break
    
    # Add operation type tags
    if operation_id:
        op_lower = operation_id.lower()
        if any(word in op_lower for word in ['create', 'add', 'post']):
            tags.append('create')
        if any(word in op_lower for word in ['get', 'find', 'search', 'list']):
            tags.append('get')
        if any(word in op_lower for word in ['update', 'edit', 'put', 'patch']):
            tags.append('update')
        if any(word in op_lower for word in ['delete', 'remove']):
            tags.append('delete')
    
    # Remove duplicates and return
    return list(set(tags))

def convert_swagger_to_documentation(swagger_data: Dict[str, Any], provider_id: int) -> List[Dict[str, Any]]:
    """Convert Swagger/OpenAPI specification to our documentation format"""
    
    docs = []
    paths = swagger_data.get('paths', {})
    
    print(f"📚 Processing {len(paths)} API paths...")
    
    for path, path_data in paths.items():
        for method, operation_data in path_data.items():
            if method.lower() not in ['get', 'post', 'put', 'patch', 'delete']:
                continue
                
            # Extract basic information
            operation_id = operation_data.get('operationId', '')
            summary = operation_data.get('summary', '')
            description = operation_data.get('description', summary)
            
            # Create title from summary or operation ID
            title = summary or operation_id.replace('_', ' ').replace('-', ' ').title()
            if not title:
                title = f"{method.upper()} {path}"
            
            # Clean and prepare content
            clean_desc = clean_description(description)
            
            # Extract parameters
            parameters = operation_data.get('parameters', [])
            request_body = operation_data.get('requestBody', {})
            responses = operation_data.get('responses', {})
            
            # Create comprehensive content JSON
            content_data = {
                "operation_id": operation_id,
                "summary": summary,
                "description": description,
                "path": path,
                "method": method.upper(),
                "parameters": {
                    "path": [p for p in parameters if p.get('in') == 'path'],
                    "query": [p for p in parameters if p.get('in') == 'query'],
                    "header": [p for p in parameters if p.get('in') == 'header']
                },
                "request_body": request_body,
                "responses": {
                    code: {
                        "description": resp.get("description", ""),
                        "schema": resp.get("content", {})
                    } for code, resp in responses.items()
                },
                "tags": operation_data.get('tags', []),
                "deprecated": operation_data.get('deprecated', False),
                "security": operation_data.get('security', []),
                "examples": operation_data.get('examples', {})
            }
            
            # Generate tags
            tags = extract_tags_from_path(path, operation_id)
            tags.extend(operation_data.get('tags', []))
            
            # Create documentation entry
            doc = {
                "provider_id": provider_id,
                "title": title,
                "description": clean_desc,
                "endpoint_path": path,
                "http_method": method.upper(),
                "content": json.dumps(content_data),
                "tags": list(set(tags)),  # Remove duplicates
                "version": "3",
                "deprecated": operation_data.get('deprecated', False)
            }
            
            docs.append(doc)
    
    return docs

def import_jira_swagger():
    """Import complete Jira API documentation from Swagger specification"""
    
    print("🚀 Starting import of complete Jira Cloud REST API documentation...")
    
    # Download Swagger specification
    swagger_url = "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json"
    print(f"📥 Downloading Swagger specification from: {swagger_url}")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(swagger_url)
            response.raise_for_status()
            swagger_data = response.json()
            print(f"✅ Downloaded {len(str(response.content))} bytes of API specification")
    except Exception as e:
        print(f"❌ Failed to download Swagger specification: {e}")
        return False
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get Jira Cloud provider
        jira_provider = db.query(APIProvider).filter(APIProvider.name == "jira_cloud").first()
        if not jira_provider:
            print("❌ Jira Cloud provider not found!")
            return False
        
        print(f"✅ Found Jira Cloud provider (ID: {jira_provider.id})")
        
        # Convert Swagger to our documentation format
        print("🔄 Converting Swagger specification to documentation entries...")
        docs = convert_swagger_to_documentation(swagger_data, jira_provider.id)
        
        print(f"📊 Generated {len(docs)} documentation entries")
        
        # Clear existing Jira documentation (optional - keep dashboard docs)
        print("🧹 Clearing existing Jira documentation (keeping dashboards)...")
        existing_count = db.query(APIDocumentation).filter(
            APIDocumentation.provider_id == jira_provider.id,
            ~APIDocumentation.title.ilike('%dashboard%')
        ).delete()
        print(f"🗑️ Removed {existing_count} existing non-dashboard entries")
        
        # Insert new documentation
        print("📝 Inserting new documentation entries...")
        
        added_count = 0
        skipped_count = 0
        dashboard_count = 0
        
        for doc_data in docs:
            # Check if this might be a duplicate of existing dashboard docs
            if 'dashboard' in doc_data['title'].lower():
                existing = db.query(APIDocumentation).filter(
                    APIDocumentation.provider_id == jira_provider.id,
                    APIDocumentation.endpoint_path == doc_data['endpoint_path'],
                    APIDocumentation.http_method == doc_data['http_method']
                ).first()
                
                if existing:
                    print(f"  ⏭️ Skipping existing dashboard: {doc_data['title']}")
                    skipped_count += 1
                    continue
                else:
                    dashboard_count += 1
            
            try:
                doc = APIDocumentation(**doc_data)
                db.add(doc)
                added_count += 1
                
                # Print progress for significant endpoints
                if any(keyword in doc_data['title'].lower() for keyword in 
                       ['issue', 'project', 'user', 'search', 'dashboard', 'comment', 'workflow']):
                    print(f"  ✅ Added: {doc_data['title']} ({doc_data['http_method']} {doc_data['endpoint_path']})")
                
            except Exception as e:
                print(f"  ❌ Failed to add {doc_data['title']}: {e}")
                continue
        
        # Commit changes
        db.commit()
        
        print(f"\n🎉 Import completed successfully!")
        print(f"📊 Statistics:")
        print(f"   - New entries added: {added_count}")
        print(f"   - Existing entries skipped: {skipped_count}")
        print(f"   - Dashboard entries found: {dashboard_count}")
        print(f"   - Total entries processed: {len(docs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = import_jira_swagger()
    if success:
        print("\n✅ Complete Jira API documentation imported!")
        print("\n🔄 Next steps:")
        print("1. Reindex Elasticsearch: python reindex_docs.py")
        print("2. Test the agent: curl \"http://localhost:8000/api/v1/jira/ask?q=create%20issue\"")
    else:
        print("\n❌ Import failed!")