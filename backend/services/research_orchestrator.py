import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from models import (
    Provider,
    ProviderReport,
    ProviderSettings,
    ResearchSession,
    ResearchStatus,
    WebSocketMessage,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from services.llm_providers import LLMProviderService
from services.models import ModelName

# Default models for each provider
DEFAULT_MODELS: Dict[Provider, ModelName] = {
    Provider.OPENAI: "o3-deep-research-2025-06-26",
    Provider.ANTHROPIC: "claude-sonnet-4-5-20250929",
    Provider.XAI: "grok-4-0709",
}


class ResearchOrchestrator:
    """Orchestrates parallel research execution across multiple providers"""

    def __init__(self, session_maker: async_sessionmaker, websocket_callback=None):
        self.session_maker = session_maker
        self.llm_service = LLMProviderService()
        self.websocket_callback = websocket_callback

    async def start_research(
        self,
        session_id: str,
        topic: str,
        providers: List[Provider],
        provider_settings: Optional[Dict[str, ProviderSettings]] = None,
    ):
        """Start parallel research across all specified providers"""

        # Update session status to in progress
        async with self.session_maker() as session:
            await session.execute(
                update(ResearchSession)
                .where(ResearchSession.id == session_id)
                .values(status=ResearchStatus.IN_PROGRESS, updated_at=datetime.utcnow())
            )
            await session.commit()

        # Create tasks for each provider
        tasks = []
        for provider in providers:
            # Get model from settings or use default
            model = DEFAULT_MODELS.get(provider)
            max_tokens = 8000  # Default

            if provider_settings and provider.value in provider_settings:
                settings = provider_settings[provider.value]
                # Use selected model if provided, otherwise use default
                if settings.model:
                    model = settings.model
                max_tokens = settings.max_tokens

            if not model:
                continue

            task = asyncio.create_task(
                self.run_provider_research(
                    session_id=session_id,
                    provider=provider,
                    topic=topic,
                    model=model,
                    max_output_tokens=max_tokens,
                )
            )
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check if all providers completed successfully
        all_success = all(
            isinstance(result, dict)
            and result.get("status") == ResearchStatus.COMPLETED
            for result in results
        )

        # Update overall session status
        final_status = (
            ResearchStatus.COMPLETED if all_success else ResearchStatus.FAILED
        )
        async with self.session_maker() as session:
            await session.execute(
                update(ResearchSession)
                .where(ResearchSession.id == session_id)
                .values(status=final_status, updated_at=datetime.utcnow())
            )
            await session.commit()

        return results

    async def run_provider_research(
        self,
        session_id: str,
        provider: Provider,
        topic: str,
        model: ModelName,
        max_output_tokens: int | None = None,
    ) -> Dict[str, Any]:
        """Run research for a single provider"""

        # Send starting notification
        await self.send_websocket_update(
            session_id=session_id,
            provider=provider.value,
            status="starting",
            progress=0.1,
        )

        # Create a new session for this provider task
        async with self.session_maker() as db:
            # Get the provider report record
            result = await db.execute(
                select(ProviderReport)
                .where(ProviderReport.session_id == session_id)
                .where(ProviderReport.provider == provider)
            )
            report_record = result.scalar_one_or_none()

            if not report_record:
                return {
                    "provider": provider.value,
                    "status": ResearchStatus.FAILED,
                    "error": "Provider report record not found",
                }

            try:
                # Update status to in progress
                report_record.status = ResearchStatus.IN_PROGRESS
                await db.commit()

                # Send progress update
                await self.send_websocket_update(
                    session_id=session_id,
                    provider=provider.value,
                    status="in_progress",
                    progress=0.3,
                )

                # Generate the research report (outside DB transaction)
                report_result = await self.llm_service.generate_research_report(
                    provider=provider,
                    topic=topic,
                    model=model,
                    max_output_tokens=max_output_tokens,
                )

                # Extract content and thinking from the result Dict
                report_content = (
                    report_result.get("content", "")
                    if isinstance(report_result, dict)
                    else str(report_result)
                )
                report_thinking = (
                    report_result.get("thinking")
                    if isinstance(report_result, dict)
                    else None
                )

                # Send progress update
                await self.send_websocket_update(
                    session_id=session_id,
                    provider=provider.value,
                    status="processing",
                    progress=0.8,
                )

                # Update the report record
                report_record.content = report_content
                report_record.thinking = report_thinking
                report_record.status = ResearchStatus.COMPLETED
                report_record.error_message = None
                await db.commit()

                # Send completion notification
                content_preview = (
                    report_content[:500] + "..."
                    if len(report_content) > 500
                    else report_content
                )
                await self.send_websocket_update(
                    session_id=session_id,
                    provider=provider.value,
                    status="completed",
                    content=content_preview,
                    progress=1.0,
                )

                return {
                    "provider": provider.value,
                    "status": ResearchStatus.COMPLETED,
                    "content_length": len(report_content),
                }

            except Exception as e:
                # Update report record with error
                report_record.status = ResearchStatus.FAILED
                report_record.error_message = str(e)
                await db.commit()

                # Send error notification
                await self.send_websocket_update(
                    session_id=session_id,
                    provider=provider.value,
                    status="failed",
                    error=str(e),
                    progress=1.0,
                )

                return {
                    "provider": provider.value,
                    "status": ResearchStatus.FAILED,
                    "error": str(e),
                }

    async def send_websocket_update(
        self,
        session_id: str,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        content: Optional[str] = None,
        error: Optional[str] = None,
        progress: Optional[float] = None,
    ):
        """Send update via websocket if callback is available"""
        if self.websocket_callback:
            message = WebSocketMessage(
                type="research_update",
                session_id=session_id,
                provider=provider,
                status=status,
                content=content,
                error=error,
                progress=progress,
            )
            await self.websocket_callback(session_id, message)
