"""
Script to add sample API documentation for testing the agent
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import Base, APIProvider, APIDocumentation
import json

def add_sample_jira_docs():
    """Add sample Jira documentation"""
    db = SessionLocal()
    
    try:
        # Get Jira provider
        jira_provider = db.query(APIProvider).filter(APIProvider.name == "jira_cloud").first()
        if not jira_provider:
            print("Jira Cloud provider not found!")
            return
        
        # Sample Jira documentation
        sample_docs = [
            {
                "title": "Create Issue",
                "description": "Creates an issue or, where the option is available, a sub-task",
                "endpoint_path": "/rest/api/3/issue",
                "http_method": "POST",
                "content": json.dumps({
                    "summary": "Create an issue in Jira",
                    "description": "This endpoint creates a new issue in a Jira project",
                    "parameters": {
                        "fields": {
                            "project": {"type": "object", "description": "Project key or ID"},
                            "summary": {"type": "string", "description": "Issue summary"},
                            "description": {"type": "string", "description": "Issue description"},
                            "issuetype": {"type": "object", "description": "Issue type"},
                            "assignee": {"type": "object", "description": "Assignee", "optional": True},
                            "priority": {"type": "object", "description": "Priority", "optional": True}
                        }
                    },
                    "authentication": "Basic Auth or Bearer Token",
                    "example_request": {
                        "fields": {
                            "project": {"key": "TEST"},
                            "summary": "New feature request",
                            "description": "Please add this new feature",
                            "issuetype": {"name": "Story"}
                        }
                    },
                    "example_response": {
                        "id": "12345",
                        "key": "TEST-123",
                        "self": "https://your-domain.atlassian.net/rest/api/3/issue/12345"
                    }
                }),
                "tags": ["issue", "create", "post", "project"],
                "category": "Issue Management",
                "version": "3",
                "deprecated": False
            },
            {
                "title": "Get Issue",
                "description": "Returns the details for an issue",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Retrieve issue details by ID or key",
                    "description": "Returns detailed information about a specific issue",
                    "parameters": {
                        "path": {
                            "issueIdOrKey": {"type": "string", "description": "Issue ID or key (e.g., TEST-123)"}
                        },
                        "query": {
                            "fields": {"type": "string", "description": "Comma-separated list of fields to return", "optional": True},
                            "expand": {"type": "string", "description": "Comma-separated list of entities to expand", "optional": True}
                        }
                    },
                    "authentication": "Basic Auth or Bearer Token",
                    "example_response": {
                        "id": "12345",
                        "key": "TEST-123",
                        "fields": {
                            "summary": "Issue summary",
                            "description": "Issue description",
                            "status": {"name": "Open"},
                            "priority": {"name": "Medium"}
                        }
                    }
                }),
                "tags": ["issue", "get", "retrieve", "details"],
                "category": "Issue Management",
                "version": "3",
                "deprecated": False
            },
            {
                "title": "Update Issue",
                "description": "Edits an issue",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}",
                "http_method": "PUT",
                "content": json.dumps({
                    "summary": "Update an existing issue",
                    "description": "Updates fields of an existing issue",
                    "parameters": {
                        "path": {
                            "issueIdOrKey": {"type": "string", "description": "Issue ID or key"}
                        },
                        "body": {
                            "fields": {"type": "object", "description": "Fields to update"}
                        }
                    },
                    "authentication": "Basic Auth or Bearer Token",
                    "example_request": {
                        "fields": {
                            "summary": "Updated summary",
                            "description": "Updated description"
                        }
                    }
                }),
                "tags": ["issue", "update", "put", "edit"],
                "category": "Issue Management", 
                "version": "3",
                "deprecated": False
            },
            {
                "title": "Add Comment",
                "description": "Adds a comment to an issue",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}/comment",
                "http_method": "POST",
                "content": json.dumps({
                    "summary": "Add comment to an issue",
                    "description": "Posts a new comment on an existing issue",
                    "parameters": {
                        "path": {
                            "issueIdOrKey": {"type": "string", "description": "Issue ID or key"}
                        },
                        "body": {
                            "body": {"type": "string", "description": "Comment text"},
                            "visibility": {"type": "object", "description": "Comment visibility", "optional": True}
                        }
                    },
                    "authentication": "Basic Auth or Bearer Token",
                    "example_request": {
                        "body": "This is a comment on the issue"
                    },
                    "example_response": {
                        "id": "10000",
                        "body": "This is a comment on the issue",
                        "author": {
                            "displayName": "John Doe"
                        }
                    }
                }),
                "tags": ["comment", "issue", "post", "add"],
                "category": "Issue Management",
                "version": "3", 
                "deprecated": False
            },
            {
                "title": "Assign Issue",
                "description": "Assigns an issue to a user",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}/assignee",
                "http_method": "PUT",
                "content": json.dumps({
                    "summary": "Assign issue to a user",
                    "description": "Changes the assignee of an issue",
                    "parameters": {
                        "path": {
                            "issueIdOrKey": {"type": "string", "description": "Issue ID or key"}
                        },
                        "body": {
                            "accountId": {"type": "string", "description": "User account ID"},
                            "name": {"type": "string", "description": "Username (deprecated)", "optional": True}
                        }
                    },
                    "authentication": "Basic Auth or Bearer Token",
                    "example_request": {
                        "accountId": "5b10a2844c20165700ede21g"
                    }
                }),
                "tags": ["assign", "issue", "user", "put"],
                "category": "Issue Management",
                "version": "3",
                "deprecated": False
            },
            {
                "title": "Get Projects",
                "description": "Returns all projects visible to the user",
                "endpoint_path": "/rest/api/3/project",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "List all accessible projects",
                    "description": "Returns a list of projects the user has access to",
                    "parameters": {
                        "query": {
                            "expand": {"type": "string", "description": "Comma-separated list of parameters to expand", "optional": True},
                            "recent": {"type": "integer", "description": "Number of recent projects to return", "optional": True}
                        }
                    },
                    "authentication": "Basic Auth or Bearer Token",
                    "example_response": [
                        {
                            "id": "10000",
                            "key": "TEST",
                            "name": "Test Project",
                            "projectTypeKey": "software"
                        }
                    ]
                }),
                "tags": ["project", "list", "get"],
                "category": "Project Management",
                "version": "3",
                "deprecated": False
            }
        ]
        
        # Add documentation
        for doc_data in sample_docs:
            # Check if documentation already exists
            existing = db.query(APIDocumentation).filter(
                APIDocumentation.provider_id == jira_provider.id,
                APIDocumentation.endpoint_path == doc_data["endpoint_path"],
                APIDocumentation.http_method == doc_data["http_method"]
            ).first()
            
            if existing:
                print(f"Documentation for {doc_data['title']} already exists, skipping...")
                continue
            
            doc = APIDocumentation(
                provider_id=jira_provider.id,
                title=doc_data["title"],
                description=doc_data["description"],
                endpoint_path=doc_data["endpoint_path"],
                http_method=doc_data["http_method"],
                content=doc_data["content"],
                tags=doc_data["tags"],
                category=doc_data["category"],
                version=doc_data["version"],
                deprecated=doc_data["deprecated"]
            )
            
            db.add(doc)
            print(f"Added documentation: {doc_data['title']}")
        
        db.commit()
        print(f"Successfully added {len(sample_docs)} Jira documentation entries!")
        
    except Exception as e:
        print(f"Error adding sample docs: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Adding sample Jira documentation...")
    add_sample_jira_docs()
    print("Done!")