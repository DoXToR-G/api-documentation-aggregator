"""
API endpoints for managing documentation sources
Admin can view and enable/disable documentation sources for AI to access
Note: Use load_openapi MCP tool for dynamic loading of OpenAPI specs
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import APIProvider

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentationSourceResponse(BaseModel):
    """Model for documentation source response"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    base_url: Optional[str]
    documentation_url: Optional[str]
    icon_color: str
    is_active: bool
    endpoint_count: int = 0

    class Config:
        from_attributes = True


@router.get("/doc-sources", response_model=List[DocumentationSourceResponse])
async def get_documentation_sources(db: Session = Depends(get_db)):
    """
    Get all documentation sources
    Returns sources available for AI to access
    """
    try:
        providers = db.query(APIProvider).all()

        result = []
        for provider in providers:
            # Count endpoints (even though we don't store them anymore, keep for compatibility)
            from app.db.models import APIDocumentation
            endpoint_count = db.query(APIDocumentation).filter(
                APIDocumentation.provider_id == provider.id
            ).count()

            result.append(DocumentationSourceResponse(
                id=provider.id,
                name=provider.name,
                display_name=provider.display_name,
                description=provider.description or f"{provider.display_name} API documentation",
                base_url=provider.base_url or "",
                documentation_url=provider.documentation_url or "",
                icon_color=getattr(provider, 'icon_color', 'from-purple-500 to-purple-600'),
                is_active=provider.is_active,
                endpoint_count=endpoint_count
            ))

        return result

    except Exception as e:
        logger.error(f"Failed to get documentation sources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@router.patch("/doc-sources/{source_id}/toggle")
async def toggle_documentation_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Enable/disable a documentation source
    When disabled, AI won't access this source
    """
    try:
        provider = db.query(APIProvider).filter(APIProvider.id == source_id).first()

        if not provider:
            raise HTTPException(status_code=404, detail="Documentation source not found")

        # Toggle active status
        provider.is_active = not provider.is_active
        db.commit()

        logger.info(f"Toggled source {provider.display_name} to {'active' if provider.is_active else 'inactive'}")

        return {
            "id": provider.id,
            "name": provider.display_name,
            "is_active": provider.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle documentation source: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


