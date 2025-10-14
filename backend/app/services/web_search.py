"""
Web Search Service for Enhanced AI Agent
Provides web search capability to supplement database results
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebSearchService:
    """Web search service for API documentation"""

    def __init__(self, provider: str = "duckduckgo", max_results: int = 5):
        self.provider = provider
        self.max_results = max_results
        self.timeout = 10.0

    async def search(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search the web for API documentation

        Args:
            query: Search query
            context: Additional context (provider_name, api_type, etc.)

        Returns:
            Dictionary with search results
        """
        try:
            logger.info(f"Web search started: '{query}' using {self.provider}")

            # Enhance query with API-specific keywords
            enhanced_query = self._enhance_query(query, context)

            # Perform search based on provider
            if self.provider == "duckduckgo":
                results = await self._search_duckduckgo(enhanced_query)
            elif self.provider == "google":
                results = await self._search_google(enhanced_query)
            else:
                results = await self._search_duckduckgo(enhanced_query)

            logger.info(f"Web search completed: {len(results)} results found")

            return {
                "query": query,
                "enhanced_query": enhanced_query,
                "provider": self.provider,
                "results": results,
                "total": len(results),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return {
                "query": query,
                "provider": self.provider,
                "results": [],
                "total": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance query with API-specific keywords"""
        enhanced = query

        # Add API documentation keywords
        if "api" not in query.lower():
            enhanced += " API"

        if "documentation" not in query.lower() and "docs" not in query.lower():
            enhanced += " documentation"

        # Add provider context if available
        if context and context.get("provider_name"):
            provider = context["provider_name"]
            if provider.lower() not in enhanced.lower():
                enhanced += f" {provider}"

        return enhanced

    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo (no API key required)
        Uses DuckDuckGo HTML search
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # DuckDuckGo HTML search
                url = "https://html.duckduckgo.com/html/"
                params = {"q": query}

                response = await client.post(url, data=params, follow_redirects=True)
                response.raise_for_status()

                # Parse HTML results
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []

                for result_div in soup.find_all('div', class_='result')[:self.max_results]:
                    try:
                        title_elem = result_div.find('a', class_='result__a')
                        snippet_elem = result_div.find('a', class_='result__snippet')

                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            url = title_elem.get('href', '')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "source": "DuckDuckGo"
                            })
                    except Exception as e:
                        logger.warning(f"Error parsing search result: {e}")
                        continue

                return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return []

    async def _search_google(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using Google Custom Search API (requires API key)
        Note: This requires GOOGLE_API_KEY and GOOGLE_CSE_ID in config
        """
        # Placeholder for Google Custom Search implementation
        # You would need to add these to config.py:
        # - google_api_key
        # - google_cse_id

        logger.warning("Google search not fully implemented - requires API key setup")
        return []

    async def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract main content from a webpage
        Useful for getting full API documentation from search results
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text content
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)

                return text[:5000]  # Limit to first 5000 chars

        except Exception as e:
            logger.error(f"Error fetching page content from {url}: {str(e)}")
            return None

    def format_results_for_ai(self, search_results: Dict[str, Any]) -> str:
        """
        Format search results for inclusion in AI context

        Returns:
            Formatted string suitable for AI agent consumption
        """
        if not search_results.get("results"):
            return "No web search results available."

        formatted = f"Web Search Results for '{search_results['query']}':\n\n"

        for i, result in enumerate(search_results["results"], 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   URL: {result['url']}\n"
            formatted += f"   {result['snippet']}\n\n"

        return formatted


# Global instance
web_search_service = WebSearchService()


async def search_web(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function for web search

    Args:
        query: Search query
        context: Additional context

    Returns:
        Search results dictionary
    """
    return await web_search_service.search(query, context)
