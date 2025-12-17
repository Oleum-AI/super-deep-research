import logging
import os
from typing import Dict, Optional

import openai
from agents import (
    Agent,
    ModelSettings,
    Runner,
    WebSearchTool,
    set_default_openai_client,
)
from models import Provider

from services.base_provider import BaseProvider
from services.models import OPENAI_MODELS, OpenAIModelName

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation for research"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.provider_name = Provider.OPENAI
        self.client = openai.AsyncOpenAI(api_key=api_key, timeout=600.0)

    async def generate_research_report(
        self,
        topic: str,
        model: OpenAIModelName = "o3-deep-research-2025-06-26",
        max_output_tokens: int | None = None,
    ) -> Dict[str, Optional[str]]:
        """Generate a comprehensive research report using OpenAI Deep Research
            Uses OpenAI Deep Research API with Agents SDK

        Returns:
            Dict with 'content' (the report) and 'thinking' (research metadata, if any)
        """

        try:
            config = OPENAI_MODELS[model]
        except KeyError:
            raise ValueError(f"Invalid model: {model}")

        try:
            # Set up the client for Agents SDK
            set_default_openai_client(self.client)
            # Disable tracing for privacy (zero data retention)
            os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
        except Exception as e:
            logger.error(f"Failed to set up OpenAI client: {str(e)}")
            raise e

        try:
            effective_max = (
                min(max_output_tokens, config.max_output_tokens)
                if max_output_tokens
                else config.max_output_tokens
            )

            # Create the research agent with web search tool
            research_agent = Agent(
                name="Deep Research Agent",
                model=model,
                model_settings=ModelSettings(
                    max_tokens=effective_max,
                ),
                tools=[WebSearchTool()],  # Use actual tool object, not string
                instructions=super().get_research_system_prompt(),
            )

            # Run the research
            result_stream = Runner.run_streamed(
                research_agent,
                self._get_agent_prompt(topic),
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

            # Build metadata about the research process (stored separately)
            thinking = None
            if search_queries:
                thinking = self._format_search_queries(search_queries)

            return {"content": final_output, "thinking": thinking}

        except Exception as e:
            logger.error(f"Deep Research failed: {str(e)}")
            raise e

    def _get_agent_prompt(self, topic: str) -> str:
        return f"Please conduct comprehensive research on the following topic and create a detailed report:\n\n{topic}"

    def _format_search_queries(self, search_queries: list[str]) -> str:
        return (
            f"Research Process: Performed {len(search_queries)} web searches to gather information.\n\nSearch queries used:\n"
            + "\n".join([f"- {q}" for q in search_queries])
        )
