from typing import Dict, Optional, List, Any
from models import Provider
from services.openai_provider import OpenAIProvider
from services.anthropic_provider import AnthropicProvider
from services.xai_provider import XAIProvider
from services.base_provider import BaseProvider
from config import settings

class LLMProviderService:
    """Service to manage all LLM providers"""
    
    def __init__(self):
        self.providers: Dict[Provider, Optional[BaseProvider]] = {
            Provider.OPENAI: None,
            Provider.ANTHROPIC: None,
            Provider.XAI: None
        }
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers based on API keys"""
        if settings.openai_api_key:
            self.providers[Provider.OPENAI] = OpenAIProvider(settings.openai_api_key)
        
        if settings.anthropic_api_key:
            self.providers[Provider.ANTHROPIC] = AnthropicProvider(settings.anthropic_api_key)
        
        if settings.xai_api_key:
            self.providers[Provider.XAI] = XAIProvider(settings.xai_api_key)
    
    def get_provider(self, provider: Provider) -> Optional[BaseProvider]:
        """Get a specific provider instance"""
        return self.providers.get(provider)
    
    def get_available_providers(self) -> List[Provider]:
        """Get list of available providers (those with API keys)"""
        return [p for p, instance in self.providers.items() if instance is not None]
    
    async def generate_research_report(
        self,
        provider: Provider,
        topic: str,
        max_tokens: int = 8000,
        include_web_search: bool = True
    ) -> Dict[str, Optional[str]]:
        """Generate a research report using the specified provider
        
        Returns:
            Dict with 'content' (the report) and 'thinking' (reasoning/metadata, if any)
        """
        provider_instance = self.get_provider(provider)
        
        if not provider_instance:
            raise ValueError(f"Provider {provider} is not configured (missing API key)")
        
        return await provider_instance.generate_research_report(
            topic=topic,
            max_tokens=max_tokens,
            include_web_search=include_web_search
        )
