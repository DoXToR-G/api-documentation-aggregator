from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # App Configuration
    app_name: str = "MCP-Based API Documentation Aggregator"
    debug: bool = True
    version: str = "2.0.0"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-jwt-token-signing"
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Database
    database_url: str = "postgresql://api_user:password@localhost:5432/api_docs_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "api_docs"
    
    # Vector Store (ChromaDB)
    chroma_persist_directory: str = "./chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # AI and MCP Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # or "gpt-4o"
    anthropic_api_key: Optional[str] = None
    mcp_server_name: str = "api-documentation-server"
    mcp_server_version: str = "2.0.0"

    # AI Agent Settings - Use OpenAI+MCP (True) or fallback rules-based (False)
    use_openai_agent: bool = True

    # Web Search Configuration
    enable_web_search: bool = False
    web_search_provider: str = "duckduckgo"  # or "google", "bing"
    web_search_max_results: int = 5
    
    # CORS
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "http://localhost:3000"]
    
    # API Provider Settings
    atlassian_api_token: Optional[str] = None
    datadog_api_key: Optional[str] = None
    datadog_app_key: Optional[str] = None
    
    # Background Jobs
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Documentation Update Intervals (in minutes)
    update_interval_atlassian: int = 60 * 24  # Daily
    update_interval_datadog: int = 60 * 12    # Twice daily
    update_interval_kubernetes: int = 60 * 24 # Daily
    
    # AI Agent Settings
    max_conversation_history: int = 100
    ai_response_timeout: int = 30  # seconds
    enable_conversation_logging: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 