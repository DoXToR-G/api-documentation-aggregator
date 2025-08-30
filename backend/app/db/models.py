from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class APIProvider(Base):
    """API Provider model - stores information about API providers like Atlassian, Datadog, etc."""
    __tablename__ = "api_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    base_url = Column(String(500), nullable=False)
    documentation_url = Column(String(500))
    icon_url = Column(String(500))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_docs = relationship("APIDocumentation", back_populates="provider")
    fetch_logs = relationship("FetchLog", back_populates="provider")


class APIDocumentation(Base):
    """API Documentation model - stores individual API endpoint documentation"""
    __tablename__ = "api_documentation"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("api_providers.id"), nullable=False)
    
    # Basic endpoint information
    endpoint_path = Column(String(500), nullable=False)
    http_method = Column(String(10), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Documentation content
    content = Column(Text)  # Main documentation content
    parameters = Column(JSON)  # Request parameters
    request_body = Column(JSON)  # Request body schema
    responses = Column(JSON)  # Response schemas
    examples = Column(JSON)  # Code examples
    
    # Metadata
    tags = Column(JSON)  # Categories/tags
    version = Column(String(50))
    deprecated = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_fetched = Column(DateTime(timezone=True))
    
    # Search optimization
    search_vector = Column(Text)  # For full-text search
    
    # Relationships
    provider = relationship("APIProvider", back_populates="api_docs")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('ix_api_docs_provider_endpoint', 'provider_id', 'endpoint_path', 'http_method'),
        Index('ix_api_docs_search', 'title', 'description'),
    )


class FetchLog(Base):
    """Fetch Log model - tracks API documentation fetch operations"""
    __tablename__ = "fetch_logs"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("api_providers.id"), nullable=False)
    
    # Fetch details
    status = Column(String(20), nullable=False)  # 'success', 'error', 'partial'
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Results
    total_endpoints = Column(Integer, default=0)
    new_endpoints = Column(Integer, default=0)
    updated_endpoints = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Error details
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Relationships
    provider = relationship("APIProvider", back_populates="fetch_logs")


class SearchQuery(Base):
    """Search Query model - tracks user search queries for analytics"""
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False)
    results_count = Column(Integer, default=0)
    clicked_result_id = Column(Integer, ForeignKey("api_documentation.id"))
    user_ip = Column(String(45))  # Support IPv6
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('ix_search_queries_created', 'created_at'),
        Index('ix_search_queries_query', 'query'),
    ) 