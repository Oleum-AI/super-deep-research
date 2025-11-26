"""Base class for research providers."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
import httpx

from models import Citation, ProviderReport, ProviderType, ResearchStatus


class ResearchProvider(ABC):
    """Abstract base class for LLM research providers."""
    
    def __init__(self, api_key: str, brave_api_key: Optional[str] = None):
        """Initialize the provider.
        
        Args:
            api_key: API key for the LLM provider
            brave_api_key: API key for Brave Search
        """
        self.api_key = api_key
        self.brave_api_key = brave_api_key
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    @abstractmethod
    async def conduct_research(
        self, 
        query: str, 
        max_sources: int = 10
    ) -> AsyncIterator[ProviderReport]:
        """Conduct deep research and generate a report.
        
        Args:
            query: Research question or topic
            max_sources: Maximum number of sources to use
            
        Yields:
            ProviderReport objects with status updates and final content
        """
        pass
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Get the provider type."""
        pass
    
    async def search_web(self, query: str, count: int = 10) -> list[dict]:
        """Search the web using Brave Search API.
        
        Args:
            query: Search query
            count: Number of results to return
            
        Returns:
            List of search results with title, url, description
        """
        if not self.brave_api_key:
            return []
        
        try:
            response = await self.http_client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.brave_api_key
                },
                params={
                    "q": query,
                    "count": count,
                    "text_decorations": False,
                    "search_lang": "en"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", "")
                })
            
            return results
        except Exception as e:
            print(f"Web search error: {e}")
            return []
    
    async def fetch_content(self, url: str, max_length: int = 5000) -> str:
        """Fetch content from a URL.
        
        Args:
            url: URL to fetch
            max_length: Maximum content length
            
        Returns:
            Text content from the URL
        """
        try:
            response = await self.http_client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            # Simple text extraction - in production use a proper HTML parser
            text = response.text
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
        except Exception as e:
            print(f"Content fetch error for {url}: {e}")
            return ""
    
    def create_initial_report(self) -> ProviderReport:
        """Create an initial report object."""
        return ProviderReport(
            provider=self.provider_type,
            status=ResearchStatus.PENDING,
            content="",
            citations=[]
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

