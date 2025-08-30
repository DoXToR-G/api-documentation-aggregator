from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.models import APIDocumentation as APIDocumentationModel, SearchQuery as SearchQueryModel
from app.schemas import SearchRequest, SearchResponse, SearchResult, HTTPMethod
from app.search.elasticsearch_client import search_documentation

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_documentation_endpoint(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Search API documentation using Elasticsearch"""
    try:
        # Perform search using Elasticsearch
        results = await search_documentation(search_request)
        
        # Log search query for analytics
        search_log = SearchQueryModel(
            query=search_request.query,
            results_count=len(results.results)
        )
        db.add(search_log)
        db.commit()
        
        return results
    
    except Exception as e:
        # Fallback to database search if Elasticsearch is not available
        return await fallback_database_search(search_request, db)


@router.get("/", response_model=SearchResponse)
async def search_documentation_get(
    q: str = Query(..., description="Search query"),
    provider_ids: Optional[List[int]] = Query(None, description="Filter by provider IDs"),
    methods: Optional[List[HTTPMethod]] = Query(None, description="Filter by HTTP methods"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    deprecated: Optional[bool] = Query(None, description="Filter by deprecated status"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Search API documentation via GET request"""
    search_request = SearchRequest(
        query=q,
        provider_ids=provider_ids,
        methods=methods,
        tags=tags,
        deprecated=deprecated,
        limit=limit,
        offset=offset
    )
    
    return await search_documentation_endpoint(search_request, db)


async def fallback_database_search(search_request: SearchRequest, db: Session) -> SearchResponse:
    """Fallback database search when Elasticsearch is not available"""
    query = db.query(APIDocumentationModel)
    
    # Apply filters
    if search_request.provider_ids:
        query = query.filter(APIDocumentationModel.provider_id.in_(search_request.provider_ids))
    
    if search_request.methods:
        method_values = [method.value for method in search_request.methods]
        query = query.filter(APIDocumentationModel.http_method.in_(method_values))
    
    if search_request.deprecated is not None:
        query = query.filter(APIDocumentationModel.deprecated == search_request.deprecated)
    
    # Text search (basic ILIKE search)
    if search_request.query:
        search_term = f"%{search_request.query}%"
        query = query.filter(
            APIDocumentationModel.title.ilike(search_term) |
            APIDocumentationModel.description.ilike(search_term) |
            APIDocumentationModel.endpoint_path.ilike(search_term) |
            APIDocumentationModel.content.ilike(search_term)
        )
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    results = query.offset(search_request.offset).limit(search_request.limit).all()
    
    # Convert to search results
    search_results = []
    for doc in results:
        search_result = SearchResult(
            id=doc.id,
            title=doc.title,
            description=doc.description,
            endpoint_path=doc.endpoint_path,
            http_method=HTTPMethod(doc.http_method),
            provider=doc.provider,
            tags=doc.tags or [],
            deprecated=doc.deprecated,
            score=1.0  # Default score for database search
        )
        search_results.append(search_result)
    
    return SearchResponse(
        results=search_results,
        total=total,
        limit=search_request.limit,
        offset=search_request.offset,
        query=search_request.query
    )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Partial search query"),
    limit: int = Query(10, ge=1, le=20, description="Number of suggestions"),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on partial query"""
    # Search in titles and endpoint paths for suggestions
    suggestions = db.query(APIDocumentationModel.title, APIDocumentationModel.endpoint_path)\
        .filter(
            APIDocumentationModel.title.ilike(f"%{q}%") |
            APIDocumentationModel.endpoint_path.ilike(f"%{q}%")
        )\
        .distinct()\
        .limit(limit)\
        .all()
    
    # Create unique suggestions list
    suggestion_set = set()
    for title, endpoint in suggestions:
        if title and q.lower() in title.lower():
            suggestion_set.add(title)
        if endpoint and q.lower() in endpoint.lower():
            suggestion_set.add(endpoint)
    
    return {
        "suggestions": list(suggestion_set)[:limit],
        "query": q
    }


@router.get("/popular")
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=50, description="Number of popular searches"),
    days: int = Query(7, ge=1, le=30, description="Time period in days"),
    db: Session = Depends(get_db)
):
    """Get popular search queries from the last N days"""
    from datetime import datetime, timedelta
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    popular_queries = db.query(
        SearchQueryModel.query,
        db.func.count(SearchQueryModel.id).label('search_count'),
        db.func.avg(SearchQueryModel.results_count).label('avg_results')
    ).filter(
        SearchQueryModel.created_at >= since_date
    ).group_by(
        SearchQueryModel.query
    ).order_by(
        db.func.count(SearchQueryModel.id).desc()
    ).limit(limit).all()
    
    return {
        "popular_searches": [
            {
                "query": query,
                "search_count": count,
                "avg_results": float(avg_results or 0)
            }
            for query, count, avg_results in popular_queries
        ],
        "period_days": days
    } 