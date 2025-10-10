"""
AI Agent Service for API Documentation
Integrates with MCP tools to provide intelligent assistance
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.mcp.server import APIDocMCPServer
from app.vector_store.chroma_client import ChromaDBClient

logger = logging.getLogger(__name__)


class AIAgentService:
    """AI Agent Service for API Documentation"""
    
    def __init__(self):
        self.mcp_server = APIDocMCPServer()
        self.vector_store = ChromaDBClient()
        self.conversation_history: List[Dict[str, Any]] = []
    
    async def process_user_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user query and provide intelligent response"""
        try:
            # Log the query
            self._log_query(query, session_id)
            
            # Analyze query intent
            intent = await self._analyze_intent(query)
            
            # Get relevant context from vector store
            relevant_docs = await self._get_relevant_context(query, intent)
            
            # Generate response using MCP tools
            response = await self._generate_response(query, intent, relevant_docs, context)
            
            # Log the response
            self._log_response(response, session_id)
            
            return {
                'query': query,
                'intent': intent,
                'response': response,
                'relevant_documents': relevant_docs,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing user query: {str(e)}")
            return {
                'error': str(e),
                'query': query,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the intent of the user query"""
        query_lower = query.lower()
        
        # Simple intent classification
        if any(word in query_lower for word in ['search', 'find', 'look for']):
            return {
                'type': 'search',
                'confidence': 0.9,
                'tools': ['search_api_docs']
            }
        elif any(word in query_lower for word in ['endpoint', 'api', 'method']):
            return {
                'type': 'endpoint_info',
                'confidence': 0.8,
                'tools': ['get_api_endpoint']
            }
        elif any(word in query_lower for word in ['usage', 'analytics', 'stats']):
            return {
                'type': 'analytics',
                'confidence': 0.85,
                'tools': ['analyze_api_usage']
            }
        elif any(word in query_lower for word in ['improve', 'better', 'suggestion']):
            return {
                'type': 'improvement',
                'confidence': 0.8,
                'tools': ['suggest_api_improvements']
            }
        else:
            return {
                'type': 'general',
                'confidence': 0.6,
                'tools': ['search_api_docs']
            }
    
    async def _get_relevant_context(
        self, 
        query: str, 
        intent: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get relevant context from vector store"""
        try:
            # Search for relevant documents
            search_results = self.vector_store.search_documents(
                query=query,
                n_results=5
            )
            
            return search_results.get('results', [])
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return []
    
    async def _generate_response(
        self, 
        query: str, 
        intent: Dict[str, Any], 
        relevant_docs: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response using MCP tools"""
        try:
            # Use appropriate MCP tool based on intent
            if intent['type'] == 'search':
                return await self._handle_search_query(query, context)
            elif intent['type'] == 'endpoint_info':
                return await self._handle_endpoint_query(query, context)
            elif intent['type'] == 'analytics':
                return await self._handle_analytics_query(query, context)
            elif intent['type'] == 'improvement':
                return await self._handle_improvement_query(query, context)
            else:
                return await self._handle_general_query(query, relevant_docs)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'type': 'error',
                'message': f"Sorry, I encountered an error: {str(e)}",
                'suggestion': 'Try rephrasing your question or contact support.'
            }
    
    async def _handle_search_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle search queries"""
        try:
            # Extract search parameters from context
            provider_ids = context.get('provider_ids') if context else None
            methods = context.get('methods') if context else None
            
            # Use MCP search tool
            search_results = await self.mcp_server.search_api_docs(
                query=query,
                provider_ids=provider_ids,
                methods=methods,
                limit=10
            )
            
            return {
                'type': 'search_results',
                'results': search_results['results'],
                'total': search_results['total'],
                'query': query,
                'filters_applied': {
                    'provider_ids': provider_ids,
                    'methods': methods
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling search query: {str(e)}")
            raise
    
    async def _handle_endpoint_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle endpoint information queries"""
        try:
            # Extract endpoint information from context
            endpoint_id = context.get('endpoint_id') if context else None
            provider_id = context.get('provider_id') if context else None
            
            if not endpoint_id:
                return {
                    'type': 'error',
                    'message': 'Please specify which endpoint you want information about.',
                    'suggestion': 'You can provide an endpoint ID or search for endpoints first.'
                }
            
            # Use MCP endpoint tool
            endpoint_info = await self.mcp_server.get_api_endpoint(
                endpoint_id=endpoint_id,
                provider_id=provider_id
            )
            
            return {
                'type': 'endpoint_info',
                'endpoint': endpoint_info,
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error handling endpoint query: {str(e)}")
            raise
    
    async def _handle_analytics_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle analytics queries"""
        try:
            # Extract analytics parameters from context
            provider_id = context.get('provider_id') if context else None
            time_range = context.get('time_range', '7d')
            metrics = context.get('metrics')
            
            # Use MCP analytics tool
            analytics_data = await self.mcp_server.analyze_api_usage(
                provider_id=provider_id,
                time_range=time_range,
                metrics=metrics
            )
            
            return {
                'type': 'analytics',
                'data': analytics_data,
                'query': query,
                'time_range': time_range
            }
            
        except Exception as e:
            logger.error(f"Error handling analytics query: {str(e)}")
            raise
    
    async def _handle_improvement_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle improvement suggestion queries"""
        try:
            # Extract improvement parameters from context
            provider_id = context.get('provider_id') if context else None
            endpoint_id = context.get('endpoint_id') if context else None
            feedback_type = context.get('feedback_type', 'clarity')
            
            # Use MCP improvement tool
            suggestions = await self.mcp_server.suggest_api_improvements(
                provider_id=provider_id,
                endpoint_id=endpoint_id,
                feedback_type=feedback_type
            )
            
            return {
                'type': 'improvements',
                'suggestions': suggestions,
                'query': query,
                'feedback_type': feedback_type
            }
            
        except Exception as e:
            logger.error(f"Error handling improvement query: {str(e)}")
            raise
    
    async def _handle_general_query(
        self, 
        query: str, 
        relevant_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle general queries"""
        return {
            'type': 'general',
            'message': f"I found {len(relevant_docs)} relevant documents for your query: '{query}'",
            'suggestions': [
                'Try being more specific about what you need',
                'Use keywords related to specific APIs or endpoints',
                'Ask about specific providers like Jira, Datadog, or Kubernetes'
            ],
            'relevant_documents': relevant_docs[:3]  # Show top 3
        }
    
    def _log_query(self, query: str, session_id: Optional[str]):
        """Log user query"""
        log_entry = {
            'type': 'query',
            'query': query,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.conversation_history.append(log_entry)
    
    def _log_response(self, response: Dict[str, Any], session_id: Optional[str]):
        """Log AI response"""
        log_entry = {
            'type': 'response',
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.conversation_history.append(log_entry)
    
    def get_conversation_history(
        self, 
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        if session_id:
            return [
                entry for entry in self.conversation_history 
                if entry.get('session_id') == session_id
            ][-limit:]
        else:
            return self.conversation_history[-limit:]
    
    def clear_conversation_history(self, session_id: Optional[str] = None):
        """Clear conversation history"""
        if session_id:
            self.conversation_history = [
                entry for entry in self.conversation_history 
                if entry.get('session_id') != session_id
            ]
        else:
            self.conversation_history.clear()
