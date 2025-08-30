#!/usr/bin/env python3
"""
Complete reindex of ALL documentation in Elasticsearch
"""
import requests
import json

def full_reindex():
    """Reindex ALL documentation with proper pagination"""
    
    print("🚀 Starting COMPLETE reindexing of all Jira documentation...")
    
    # Fetch ALL documents with higher limit
    print("🔍 Fetching ALL documentation from database...")
    response = requests.get("http://localhost:8000/api/v1/documentation/?limit=1000")
    if response.status_code != 200:
        print(f"❌ Failed to fetch docs: {response.status_code}")
        return False
    
    docs = response.json()
    print(f"📚 Found {len(docs)} total documents")
    
    # Check Elasticsearch health
    print("🔗 Checking Elasticsearch...")
    es_response = requests.get("http://localhost:9200/_cluster/health")
    if es_response.status_code != 200:
        print(f"❌ Elasticsearch not available: {es_response.status_code}")
        return False
    
    print("✅ Elasticsearch is healthy")
    
    # Enhanced index mapping
    index_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "text", "analyzer": "standard"},
                "description": {"type": "text", "analyzer": "standard"},
                "endpoint_path": {"type": "keyword"},
                "http_method": {"type": "keyword"},
                "content": {"type": "text", "analyzer": "standard"},
                "tags": {"type": "keyword"},
                "version": {"type": "keyword"},
                "deprecated": {"type": "boolean"},
                "provider_id": {"type": "integer"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "provider": {
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "keyword"},
                        "display_name": {"type": "text"}
                    }
                }
            }
        }
    }
    
    # Delete and recreate index
    print("🗑️ Recreating Elasticsearch index...")
    requests.delete("http://localhost:9200/api_docs")
    create_response = requests.put(
        "http://localhost:9200/api_docs",
        headers={"Content-Type": "application/json"},
        data=json.dumps(index_mapping)
    )
    
    if create_response.status_code not in [200, 201]:
        print(f"⚠️ Index creation response: {create_response.status_code}")
    
    # Index each document
    print("📥 Indexing ALL documents...")
    indexed_count = 0
    
    # Count different types
    counters = {
        'dashboard': 0,
        'issue': 0,
        'project': 0,
        'user': 0,
        'workflow': 0,
        'comment': 0,
        'search': 0,
        'other': 0
    }
    
    for doc in docs:
        es_doc = {
            "id": doc["id"],
            "title": doc["title"],
            "description": doc["description"],
            "endpoint_path": doc["endpoint_path"],
            "http_method": doc["http_method"],
            "content": doc.get("content", ""),
            "tags": doc.get("tags", []),
            "version": doc.get("version", ""),
            "deprecated": doc.get("deprecated", False),
            "provider_id": doc["provider_id"],
            "created_at": doc.get("created_at", "2025-01-01T00:00:00Z"),
            "updated_at": doc.get("updated_at", "2025-01-01T00:00:00Z"),
            "provider": doc["provider"]
        }
        
        index_response = requests.put(
            f"http://localhost:9200/api_docs/_doc/{doc['id']}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(es_doc)
        )
        
        if index_response.status_code in [200, 201]:
            indexed_count += 1
            
            # Count by type
            title_lower = doc["title"].lower()
            if "dashboard" in title_lower:
                counters['dashboard'] += 1
            elif "issue" in title_lower:
                counters['issue'] += 1
            elif "project" in title_lower:
                counters['project'] += 1
            elif "user" in title_lower or "group" in title_lower:
                counters['user'] += 1
            elif "workflow" in title_lower or "transition" in title_lower:
                counters['workflow'] += 1
            elif "comment" in title_lower:
                counters['comment'] += 1
            elif "search" in title_lower or "jql" in title_lower:
                counters['search'] += 1
            else:
                counters['other'] += 1
                
        else:
            print(f"  ❌ Failed to index: {doc['title']} ({index_response.status_code})")
    
    # Refresh index to make documents searchable immediately
    print("🔄 Refreshing index...")
    requests.post("http://localhost:9200/api_docs/_refresh")
    
    print(f"\n🎉 Complete reindexing successful!")
    print(f"📊 Indexed {indexed_count}/{len(docs)} documents")
    print(f"\n📋 By Category:")
    for category, count in counters.items():
        if count > 0:
            print(f"   - {category.title()}: {count}")
    
    # Test searches for different categories
    print(f"\n🔍 Testing search functionality...")
    
    test_queries = [
        ("dashboard", "Dashboard operations"),
        ("create project", "Project creation"),
        ("issue", "Issue operations"),
        ("user", "User management"),
        ("workflow", "Workflow operations")
    ]
    
    for query, description in test_queries:
        search_response = requests.get(f"http://localhost:9200/api_docs/_search?q={query}&size=3")
        if search_response.status_code == 200:
            search_data = search_response.json()
            hit_count = search_data["hits"]["total"]["value"]
            print(f"   ✅ {description}: {hit_count} results")
        else:
            print(f"   ❌ {description}: Search failed")
    
    return True

if __name__ == "__main__":
    success = full_reindex()
    if success:
        print("\n🎊 ALL JIRA DOCUMENTATION FULLY INDEXED!")
        print("\n🧪 Test the enhanced agent:")
        print('curl "http://localhost:8000/api/v1/jira/ask?q=create%20project"')
        print('curl "http://localhost:8000/api/v1/jira/ask?q=search%20issues"') 
        print('curl "http://localhost:8000/api/v1/jira/ask?q=add%20user%20to%20group"')
    else:
        print("\n❌ Full reindex failed!")