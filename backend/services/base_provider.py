from abc import ABC, abstractmethod
from typing import Dict, Optional

from models import Provider

from services.models import ModelName


class ReportResult:
    """Structured result from report generation containing content and thinking/metadata separately"""

    def __init__(self, content: str, thinking: Optional[str] = None):
        self.content = content
        self.thinking = thinking

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {"content": self.content, "thinking": self.thinking}


class BaseProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider_name = Provider.OPENAI  # Override in subclasses

    @abstractmethod
    async def generate_research_report(
        self,
        topic: str,
        model: ModelName,
        max_output_tokens: int | None = None,
    ) -> Dict[str, Optional[str]]:
        """Generate a comprehensive research report on the given topic.

        Returns:
            Dict with 'content' (the report) and 'thinking' (reasoning/metadata, if any)
        """
        pass

    def get_citation_instructions(self) -> str:
        """Get strict citation formatting instructions"""
        return """
        IMPORTANT - Citation Requirements:
        - You MUST use inline citations in the format [1], [2], [3], etc. throughout your report
        - Every major claim, statistic, or fact should have a citation
        - At the END of your report, you MUST include a "## References" section
        - List all citations in the References section using this format:
        [1] Author/Organization. "Title of Article/Report." Source Name, Date. URL
        [2] Author/Organization. "Title." Source Name, Date. URL
        - Number your references to match the inline citations
        - Include at least 5-10 cited sources in your report
        """

    def get_research_system_prompt(self) -> str:
        """Get the system prompt for research tasks"""
        citation_instructions = self.get_citation_instructions()

        return f"""You are an expert research assistant specializing in creating comprehensive, in-depth research reports. Your goal is to produce detailed, well-structured reports that thoroughly explore the given topic.

        When conducting research:
        1. Start with a clear overview of the topic
        2. Explore multiple perspectives and viewpoints
        3. Include relevant data, statistics, and examples
        4. ALWAYS cite your sources using inline citations [1], [2], etc.
        5. Identify key trends, challenges, and opportunities
        6. Provide analysis and insights, not just information
        7. Structure the report with clear sections and subsections
        8. Include a summary of key findings
        9. Suggest areas for further research

        {citation_instructions}

        Format your report in Markdown with:
        - Clear headings and subheadings
        - Bullet points for key information
        - Tables for comparative data
        - Block quotes for important citations
        - Bold and italic text for emphasis
        - A ## References section at the end with numbered sources

        Your report should be comprehensive and provide real value to someone researching this topic.
        """
