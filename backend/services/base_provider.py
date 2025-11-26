from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from models import Provider
import json

class BaseProvider(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider_name = Provider.OPENAI  # Override in subclasses
    
    @abstractmethod
    async def generate_research_report(
        self, 
        topic: str, 
        max_tokens: int = 8000,
        include_web_search: bool = True
    ) -> str:
        """Generate a comprehensive research report on the given topic"""
        pass
    
    def get_research_system_prompt(self) -> str:
        """Get the system prompt for research tasks"""
        return """You are an expert research assistant specializing in creating comprehensive, in-depth research reports. Your goal is to produce detailed, well-structured reports that thoroughly explore the given topic.

When conducting research:
1. Start with a clear overview of the topic
2. Explore multiple perspectives and viewpoints
3. Include relevant data, statistics, and examples
4. Cite sources when possible (even if simulated)
5. Identify key trends, challenges, and opportunities
6. Provide analysis and insights, not just information
7. Structure the report with clear sections and subsections
8. Include a summary of key findings
9. Suggest areas for further research

Format your report in Markdown with:
- Clear headings and subheadings
- Bullet points for key information
- Tables for comparative data
- Block quotes for important citations
- Bold and italic text for emphasis

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
                                "description": "The search query"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
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
                                "description": "Type of data to analyze"
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Analysis parameters"
                            }
                        },
                        "required": ["data_type"]
                    }
                }
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
                                "description": "The news topic"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back",
                                "default": 7
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]
    
    async def simulate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Simulate tool calls for research (to be replaced with real implementations)"""
        # This is a placeholder - in production, you would implement real web search, etc.
        if tool_name == "web_search":
            query = arguments.get("query", "")
            return f"""Search results for "{query}":
1. **Recent Developments**: Latest research shows significant progress in this area with new methodologies being developed.
2. **Key Statistics**: Market size estimated at $X billion with Y% annual growth rate.
3. **Expert Opinions**: Leading researchers suggest that this field will see major breakthroughs in the next 2-3 years.
4. **Case Studies**: Several successful implementations have been documented across various industries.
5. **Challenges**: Main obstacles include technical complexity, cost considerations, and regulatory requirements."""
        
        elif tool_name == "analyze_data":
            data_type = arguments.get("data_type", "")
            return f"""Data analysis for {data_type}:
- Growth Rate: 15% year-over-year
- Market Leaders: Company A (30%), Company B (25%), Others (45%)
- Regional Distribution: North America (40%), Europe (30%), Asia-Pacific (25%), Others (5%)
- Key Trends: Increasing adoption, technological advancement, cost reduction"""
        
        elif tool_name == "get_recent_news":
            topic = arguments.get("topic", "")
            return f"""Recent news about {topic}:
1. **Breaking**: Major announcement from industry leader about new initiative (2 days ago)
2. **Research**: New study published in Nature shows promising results (5 days ago)
3. **Market**: Investment of $500M announced in this sector (1 week ago)
4. **Policy**: New regulations proposed that could impact the industry (3 days ago)"""
        
        return "No data available for this tool call."
