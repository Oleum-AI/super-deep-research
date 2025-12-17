from typing import Dict, Optional

from config import settings
from models import Provider
from xai_sdk import AsyncClient
from xai_sdk.chat import system, user
from xai_sdk.tools import web_search

from services.base_provider import BaseProvider
from services.models import XAI_MODELS, XAIModelName


class XAIProvider(BaseProvider):
    """xAI provider implementation for research"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.provider_name = Provider.XAI
        self.base_url = settings.xai_base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.temperature: float = 0.7
        self.client = AsyncClient(
            api_key=api_key, timeout=3600
        )  # Override default timeout with longer timeout for reasoning models

    async def generate_research_report(
        self,
        topic: str,
        model: XAIModelName = "grok-4-0709",
        max_output_tokens: int | None = None,
    ) -> Dict[str, Optional[str]]:
        """Generate a comprehensive research report using xAI Grok

        Returns:
            Dict with 'content' (the report) and 'thinking' (None for xAI as it doesn't expose reasoning)
        """

        try:
            config = XAI_MODELS[model]
        except KeyError:
            raise ValueError(f"Invalid model: {model}")

        effective_max = (
            min(max_output_tokens, config.max_output_tokens)
            if max_output_tokens
            else config.max_output_tokens
        )
        safe_max_output_tokens = effective_max - 2000  # 2000 tokens for safety

        # Make the API call to xAI using the SDK
        try:
            async with self.client as client:
                chat = client.chat.create(
                    model=model,  # model is already a string
                    max_tokens=effective_max,
                    temperature=self.temperature,
                    tools=[web_search()],
                )
                chat.append(system(super().get_research_system_prompt()))
                chat.append(user(self.get_user_prompt(topic, safe_max_output_tokens)))
                response = await chat.sample()

                # xai_sdk returns the message content directly
                content = str(response) if response else ""

                if content:
                    return {"content": content, "thinking": None}
                else:
                    return {
                        "content": "Error: Empty response from xAI",
                        "thinking": None,
                    }

        except Exception as e:
            return {
                "content": f"Unexpected error with xAI: {str(e)}",
                "thinking": None,
            }

    def get_user_prompt(self, topic: str, safe_max_output_tokens: int) -> str:
        return f"""
        Please conduct comprehensive research on the following topic and create a detailed report:
        Topic: {topic}

        Requirements:
        - Provide an in-depth analysis with multiple perspectives
        - Include relevant data, statistics, and examples
        - Structure the report with clear sections
        - Make it comprehensive (aim for {safe_max_output_tokens // 4} words)
        - Use markdown formatting
        - IMPORTANT: Use inline citations [1], [2], etc. throughout your report
        - IMPORTANT: Include a ## References section at the end with all cited sources
        - Focus on technical accuracy and scientific rigor
        - Include mathematical or computational aspects where relevant
        - Discuss cutting-edge developments and research frontiers
        """
