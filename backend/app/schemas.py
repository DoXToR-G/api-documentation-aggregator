from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class FetchStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


# API Provider schemas
class APIProviderBase(BaseModel):
    name: str
    display_name: str
    base_url: str
    documentation_url: Optional[str] = None
    icon_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class APIProviderCreate(APIProviderBase):
    pass


class APIProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    base_url: Optional[str] = None
    documentation_url: Optional[str] = None
    icon_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class APIProvider(APIProviderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# API Documentation schemas
class APIDocumentationBase(BaseModel):
    endpoint_path: str
    http_method: HTTPMethod
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    responses: Optional[Dict[str, Any]] = None
    examples: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    deprecated: bool = False


class APIDocumentationCreate(APIDocumentationBase):
    provider_id: int


class APIDocumentationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    responses: Optional[Dict[str, Any]] = None
    examples: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    deprecated: Optional[bool] = None


class APIDocumentation(APIDocumentationBase):
    id: int
    provider_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_fetched: Optional[datetime] = None
    provider: APIProvider

    model_config = {"from_attributes": True}


# Search schemas
class SearchRequest(BaseModel):
    query: str
    provider_ids: Optional[List[int]] = None
    methods: Optional[List[HTTPMethod]] = None
    tags: Optional[List[str]] = None
    deprecated: Optional[bool] = None
    limit: int = 20
    offset: int = 0


class SearchResult(BaseModel):
    id: int
    title: str
    description: Optional[str]
    endpoint_path: str
    http_method: HTTPMethod
    provider: APIProvider
    tags: Optional[List[str]]
    deprecated: bool
    score: float  # Relevance score


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    limit: int
    offset: int
    query: str


# Fetch Log schemas
class FetchLogBase(BaseModel):
    status: FetchStatus
    total_endpoints: int = 0
    new_endpoints: int = 0
    updated_endpoints: int = 0
    error_count: int = 0
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class FetchLogCreate(FetchLogBase):
    provider_id: int


class FetchLog(FetchLogBase):
    id: int
    provider_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    provider: APIProvider

    model_config = {"from_attributes": True}


# Analytics schemas
class SearchAnalytics(BaseModel):
    total_searches: int
    unique_queries: int
    top_queries: List[Dict[str, Any]]
    search_trends: Dict[str, int]


class ProviderStats(BaseModel):
    provider: APIProvider
    total_endpoints: int
    last_updated: Optional[datetime]
    fetch_success_rate: float


class DashboardStats(BaseModel):
    total_providers: int
    total_endpoints: int
    active_providers: int
    recent_searches: int
    provider_stats: List[ProviderStats]
    search_analytics: SearchAnalytics 