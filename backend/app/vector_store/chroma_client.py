"""
Mock ChromaDB Vector Store Client for fast testing
No ML dependencies required
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """Mock vector store client for testing without ML dependencies"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.documents = []  # Simple in-memory storage
        logger.info(f"Mock ChromaDB initialized (no ML dependencies)")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Mock add documents - stores in memory"""
        for doc, metadata, doc_id in zip(documents, metadatas, ids):
            self.documents.append({
                'id': doc_id,
                'document': doc,
                'metadata': metadata
            })
        logger.info(f"Added {len(documents)} documents to mock vector store")

    def search_documents(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mock search - simple text matching"""
        query_lower = query.lower()
        results = []

        for doc in self.documents:
            if query_lower in doc['document'].lower():
                results.append({
                    'id': doc['id'],
                    'document': doc['document'],
                    'metadata': doc['metadata'],
                    'distance': 0.5
                })
                if len(results) >= n_results:
                    break

        return {
            'query': query,
            'results': results,
            'total': len(results)
        }

    def update_document(
        self,
        doc_id: str,
        document: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Mock update document"""
        for doc in self.documents:
            if doc['id'] == doc_id:
                doc['document'] = document
                doc['metadata'] = metadata
                break
        logger.info(f"Updated document {doc_id}")

    def delete_document(self, doc_id: str) -> None:
        """Mock delete document"""
        self.documents = [doc for doc in self.documents if doc['id'] != doc_id]
        logger.info(f"Deleted document {doc_id}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Mock get collection statistics"""
        return {
            'total_documents': len(self.documents),
            'collection_name': 'api_documentation',
            'mode': 'mock'
        }

    def reset_collection(self) -> None:
        """Mock reset collection"""
        self.documents = []
        logger.info("Mock collection reset")
