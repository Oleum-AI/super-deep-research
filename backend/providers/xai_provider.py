"""xAI Grok provider for deep research."""
from datetime import datetime
from typing import AsyncIterator
import httpx

from models import Citation, ProviderReport, ProviderType, ResearchStatus
from .base import ResearchProvider


class XAIProvider(ResearchProvider):
    """xAI Grok research provider."""
    
    def __init__(self, api_key: str, brave_api_key: str = None):
        super().__init__(api_key, brave_api_key)
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-beta"
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.XAI
    
    async def conduct_research(
        self, 
        query: str, 
        max_sources: int = 10
    ) -> AsyncIterator[ProviderReport]:
        """Conduct deep research using xAI Grok with web search."""
        report = self.create_initial_report()
        report.started_at = datetime.utcnow()
        
        try:
            # Phase 1: Search for sources
            report.status = ResearchStatus.SEARCHING
            yield report
            
            search_results = await self.search_web(query, count=max_sources)
            
            if not search_results:
                report.status = ResearchStatus.FAILED
                report.error = "No search results found"
                yield report
                return
            
            # Phase 2: Analyze sources
            report.status = ResearchStatus.ANALYZING
            yield report
            
            # Create citations
            citations = []
            sources_text = []
            for idx, result in enumerate(search_results[:max_sources], 1):
                citation = Citation(
                    title=result["title"],
                    url=result["url"],
                    snippet=result.get("description", "")
                )
                citations.append(citation)
                sources_text.append(
                    f"[{idx}] {result['title']}\n"
                    f"URL: {result['url']}\n"
                    f"Description: {result.get('description', 'N/A')}\n"
                )
            
            report.citations = citations
            
            # Phase 3: Generate report
            report.status = ResearchStatus.WRITING
            yield report
            
            # Create comprehensive research prompt
            system_prompt = """You are an expert research analyst. Create comprehensive, well-structured research reports that synthesize information from multiple sources.

Your reports should:
- Be detailed and thorough (1500-3000 words)
- Use markdown formatting with clear sections
- Start with an executive summary
- Include deep analysis and insights
- Cite sources using [1], [2], etc.
- Present balanced perspectives
- Include relevant data and examples
- Conclude with key findings"""

            user_prompt = f"""Research Query: {query}

Available Sources:
{chr(10).join(sources_text)}

Create a comprehensive research report using these sources. Make sure to:
1. Synthesize information across sources
2. Provide detailed analysis
3. Use [1], [2], etc. for citations
4. Structure with clear sections
5. Include executive summary and conclusions"""

            # Generate report using xAI API (OpenAI-compatible)
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            report.content = data["choices"][0]["message"]["content"]
            report.status = ResearchStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            yield report
            
        except Exception as e:
            report.status = ResearchStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow()
            yield report

