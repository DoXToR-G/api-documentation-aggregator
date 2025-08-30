#!/usr/bin/env python3
"""
Simple script to reindex all documentation in Elasticsearch
"""
import requests
import json

def reindex_docs():
    """Trigger reindexing of all documentation"""
    try:
        # Get all documentation from the API
        print("🔍 Fetching all documentation...")
        response = requests.get("http://localhost:8000/api/v1/documentation/?limit=100")
        if response.status_code != 200:
            print(f"❌ Failed to fetch docs: {response.status_code}")
            return False
        
        docs = response.json()
        print(f"📚 Found {len(docs)} documents")
        
        # Check Elasticsearch health
        print("🔗 Checking Elasticsearch...")
        es_response = requests.get("http://localhost:9200/_cluster/health")
        if es_response.status_code != 200:
            print(f"❌ Elasticsearch not available: {es_response.status_code}")
            return False
        
        print("✅ Elasticsearch is healthy")
        
        # Create index if it doesn't exist
        print("📝 Creating/updating index...")
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
        requests.delete("http://localhost:9200/api_docs")
        create_response = requests.put(
            "http://localhost:9200/api_docs",
            headers={"Content-Type": "application/json"},
            data=json.dumps(index_mapping)
        )
        
        if create_response.status_code not in [200, 201]:
            print(f"⚠️ Index creation response: {create_response.status_code}")
        
        # Index each document
        print("📥 Indexing documents...")
        indexed_count = 0
        
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
                    print(f"  ✅ Indexed: {doc['title']}")
            else:
                print(f"  ❌ Failed to index: {doc['title']} ({index_response.status_code})")
        
        # Refresh index
        requests.post("http://localhost:9200/api_docs/_refresh")
        
        print(f"\n🎉 Successfully indexed {indexed_count}/{len(docs)} documents!")
        
        # Test search
        print("\n🔍 Testing search...")
        search_response = requests.get("http://localhost:9200/api_docs/_search?q=dashboard&size=3")
        if search_response.status_code == 200:
            search_data = search_response.json()
            hit_count = search_data["hits"]["total"]["value"]
            print(f"✅ Search test: Found {hit_count} dashboard documents")
            
            for hit in search_data["hits"]["hits"][:3]:
                print(f"  📄 {hit['_source']['title']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during reindexing: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting documentation reindexing...")
    success = reindex_docs()
    if success:
        print("✅ Reindexing completed successfully!")
    else:
        print("❌ Reindexing failed!")