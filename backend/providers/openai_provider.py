"""OpenAI provider for deep research."""
from datetime import datetime
from typing import AsyncIterator
import json
from openai import AsyncOpenAI

from models import Citation, ProviderReport, ProviderType, ResearchStatus
from .base import ResearchProvider


class OpenAIProvider(ResearchProvider):
    """OpenAI GPT-4 research provider."""
    
    def __init__(self, api_key: str, brave_api_key: str = None):
        super().__init__(api_key, brave_api_key)
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    async def conduct_research(
        self, 
        query: str, 
        max_sources: int = 10
    ) -> AsyncIterator[ProviderReport]:
        """Conduct deep research using OpenAI with web search."""
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
            system_prompt = """You are an expert research analyst. Your task is to synthesize information from multiple sources into a comprehensive, well-structured research report.

Guidelines:
- Create a detailed, long-form report (1500-3000 words)
- Use markdown formatting with clear sections
- Include an executive summary at the beginning
- Cite sources using [1], [2], etc. notation
- Provide in-depth analysis and insights
- Include relevant data, statistics, and examples
- End with key takeaways or conclusions"""

            user_prompt = f"""Research Query: {query}

Available Sources:
{chr(10).join(sources_text)}

Please create a comprehensive research report based on these sources. Make sure to:
1. Synthesize information across multiple sources
2. Provide detailed analysis and context
3. Use citations [1], [2], etc. to reference sources
4. Structure the report with clear sections
5. Include an executive summary and conclusions"""

            # Generate report using OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            report.content = response.choices[0].message.content
            report.status = ResearchStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            yield report
            
        except Exception as e:
            report.status = ResearchStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow()
            yield report

