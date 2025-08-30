#!/usr/bin/env python3
"""
Quick fix for Elasticsearch search mapping issue
"""
import requests
import json

def fix_elasticsearch_mapping():
    """Fix the Elasticsearch mapping to include created_at field"""
    
    # Update index mapping to include created_at field
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
                "created_at": {"type": "date"},  # Add missing field
                "updated_at": {"type": "date"},  # Add missing field
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
    
    print("🔧 Fixing Elasticsearch mapping...")
    
    # Delete and recreate index with proper mapping
    delete_response = requests.delete("http://localhost:9200/api_docs")
    print(f"Index deletion: {delete_response.status_code}")
    
    create_response = requests.put(
        "http://localhost:9200/api_docs",
        headers={"Content-Type": "application/json"},
        data=json.dumps(index_mapping)
    )
    print(f"Index creation: {create_response.status_code}")
    
    # Reindex all documents
    print("📚 Fetching documentation...")
    docs_response = requests.get("http://localhost:8000/api/v1/documentation/?limit=100")
    if docs_response.status_code != 200:
        print(f"❌ Failed to fetch docs: {docs_response.status_code}")
        return False
    
    docs = docs_response.json()
    print(f"Found {len(docs)} documents")
    
    # Index each document with proper fields
    print("📥 Reindexing documents...")
    indexed_count = 0
    dashboard_count = 0
    
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
            "created_at": doc.get("created_at", "2025-01-01T00:00:00Z"),  # Default date
            "updated_at": doc.get("updated_at", "2025-01-01T00:00:00Z"),  # Default date
            "provider": doc["provider"]
        }
        
        index_response = requests.put(
            f"http://localhost:9200/api_docs/_doc/{doc['id']}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(es_doc)
        )
        
        if index_response.status_code in [200, 201]:
            indexed_count += 1
            if "dashboard" in doc["title"].lower():
                dashboard_count += 1
                print(f"  ✅ Dashboard: {doc['title']}")
        else:
            print(f"  ❌ Failed: {doc['title']}")
    
    # Refresh index
    requests.post("http://localhost:9200/api_docs/_refresh")
    
    print(f"\n🎉 Indexed {indexed_count}/{len(docs)} documents!")
    print(f"📊 Dashboard documents: {dashboard_count}")
    
    # Test the fixed search
    print("\n🔍 Testing search...")
    test_response = requests.get("http://localhost:9200/api_docs/_search?q=dashboard&size=3")
    if test_response.status_code == 200:
        test_data = test_response.json()
        hits = test_data["hits"]["total"]["value"]
        print(f"✅ Search test: Found {hits} dashboard documents")
    
    return True

if __name__ == "__main__":
    print("🚀 Fixing Elasticsearch search issue...")
    success = fix_elasticsearch_mapping()
    if success:
        print("✅ Search mapping fixed!")
        print("\n🧪 Now test the Jira agent:")
        print("curl \"http://localhost:8000/api/v1/jira/ask?q=Get%20all%20dashboards\"")
    else:
        print("❌ Fix failed!")