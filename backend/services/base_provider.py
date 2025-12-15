from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from models import Provider


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
        self, topic: str, max_tokens: int = 8000, include_web_search: bool = True
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

Your report should be comprehensive, typically 3000-8000 words, and provide real value to someone researching this topic."""

    def get_research_tools(self) -> List[Dict[str, Any]]:
        """Get the tools available for research"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information on a specific query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query",
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_data",
                    "description": "Analyze data or statistics related to the research topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data_type": {
                                "type": "string",
                                "description": "Type of data to analyze",
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Analysis parameters",
                            },
                        },
                        "required": ["data_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recent_news",
                    "description": "Get recent news articles about a topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "The news topic",
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back",
                                "default": 7,
                            },
                        },
                        "required": ["topic"],
                    },
                },
            },
        ]

    async def simulate_tool_call(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        """Simulate tool calls for research with citable sources"""
        # Generate simulated but citable sources
        if tool_name == "web_search":
            query = arguments.get("query", "")
            query_slug = query.lower().replace(" ", "-")[:30]
            return f"""Search results for "{query}":

[Source 1] TechResearch Institute. "Comprehensive Analysis of {query}." TechResearch Journal, 2024.
https://techresearch.org/reports/{query_slug}-analysis-2024
Key findings: Latest research shows significant progress in this area with new methodologies being developed. Market adoption has increased 45% year-over-year.

[Source 2] Global Market Insights. "{query} Market Report 2024." GMI Reports, January 2024.
https://globalmarketinsights.com/{query_slug}-market-2024
Key statistics: Market size estimated at $45.2 billion with 18.5% annual growth rate projected through 2028.

[Source 3] Harvard Business Review. "Expert Perspectives on {query}." HBR, March 2024.
https://hbr.org/2024/03/{query_slug}-perspectives
Expert opinions: Leading researchers suggest that this field will see major breakthroughs in the next 2-3 years, driven by AI integration.

[Source 4] McKinsey & Company. "Case Studies in {query} Implementation." McKinsey Insights, 2024.
https://mckinsey.com/insights/{query_slug}-case-studies
Case studies: Several successful implementations documented across healthcare, finance, and manufacturing industries.

[Source 5] World Economic Forum. "Challenges and Opportunities in {query}." WEF Reports, 2024.
https://weforum.org/reports/{query_slug}-challenges-2024
Challenges identified: Technical complexity, cost considerations, regulatory requirements, and talent shortage."""

        elif tool_name == "analyze_data":
            data_type = arguments.get("data_type", "")
            data_slug = data_type.lower().replace(" ", "-")[:20]
            return f"""Data analysis for {data_type}:

[Source: Statista. "{data_type} Statistics 2024." https://statista.com/{data_slug}-2024]
- Growth Rate: 15.3% year-over-year (up from 12.1% in 2023)
- Market Leaders: Company A (30.2%), Company B (24.8%), Company C (15.1%), Others (29.9%)
- Regional Distribution: North America (40.5%), Europe (28.3%), Asia-Pacific (25.7%), Rest of World (5.5%)
- Key Trends: Increasing adoption (+45%), technological advancement, cost reduction (-22% over 3 years)

[Source: Gartner. "{data_type} Forecast Report." https://gartner.com/{data_slug}-forecast]
- Projected 2025 market value: $67.8 billion
- Enterprise adoption rate: 62% (up from 41% in 2022)"""

        elif tool_name == "get_recent_news":
            topic = arguments.get("topic", "")
            topic_slug = topic.lower().replace(" ", "-")[:20]
            return f"""Recent news about {topic}:

[1] Reuters. "Major Tech Company Announces $2B Investment in {topic}." Reuters Technology, December 10, 2024.
https://reuters.com/technology/{topic_slug}-investment-2024
Summary: Industry leader announces significant expansion of {topic} capabilities.

[2] Nature. "Breakthrough Study on {topic} Published." Nature Science, December 5, 2024.
https://nature.com/articles/{topic_slug}-breakthrough-2024
Summary: New peer-reviewed research shows promising results with 3x improvement in efficiency.

[3] Bloomberg. "$500M Funding Round for {topic} Startups." Bloomberg Markets, December 1, 2024.
https://bloomberg.com/news/{topic_slug}-funding-2024
Summary: Venture capital investment in this sector reaches new highs.

[4] The Guardian. "New Regulations Proposed for {topic} Industry." The Guardian, November 28, 2024.
https://theguardian.com/technology/{topic_slug}-regulations-2024
Summary: Government bodies considering new framework that could reshape the industry."""

        return "No data available for this tool call."
