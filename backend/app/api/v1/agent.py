"""
AI Agent API endpoints for intelligent API documentation assistance
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.services.ai_agent import get_agent_response

router = APIRouter()


class AgentRequest(BaseModel):
    """Request model for agent interactions"""
    query: str
    provider: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How to create a task in Jira?",
                "provider": "jira"
            }
        }


class AgentResponse(BaseModel):
    """Response model for agent interactions"""
    endpoint: str
    method: str
    description: str
    curl_example: str
    python_example: str
    troubleshooting: list[str]
    related_operations: list[str]
    agent_type: str
    confidence: str
    sources: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "POST /rest/api/3/issue",
                "method": "POST", 
                "description": "Create a new issue in Jira",
                "curl_example": "curl -X POST ...",
                "python_example": "import requests...",
                "troubleshooting": ["Check API token", "Verify permissions"],
                "related_operations": ["Update issue", "Add comment"],
                "agent_type": "ai_generated",
                "confidence": "high",
                "sources": 3
            }
        }


@router.post("/ask", response_model=AgentResponse)
async def ask_agent(
    request: AgentRequest,
    db: Session = Depends(get_db)
):
    """
    Ask the AI agent for help with API operations
    
    The agent will:
    1. Search relevant documentation
    2. Generate code examples (cURL, Python)
    3. Provide troubleshooting tips
    4. Suggest related operations
    """
    try:
        response = await get_agent_response(
            user_request=request.query,
            provider_name=request.provider,
            db=db
        )
        
        return AgentResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@router.get("/ask")
async def ask_agent_get(
    q: str = Query(..., description="Your question about API usage"),
    provider: Optional[str] = Query(None, description="Specific API provider (jira, datadog, kubernetes, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Ask the AI agent via GET request (for easy testing)
    
    Example: /api/v1/agent/ask?q=create%20jira%20issue&provider=jira
    """
    request = AgentRequest(query=q, provider=provider)
    return await ask_agent(request, db)


@router.get("/examples")
async def get_example_queries():
    """Get example queries to help users understand what the agent can do"""
    return {
        "examples": [
            {
                "query": "How to create a task in Jira?",
                "provider": "jira",
                "description": "Get code examples for creating Jira issues"
            },
            {
                "query": "List all pods in Kubernetes",
                "provider": "kubernetes", 
                "description": "Get kubectl and API examples for listing pods"
            },
            {
                "query": "Get metrics from Datadog",
                "provider": "datadog",
                "description": "Query Datadog API for metrics data"
            },
            {
                "query": "Create dashboard in Grafana",
                "provider": "grafana",
                "description": "API calls to create Grafana dashboards"
            },
            {
                "query": "Search logs in Kibana",
                "provider": "kibana",
                "description": "Elasticsearch queries via Kibana API"
            },
            {
                "query": "Configure alerts in Prometheus",
                "provider": "prometheus",
                "description": "Set up Prometheus alerting rules"
            }
        ],
        "tips": [
            "Be specific about what you want to do",
            "Mention the provider if you have a preference", 
            "Ask about specific operations like 'create', 'update', 'delete'",
            "Include context like 'project management', 'monitoring', 'deployment'"
        ]
    }


@router.get("/providers")
async def get_supported_providers():
    """Get list of supported providers for the agent"""
    return {
        "providers": [
            {
                "name": "jira",
                "display_name": "Jira Cloud",
                "description": "Atlassian Jira project management",
                "capabilities": ["Issues", "Projects", "Users", "Workflows"]
            },
            {
                "name": "datadog", 
                "display_name": "Datadog",
                "description": "Monitoring and analytics platform",
                "capabilities": ["Metrics", "Logs", "Traces", "Dashboards"]
            },
            {
                "name": "kubernetes",
                "display_name": "Kubernetes", 
                "description": "Container orchestration platform",
                "capabilities": ["Pods", "Services", "Deployments", "ConfigMaps"]
            },
            {
                "name": "prometheus",
                "display_name": "Prometheus",
                "description": "Monitoring and alerting toolkit", 
                "capabilities": ["Metrics", "Alerts", "Queries", "Rules"]
            },
            {
                "name": "grafana",
                "display_name": "Grafana",
                "description": "Visualization and dashboards",
                "capabilities": ["Dashboards", "Panels", "Data Sources", "Alerts"]
            },
            {
                "name": "kibana",
                "display_name": "Kibana", 
                "description": "Elasticsearch data exploration",
                "capabilities": ["Search", "Visualizations", "Dashboards", "Index Management"]
            }
        ]
    }