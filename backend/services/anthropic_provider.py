import anthropic
from typing import Optional, Dict, Any
import json
from services.base_provider import BaseProvider
from models import Provider

class AnthropicProvider(BaseProvider):
    """Anthropic provider implementation for research"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.provider_name = Provider.ANTHROPIC
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def generate_research_report(
        self, 
        topic: str, 
        max_tokens: int = 8000,
        include_web_search: bool = True
    ) -> str:
        """Generate a comprehensive research report using Anthropic Claude Sonnet 4.5"""
        
        # Claude Sonnet 4.5 supports max 64K output tokens
        # Use a safe limit based on user request, capped at 16K for performance
        safe_max_tokens = min(max_tokens, 16384)
        
        # Calculate thinking budget: 25% of max_tokens, but ensure max_tokens > thinking_budget
        # Minimum max_tokens should be 2000 to allow for at least 500 thinking tokens
        thinking_budget = min(int(safe_max_tokens * 0.25), 10000)
        
        # Ensure max_tokens is greater than thinking_budget (required by API)
        if safe_max_tokens <= thinking_budget:
            # Increase max_tokens to be at least 1.5x the thinking budget
            safe_max_tokens = max(thinking_budget + 2000, 4096)
        
        system_prompt = self.get_research_system_prompt()
        
        # Prepare the research query
        user_message = f"""Please conduct comprehensive research on the following topic and create a detailed report:

Topic: {topic}

Requirements:
- Provide an in-depth analysis with multiple perspectives
- Include relevant data, statistics, and examples
- Structure the report with clear sections
- Make it comprehensive (aim for {(safe_max_tokens - thinking_budget) // 4} words)
- Use markdown formatting
- Include citations where appropriate
- Explore historical context, current state, and future projections
- Identify key stakeholders and their perspectives
- Analyze potential impacts and implications
- Use your extended thinking capabilities to reason deeply about the topic
"""

        # If web search is enabled, add context about using simulated data
        if include_web_search:
            user_message += """

Note: While I'll structure this as if I've conducted web searches and gathered recent data, please understand that I'll be drawing from my training data and using reasonable estimates where specific current data isn't available. I'll clearly indicate when I'm making projections or estimates.
"""
        
        # Generate the research report using Claude Sonnet 4.5 with extended thinking
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",  # Latest Claude Sonnet 4.5
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=safe_max_tokens,
            temperature=1,  # Must be 1 when using extended thinking
            # Enable extended thinking for deeper reasoning
            thinking={
                "type": "enabled",
                "budget_tokens": thinking_budget  # Dynamic based on max_tokens
            }
        )
        
        # Extract the text content
        if response.content and len(response.content) > 0:
            # Combine thinking and response if thinking is present
            full_response = ""
            for block in response.content:
                if block.type == "thinking":
                    # Optionally include thinking process as a collapsed section
                    full_response += f"\n\n<details>\n<summary>🧠 Reasoning Process</summary>\n\n{block.thinking}\n\n</details>\n\n"
                elif block.type == "text":
                    full_response += block.text
            
            return full_response if full_response else "Failed to generate report"
        
        return "Failed to generate report"
    
    def get_research_system_prompt(self) -> str:
        """Enhanced system prompt for Anthropic Claude"""
        base_prompt = super().get_research_system_prompt()
        return f"""{base_prompt}

Additional guidelines for Claude research:
- Leverage your analytical capabilities to provide deep, nuanced insights
- Use your training to identify connections between different aspects of the topic
- Be transparent about the limitations of available information
- Provide balanced perspectives while clearly stating your analytical conclusions
- Structure arguments logically with clear reasoning
- When discussing technical topics, explain complex concepts clearly
- Include ethical considerations where relevant"""
