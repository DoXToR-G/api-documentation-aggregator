from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import APIProvider as APIProviderModel
from app.schemas import APIProvider, APIProviderCreate, APIProviderUpdate

router = APIRouter()


@router.get("/", response_model=List[APIProvider])
async def get_providers(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all API providers"""
    query = db.query(APIProviderModel)
    
    if active_only:
        query = query.filter(APIProviderModel.is_active == True)
    
    providers = query.offset(skip).limit(limit).all()
    return providers


@router.get("/{provider_id}", response_model=APIProvider)
async def get_provider(provider_id: int, db: Session = Depends(get_db)):
    """Get specific API provider by ID"""
    provider = db.query(APIProviderModel).filter(APIProviderModel.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.post("/", response_model=APIProvider, status_code=status.HTTP_201_CREATED)
async def create_provider(provider: APIProviderCreate, db: Session = Depends(get_db)):
    """Create new API provider"""
    # Check if provider with this name already exists
    existing = db.query(APIProviderModel).filter(APIProviderModel.name == provider.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Provider with name '{provider.name}' already exists"
        )
    
    db_provider = APIProviderModel(**provider.dict())
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider


@router.put("/{provider_id}", response_model=APIProvider)
async def update_provider(
    provider_id: int,
    provider_update: APIProviderUpdate,
    db: Session = Depends(get_db)
):
    """Update API provider"""
    db_provider = db.query(APIProviderModel).filter(APIProviderModel.id == provider_id).first()
    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    update_data = provider_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_provider, field, value)
    
    db.commit()
    db.refresh(db_provider)
    return db_provider


@router.delete("/{provider_id}")
async def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    """Delete API provider (soft delete by setting is_active=False)"""
    db_provider = db.query(APIProviderModel).filter(APIProviderModel.id == provider_id).first()
    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    db_provider.is_active = False
    db.commit()
    return {"message": "Provider deactivated successfully"}


@router.post("/{provider_id}/activate")
async def activate_provider(provider_id: int, db: Session = Depends(get_db)):
    """Activate API provider"""
    db_provider = db.query(APIProviderModel).filter(APIProviderModel.id == provider_id).first()
    if not db_provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    db_provider.is_active = True
    db.commit()
    return {"message": "Provider activated successfully"} 