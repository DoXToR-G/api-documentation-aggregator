"""
Script to add Jira Dashboard API documentation from Atlassian official docs
Based on: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-dashboards/
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import APIProvider, APIDocumentation
import json

def add_dashboard_docs():
    """Add comprehensive Jira Dashboard API documentation from Atlassian docs"""
    db = SessionLocal()
    
    try:
        # Get Jira Cloud provider
        jira_provider = db.query(APIProvider).filter(APIProvider.name == "jira_cloud").first()
        if not jira_provider:
            print("Jira Cloud provider not found!")
            return
        
        # Dashboard documentation from official Atlassian docs
        dashboard_docs = [
            {
                "title": "Get All Dashboards",
                "description": "Returns a list of dashboards owned by or shared with the user. The list may be filtered to include only favorite or owned dashboards.",
                "endpoint_path": "/rest/api/3/dashboard",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Get all dashboards accessible to the current user",
                    "description": "Returns a list of dashboards owned by or shared with the user. The list may be filtered to include only favorite or owned dashboards. This operation can be accessed anonymously.",
                    "permissions": "None - This operation can be accessed anonymously",
                    "data_security": "Exempt from app access rules",
                    "query_parameters": {
                        "filter": {
                            "type": "string",
                            "description": "The filter applied to the list of dashboards",
                            "values": ["favourite", "my"],
                            "optional": True
                        },
                        "startAt": {
                            "type": "integer", 
                            "description": "The index of the first item to return in a page of results",
                            "default": 0,
                            "optional": True
                        },
                        "maxResults": {
                            "type": "integer",
                            "description": "The maximum number of items to return per page",
                            "default": 20,
                            "maximum": 1000,
                            "optional": True
                        }
                    },
                    "response_schema": {
                        "type": "PageOfDashboards",
                        "properties": {
                            "dashboards": "Array of dashboard objects",
                            "startAt": "Index of first item returned",
                            "maxResults": "Maximum number of items per page", 
                            "total": "Total number of dashboards",
                            "prev": "URL of previous page",
                            "next": "URL of next page"
                        }
                    },
                    "example_response": {
                        "dashboards": [
                            {
                                "id": "10000",
                                "name": "System Dashboard",
                                "isFavourite": False,
                                "popularity": 1,
                                "self": "https://your-domain.atlassian.net/rest/api/3/dashboard/10000",
                                "view": "https://your-domain.atlassian.net/secure/Dashboard.jspa?selectPageId=10000",
                                "sharePermissions": [{"type": "global"}]
                            }
                        ],
                        "startAt": 0,
                        "maxResults": 20,
                        "total": 143
                    },
                    "oauth_scopes": {
                        "classic": "read:jira-work",
                        "granular": ["read:dashboard:jira", "read:group:jira", "read:project:jira", "read:project-role:jira", "read:user:jira"]
                    },
                    "authentication": "Basic Auth, OAuth 2.0, or anonymous access",
                    "rate_limits": "Standard Jira API rate limits apply"
                }),
                "tags": ["dashboard", "get", "list", "all", "dashboards", "dashboard-management"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Create Dashboard",
                "description": "Creates a dashboard",
                "endpoint_path": "/rest/api/3/dashboard",
                "http_method": "POST",
                "content": json.dumps({
                    "summary": "Create a new dashboard",
                    "description": "Creates a dashboard. This is an experimental feature.",
                    "permissions": "None",
                    "data_security": "Exempt from app access rules",
                    "experimental": True,
                    "query_parameters": {
                        "extendAdminPermissions": {
                            "type": "boolean",
                            "description": "Whether to extend admin permissions",
                            "optional": True
                        }
                    },
                    "request_body": {
                        "type": "DashboardDetails",
                        "required_fields": ["name", "sharePermissions", "editPermissions"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the dashboard",
                                "required": True
                            },
                            "description": {
                                "type": "string", 
                                "description": "The description of the dashboard",
                                "optional": True
                            },
                            "sharePermissions": {
                                "type": "array",
                                "description": "The share permissions for the dashboard",
                                "required": True
                            },
                            "editPermissions": {
                                "type": "array",
                                "description": "The edit permissions for the dashboard", 
                                "required": True
                            }
                        }
                    },
                    "example_request": {
                        "name": "My New Dashboard",
                        "description": "A dashboard for monitoring project progress",
                        "sharePermissions": [{"type": "global"}],
                        "editPermissions": []
                    },
                    "example_response": {
                        "id": "10000",
                        "name": "My New Dashboard",
                        "isFavourite": False,
                        "popularity": 0,
                        "self": "https://your-domain.atlassian.net/rest/api/3/dashboard/10000",
                        "sharePermissions": [{"type": "global"}]
                    },
                    "oauth_scopes": {
                        "classic": "write:jira-work",
                        "granular": ["read:dashboard:jira", "write:dashboard:jira", "read:group:jira", "read:project:jira"]
                    },
                    "authentication": "Basic Auth or OAuth 2.0"
                }),
                "tags": ["dashboard", "create", "post", "new", "dashboard-management"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Get Dashboard",
                "description": "Returns a dashboard",
                "endpoint_path": "/rest/api/3/dashboard/{id}",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Get dashboard details by ID",
                    "description": "Returns a dashboard. This operation can be accessed anonymously. However, to get a dashboard, the dashboard must be shared with the user or the user must own it.",
                    "permissions": "None - but dashboard must be shared with user or user must own it",
                    "data_security": "Exempt from app access rules",
                    "path_parameters": {
                        "id": {
                            "type": "string",
                            "description": "The ID of the dashboard",
                            "required": True
                        }
                    },
                    "special_permissions": [
                        "Users with 'Administer Jira' global permission are considered owners of the System dashboard",
                        "The System dashboard is considered to be shared with all other users"
                    ],
                    "example_response": {
                        "id": "10000",
                        "name": "System Dashboard", 
                        "isFavourite": False,
                        "popularity": 1,
                        "self": "https://your-domain.atlassian.net/rest/api/3/dashboard/10000",
                        "view": "https://your-domain.atlassian.net/secure/Dashboard.jspa?selectPageId=10000",
                        "sharePermissions": [{"type": "global"}]
                    },
                    "oauth_scopes": {
                        "classic": "read:jira-work",
                        "granular": ["read:dashboard:jira", "read:group:jira", "read:project:jira", "read:project-role:jira", "read:user:jira"]
                    },
                    "authentication": "Basic Auth, OAuth 2.0, or anonymous access"
                }),
                "tags": ["dashboard", "get", "retrieve", "details", "dashboard-management"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Update Dashboard",
                "description": "Updates a dashboard, replacing all the dashboard details with those provided",
                "endpoint_path": "/rest/api/3/dashboard/{id}",
                "http_method": "PUT", 
                "content": json.dumps({
                    "summary": "Update an existing dashboard",
                    "description": "Updates a dashboard, replacing all the dashboard details with those provided. The dashboard to be updated must be owned by the user.",
                    "permissions": "The dashboard to be updated must be owned by the user",
                    "data_security": "Exempt from app access rules",
                    "experimental": True,
                    "path_parameters": {
                        "id": {
                            "type": "string",
                            "description": "The ID of the dashboard to update",
                            "required": True
                        }
                    },
                    "query_parameters": {
                        "extendAdminPermissions": {
                            "type": "boolean",
                            "description": "Whether to extend admin permissions",
                            "optional": True
                        }
                    },
                    "request_body": {
                        "type": "DashboardDetails",
                        "description": "Replacement dashboard details",
                        "required_fields": ["name", "sharePermissions", "editPermissions"],
                        "properties": {
                            "name": {"type": "string", "required": True},
                            "description": {"type": "string", "optional": True},
                            "sharePermissions": {"type": "array", "required": True},
                            "editPermissions": {"type": "array", "required": True}
                        }
                    },
                    "example_request": {
                        "name": "Updated Dashboard Name",
                        "description": "Updated dashboard description",
                        "sharePermissions": [{"type": "global"}],
                        "editPermissions": []
                    },
                    "oauth_scopes": {
                        "classic": "write:jira-work", 
                        "granular": ["read:dashboard:jira", "write:dashboard:jira", "read:group:jira", "read:project:jira"]
                    },
                    "authentication": "Basic Auth or OAuth 2.0"
                }),
                "tags": ["dashboard", "update", "put", "edit", "dashboard-management"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Delete Dashboard",
                "description": "Deletes a dashboard",
                "endpoint_path": "/rest/api/3/dashboard/{id}",
                "http_method": "DELETE",
                "content": json.dumps({
                    "summary": "Delete a dashboard permanently",
                    "description": "Deletes a dashboard. The dashboard to be deleted must be owned by the user.",
                    "permissions": "The dashboard to be deleted must be owned by the user",
                    "data_security": "Exempt from app access rules",
                    "experimental": True,
                    "path_parameters": {
                        "id": {
                            "type": "string",
                            "description": "The ID of the dashboard to delete",
                            "required": True
                        }
                    },
                    "response": "204 No Content on successful deletion",
                    "important_notes": [
                        "Deletion is permanent and cannot be undone",
                        "Only the dashboard owner can delete the dashboard",
                        "All dashboard gadgets and configurations will be lost"
                    ],
                    "oauth_scopes": {
                        "classic": "write:jira-work",
                        "granular": ["delete:dashboard:jira"]
                    },
                    "authentication": "Basic Auth or OAuth 2.0"
                }),
                "tags": ["dashboard", "delete", "remove", "permanent", "dashboard-management"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Copy Dashboard",
                "description": "Copies a dashboard. Any values provided in the dashboard parameter replace those in the copied dashboard",
                "endpoint_path": "/rest/api/3/dashboard/{id}/copy",
                "http_method": "POST",
                "content": json.dumps({
                    "summary": "Copy an existing dashboard",
                    "description": "Copies a dashboard. Any values provided in the dashboard parameter replace those in the copied dashboard. The dashboard to be copied must be owned by or shared with the user.",
                    "permissions": "The dashboard to be copied must be owned by or shared with the user",
                    "data_security": "Exempt from app access rules",
                    "experimental": True,
                    "path_parameters": {
                        "id": {
                            "type": "string",
                            "description": "The ID of the dashboard to copy",
                            "required": True
                        }
                    },
                    "query_parameters": {
                        "extendAdminPermissions": {
                            "type": "boolean",
                            "description": "Whether to extend admin permissions",
                            "optional": True
                        }
                    },
                    "request_body": {
                        "type": "DashboardDetails",
                        "description": "Dashboard details for the copy",
                        "required_fields": ["name", "sharePermissions", "editPermissions"],
                        "properties": {
                            "name": {"type": "string", "required": True},
                            "description": {"type": "string", "optional": True},
                            "sharePermissions": {"type": "array", "required": True},
                            "editPermissions": {"type": "array", "required": True}
                        }
                    },
                    "example_request": {
                        "name": "Copy of My Dashboard",
                        "description": "A copy of the original dashboard",
                        "sharePermissions": [{"type": "global"}],
                        "editPermissions": []
                    },
                    "use_cases": [
                        "Create a backup of an existing dashboard",
                        "Create a template dashboard for different teams",
                        "Duplicate a dashboard with modifications"
                    ],
                    "oauth_scopes": {
                        "classic": "write:jira-work",
                        "granular": ["read:dashboard:jira", "write:dashboard:jira", "read:group:jira", "read:project:jira"]
                    },
                    "authentication": "Basic Auth or OAuth 2.0"
                }),
                "tags": ["dashboard", "copy", "post", "duplicate", "dashboard-management"],
                "version": "3", 
                "deprecated": False
            },
            
            {
                "title": "Search For Dashboards",
                "description": "Returns a paginated list of dashboards. Results can be filtered by owner.",
                "endpoint_path": "/rest/api/3/dashboard/search",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Search for dashboards with filtering options",
                    "description": "Returns a paginated list of dashboards. Results can be filtered by owner and other criteria.",
                    "permissions": "None",
                    "data_security": "Exempt from app access rules",
                    "query_parameters": {
                        "dashboardName": {
                            "type": "string",
                            "description": "String used to perform a case-insensitive partial match with dashboard name",
                            "optional": True
                        },
                        "accountId": {
                            "type": "string",
                            "description": "User account ID used to return dashboards with the matching owner",
                            "optional": True
                        },
                        "owner": {
                            "type": "string", 
                            "description": "This parameter is deprecated because of privacy changes. Use accountId instead",
                            "deprecated": True,
                            "optional": True
                        },
                        "groupname": {
                            "type": "string",
                            "description": "Group name used to return dashboards that are shared with a group that matches the name",
                            "optional": True
                        },
                        "projectId": {
                            "type": "integer",
                            "description": "Project ID used to return dashboards that are shared with a project that matches the ID",
                            "optional": True
                        },
                        "orderBy": {
                            "type": "string",
                            "description": "Ordering of the results",
                            "values": ["description", "-description", "+description", "favourite_count", "-favourite_count", "+favourite_count", "id", "-id", "+id", "is_favourite", "-is_favourite", "+is_favourite", "name", "-name", "+name", "owner", "-owner", "+owner", "popularity", "-popularity", "+popularity"],
                            "default": "name",
                            "optional": True
                        },
                        "startAt": {
                            "type": "integer",
                            "description": "The index of the first item to return",
                            "default": 0,
                            "optional": True
                        },
                        "maxResults": {
                            "type": "integer",
                            "description": "The maximum number of items to return per page",
                            "default": 20,
                            "maximum": 1000,
                            "optional": True
                        },
                        "expand": {
                            "type": "string",
                            "description": "Use expand to include additional information in the response",
                            "optional": True
                        }
                    },
                    "example_usage": [
                        "Search by name: ?dashboardName=System",
                        "Filter by owner: ?accountId=5b10a2844c20165700ede21g",
                        "Order results: ?orderBy=popularity",
                        "Paginate: ?startAt=20&maxResults=50"
                    ],
                    "oauth_scopes": {
                        "classic": "read:jira-work",
                        "granular": ["read:dashboard:jira", "read:group:jira", "read:project:jira", "read:project-role:jira", "read:user:jira"]
                    },
                    "authentication": "Basic Auth or OAuth 2.0"
                }),
                "tags": ["dashboard", "search", "filter", "query", "dashboard-management"],
                "version": "3",
                "deprecated": False
            }
        ]
        
        # Add each documentation entry
        added_count = 0
        for doc_data in dashboard_docs:
            # Check if documentation already exists
            existing = db.query(APIDocumentation).filter(
                APIDocumentation.provider_id == jira_provider.id,
                APIDocumentation.endpoint_path == doc_data["endpoint_path"],
                APIDocumentation.http_method == doc_data["http_method"]
            ).first()
            
            if existing:
                print(f"Documentation for {doc_data['title']} already exists, updating...")
                # Update existing documentation
                existing.title = doc_data["title"]
                existing.description = doc_data["description"]
                existing.content = doc_data["content"]
                existing.tags = doc_data["tags"]
                existing.version = doc_data["version"]
                existing.deprecated = doc_data["deprecated"]
            else:
                # Create new documentation
                doc = APIDocumentation(
                    provider_id=jira_provider.id,
                    title=doc_data["title"],
                    description=doc_data["description"],
                    endpoint_path=doc_data["endpoint_path"],
                    http_method=doc_data["http_method"],
                    content=doc_data["content"],
                    tags=doc_data["tags"],
                    version=doc_data["version"],
                    deprecated=doc_data["deprecated"]
                )
                db.add(doc)
                print(f"Added documentation: {doc_data['title']}")
                added_count += 1
        
        db.commit()
        print(f"\n✅ Successfully processed {len(dashboard_docs)} Dashboard documentation entries!")
        print(f"📝 Added {added_count} new entries")
        print(f"🔄 Updated {len(dashboard_docs) - added_count} existing entries")
        
    except Exception as e:
        print(f"❌ Error adding Dashboard documentation: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Adding comprehensive Jira Dashboard API documentation from Atlassian docs...")
    add_dashboard_docs()
    print("✅ Done!")