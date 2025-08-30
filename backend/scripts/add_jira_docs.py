"""
Script to add comprehensive Jira Cloud REST API documentation
Based on official Atlassian Jira Cloud REST API v3 documentation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import APIProvider, APIDocumentation
import json

def add_comprehensive_jira_docs():
    """Add comprehensive Jira Cloud REST API v3 documentation"""
    db = SessionLocal()
    
    try:
        # Get Jira Cloud provider
        jira_provider = db.query(APIProvider).filter(APIProvider.name == "jira_cloud").first()
        if not jira_provider:
            print("Jira Cloud provider not found!")
            return
        
        # Comprehensive Jira documentation based on official API
        jira_docs = [
            # ISSUE OPERATIONS
            {
                "title": "Create Issue",
                "description": "Creates an issue or a sub-task from a JSON representation",
                "endpoint_path": "/rest/api/3/issue",
                "http_method": "POST",
                "content": json.dumps({
                    "summary": "Create a new issue in Jira project",
                    "description": "Creates issues and sub-tasks. The fields that can be set on issue creation are project, summary, description, issuetype, and any other fields supported by the create screen for the issue type.",
                    "required_fields": ["project", "summary", "issuetype"],
                    "optional_fields": ["description", "assignee", "priority", "labels", "components", "fixVersions", "duedate", "parent"],
                    "request_example": {
                        "fields": {
                            "project": {"key": "TEST"},
                            "summary": "Something's wrong",
                            "description": "Look into this one",
                            "issuetype": {"name": "Bug"},
                            "assignee": {"accountId": "5b10a2844c20165700ede21g"},
                            "priority": {"name": "High"},
                            "labels": ["bugfix", "blitz_test"],
                            "components": [{"name": "Component 1"}],
                            "duedate": "2023-12-31"
                        }
                    },
                    "response_example": {
                        "id": "10000",
                        "key": "TEST-24",
                        "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000"
                    },
                    "authentication": "Basic Auth with email:api_token or OAuth 2.0",
                    "permissions": "Browse Projects and Create Issues permission for the project",
                    "rate_limits": "Standard rate limits apply"
                }),
                "tags": ["issue", "create", "post", "project", "fields", "issue-management"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Get Issue",
                "description": "Returns the details for an issue by issue ID or key",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Retrieve detailed information about a specific issue",
                    "description": "Returns a full representation of the issue for the given issue key or ID. The fields returned in the response can be configured using the 'fields' parameter.",
                    "path_parameters": {
                        "issueIdOrKey": "The ID or key of the issue (e.g., TEST-123 or 10000)"
                    },
                    "query_parameters": {
                        "fields": "Comma-separated list of fields to return (default: all navigable fields)",
                        "expand": "Use expand to include additional information in the response (renderedFields, names, schema, transitions, operations, changelog)",
                        "properties": "Comma-separated list of properties to return"
                    },
                    "expand_options": ["renderedFields", "names", "schema", "transitions", "operations", "editmeta", "changelog", "versionedRepresentations"],
                    "field_examples": ["summary", "status", "assignee", "reporter", "created", "updated", "description", "priority", "labels"],
                    "response_example": {
                        "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
                        "id": "10002",
                        "self": "https://your-domain.atlassian.net/rest/api/3/issue/10002",
                        "key": "TEST-1",
                        "fields": {
                            "summary": "Bug in login system",
                            "status": {"name": "Open", "id": "1"},
                            "assignee": {"displayName": "John Doe", "accountId": "5b10a2844c20165700ede21g"},
                            "reporter": {"displayName": "Jane Smith", "accountId": "5b10a0efcc4c6f8abc123456"},
                            "created": "2023-01-15T10:30:00.000+0000",
                            "updated": "2023-01-15T14:20:00.000+0000",
                            "priority": {"name": "High", "id": "2"}
                        }
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Browse Projects permission for the project containing the issue"
                }),
                "tags": ["issue", "get", "retrieve", "details", "fields", "issue-management"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Update Issue",
                "description": "Edits an issue from a JSON representation",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}",
                "http_method": "PUT",
                "content": json.dumps({
                    "summary": "Update fields of an existing issue",
                    "description": "Edits an issue. Issue properties and fields can be updated. To update an issue field, specify the field name and the new value. Complex fields like assignee require specific object formats.",
                    "path_parameters": {
                        "issueIdOrKey": "The ID or key of the issue"
                    },
                    "updatable_fields": ["summary", "description", "assignee", "priority", "labels", "components", "fixVersions", "duedate"],
                    "request_example": {
                        "fields": {
                            "summary": "Updated bug summary",
                            "description": "Updated description with more details",
                            "assignee": {"accountId": "5b10a2844c20165700ede21g"},
                            "priority": {"name": "Critical"},
                            "labels": ["urgent", "customer-issue"],
                            "duedate": "2023-12-25"
                        }
                    },
                    "assignee_formats": {
                        "by_account_id": {"accountId": "5b10a2844c20165700ede21g"},
                        "unassign": {"accountId": None}
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Edit Issues permission for the project",
                    "response": "204 No Content on success"
                }),
                "tags": ["issue", "update", "put", "edit", "fields", "issue-management"],
                "version": "3", 
                "deprecated": False
            },
            
            {
                "title": "Delete Issue",
                "description": "Deletes an issue",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}",
                "http_method": "DELETE",
                "content": json.dumps({
                    "summary": "Delete an issue permanently",
                    "description": "Deletes an issue. An issue cannot be deleted if it has one or more subtasks. To delete an issue with subtasks, set deleteSubtasks to true.",
                    "path_parameters": {
                        "issueIdOrKey": "The ID or key of the issue"
                    },
                    "query_parameters": {
                        "deleteSubtasks": "Whether the issue's subtasks are deleted when the issue is deleted (default: false)"
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Delete Issues permission for the project",
                    "response": "204 No Content on success",
                    "important_notes": [
                        "Deletion is permanent and cannot be undone",
                        "Issues with subtasks require deleteSubtasks=true parameter",
                        "All issue links and comments are also deleted"
                    ]
                }),
                "tags": ["issue", "delete", "remove", "permanent", "issue-management"],
                "version": "3",
                "deprecated": False
            },
            
            # SEARCH OPERATIONS
            {
                "title": "Search Issues (JQL)",
                "description": "Search for issues using JQL (Jira Query Language)",
                "endpoint_path": "/rest/api/3/search",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Search for issues using JQL queries",
                    "description": "Searches for issues using JQL. The search results can be sorted and paginated. Fields can be specified to return only required data.",
                    "query_parameters": {
                        "jql": "JQL query string",
                        "startAt": "Index of the first item to return (default: 0)",
                        "maxResults": "Maximum number of issues to return (default: 50, max: 100)",
                        "fields": "List of fields to return for each issue",
                        "expand": "Use expand to include additional information",
                        "validateQuery": "Whether to validate the JQL query (default: true)"
                    },
                    "jql_examples": [
                        "project = TEST",
                        "assignee = currentUser()",
                        "status IN ('To Do', 'In Progress')",
                        "created >= -7d",
                        "project = TEST AND assignee = currentUser() AND status != Done",
                        "summary ~ 'bug' OR description ~ 'error'",
                        "priority = High AND created >= startOfWeek()",
                        "fixVersion in unreleasedVersions()"
                    ],
                    "jql_fields": ["project", "status", "assignee", "reporter", "priority", "issuetype", "created", "updated", "summary", "description"],
                    "jql_operators": ["=", "!=", ">", ">=", "<", "<=", "IN", "NOT IN", "~", "!~", "IS EMPTY", "IS NOT EMPTY"],
                    "jql_functions": ["currentUser()", "now()", "startOfDay()", "endOfDay()", "startOfWeek()", "endOfWeek()"],
                    "response_example": {
                        "expand": "schema,names",
                        "startAt": 0,
                        "maxResults": 50,
                        "total": 1,
                        "issues": [
                            {
                                "expand": "",
                                "id": "10001",
                                "self": "https://your-domain.atlassian.net/rest/api/3/issue/10001",
                                "key": "TEST-1",
                                "fields": {
                                    "summary": "Sample issue",
                                    "status": {"name": "Open"},
                                    "assignee": {"displayName": "John Doe"}
                                }
                            }
                        ]
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Browse Projects permission for projects in the search scope"
                }),
                "tags": ["search", "jql", "query", "filter", "issues", "search-query"],
                "version": "3",
                "deprecated": False
            },
            
            # COMMENT OPERATIONS
            {
                "title": "Add Comment to Issue",
                "description": "Adds a comment to an issue",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}/comment",
                "http_method": "POST",
                "content": json.dumps({
                    "summary": "Add a comment to an existing issue",
                    "description": "Adds a comment to an issue. Comments can include rich text formatting, mentions, and visibility restrictions.",
                    "path_parameters": {
                        "issueIdOrKey": "The ID or key of the issue"
                    },
                    "request_fields": {
                        "body": "Content of the comment (required)",
                        "visibility": "Who can view this comment (optional)",
                        "author": "Automatically set to current user"
                    },
                    "body_formats": {
                        "plain_text": "Simple text comment",
                        "mention": "Comment with @accountId mention",
                        "rich_text": "ADF (Atlassian Document Format) for rich formatting"
                    },
                    "request_example": {
                        "body": "This is a comment about the issue. CC: @5b10a2844c20165700ede21g",
                        "visibility": {
                            "type": "role",
                            "value": "Administrators"
                        }
                    },
                    "visibility_options": {
                        "public": "No visibility restriction",
                        "role_based": {"type": "role", "value": "Administrators"},
                        "group_based": {"type": "group", "value": "jira-developers"}
                    },
                    "response_example": {
                        "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000",
                        "id": "10000",
                        "author": {
                            "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g",
                            "accountId": "5b10a2844c20165700ede21g",
                            "displayName": "John Doe"
                        },
                        "body": "This is a comment about the issue.",
                        "created": "2023-01-15T10:30:00.000+0000",
                        "updated": "2023-01-15T10:30:00.000+0000"
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Add Comments permission for the project"
                }),
                "tags": ["comment", "add", "post", "mention", "visibility", "comments-collaboration"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Get Issue Comments",
                "description": "Returns all comments for an issue",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}/comment",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Retrieve all comments for a specific issue",
                    "description": "Returns a paginated list of all comments for an issue. Results can be ordered and expanded to include additional information.",
                    "path_parameters": {
                        "issueIdOrKey": "The ID or key of the issue"
                    },
                    "query_parameters": {
                        "startAt": "Index of the first comment to return (default: 0)",
                        "maxResults": "Maximum number of comments to return (default: 5000)",
                        "orderBy": "Order results by created date (+created, -created) (default: +created)",
                        "expand": "Use expand to include additional information about comments"
                    },
                    "expand_options": ["renderedBody", "properties"],
                    "response_example": {
                        "startAt": 0,
                        "maxResults": 1,
                        "total": 1,
                        "comments": [
                            {
                                "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000",
                                "id": "10000",
                                "author": {
                                    "displayName": "John Doe",
                                    "accountId": "5b10a2844c20165700ede21g"
                                },
                                "body": "This is a comment about the issue.",
                                "created": "2023-01-15T10:30:00.000+0000",
                                "updated": "2023-01-15T10:30:00.000+0000"
                            }
                        ]
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Browse Projects permission and appropriate comment visibility permissions"
                }),
                "tags": ["comment", "get", "list", "retrieve", "pagination", "comments-collaboration"],
                "version": "3",
                "deprecated": False
            },
            
            # ASSIGNMENT OPERATIONS
            {
                "title": "Assign Issue",
                "description": "Assigns an issue to a user",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}/assignee",
                "http_method": "PUT",
                "content": json.dumps({
                    "summary": "Assign an issue to a specific user",
                    "description": "Assigns an issue to a user. You can assign by account ID. To unassign an issue, set the assignee to null.",
                    "path_parameters": {
                        "issueIdOrKey": "The ID or key of the issue"
                    },
                    "request_body": {
                        "accountId": "The account ID of the user to assign the issue to"
                    },
                    "request_examples": {
                        "assign_user": {"accountId": "5b10a2844c20165700ede21g"},
                        "unassign": {"accountId": None}
                    },
                    "user_identification": {
                        "account_id": "Preferred method - use user's account ID",
                        "note": "Username and user key are deprecated in Jira Cloud"
                    },
                    "get_account_id": {
                        "search_users": "Use /rest/api/3/user/search to find users and their account IDs",
                        "assignable_users": "Use /rest/api/3/user/assignable/search for users who can be assigned to issues"
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Assign Issues permission for the project",
                    "response": "204 No Content on success"
                }),
                "tags": ["assign", "assignee", "user", "put", "unassign", "assignment-users"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Get Assignable Users",
                "description": "Find users that can be assigned to issues",
                "endpoint_path": "/rest/api/3/user/assignable/search",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Search for users who can be assigned to issues",
                    "description": "Returns a list of users that can be assigned to issues. The search can be filtered by project, issue key, or username.",
                    "query_parameters": {
                        "query": "A query string to match usernames, display names, or email addresses",
                        "project": "The project key or ID to find assignable users for",
                        "issueKey": "The issue key for the issue being edited (optional)",
                        "startAt": "Index of the first user to return (default: 0)",
                        "maxResults": "Maximum number of users to return (default: 50, max: 1000)"
                    },
                    "usage_examples": [
                        "Find all assignable users in project: ?project=TEST",
                        "Search for user by name: ?query=john&project=TEST",
                        "Find users for specific issue: ?issueKey=TEST-123"
                    ],
                    "response_example": [
                        {
                            "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g",
                            "accountId": "5b10a2844c20165700ede21g",
                            "accountType": "atlassian",
                            "displayName": "John Doe",
                            "emailAddress": "john.doe@example.com",
                            "avatarUrls": {
                                "48x48": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/..."
                            },
                            "active": True
                        }
                    ],
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Browse Users global permission and Browse Projects permission for the project"
                }),
                "tags": ["user", "assignable", "search", "project", "permissions", "assignment-users"],
                "version": "3",
                "deprecated": False
            },
            
            # PROJECT OPERATIONS
            {
                "title": "Get All Projects",
                "description": "Returns all projects visible to the user",
                "endpoint_path": "/rest/api/3/project",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Get a list of all projects accessible to the current user",
                    "description": "Returns a list of projects that the user has permission to browse. Project details can be expanded using the expand parameter.",
                    "query_parameters": {
                        "expand": "Use expand to include additional information about each project",
                        "recent": "Returns the user's most recently accessed projects (max: 20)",
                        "properties": "Comma-separated list of project properties to return"
                    },
                    "expand_options": [
                        "description", "lead", "issueTypes", "url", "projectKeys", 
                        "permissions", "insight", "deleted", "projectCategory"
                    ],
                    "response_example": [
                        {
                            "expand": "description,lead,issueTypes,url,projectKeys",
                            "self": "https://your-domain.atlassian.net/rest/api/3/project/10000",
                            "id": "10000",
                            "key": "TEST",
                            "name": "Test Project",
                            "avatarUrls": {
                                "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000"
                            },
                            "projectCategory": {
                                "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000",
                                "id": "10000", 
                                "name": "Development",
                                "description": "Development projects"
                            },
                            "simplified": False,
                            "style": "classic",
                            "isPrivate": False
                        }
                    ],
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Browse Projects permission for each project returned"
                }),
                "tags": ["project", "list", "get", "browse", "accessible", "project-management"],
                "version": "3", 
                "deprecated": False
            },
            
            # TRANSITION OPERATIONS
            {
                "title": "Get Issue Transitions",
                "description": "Get available transitions for an issue",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}/transitions",
                "http_method": "GET",
                "content": json.dumps({
                    "summary": "Get the list of transitions available for an issue",
                    "description": "Returns a list of transitions available for an issue. The list will be different for each issue, as it depends on the issue's status and the user's permissions.",
                    "path_parameters": {
                        "issueIdOrKey": "The ID or key of the issue"
                    },
                    "query_parameters": {
                        "expand": "Use expand to include additional information about transitions",
                        "transitionId": "ID of a specific transition to return",
                        "skipRemoteOnlyCondition": "Whether transitions with 'remote only' condition are included (default: false)"
                    },
                    "expand_options": ["transitions.fields"],
                    "response_example": {
                        "expand": "transitions",
                        "transitions": [
                            {
                                "id": "2",
                                "name": "Close Issue",
                                "to": {
                                    "self": "https://your-domain.atlassian.net/rest/api/3/status/6",
                                    "description": "The issue is closed",
                                    "name": "Closed",
                                    "id": "6",
                                    "statusCategory": {
                                        "self": "https://your-domain.atlassian.net/rest/api/3/statuscategory/3",
                                        "id": 3,
                                        "key": "done",
                                        "colorName": "green",
                                        "name": "Done"
                                    }
                                },
                                "hasScreen": False,
                                "isGlobal": True,
                                "isInitial": False,
                                "isAvailable": True
                            }
                        ]
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Browse Projects permission for the project"
                }),
                "tags": ["transition", "status", "workflow", "get", "available", "workflow-status"],
                "version": "3",
                "deprecated": False
            },
            
            {
                "title": "Transition Issue",
                "description": "Perform a workflow transition on an issue",
                "endpoint_path": "/rest/api/3/issue/{issueIdOrKey}/transitions",
                "http_method": "POST",
                "content": json.dumps({
                    "summary": "Perform a workflow transition on an issue",
                    "description": "Performs an issue transition and, if the transition has a screen, updates the fields from the transition screen. The fields that can be set on transition, in either the fields parameter or the update parameter, are determined by the conditions of the workflow transition.",
                    "path_parameters": {
                        "issueIdOrKey": "The ID or key of the issue"
                    },
                    "request_fields": {
                        "transition": "Details of the transition being performed (required)",
                        "fields": "Fields to update during the transition (optional)",
                        "update": "Additional field updates to perform (optional)"
                    },
                    "request_example": {
                        "transition": {
                            "id": "5"
                        },
                        "fields": {
                            "resolution": {
                                "name": "Fixed"
                            },
                            "assignee": {
                                "accountId": "5b10a2844c20165700ede21g"
                            }
                        },
                        "update": {
                            "comment": [
                                {
                                    "add": {
                                        "body": "Issue has been resolved"
                                    }
                                }
                            ]
                        }
                    },
                    "common_transitions": {
                        "start_progress": "Move issue from 'To Do' to 'In Progress'",
                        "resolve_issue": "Move issue to 'Done' status with resolution",
                        "reopen_issue": "Move closed issue back to 'Open'",
                        "close_issue": "Move issue to final 'Closed' state"
                    },
                    "authentication": "Basic Auth or OAuth 2.0",
                    "permissions": "Browse Projects permission and Transition Issues permission for the transition",
                    "response": "204 No Content on success"
                }),
                "tags": ["transition", "workflow", "status", "post", "move", "workflow-status"],
                "version": "3",
                "deprecated": False
            }
        ]
        
        # Add each documentation entry
        added_count = 0
        for doc_data in jira_docs:
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
        print(f"\n✅ Successfully processed {len(jira_docs)} Jira documentation entries!")
        print(f"📝 Added {added_count} new entries")
        print(f"🔄 Updated {len(jira_docs) - added_count} existing entries")
        
    except Exception as e:
        print(f"❌ Error adding Jira documentation: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Adding comprehensive Jira Cloud REST API documentation...")
    add_comprehensive_jira_docs()
    print("✅ Done!")