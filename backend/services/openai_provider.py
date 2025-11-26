import json

import openai
from models import Provider

from services.base_provider import BaseProvider

try:
    from agents import Agent, Runner, WebSearchTool

    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation for research"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.provider_name = Provider.OPENAI
        self.client = openai.AsyncOpenAI(api_key=api_key, timeout=600.0)

    async def generate_research_report(
        self, topic: str, max_tokens: int = 8000, include_web_search: bool = True
    ) -> str:
        """Generate a comprehensive research report using OpenAI Deep Research"""

        # Try to use Deep Research API if available
        if AGENTS_SDK_AVAILABLE and include_web_search:
            try:
                return await self._deep_research(topic)
            except Exception as e:
                print(f"Deep Research failed, falling back to GPT-4o: {str(e)}")
                # Fall back to standard GPT-4o

        # Fallback to standard GPT-4o
        return await self._standard_research(topic, max_tokens, include_web_search)

    async def _deep_research(self, topic: str) -> str:
        """Use OpenAI Deep Research API with Agents SDK"""
        import os

        from agents import Agent, Runner, set_default_openai_client

        # Set up the client for Agents SDK
        set_default_openai_client(self.client)

        # Disable tracing for privacy (zero data retention)
        os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

        # Create the research agent with web search tool
        research_agent = Agent(
            name="Deep Research Agent",
            model="o4-mini-deep-research-2025-06-26",
            tools=[WebSearchTool()],  # Use actual tool object, not string
            instructions="""You are an expert research assistant that conducts comprehensive, in-depth research.
            
Your research should:
- Be thorough and explore multiple perspectives
- Include relevant data, statistics, and examples
- Be well-structured with clear sections
- Use markdown formatting
- Include citations from web sources
- Provide historical context, current state, and future projections
- Identify key stakeholders and their perspectives
- Analyze potential impacts and implications

Conduct web searches as needed to gather current, accurate information.""",
        )

        # Run the research
        result_stream = Runner.run_streamed(
            research_agent,
            f"Please conduct comprehensive research on the following topic and create a detailed report:\n\n{topic}",
        )

        # Process stream and collect results
        search_queries = []
        async for event in result_stream.stream_events():
            # Track search queries for debugging
            if event.type == "raw_response_event" and hasattr(event.data, "item"):
                item = event.data.item
                if hasattr(item, "action") and item.action:
                    action = item.action
                    # Access as object attributes, not dictionary
                    if hasattr(action, "type") and action.type == "search":
                        query = getattr(action, "query", "")
                        if query:
                            search_queries.append(query)

        # Get final output
        final_output = result_stream.final_output

        # Add metadata about searches performed
        if search_queries:
            final_output += f"\n\n---\n\n**Research Process**: Performed {len(search_queries)} web searches to gather information.\n"

        return final_output

    async def _standard_research(
        self, topic: str, max_tokens: int = 8000, include_web_search: bool = True
    ) -> str:
        """Fallback to standard GPT-4o research"""

        # GPT-4o supports max 16384 completion tokens, use 4096 as safe default
        safe_max_tokens = min(max_tokens, 4096)

        messages = [
            {"role": "system", "content": self.get_research_system_prompt()},
            {
                "role": "user",
                "content": f"""Please conduct comprehensive research on the following topic and create a detailed report:

Topic: {topic}

Requirements:
- Provide an in-depth analysis with multiple perspectives
- Include relevant data, statistics, and examples
- Structure the report with clear sections
- Make it comprehensive (aim for {safe_max_tokens // 4} words)
- Use markdown formatting
- Include citations where appropriate
""",
            },
        ]

        # If web search is enabled, make an initial call with tools
        if include_web_search:
            # First, gather information using tools
            tool_response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.get_research_tools(),
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000,
            )

            # Process tool calls
            if tool_response.choices[0].message.tool_calls:
                messages.append(tool_response.choices[0].message)

                for tool_call in tool_response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # Simulate tool execution
                    tool_result = await self.simulate_tool_call(
                        function_name, function_args
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        }
                    )

        # Generate the final research report using GPT-4o (latest model)
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=safe_max_tokens,
            presence_penalty=0.1,
            frequency_penalty=0.1,
        )

        return response.choices[0].message.content or "Failed to generate report"

    def get_research_system_prompt(self) -> str:
        """Enhanced system prompt for OpenAI"""
        base_prompt = super().get_research_system_prompt()
        return f"""{base_prompt}

Additional guidelines for OpenAI research:
- Leverage your training data to provide accurate, up-to-date information
- Use a balanced, analytical tone
- When using tools, integrate the findings seamlessly into the narrative
- Ensure factual accuracy and avoid speculation without clear indication
- Provide actionable insights and recommendations where appropriate"""
