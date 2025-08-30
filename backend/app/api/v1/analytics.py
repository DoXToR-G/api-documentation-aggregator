from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app.db.database import get_db
from app.db.models import (
    APIProvider as APIProviderModel,
    APIDocumentation as APIDocumentationModel,
    SearchQuery as SearchQueryModel,
    FetchLog as FetchLogModel
)
from app.schemas import DashboardStats, SearchAnalytics, ProviderStats

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive dashboard statistics"""
    
    # Basic counts
    total_providers = db.query(APIProviderModel).count()
    active_providers = db.query(APIProviderModel).filter(APIProviderModel.is_active == True).count()
    total_endpoints = db.query(APIDocumentationModel).count()
    
    # Recent searches (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    recent_searches = db.query(SearchQueryModel).filter(
        SearchQueryModel.created_at >= yesterday
    ).count()
    
    # Provider statistics
    provider_stats = []
    providers = db.query(APIProviderModel).filter(APIProviderModel.is_active == True).all()
    
    for provider in providers:
        endpoint_count = db.query(APIDocumentationModel).filter(
            APIDocumentationModel.provider_id == provider.id
        ).count()
        
        # Get last successful fetch
        last_fetch = db.query(FetchLogModel).filter(
            FetchLogModel.provider_id == provider.id,
            FetchLogModel.status == "success"
        ).order_by(FetchLogModel.completed_at.desc()).first()
        
        # Calculate success rate (last 10 fetches)
        recent_fetches = db.query(FetchLogModel).filter(
            FetchLogModel.provider_id == provider.id
        ).order_by(FetchLogModel.started_at.desc()).limit(10).all()
        
        success_rate = 0.0
        if recent_fetches:
            successful = sum(1 for fetch in recent_fetches if fetch.status == "success")
            success_rate = successful / len(recent_fetches)
        
        provider_stat = ProviderStats(
            provider=provider,
            total_endpoints=endpoint_count,
            last_updated=last_fetch.completed_at if last_fetch else None,
            fetch_success_rate=success_rate
        )
        provider_stats.append(provider_stat)
    
    # Search analytics
    search_analytics = await get_search_analytics_data(db)
    
    return DashboardStats(
        total_providers=total_providers,
        total_endpoints=total_endpoints,
        active_providers=active_providers,
        recent_searches=recent_searches,
        provider_stats=provider_stats,
        search_analytics=search_analytics
    )


@router.get("/search", response_model=SearchAnalytics)
async def get_search_analytics(
    days: int = Query(30, ge=1, le=365, description="Time period in days"),
    db: Session = Depends(get_db)
):
    """Get detailed search analytics"""
    return await get_search_analytics_data(db, days)


async def get_search_analytics_data(db: Session, days: int = 30) -> SearchAnalytics:
    """Helper function to get search analytics data"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Total and unique searches
    total_searches = db.query(SearchQueryModel).filter(
        SearchQueryModel.created_at >= since_date
    ).count()
    
    unique_queries = db.query(SearchQueryModel.query).filter(
        SearchQueryModel.created_at >= since_date
    ).distinct().count()
    
    # Top queries
    top_queries_raw = db.query(
        SearchQueryModel.query,
        db.func.count(SearchQueryModel.id).label('count'),
        db.func.avg(SearchQueryModel.results_count).label('avg_results')
    ).filter(
        SearchQueryModel.created_at >= since_date
    ).group_by(
        SearchQueryModel.query
    ).order_by(
        db.func.count(SearchQueryModel.id).desc()
    ).limit(10).all()
    
    top_queries = [
        {
            "query": query,
            "count": count,
            "avg_results": float(avg_results or 0)
        }
        for query, count, avg_results in top_queries_raw
    ]
    
    # Search trends (daily counts for the period)
    search_trends = {}
    for i in range(days):
        date = datetime.utcnow().date() - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        count = db.query(SearchQueryModel).filter(
            SearchQueryModel.created_at >= date_start,
            SearchQueryModel.created_at <= date_end
        ).count()
        
        search_trends[date.isoformat()] = count
    
    return SearchAnalytics(
        total_searches=total_searches,
        unique_queries=unique_queries,
        top_queries=top_queries,
        search_trends=search_trends
    )


@router.get("/providers/{provider_id}/stats")
async def get_provider_analytics(
    provider_id: int,
    days: int = Query(30, ge=1, le=365, description="Time period in days"),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific provider"""
    provider = db.query(APIProviderModel).filter(APIProviderModel.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Basic stats
    total_endpoints = db.query(APIDocumentationModel).filter(
        APIDocumentationModel.provider_id == provider_id
    ).count()
    
    deprecated_endpoints = db.query(APIDocumentationModel).filter(
        APIDocumentationModel.provider_id == provider_id,
        APIDocumentationModel.deprecated == True
    ).count()
    
    # Fetch history
    fetch_logs = db.query(FetchLogModel).filter(
        FetchLogModel.provider_id == provider_id,
        FetchLogModel.started_at >= since_date
    ).order_by(FetchLogModel.started_at.desc()).all()
    
    # Method distribution
    method_stats = db.query(
        APIDocumentationModel.http_method,
        db.func.count(APIDocumentationModel.id).label('count')
    ).filter(
        APIDocumentationModel.provider_id == provider_id
    ).group_by(APIDocumentationModel.http_method).all()
    
    return {
        "provider": provider,
        "total_endpoints": total_endpoints,
        "deprecated_endpoints": deprecated_endpoints,
        "method_distribution": {method: count for method, count in method_stats},
        "fetch_history": [
            {
                "id": log.id,
                "status": log.status,
                "started_at": log.started_at,
                "completed_at": log.completed_at,
                "total_endpoints": log.total_endpoints,
                "new_endpoints": log.new_endpoints,
                "updated_endpoints": log.updated_endpoints,
                "error_count": log.error_count,
                "error_message": log.error_message
            }
            for log in fetch_logs
        ]
    }


@router.get("/fetch-logs")
async def get_fetch_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    provider_id: Optional[int] = Query(None, description="Filter by provider ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get fetch log history with optional filtering"""
    query = db.query(FetchLogModel)
    
    if provider_id:
        query = query.filter(FetchLogModel.provider_id == provider_id)
    
    if status:
        query = query.filter(FetchLogModel.status == status)
    
    logs = query.order_by(FetchLogModel.started_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "provider": log.provider.display_name,
                "status": log.status,
                "started_at": log.started_at,
                "completed_at": log.completed_at,
                "total_endpoints": log.total_endpoints,
                "new_endpoints": log.new_endpoints,
                "updated_endpoints": log.updated_endpoints,
                "error_count": log.error_count,
                "error_message": log.error_message
            }
            for log in logs
        ]
    } 