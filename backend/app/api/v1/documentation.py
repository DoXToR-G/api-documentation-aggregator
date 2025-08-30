from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.models import APIDocumentation as APIDocumentationModel, APIProvider as APIProviderModel
from app.schemas import APIDocumentation, APIDocumentationCreate, APIDocumentationUpdate, HTTPMethod

router = APIRouter()


@router.get("/", response_model=List[APIDocumentation])
async def get_documentation(
    skip: int = 0,
    limit: int = 100,
    provider_id: Optional[int] = None,
    method: Optional[HTTPMethod] = None,
    deprecated: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get API documentation with optional filtering"""
    query = db.query(APIDocumentationModel)
    
    if provider_id:
        query = query.filter(APIDocumentationModel.provider_id == provider_id)
    
    if method:
        query = query.filter(APIDocumentationModel.http_method == method.value)
    
    if deprecated is not None:
        query = query.filter(APIDocumentationModel.deprecated == deprecated)
    
    if search:
        query = query.filter(
            APIDocumentationModel.title.ilike(f"%{search}%") |
            APIDocumentationModel.description.ilike(f"%{search}%") |
            APIDocumentationModel.endpoint_path.ilike(f"%{search}%")
        )
    
    documentation = query.offset(skip).limit(limit).all()
    return documentation


@router.get("/{doc_id}", response_model=APIDocumentation)
async def get_documentation_by_id(doc_id: int, db: Session = Depends(get_db)):
    """Get specific API documentation by ID"""
    doc = db.query(APIDocumentationModel).filter(APIDocumentationModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")
    return doc


@router.post("/", response_model=APIDocumentation)
async def create_documentation(doc: APIDocumentationCreate, db: Session = Depends(get_db)):
    """Create new API documentation"""
    # Verify provider exists
    provider = db.query(APIProviderModel).filter(APIProviderModel.id == doc.provider_id).first()
    if not provider:
        raise HTTPException(status_code=400, detail="Provider not found")
    
    # Check for duplicate endpoint
    existing = db.query(APIDocumentationModel).filter(
        APIDocumentationModel.provider_id == doc.provider_id,
        APIDocumentationModel.endpoint_path == doc.endpoint_path,
        APIDocumentationModel.http_method == doc.http_method.value
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Documentation for {doc.http_method.value} {doc.endpoint_path} already exists for this provider"
        )
    
    db_doc = APIDocumentationModel(**doc.dict())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc


@router.put("/{doc_id}", response_model=APIDocumentation)
async def update_documentation(
    doc_id: int,
    doc_update: APIDocumentationUpdate,
    db: Session = Depends(get_db)
):
    """Update API documentation"""
    db_doc = db.query(APIDocumentationModel).filter(APIDocumentationModel.id == doc_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Documentation not found")
    
    update_data = doc_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_doc, field, value)
    
    db.commit()
    db.refresh(db_doc)
    return db_doc


@router.delete("/{doc_id}")
async def delete_documentation(doc_id: int, db: Session = Depends(get_db)):
    """Delete API documentation"""
    db_doc = db.query(APIDocumentationModel).filter(APIDocumentationModel.id == doc_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Documentation not found")
    
    db.delete(db_doc)
    db.commit()
    return {"message": "Documentation deleted successfully"}


@router.get("/provider/{provider_id}/endpoints", response_model=List[APIDocumentation])
async def get_provider_endpoints(
    provider_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all endpoints for a specific provider"""
    # Verify provider exists
    provider = db.query(APIProviderModel).filter(APIProviderModel.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    endpoints = db.query(APIDocumentationModel)\
        .filter(APIDocumentationModel.provider_id == provider_id)\
        .offset(skip).limit(limit).all()
    
    return endpoints


@router.get("/stats/overview")
async def get_documentation_stats(db: Session = Depends(get_db)):
    """Get overview statistics for API documentation"""
    total_docs = db.query(APIDocumentationModel).count()
    total_providers = db.query(APIProviderModel).filter(APIProviderModel.is_active == True).count()
    deprecated_docs = db.query(APIDocumentationModel).filter(APIDocumentationModel.deprecated == True).count()
    
    # Method distribution
    method_stats = db.query(
        APIDocumentationModel.http_method,
        db.func.count(APIDocumentationModel.id).label('count')
    ).group_by(APIDocumentationModel.http_method).all()
    
    return {
        "total_documentation": total_docs,
        "total_providers": total_providers,
        "deprecated_documentation": deprecated_docs,
        "method_distribution": {method: count for method, count in method_stats}
    } 