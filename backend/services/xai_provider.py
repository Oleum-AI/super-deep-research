import httpx
from typing import Optional, Dict, Any
import json
from services.base_provider import BaseProvider
from models import Provider
from config import settings

class XAIProvider(BaseProvider):
    """xAI provider implementation for research"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.provider_name = Provider.XAI
        self.base_url = settings.xai_base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_research_report(
        self, 
        topic: str, 
        max_tokens: int = 8000,
        include_web_search: bool = True
    ) -> Dict[str, Optional[str]]:
        """Generate a comprehensive research report using xAI Grok
        
        Returns:
            Dict with 'content' (the report) and 'thinking' (None for xAI as it doesn't expose reasoning)
        """
        
        # Grok supports large output, but use reasonable limit
        safe_max_tokens = min(max_tokens, 8192)
        
        messages = [
            {
                "role": "system",
                "content": self.get_research_system_prompt()
            },
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
- IMPORTANT: Use inline citations [1], [2], etc. throughout your report
- IMPORTANT: Include a ## References section at the end with all cited sources
- Focus on technical accuracy and scientific rigor
- Include mathematical or computational aspects where relevant
- Discuss cutting-edge developments and research frontiers
"""
            }
        ]
        
        # Make the API call to xAI
        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "grok-2-latest",  # Use latest Grok 2 model
                        "messages": messages,
                        "max_tokens": safe_max_tokens,
                        "temperature": 0.7,
                        "stream": False
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    # xAI/Grok doesn't expose thinking, so return None
                    return {"content": content, "thinking": None}
                else:
                    return {"content": f"Error: Unexpected response format from xAI: {result}", "thinking": None}
                
            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_body = e.response.json()
                    error_detail = f" - {error_body.get('error', {}).get('message', str(error_body))}"
                except:
                    error_detail = f" - {e.response.text[:200]}"
                return {"content": f"Error generating report with xAI: {e.response.status_code} {e.response.reason_phrase}{error_detail}", "thinking": None}
            except httpx.RequestError as e:
                return {"content": f"Error generating report with xAI: Network error - {str(e)}", "thinking": None}
            except Exception as e:
                return {"content": f"Unexpected error with xAI: {str(e)}", "thinking": None}
        
        return {"content": "Failed to generate report", "thinking": None}
    
    def get_research_system_prompt(self) -> str:
        """Enhanced system prompt for xAI"""
        base_prompt = super().get_research_system_prompt()
        return f"""{base_prompt}

Additional guidelines for xAI research:
- Emphasize technical depth and scientific accuracy
- Include mathematical formulations where appropriate
- Discuss computational aspects and algorithmic considerations
- Analyze scalability and performance implications
- Consider both theoretical foundations and practical applications
- Highlight innovative approaches and breakthrough technologies
- Include code examples or pseudocode where relevant
- Discuss open problems and research challenges in the field"""
