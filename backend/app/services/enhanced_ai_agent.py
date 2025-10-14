"""
Enhanced AI Agent Service for API Documentation
Integrates with MCP client and provides advanced AI capabilities
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from app.mcp.client import MCPClient
from app.vector_store.chroma_client import ChromaDBClient
from app.services.web_search import WebSearchService
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedAIAgent:
    """Enhanced AI Agent Service for API Documentation"""
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.vector_store = ChromaDBClient()
        self.web_search = WebSearchService(
            provider=settings.web_search_provider,
            max_results=settings.web_search_max_results
        )
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
        self.agent_id = str(uuid.uuid4())
    
    async def initialize(self) -> bool:
        """Initialize the AI agent"""
        try:
            # Connect to MCP server
            mcp_connected = await self.mcp_client.connect()
            if not mcp_connected:
                logger.warning("Failed to connect to MCP server, continuing with limited functionality")
            
            # List available tools
            tools = await self.mcp_client.list_tools()
            logger.info(f"AI Agent initialized with {len(tools)} MCP tools")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {str(e)}")
            return False
    
    async def process_user_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user query and provide intelligent response"""
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Initialize session context if new
            if session_id not in self.session_contexts:
                self.session_contexts[session_id] = {
                    "created_at": datetime.utcnow().isoformat(),
                    "query_count": 0,
                    "last_query": None,
                    "preferences": {},
                    "conversation_summary": ""
                }
            
            # Update session context
            self.session_contexts[session_id]["query_count"] += 1
            self.session_contexts[session_id]["last_query"] = query
            
            # Log the query
            self._log_query(query, session_id)
            
            # Analyze query intent with enhanced logic
            intent = await self._analyze_intent_enhanced(query, session_id)
            
            # Get relevant context from vector store
            relevant_docs = await self._get_relevant_context(query, intent)
            
            # Generate response using MCP tools and AI logic
            response = await self._generate_enhanced_response(query, intent, relevant_docs, context, session_id)
            
            # Update conversation summary
            self._update_conversation_summary(session_id, query, response)
            
            # Log the response
            self._log_response(response, session_id)
            
            return {
                'query': query,
                'intent': intent,
                'response': response,
                'relevant_documents': relevant_docs,
                'session_id': session_id,
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat(),
                'session_context': self.session_contexts[session_id]
            }
            
        except Exception as e:
            logger.error(f"Error processing user query: {str(e)}")
            return {
                'error': str(e),
                'query': query,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _analyze_intent_enhanced(self, query: str, session_id: str) -> Dict[str, Any]:
        """Enhanced intent analysis with context awareness"""
        query_lower = query.lower()
        session_context = self.session_contexts.get(session_id, {})
        
        # Enhanced intent classification with confidence scoring
        intent_patterns = {
            'search': {
                'keywords': ['search', 'find', 'look for', 'where is', 'how to', 'list', 'show', 'get all', 'display'],
                'confidence_base': 0.9
            },
            'endpoint_info': {
                'keywords': ['endpoint', 'tell me about', 'what does', 'how does', 'explain'],
                'confidence_base': 0.8
            },
            'analytics': {
                'keywords': ['usage', 'analytics', 'stats', 'performance', 'metrics'],
                'confidence_base': 0.85
            },
            'improvement': {
                'keywords': ['improve', 'better', 'suggestion', 'enhance', 'optimize'],
                'confidence_base': 0.8
            },
            'tutorial': {
                'keywords': ['tutorial', 'example', 'how to use', 'guide', 'walkthrough'],
                'confidence_base': 0.75
            },
            'comparison': {
                'keywords': ['compare', 'difference', 'vs', 'versus', 'alternative'],
                'confidence_base': 0.7
            }
        }
        
        # Find best matching intent
        best_intent = None
        best_confidence = 0
        
        for intent_type, pattern in intent_patterns.items():
            keyword_matches = sum(1 for keyword in pattern['keywords'] if keyword in query_lower)
            if keyword_matches > 0:
                confidence = pattern['confidence_base'] + (keyword_matches * 0.05)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent_type
        
        # Context-aware adjustments
        if session_context.get("query_count", 0) > 1:
            # User has asked multiple questions, might be exploring
            if best_intent == 'search':
                best_confidence += 0.1
        
        # Fallback to general search if no clear intent
        if not best_intent:
            best_intent = 'search'
            best_confidence = 0.6
        
        return {
            'type': best_intent,
            'confidence': min(best_confidence, 1.0),
            'tools': self._get_tools_for_intent(best_intent),
            'context_factors': {
                'session_query_count': session_context.get("query_count", 0),
                'previous_intent': session_context.get("last_intent"),
                'query_complexity': self._assess_query_complexity(query)
            }
        }
    
    def _get_tools_for_intent(self, intent_type: str) -> List[str]:
        """Get appropriate MCP tools for the intent"""
        tool_mapping = {
            'search': ['search_api_docs'],
            'endpoint_info': ['get_api_endpoint', 'search_api_docs'],
            'analytics': ['analyze_api_usage'],
            'improvement': ['suggest_api_improvements', 'analyze_api_usage'],
            'tutorial': ['search_api_docs', 'get_api_endpoint'],
            'comparison': ['search_api_docs', 'analyze_api_usage']
        }
        return tool_mapping.get(intent_type, ['search_api_docs'])
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess the complexity of a query"""
        word_count = len(query.split())
        if word_count <= 3:
            return "simple"
        elif word_count <= 8:
            return "moderate"
        else:
            return "complex"
    
    async def _get_relevant_context(
        self, 
        query: str, 
        intent: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get relevant context from vector store with intent-aware filtering"""
        try:
            # Adjust search parameters based on intent
            n_results = 10 if intent['type'] == 'search' else 5
            
            # Search for relevant documents
            search_results = self.vector_store.search_documents(
                query=query,
                n_results=n_results
            )
            
            return search_results.get('results', [])
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return []
    
    async def _generate_enhanced_response(
        self, 
        query: str, 
        intent: Dict[str, Any], 
        relevant_docs: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """Generate enhanced response using MCP tools and AI logic"""
        try:
            # Use appropriate MCP tool based on intent
            if intent['type'] == 'search':
                return await self._handle_enhanced_search_query(query, context, session_id)
            elif intent['type'] == 'endpoint_info':
                return await self._handle_enhanced_endpoint_query(query, context, session_id)
            elif intent['type'] == 'analytics':
                return await self._handle_enhanced_analytics_query(query, context, session_id)
            elif intent['type'] == 'improvement':
                return await self._handle_enhanced_improvement_query(query, context, session_id)
            elif intent['type'] == 'tutorial':
                return await self._handle_tutorial_query(query, context, session_id)
            elif intent['type'] == 'comparison':
                return await self._handle_comparison_query(query, context, session_id)
            else:
                return await self._handle_general_query(query, relevant_docs, session_id)
                
        except Exception as e:
            logger.error(f"Error generating enhanced response: {str(e)}")
            return {
                'type': 'error',
                'message': f"Sorry, I encountered an error: {str(e)}",
                'suggestion': 'Try rephrasing your question or contact support.',
                'intent_confidence': intent.get('confidence', 0)
            }
    
    async def _handle_enhanced_search_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """Handle enhanced search queries with context awareness"""
        try:
            # Extract search parameters from context - ensure they're arrays
            provider_ids = context.get('provider_ids', []) if context else []
            methods = context.get('methods', []) if context else []

            # Detect provider names in query
            query_lower = query.lower()
            provider_map = {
                'atlassian': 2,
                'jira': 2,
                'kubernetes': 3,
                'k8s': 3,
                'datadog': 1
            }

            # Auto-detect provider if not specified in context
            if not provider_ids:
                for provider_name, provider_id in provider_map.items():
                    if provider_name in query_lower:
                        provider_ids = [provider_id]
                        logger.info(f"Auto-detected provider: {provider_name} (ID: {provider_id})")
                        break

            # Clean query by removing noise words
            noise_words = [
                'list', 'show', 'display', 'get', 'all', 'the', 'a', 'an',
                'apis', 'api', 'endpoints', 'endpoint',
                'how', 'what', 'when', 'where', 'why', 'which', 'who',
                'can', 'could', 'should', 'would', 'do', 'does', 'did',
                'any', 'some', 'provide', 'give', 'tell', 'me', 'you',
                'from', 'for', 'with', 'about', 'to', 'of', 'in', 'on', 'at'
            ]
            cleaned_query = query_lower
            for noise_word in noise_words:
                # Remove as whole word to avoid partial matches
                cleaned_query = cleaned_query.replace(f' {noise_word} ', ' ')
                cleaned_query = cleaned_query.replace(f'{noise_word} ', '')
                cleaned_query = cleaned_query.replace(f' {noise_word}', '')

            cleaned_query = cleaned_query.strip()

            # If query becomes empty after cleaning and provider is detected, search all from that provider
            if not cleaned_query and provider_ids:
                cleaned_query = ""  # Empty query with provider filter = all endpoints from that provider
                logger.info(f"Query cleaned to empty, will return all endpoints from provider {provider_ids}")
            elif cleaned_query != query_lower:
                logger.info(f"Query cleaned from '{query}' to '{cleaned_query}'")

            search_query = cleaned_query if cleaned_query else query

            # Ensure they're lists
            if not isinstance(provider_ids, list):
                provider_ids = [provider_ids] if provider_ids else []
            if not isinstance(methods, list):
                methods = [methods] if methods else []

            # Use MCP search tool with cleaned query
            search_results = await self.mcp_client.call_tool(
                "search_api_docs",
                {
                    "query": search_query,
                    "provider_ids": provider_ids,
                    "methods": methods,
                    "limit": 10
                }
            )
            
            if "error" in search_results:
                return search_results

            logger.info(f"MCP search returned {len(search_results.get('results', []))} results")

            # Enhance results with additional context
            enhanced_results = []
            for result in search_results.get('results', []):
                enhanced_result = result.copy()
                enhanced_result['search_relevance'] = self._calculate_search_relevance(query, result)
                enhanced_result['usage_tips'] = self._generate_usage_tips(result)
                enhanced_results.append(enhanced_result)

            logger.info(f"Returning {len(enhanced_results)} enhanced results from database")

            # If web search is enabled and results are insufficient, supplement with web search
            web_results = []
            if settings.enable_web_search and len(enhanced_results) < 3:
                logger.info("Web search is enabled and database results are insufficient. Searching web...")
                try:
                    web_search_context = {
                        "provider_name": self._get_provider_name(provider_ids) if provider_ids else None
                    }
                    web_response = await self.web_search.search(query, web_search_context)
                    web_results = web_response.get('results', [])
                    logger.info(f"Web search returned {len(web_results)} additional results")
                except Exception as e:
                    logger.error(f"Web search failed: {str(e)}")

            return {
                'type': 'enhanced_search_results',
                'results': enhanced_results,
                'web_results': web_results,
                'total': len(enhanced_results),
                'web_total': len(web_results),
                'query': query,
                'filters_applied': {
                    'provider_ids': provider_ids,
                    'methods': methods
                },
                'search_insights': {
                    'query_complexity': self._assess_query_complexity(query),
                    'suggested_refinements': self._suggest_search_refinements(query),
                    'web_search_used': len(web_results) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling enhanced search query: {str(e)}")
            raise
    
    def _calculate_search_relevance(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate search relevance score"""
        # Simple relevance calculation
        query_words = set(query.lower().split())
        title_words = set(result.get('title', '').lower().split())
        desc_words = set(result.get('description', '').lower().split())
        
        title_match = len(query_words.intersection(title_words)) / len(query_words) if query_words else 0
        desc_match = len(query_words.intersection(desc_words)) / len(query_words) if query_words else 0
        
        return (title_match * 0.7) + (desc_match * 0.3)
    
    def _generate_usage_tips(self, result: Dict[str, Any]) -> List[str]:
        """Generate usage tips for search results"""
        tips = []
        
        if result.get('method') == 'GET':
            tips.append("This is a read-only endpoint, safe to call multiple times")
        elif result.get('method') == 'POST':
            tips.append("This endpoint modifies data, use with caution")
        
        if 'auth' in result.get('title', '').lower() or 'token' in result.get('title', '').lower():
            tips.append("Authentication required for this endpoint")
        
        return tips
    
    def _suggest_search_refinements(self, query: str) -> List[str]:
        """Suggest search refinements"""
        suggestions = []

        if len(query.split()) < 3:
            suggestions.append("Try adding more specific keywords")

        if 'api' not in query.lower():
            suggestions.append("Include 'API' in your search for better results")

        return suggestions

    def _get_provider_name(self, provider_ids: List[int]) -> Optional[str]:
        """Get provider name from ID"""
        provider_map = {
            1: "Datadog",
            2: "Atlassian",
            3: "Kubernetes"
        }
        if provider_ids and len(provider_ids) > 0:
            return provider_map.get(provider_ids[0])
        return None
    
    async def _handle_enhanced_endpoint_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """Handle enhanced endpoint queries"""
        try:
            # Extract endpoint information from context
            endpoint_id = context.get('endpoint_id') if context else None
            provider_id = context.get('provider_id') if context else None
            
            if not endpoint_id:
                return {
                    'type': 'error',
                    'message': 'Please specify which endpoint you want information about.',
                    'suggestion': 'You can provide an endpoint ID or search for endpoints first.',
                    'help_examples': [
                        'Try: "Tell me about endpoint 123"',
                        'Try: "What does the user creation API do?"'
                    ]
                }
            
            # Use MCP endpoint tool
            endpoint_info = await self.mcp_client.call_tool(
                "get_api_endpoint",
                {
                    "endpoint_id": endpoint_id,
                    "provider_id": provider_id
                }
            )
            
            if "error" in endpoint_info:
                return endpoint_info
            
            # Enhance endpoint information
            enhanced_endpoint = endpoint_info.copy()
            enhanced_endpoint['usage_examples'] = self._generate_endpoint_examples(endpoint_info)
            enhanced_endpoint['common_issues'] = self._identify_common_issues(endpoint_info)
            
            return {
                'type': 'enhanced_endpoint_info',
                'endpoint': enhanced_endpoint,
                'query': query,
                'related_endpoints': self._suggest_related_endpoints(endpoint_info)
            }
            
        except Exception as e:
            logger.error(f"Error handling enhanced endpoint query: {str(e)}")
            raise
    
    def _generate_endpoint_examples(self, endpoint_info: Dict[str, Any]) -> List[str]:
        """Generate usage examples for endpoints"""
        examples = []
        
        if endpoint_info.get('method') == 'GET':
            examples.append(f"curl -X GET '{endpoint_info.get('endpoint', '')}'")
        elif endpoint_info.get('method') == 'POST':
            examples.append(f"curl -X POST '{endpoint_info.get('endpoint', '')}' -H 'Content-Type: application/json' -d '{{}}'")
        
        return examples
    
    def _identify_common_issues(self, endpoint_info: Dict[str, Any]) -> List[str]:
        """Identify common issues with endpoints"""
        issues = []
        
        if not endpoint_info.get('parameters'):
            issues.append("No parameters documented - check if authentication is required")
        
        if not endpoint_info.get('examples'):
            issues.append("No examples provided - consider adding usage examples")
        
        return issues
    
    def _suggest_related_endpoints(self, endpoint_info: Dict[str, Any]) -> List[str]:
        """Suggest related endpoints"""
        # This would typically query the database for related endpoints
        return ["Related endpoint 1", "Related endpoint 2"]
    
    async def _handle_enhanced_analytics_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """Handle enhanced analytics queries"""
        try:
            # Extract analytics parameters from context
            provider_id = context.get('provider_id') if context else None
            time_range = context.get('time_range', '7d')
            metrics = context.get('metrics')
            
            # Use MCP analytics tool
            analytics_data = await self.mcp_client.call_tool(
                "analyze_api_usage",
                {
                    "provider_id": provider_id,
                    "time_range": time_range,
                    "metrics": metrics
                }
            )
            
            if "error" in analytics_data:
                return analytics_data
            
            # Enhance analytics with insights
            enhanced_analytics = analytics_data.copy()
            enhanced_analytics['insights'] = self._generate_analytics_insights(analytics_data)
            enhanced_analytics['recommendations'] = self._generate_analytics_recommendations(analytics_data)
            
            return {
                'type': 'enhanced_analytics',
                'data': enhanced_analytics,
                'query': query,
                'time_range': time_range
            }
            
        except Exception as e:
            logger.error(f"Error handling enhanced analytics query: {str(e)}")
            raise
    
    def _generate_analytics_insights(self, analytics_data: Dict[str, Any]) -> List[str]:
        """Generate insights from analytics data"""
        insights = []
        data = analytics_data.get('data', {})
        
        if data.get('error_rate', 0) > 0.05:
            insights.append("High error rate detected - consider investigating API stability")
        
        if data.get('avg_response_time', 0) > 200:
            insights.append("Response times are above average - performance optimization may be needed")
        
        return insights
    
    def _generate_analytics_recommendations(self, analytics_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations from analytics data"""
        recommendations = []
        data = analytics_data.get('data', {})
        
        if data.get('total_requests', 0) < 100:
            recommendations.append("Low usage detected - consider promoting this API")
        
        return recommendations
    
    async def _handle_enhanced_improvement_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """Handle enhanced improvement queries"""
        try:
            # Extract improvement parameters from context
            provider_id = context.get('provider_id') if context else None
            endpoint_id = context.get('endpoint_id') if context else None
            feedback_type = context.get('feedback_type', 'clarity')
            
            # Use MCP improvement tool
            suggestions = await self.mcp_client.call_tool(
                "suggest_api_improvements",
                {
                    "provider_id": provider_id,
                    "endpoint_id": endpoint_id,
                    "feedback_type": feedback_type
                }
            )
            
            if "error" in suggestions:
                return suggestions
            
            # Enhance suggestions with implementation details
            enhanced_suggestions = suggestions.copy()
            enhanced_suggestions['implementation_priority'] = self._prioritize_suggestions(suggestions)
            enhanced_suggestions['estimated_effort'] = self._estimate_effort(suggestions)
            
            return {
                'type': 'enhanced_improvements',
                'suggestions': enhanced_suggestions,
                'query': query,
                'feedback_type': feedback_type
            }
            
        except Exception as e:
            logger.error(f"Error handling enhanced improvement query: {str(e)}")
            raise
    
    def _prioritize_suggestions(self, suggestions: Dict[str, Any]) -> List[str]:
        """Prioritize improvement suggestions"""
        # Simple prioritization logic
        return ["High", "Medium", "Low"]
    
    def _estimate_effort(self, suggestions: Dict[str, Any]) -> List[str]:
        """Estimate effort for implementing suggestions"""
        # Simple effort estimation
        return ["1-2 hours", "3-5 hours", "1-2 days"]
    
    async def _handle_tutorial_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """Handle tutorial queries"""
        return {
            'type': 'tutorial',
            'message': f"I'll help you learn about: {query}",
            'tutorial_steps': [
                "Step 1: Understanding the basics",
                "Step 2: Setting up your environment",
                "Step 3: Making your first API call",
                "Step 4: Handling responses and errors"
            ],
            'resources': [
                "API Documentation",
                "Code Examples",
                "Best Practices Guide"
            ]
        }
    
    async def _handle_comparison_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """Handle comparison queries"""
        return {
            'type': 'comparison',
            'message': f"Let me compare the options for: {query}",
            'comparison_criteria': [
                "Performance",
                "Ease of use",
                "Documentation quality",
                "Community support"
            ],
            'recommendation': "Based on your needs, I recommend starting with the most documented option"
        }
    
    async def _handle_general_query(
        self, 
        query: str, 
        relevant_docs: List[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """Handle general queries with enhanced suggestions"""
        session_context = self.session_contexts.get(session_id, {})
        
        return {
            'type': 'general',
            'message': f"I found {len(relevant_docs)} relevant documents for your query: '{query}'",
            'suggestions': [
                'Try being more specific about what you need',
                'Use keywords related to specific APIs or endpoints',
                'Ask about specific providers like Jira, Datadog, or Kubernetes'
            ],
            'relevant_documents': relevant_docs[:3],  # Show top 3
            'session_insights': {
                'total_queries': session_context.get('query_count', 0),
                'suggested_next_steps': self._suggest_next_steps(session_context)
            }
        }
    
    def _suggest_next_steps(self, session_context: Dict[str, Any]) -> List[str]:
        """Suggest next steps based on session context"""
        query_count = session_context.get('query_count', 0)
        
        if query_count == 1:
            return ["Try asking a more specific question", "Explore different API providers"]
        elif query_count == 2:
            return ["Ask about specific endpoints", "Request usage examples"]
        else:
            return ["Ask for analytics insights", "Request improvement suggestions"]
    
    def _update_conversation_summary(self, session_id: str, query: str, response: Dict[str, Any]):
        """Update conversation summary for the session"""
        if session_id in self.session_contexts:
            current_summary = self.session_contexts[session_id].get('conversation_summary', '')
            
            # Add current interaction to summary
            new_summary = f"{current_summary}\nQ: {query[:100]}...\nA: {response.get('type', 'response')}"
            
            # Keep summary manageable
            if len(new_summary) > 500:
                new_summary = new_summary[-500:]
            
            self.session_contexts[session_id]['conversation_summary'] = new_summary
    
    def _log_query(self, query: str, session_id: str):
        """Log user query"""
        log_entry = {
            'type': 'query',
            'query': query,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.conversation_history.append(log_entry)
    
    def _log_response(self, response: Dict[str, Any], session_id: str):
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
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        return self.session_contexts.get(session_id, {})
    
    def clear_conversation_history(self, session_id: Optional[str] = None):
        """Clear conversation history"""
        if session_id:
            self.conversation_history = [
                entry for entry in self.conversation_history 
                if entry.get('session_id') != session_id
            ]
            if session_id in self.session_contexts:
                del self.session_contexts[session_id]
        else:
            self.conversation_history.clear()
            self.session_contexts.clear()
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and statistics"""
        return {
            'agent_id': self.agent_id,
            'mcp_connection_status': self.mcp_client.get_connection_status(),
            'total_conversations': len(self.session_contexts),
            'total_queries': len(self.conversation_history),
            'available_tools': len(self.mcp_client.available_tools),
            'uptime': datetime.utcnow().isoformat()
        }
