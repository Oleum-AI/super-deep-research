from typing import Dict, Optional

import anthropic
from models import Provider

from services.base_provider import BaseProvider
from services.models import ANTHROPIC_MODELS, AnthropicModelName


class AnthropicProvider(BaseProvider):
    """Anthropic provider implementation for research"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.provider_name = Provider.ANTHROPIC
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate_research_report(
        self,
        topic: str,
        model: AnthropicModelName = "claude-sonnet-4-5-20250929",
        max_output_tokens: int | None = None,
    ) -> Dict[str, Optional[str]]:
        """Generate a comprehensive research report using Anthropic Claude Sonnet 4.5

        Returns:
            Dict with 'content' (the report) and 'thinking' (reasoning process, if any)
        """

        try:
            config = ANTHROPIC_MODELS[model]
        except KeyError:
            raise ValueError(f"Invalid model: {model}")

        effective_max = (
            min(max_output_tokens, config.max_output_tokens)
            if max_output_tokens
            else config.max_output_tokens
        )

        effective_max = max(
            effective_max, 42000
        )  # Ensure at least 42000 tokens are available

        safe_max_tokens = (
            effective_max - 2000
        )  # 2000 tokens for safety, at least 40000 total, 10000 for thinking 30000 for content left

        # Calculate thinking budget: 25% of max_tokens
        thinking_budget = int(safe_max_tokens * 0.25)

        system_prompt = super().get_research_system_prompt()

        user_message = self.get_user_prompt(topic, safe_max_tokens, thinking_budget)

        # Generate the research report using Claude Sonnet 4.5 with extended thinking
        # Use streaming to handle long operations (required for >10 min operations)
        content = ""
        thinking = None

        async with self.client.messages.stream(
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=safe_max_tokens,
            temperature=1.0,  # must be 1.0 for extended thinking to work
            tools=[{"name": "web_search", "type": "web_search_20250305"}],
            tool_choice={"type": "auto"},
            # Enable extended thinking for deeper reasoning
            thinking={
                "budget_tokens": thinking_budget,  # Dynamic based on max_tokens
                "type": "enabled",
            },
        ) as stream:
            # Collect the full response from streaming
            response = await stream.get_final_message()

        # Extract content and thinking SEPARATELY
        if response.content and len(response.content) > 0:
            for block in response.content:
                if block.type == "thinking":
                    # Store thinking separately instead of embedding in content
                    thinking = block.thinking
                elif block.type == "text":
                    content += block.text

        if not content:
            content = "Failed to generate report"

        return {"content": content, "thinking": thinking}

    def get_user_prompt(
        self, topic: str, safe_max_tokens: int, thinking_budget: int
    ) -> str:
        return f"""Please conduct comprehensive research on the following topic and create a detailed report:
        Topic: {topic}

        Requirements:
        - Provide an in-depth analysis with multiple perspectives
        - Include relevant data, statistics, and examples
        - Structure the report with clear sections
        - Make it comprehensive (aim for {(safe_max_tokens - thinking_budget) // 4} words)
        - Use markdown formatting
        - IMPORTANT: Use inline citations [1], [2], etc. throughout your report
        - IMPORTANT: Include a ## References section at the end with all cited sources
        - Explore historical context, current state, and future projections
        - Identify key stakeholders and their perspectives
        - Analyze potential impacts and implications
        - Use your extended thinking capabilities to reason deeply about the topic
        """
