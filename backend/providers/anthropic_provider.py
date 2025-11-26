"""Anthropic Claude provider for deep research."""
from datetime import datetime
from typing import AsyncIterator
from anthropic import AsyncAnthropic

from models import Citation, ProviderReport, ProviderType, ResearchStatus
from .base import ResearchProvider


class AnthropicProvider(ResearchProvider):
    """Anthropic Claude research provider."""
    
    def __init__(self, api_key: str, brave_api_key: str = None):
        super().__init__(api_key, brave_api_key)
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC
    
    async def conduct_research(
        self, 
        query: str, 
        max_sources: int = 10
    ) -> AsyncIterator[ProviderReport]:
        """Conduct deep research using Anthropic Claude with web search."""
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
            system_prompt = """You are an expert research analyst with deep expertise across multiple domains. Your task is to create thorough, well-researched reports that synthesize information from multiple sources.

Your reports should:
- Be comprehensive and detailed (1500-3000 words)
- Use clear markdown formatting with logical sections
- Begin with an executive summary
- Include in-depth analysis and critical thinking
- Reference sources using [1], [2], etc. citations
- Present multiple perspectives when relevant
- Include data, examples, and specific details
- End with actionable insights or conclusions"""

            user_prompt = f"""Research Topic: {query}

Source Materials:
{chr(10).join(sources_text)}

Please create a comprehensive research report on this topic. Ensure you:
1. Synthesize information from all provided sources
2. Provide thorough analysis with supporting evidence
3. Use [1], [2], etc. to cite sources throughout
4. Structure content with clear, logical sections
5. Include both overview and detailed exploration
6. Provide executive summary and key takeaways"""

            # Generate report using Claude
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            report.content = message.content[0].text
            report.status = ResearchStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            yield report
            
        except Exception as e:
            report.status = ResearchStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow()
            yield report

