"""
Fetcher Service - Coordinates API documentation fetching from multiple providers
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import asyncio

from app.fetchers.atlassian import AtlassianFetcher
from app.fetchers.datadog import DatadogFetcher
from app.fetchers.kubernetes import KubernetesFetcher
from app.db.models import APIProvider, APIDocumentation, FetchLog
from app.schemas import APIDocumentationCreate, HTTPMethod
from app.vector_store.chroma_client import ChromaDBClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class FetcherService:
    """Service to coordinate API documentation fetching from multiple providers"""

    def __init__(self, db: Session, vector_store: Optional[ChromaDBClient] = None):
        self.db = db
        self.vector_store = vector_store or ChromaDBClient()
        self.fetchers = {
            'atlassian': AtlassianFetcher,
            'datadog': DatadogFetcher,
            'kubernetes': KubernetesFetcher
        }

    async def fetch_all_providers(self) -> Dict[str, Any]:
        """Fetch documentation from all active providers"""
        results = {
            'total_providers': 0,
            'successful': 0,
            'failed': 0,
            'total_endpoints': 0,
            'details': []
        }

        try:
            # Get all active providers
            providers = self.db.query(APIProvider).filter(APIProvider.is_active == True).all()
            results['total_providers'] = len(providers)

            logger.info(f"Starting documentation fetch for {len(providers)} providers")

            # Fetch from each provider
            for provider in providers:
                try:
                    provider_result = await self.fetch_provider(provider)
                    results['details'].append(provider_result)

                    if provider_result['status'] == 'success':
                        results['successful'] += 1
                        results['total_endpoints'] += provider_result.get('total_endpoints', 0)
                    else:
                        results['failed'] += 1

                except Exception as e:
                    logger.error(f"Failed to fetch from provider {provider.name}: {str(e)}")
                    results['failed'] += 1
                    results['details'].append({
                        'provider_id': provider.id,
                        'provider_name': provider.name,
                        'status': 'error',
                        'error': str(e)
                    })

            logger.info(f"Fetch complete: {results['successful']}/{results['total_providers']} successful")

        except Exception as e:
            logger.error(f"Failed to fetch from providers: {str(e)}")
            raise

        return results

    async def fetch_provider(self, provider: APIProvider) -> Dict[str, Any]:
        """Fetch documentation from a specific provider"""
        fetch_log = FetchLog(
            provider_id=provider.id,
            status='running',
            started_at=datetime.utcnow()
        )
        self.db.add(fetch_log)
        self.db.commit()

        result = {
            'provider_id': provider.id,
            'provider_name': provider.name,
            'status': 'error',
            'total_endpoints': 0,
            'new_endpoints': 0,
            'updated_endpoints': 0,
            'error': None
        }

        try:
            logger.info(f"Fetching documentation for {provider.name}")

            # Get appropriate fetcher class
            fetcher_class = self.fetchers.get(provider.name.lower())
            if not fetcher_class:
                raise ValueError(f"No fetcher available for provider: {provider.name}")

            # Initialize fetcher with credentials from config
            fetcher_kwargs = self._get_fetcher_credentials(provider.name)

            # Fetch documentation using context manager
            async with fetcher_class(provider_id=provider.id, **fetcher_kwargs) as fetcher:
                docs = await fetcher.fetch_documentation()

                # Process and store documentation
                stats = await self._process_documentation(provider, docs)

                result.update({
                    'status': 'success',
                    'total_endpoints': stats['total'],
                    'new_endpoints': stats['new'],
                    'updated_endpoints': stats['updated']
                })

                # Update fetch log
                fetch_log.status = 'success'
                fetch_log.completed_at = datetime.utcnow()
                fetch_log.total_endpoints = stats['total']
                fetch_log.new_endpoints = stats['new']
                fetch_log.updated_endpoints = stats['updated']

                logger.info(f"Successfully fetched {stats['total']} endpoints from {provider.name}")

        except Exception as e:
            logger.error(f"Error fetching from {provider.name}: {str(e)}")
            result['error'] = str(e)
            result['status'] = 'error'

            # Update fetch log
            fetch_log.status = 'error'
            fetch_log.completed_at = datetime.utcnow()
            fetch_log.error_message = str(e)

        finally:
            self.db.commit()

        return result

    async def _process_documentation(
        self,
        provider: APIProvider,
        docs: List[APIDocumentationCreate]
    ) -> Dict[str, int]:
        """Process and store documentation in database and vector store"""
        stats = {'total': 0, 'new': 0, 'updated': 0}

        for doc_create in docs:
            try:
                stats['total'] += 1

                # Check if endpoint already exists
                existing_doc = self.db.query(APIDocumentation).filter(
                    APIDocumentation.provider_id == provider.id,
                    APIDocumentation.endpoint_path == doc_create.endpoint_path,
                    APIDocumentation.http_method == doc_create.http_method.value
                ).first()

                if existing_doc:
                    # Update existing documentation
                    existing_doc.title = doc_create.title
                    existing_doc.description = doc_create.description
                    existing_doc.content = doc_create.content
                    existing_doc.parameters = doc_create.parameters
                    existing_doc.request_body = doc_create.request_body
                    existing_doc.responses = doc_create.responses
                    existing_doc.examples = doc_create.examples
                    existing_doc.tags = doc_create.tags
                    existing_doc.version = doc_create.version
                    existing_doc.deprecated = doc_create.deprecated
                    existing_doc.last_fetched = datetime.utcnow()
                    existing_doc.updated_at = datetime.utcnow()

                    doc_id = existing_doc.id
                    stats['updated'] += 1

                else:
                    # Create new documentation
                    new_doc = APIDocumentation(
                        provider_id=provider.id,
                        endpoint_path=doc_create.endpoint_path,
                        http_method=doc_create.http_method.value,
                        title=doc_create.title,
                        description=doc_create.description,
                        content=doc_create.content,
                        parameters=doc_create.parameters,
                        request_body=doc_create.request_body,
                        responses=doc_create.responses,
                        examples=doc_create.examples,
                        tags=doc_create.tags,
                        version=doc_create.version,
                        deprecated=doc_create.deprecated,
                        last_fetched=datetime.utcnow()
                    )

                    self.db.add(new_doc)
                    self.db.flush()  # Get the ID

                    doc_id = new_doc.id
                    stats['new'] += 1

                # Store in vector store for semantic search
                await self._store_in_vector_store(
                    doc_id=doc_id,
                    provider_name=provider.name,
                    endpoint_path=doc_create.endpoint_path,
                    http_method=doc_create.http_method.value,
                    title=doc_create.title,
                    description=doc_create.description or "",
                    content=doc_create.content or "",
                    tags=doc_create.tags or []
                )

                # Commit every 100 documents to avoid large transactions
                if stats['total'] % 100 == 0:
                    self.db.commit()
                    logger.info(f"Processed {stats['total']} documents...")

            except Exception as e:
                logger.error(f"Error processing document {doc_create.endpoint_path}: {str(e)}")
                continue

        # Final commit
        self.db.commit()

        return stats

    async def _store_in_vector_store(
        self,
        doc_id: int,
        provider_name: str,
        endpoint_path: str,
        http_method: str,
        title: str,
        description: str,
        content: str,
        tags: List[str]
    ):
        """Store documentation in vector store for semantic search"""
        try:
            # Combine all text for embedding
            combined_text = f"""
            Provider: {provider_name}
            Method: {http_method}
            Endpoint: {endpoint_path}
            Title: {title}
            Description: {description}
            Content: {content}
            Tags: {', '.join(tags)}
            """

            # Store in ChromaDB
            self.vector_store.add_documents(
                documents=[combined_text.strip()],
                metadatas=[{
                    'doc_id': doc_id,
                    'provider': provider_name,
                    'endpoint': endpoint_path,
                    'method': http_method,
                    'title': title,
                    'tags': tags
                }],
                ids=[f"doc_{doc_id}"]
            )

        except Exception as e:
            logger.error(f"Error storing in vector store for doc {doc_id}: {str(e)}")
            # Don't raise - vector store failures shouldn't block the main flow

    def _get_fetcher_credentials(self, provider_name: str) -> Dict[str, Any]:
        """Get credentials for a specific provider from config"""
        credentials = {}

        provider_lower = provider_name.lower()

        if provider_lower == 'atlassian':
            if hasattr(settings, 'atlassian_api_token'):
                credentials['api_token'] = settings.atlassian_api_token

        elif provider_lower == 'datadog':
            if hasattr(settings, 'datadog_api_key'):
                credentials['api_key'] = settings.datadog_api_key
            if hasattr(settings, 'datadog_app_key'):
                credentials['app_key'] = settings.datadog_app_key

        # Kubernetes doesn't require credentials for public OpenAPI spec

        return credentials

    async def sync_provider_by_name(self, provider_name: str) -> Dict[str, Any]:
        """Sync documentation for a specific provider by name"""
        provider = self.db.query(APIProvider).filter(
            APIProvider.name == provider_name,
            APIProvider.is_active == True
        ).first()

        if not provider:
            raise ValueError(f"Provider '{provider_name}' not found or inactive")

        return await self.fetch_provider(provider)

    async def sync_provider_by_id(self, provider_id: int) -> Dict[str, Any]:
        """Sync documentation for a specific provider by ID"""
        provider = self.db.query(APIProvider).filter(
            APIProvider.id == provider_id,
            APIProvider.is_active == True
        ).first()

        if not provider:
            raise ValueError(f"Provider with ID {provider_id} not found or inactive")

        return await self.fetch_provider(provider)
