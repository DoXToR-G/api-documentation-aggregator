"""
Jira API Documentation Agent endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.services.jira_agent import get_jira_help

router = APIRouter()


class JiraAgentRequest(BaseModel):
    """Request model for Jira agent interactions"""
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "How do I create a new issue in Jira?"
            }
        }


class JiraAgentResponse(BaseModel):
    """Response model for Jira agent interactions"""
    endpoint: str
    method: str
    description: str
    authentication: str
    curl_example: str
    python_example: str
    common_issues: list[str]
    related_operations: list[str]
    agent_type: str
    confidence: str
    jira_docs_found: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "POST /rest/api/3/issue",
                "method": "POST",
                "description": "Creates a new issue in a Jira project",
                "authentication": "Basic Auth (email:api_token)",
                "curl_example": "curl -X POST ...",
                "python_example": "import requests...",
                "common_issues": ["Invalid project key", "Missing required fields"],
                "related_operations": ["Update issue", "Add comment"],
                "agent_type": "jira_ai_generated",
                "confidence": "high",
                "jira_docs_found": 3
            }
        }


@router.post("/ask", response_model=JiraAgentResponse)
async def ask_jira_agent(
    request: JiraAgentRequest,
    db: Session = Depends(get_db)
):
    """
    Ask the Jira API Documentation Agent for help
    
    The Jira agent specializes in:
    - Creating, updating, and managing Jira issues
    - Searching and filtering issues with JQL
    - User and project management
    - Workflow and transition operations
    - Comments, attachments, and metadata
    
    Provides ready-to-use code examples for Jira Cloud REST API v3.
    """
    try:
        response = await get_jira_help(
            user_request=request.question,
            db=db
        )
        
        return JiraAgentResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Jira Agent error: {str(e)}"
        )


@router.get("/ask")
async def ask_jira_agent_get(
    q: str = Query(..., description="Your question about Jira API", example="How to create an issue?"),
    db: Session = Depends(get_db)
):
    """
    Ask the Jira Agent via GET request (for easy testing)
    
    Example: /api/v1/jira/ask?q=how%20to%20create%20issue
    """
    request = JiraAgentRequest(question=q)
    return await ask_jira_agent(request, db)


@router.get("/examples")
async def get_jira_examples():
    """Get example questions you can ask the Jira agent"""
    return {
        "jira_agent_examples": [
            {
                "question": "How do I create a new issue?",
                "category": "Issue Management",
                "description": "Get code examples for creating Jira issues with all required fields"
            },
            {
                "question": "How to search for issues?", 
                "category": "Search & Query",
                "description": "Learn JQL syntax and search API usage"
            },
            {
                "question": "How to update an issue?",
                "category": "Issue Management", 
                "description": "Update issue fields, status, assignee, etc."
            },
            {
                "question": "How to add a comment to an issue?",
                "category": "Comments & Collaboration",
                "description": "Add comments, mentions, and attachments"
            },
            {
                "question": "How to assign an issue to someone?",
                "category": "Assignment & Users",
                "description": "Assign issues using accountId or email"
            },
            {
                "question": "How to get all issues in a project?",
                "category": "Project Management", 
                "description": "List and filter issues by project, status, etc."
            },
            {
                "question": "How to transition an issue status?",
                "category": "Workflow & Status",
                "description": "Move issues through workflow states"
            },
            {
                "question": "How to get issue details?",
                "category": "Data Retrieval",
                "description": "Fetch complete issue information with fields"
            },
            {
                "question": "How to create a custom field?",
                "category": "Configuration",
                "description": "Manage custom fields and project settings"
            },
            {
                "question": "How to upload an attachment?",
                "category": "Files & Attachments", 
                "description": "Attach files and images to issues"
            }
        ],
        "common_operations": {
            "CRUD Operations": [
                "Create issue", "Read/Get issue", "Update issue", "Delete issue"
            ],
            "Search & Filter": [
                "JQL queries", "Advanced search", "Filter results", "Pagination"
            ],
            "User Management": [
                "Get users", "Assign issues", "User permissions", "Groups"
            ],
            "Project Operations": [
                "List projects", "Project details", "Components", "Versions"
            ]
        },
        "authentication_help": {
            "basic_auth": "Use email:api_token with Base64 encoding",
            "api_token_url": "https://id.atlassian.com/manage-profile/security/api-tokens",
            "bearer_token": "OAuth 2.0 for app authentication"
        }
    }


@router.get("/common-operations")
async def get_common_jira_operations():
    """Get common Jira API operations and their endpoints"""
    return {
        "issue_operations": {
            "create_issue": {
                "endpoint": "POST /rest/api/3/issue",
                "description": "Create a new issue",
                "required_fields": ["project", "summary", "issuetype"]
            },
            "get_issue": {
                "endpoint": "GET /rest/api/3/issue/{issueIdOrKey}",
                "description": "Get issue details",
                "parameters": ["expand", "fields", "properties"]
            },
            "update_issue": {
                "endpoint": "PUT /rest/api/3/issue/{issueIdOrKey}",
                "description": "Update issue fields",
                "updatable_fields": ["summary", "description", "assignee", "priority"]
            },
            "delete_issue": {
                "endpoint": "DELETE /rest/api/3/issue/{issueIdOrKey}",
                "description": "Delete an issue",
                "parameters": ["deleteSubtasks"]
            }
        },
        "search_operations": {
            "search_issues": {
                "endpoint": "GET /rest/api/3/search",
                "description": "Search issues with JQL",
                "parameters": ["jql", "maxResults", "startAt", "fields"]
            },
            "advanced_search": {
                "endpoint": "POST /rest/api/3/search",
                "description": "Advanced search with POST body",
                "features": ["Complex JQL", "Field expansion", "Custom pagination"]
            }
        },
        "comment_operations": {
            "add_comment": {
                "endpoint": "POST /rest/api/3/issue/{issueIdOrKey}/comment",
                "description": "Add a comment to an issue",
                "features": ["Rich text", "Mentions", "Visibility restrictions"]
            },
            "get_comments": {
                "endpoint": "GET /rest/api/3/issue/{issueIdOrKey}/comment",
                "description": "Get all comments for an issue",
                "parameters": ["orderBy", "expand"]
            }
        },
        "assignment_operations": {
            "assign_issue": {
                "endpoint": "PUT /rest/api/3/issue/{issueIdOrKey}/assignee",
                "description": "Assign issue to a user",
                "required": ["accountId"]
            },
            "get_assignable_users": {
                "endpoint": "GET /rest/api/3/user/assignable/search",
                "description": "Find users who can be assigned",
                "parameters": ["query", "project"]
            }
        }
    }


@router.get("/jql-help")
async def get_jql_help():
    """Get help with JQL (Jira Query Language) syntax"""
    return {
        "jql_basics": {
            "description": "JQL is used to search and filter issues in Jira",
            "syntax": "field operator value",
            "example": "project = MYPROJ AND status = 'In Progress'"
        },
        "common_fields": {
            "project": "Project key or name",
            "status": "Issue status (To Do, In Progress, Done)",
            "assignee": "Assigned user (currentUser(), email, accountId)",
            "reporter": "User who created the issue",
            "priority": "Issue priority (Highest, High, Medium, Low, Lowest)",
            "issuetype": "Type of issue (Bug, Task, Story, Epic)",
            "created": "When the issue was created",
            "updated": "When the issue was last updated",
            "summary": "Issue title/summary",
            "description": "Issue description"
        },
        "common_operators": {
            "=": "Equals",
            "!=": "Not equals", 
            ">": "Greater than",
            ">=": "Greater than or equal",
            "<": "Less than",
            "<=": "Less than or equal",
            "IN": "In a list of values",
            "NOT IN": "Not in a list of values",
            "~": "Contains text",
            "!~": "Does not contain text",
            "IS EMPTY": "Field is empty",
            "IS NOT EMPTY": "Field is not empty"
        },
        "example_queries": [
            {
                "query": "project = MYPROJ",
                "description": "All issues in project MYPROJ"
            },
            {
                "query": "assignee = currentUser()",
                "description": "Issues assigned to me"
            },
            {
                "query": "status IN ('To Do', 'In Progress')",
                "description": "Open issues"
            },
            {
                "query": "created >= -7d",
                "description": "Issues created in the last 7 days"
            },
            {
                "query": "project = MYPROJ AND assignee = currentUser() AND status != Done",
                "description": "My active issues in MYPROJ"
            },
            {
                "query": "summary ~ 'bug' OR description ~ 'error'",
                "description": "Issues mentioning 'bug' or 'error'"
            }
        ],
        "functions": {
            "currentUser()": "The currently logged in user",
            "now()": "Current date and time",
            "startOfDay()": "Start of current day",
            "endOfDay()": "End of current day",
            "startOfWeek()": "Start of current week",
            "endOfWeek()": "End of current week"
        }
    }