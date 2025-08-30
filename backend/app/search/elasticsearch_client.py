from elasticsearch import AsyncElasticsearch
from typing import List, Dict, Any
import json
import logging

from app.core.config import settings
from app.schemas import SearchRequest, SearchResponse, SearchResult, HTTPMethod, APIProvider

logger = logging.getLogger(__name__)

# Initialize Elasticsearch client
es_client = AsyncElasticsearch(
    [settings.elasticsearch_url],
    verify_certs=False,
    ssl_show_warn=False
)


async def search_documentation(search_request: SearchRequest) -> SearchResponse:
    """Search API documentation using Elasticsearch"""
    try:
        # Build Elasticsearch query
        query = build_search_query(search_request)
        
        # Execute search
        response = await es_client.search(
            index=settings.elasticsearch_index,
            body=query,
            size=search_request.limit,
            from_=search_request.offset
        )
        
        # Parse results
        results = parse_search_results(response)
        
        return SearchResponse(
            results=results,
            total=response['hits']['total']['value'],
            limit=search_request.limit,
            offset=search_request.offset,
            query=search_request.query
        )
        
    except Exception as e:
        logger.error(f"Elasticsearch search failed: {str(e)}")
        raise


def build_search_query(search_request: SearchRequest) -> Dict[str, Any]:
    """Build Elasticsearch query from search request"""
    query = {
        "query": {
            "bool": {
                "must": [],
                "filter": []
            }
        },
        "highlight": {
            "fields": {
                "title": {},
                "description": {},
                "content": {},
                "endpoint_path": {}
            }
        },
        "sort": [
            {"_score": {"order": "desc"}},
            {"created_at": {"order": "desc"}}
        ]
    }
    
    # Main search query
    if search_request.query:
        query["query"]["bool"]["must"].append({
            "multi_match": {
                "query": search_request.query,
                "fields": [
                    "title^3",
                    "description^2",
                    "endpoint_path^2",
                    "content",
                    "tags"
                ],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        })
    else:
        query["query"]["bool"]["must"].append({"match_all": {}})
    
    # Provider filter
    if search_request.provider_ids:
        query["query"]["bool"]["filter"].append({
            "terms": {"provider_id": search_request.provider_ids}
        })
    
    # Method filter
    if search_request.methods:
        method_values = [method.value for method in search_request.methods]
        query["query"]["bool"]["filter"].append({
            "terms": {"http_method": method_values}
        })
    
    # Tags filter
    if search_request.tags:
        query["query"]["bool"]["filter"].append({
            "terms": {"tags": search_request.tags}
        })
    
    # Deprecated filter
    if search_request.deprecated is not None:
        query["query"]["bool"]["filter"].append({
            "term": {"deprecated": search_request.deprecated}
        })
    
    return query


def parse_search_results(response: Dict[str, Any]) -> List[SearchResult]:
    """Parse Elasticsearch response into SearchResult objects"""
    results = []
    
    for hit in response['hits']['hits']:
        source = hit['_source']
        
        # Create provider object
        provider = APIProvider(
            id=source['provider']['id'],
            name=source['provider']['name'],
            display_name=source['provider']['display_name'],
            base_url=source['provider']['base_url'],
            documentation_url=source['provider'].get('documentation_url'),
            icon_url=source['provider'].get('icon_url'),
            description=source['provider'].get('description'),
            is_active=source['provider']['is_active'],
            created_at=source['provider']['created_at']
        )
        
        result = SearchResult(
            id=source['id'],
            title=source['title'],
            description=source.get('description'),
            endpoint_path=source['endpoint_path'],
            http_method=HTTPMethod(source['http_method']),
            provider=provider,
            tags=source.get('tags', []),
            deprecated=source.get('deprecated', False),
            score=hit['_score']
        )
        
        results.append(result)
    
    return results


async def index_documentation(doc_data: Dict[str, Any]) -> bool:
    """Index a single documentation entry in Elasticsearch"""
    try:
        await es_client.index(
            index=settings.elasticsearch_index,
            id=doc_data['id'],
            body=doc_data
        )
        return True
    except Exception as e:
        logger.error(f"Failed to index document {doc_data.get('id')}: {str(e)}")
        return False


async def bulk_index_documentation(docs: List[Dict[str, Any]]) -> int:
    """Bulk index multiple documentation entries"""
    if not docs:
        return 0
    
    try:
        # Prepare bulk actions
        actions = []
        for doc in docs:
            actions.append({
                "index": {
                    "_index": settings.elasticsearch_index,
                    "_id": doc['id']
                }
            })
            actions.append(doc)
        
        # Execute bulk operation
        response = await es_client.bulk(body=actions)
        
        # Count successful operations
        successful = 0
        for item in response['items']:
            if 'index' in item and item['index']['status'] in [200, 201]:
                successful += 1
        
        logger.info(f"Successfully indexed {successful}/{len(docs)} documents")
        return successful
        
    except Exception as e:
        logger.error(f"Bulk indexing failed: {str(e)}")
        return 0


async def delete_documentation(doc_id: int) -> bool:
    """Delete a documentation entry from Elasticsearch"""
    try:
        await es_client.delete(
            index=settings.elasticsearch_index,
            id=doc_id
        )
        return True
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {str(e)}")
        return False


async def create_index():
    """Create Elasticsearch index with proper mappings"""
    index_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "description": {"type": "text", "analyzer": "standard"},
                "endpoint_path": {
                    "type": "text",
                    "analyzer": "keyword",
                    "fields": {
                        "text": {"type": "text", "analyzer": "standard"}
                    }
                },
                "http_method": {"type": "keyword"},
                "content": {"type": "text", "analyzer": "standard"},
                "tags": {"type": "keyword"},
                "version": {"type": "keyword"},
                "deprecated": {"type": "boolean"},
                "provider_id": {"type": "integer"},
                "provider": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "keyword"},
                        "display_name": {"type": "text"},
                        "base_url": {"type": "keyword"},
                        "documentation_url": {"type": "keyword"},
                        "icon_url": {"type": "keyword"},
                        "description": {"type": "text"},
                        "is_active": {"type": "boolean"},
                        "created_at": {"type": "date"}
                    }
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "last_fetched": {"type": "date"}
            }
        }
    }
    
    try:
        # Check if index exists
        if await es_client.indices.exists(index=settings.elasticsearch_index):
            logger.info(f"Index {settings.elasticsearch_index} already exists")
            return True
        
        # Create index
        await es_client.indices.create(
            index=settings.elasticsearch_index,
            body=index_mapping
        )
        
        logger.info(f"Created Elasticsearch index: {settings.elasticsearch_index}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create index: {str(e)}")
        return False


async def health_check() -> bool:
    """Check if Elasticsearch is healthy"""
    try:
        await es_client.ping()
        return True
    except Exception:
        return False 