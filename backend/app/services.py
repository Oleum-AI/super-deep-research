import asyncio
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from groq import AsyncGroq
import os
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    async def generate_report(self, provider: str, query: str) -> str:
        if provider == "openai":
            return await self._generate_openai_report(query)
        elif provider == "anthropic":
            return await self._generate_anthropic_report(query)
        elif provider == "groq":
            return await self._generate_groq_report(query)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _generate_openai_report(self, query: str) -> str:
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Generate a detailed research report on: {query}"}],
        )
        return response.choices[0].message.content

    async def _generate_anthropic_report(self, query: str) -> str:
        response = await self.anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2048,
            messages=[{"role": "user", "content": f"Generate a detailed research report on: {query}"}],
        )
        return response.content[0].text

    async def _generate_groq_report(self, query: str) -> str:
        response = await self.groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": f"Generate a detailed research report on: {query}"}],
        )
        return response.choices[0].message.content

    async def synthesize_reports(self, provider: str, reports: list[str]) -> str:
        reports_text = "\n\n---\n\n".join(reports)
        prompt = f"Synthesize the following reports into a single, comprehensive master report:\n\n{reports_text}"
        
        if provider == "openai":
            return await self._generate_openai_report(prompt)
        elif provider == "anthropic":
            return await self._generate_anthropic_report(prompt)
        elif provider == "groq":
            return await self._generate_groq_report(prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

llm_service = LLMService()
