"""Research orchestration service."""
import asyncio
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import ResearchSessionDB
from models import (
    ProviderType, 
    ResearchSession, 
    ResearchStatus,
    ProviderReport,
    Citation
)
from providers import OpenAIProvider, AnthropicProvider, XAIProvider, ResearchProvider


class ResearchService:
    """Service for managing research sessions and coordinating multiple providers."""
    
    def __init__(self):
        """Initialize the research service."""
        self.active_sessions: dict[str, ResearchSession] = {}
        self._provider_cache: dict[ProviderType, ResearchProvider] = {}
    
    def _get_provider(self, provider_type: ProviderType) -> Optional[ResearchProvider]:
        """Get or create a provider instance.
        
        Args:
            provider_type: Type of provider to get
            
        Returns:
            Provider instance or None if not configured
        """
        if provider_type in self._provider_cache:
            return self._provider_cache[provider_type]
        
        brave_key = settings.brave_search_api_key
        
        try:
            if provider_type == ProviderType.OPENAI:
                if not settings.openai_api_key:
                    return None
                provider = OpenAIProvider(settings.openai_api_key, brave_key)
            elif provider_type == ProviderType.ANTHROPIC:
                if not settings.anthropic_api_key:
                    return None
                provider = AnthropicProvider(settings.anthropic_api_key, brave_key)
            elif provider_type == ProviderType.XAI:
                if not settings.xai_api_key:
                    return None
                provider = XAIProvider(settings.xai_api_key, brave_key)
            else:
                return None
            
            self._provider_cache[provider_type] = provider
            return provider
        except Exception as e:
            print(f"Error creating provider {provider_type}: {e}")
            return None
    
    async def create_session(
        self,
        query: str,
        providers: list[ProviderType],
        max_sources: int,
        db: AsyncSession
    ) -> ResearchSession:
        """Create a new research session.
        
        Args:
            query: Research query
            providers: List of providers to use
            max_sources: Maximum number of sources
            db: Database session
            
        Returns:
            Created research session
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = ResearchSession(
            session_id=session_id,
            query=query,
            providers=providers,
            status=ResearchStatus.PENDING,
            reports={},
            created_at=now,
            updated_at=now
        )
        
        self.active_sessions[session_id] = session
        
        # Save to database
        db_session = ResearchSessionDB(
            id=session_id,
            query=query,
            providers=[p.value for p in providers],
            status=ResearchStatus.PENDING.value,
            reports={},
            created_at=now,
            updated_at=now
        )
        db.add(db_session)
        await db.commit()
        
        # Start research in background
        asyncio.create_task(
            self._conduct_research(session_id, query, providers, max_sources, db)
        )
        
        return session
    
    async def _conduct_research(
        self,
        session_id: str,
        query: str,
        providers: list[ProviderType],
        max_sources: int,
        db: AsyncSession
    ):
        """Conduct research using multiple providers in parallel.
        
        Args:
            session_id: Session ID
            query: Research query
            providers: List of providers to use
            max_sources: Maximum number of sources
            db: Database session
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        # Create tasks for each provider
        tasks = []
        for provider_type in providers:
            task = asyncio.create_task(
                self._run_provider_research(
                    session_id, 
                    provider_type, 
                    query, 
                    max_sources
                )
            )
            tasks.append(task)
        
        # Wait for all providers to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update final session status
        session.status = ResearchStatus.COMPLETED
        session.updated_at = datetime.utcnow()
        
        # Save to database
        await self._save_session(session_id, db)
    
    async def _run_provider_research(
        self,
        session_id: str,
        provider_type: ProviderType,
        query: str,
        max_sources: int
    ):
        """Run research for a single provider.
        
        Args:
            session_id: Session ID
            provider_type: Provider to use
            query: Research query
            max_sources: Maximum number of sources
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        provider = self._get_provider(provider_type)
        if not provider:
            # Provider not configured
            report = ProviderReport(
                provider=provider_type,
                status=ResearchStatus.FAILED,
                error=f"{provider_type.value} provider not configured",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            session.reports[provider_type.value] = report
            return
        
        try:
            # Stream updates from provider
            async for report in provider.conduct_research(query, max_sources):
                session.reports[provider_type.value] = report
                session.updated_at = datetime.utcnow()
        except Exception as e:
            # Handle provider errors
            report = ProviderReport(
                provider=provider_type,
                status=ResearchStatus.FAILED,
                error=str(e),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            session.reports[provider_type.value] = report
    
    async def synthesize_reports(
        self,
        session_id: str,
        synthesis_provider: ProviderType,
        db: AsyncSession
    ) -> str:
        """Synthesize multiple reports into a master report.
        
        Args:
            session_id: Session ID
            synthesis_provider: Provider to use for synthesis
            db: Database session
            
        Returns:
            Master report content
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        provider = self._get_provider(synthesis_provider)
        if not provider:
            raise ValueError(f"{synthesis_provider.value} provider not configured")
        
        # Collect completed reports
        completed_reports = []
        all_citations = []
        
        for provider_name, report in session.reports.items():
            if report.status == ResearchStatus.COMPLETED and report.content:
                completed_reports.append({
                    "provider": provider_name,
                    "content": report.content
                })
                all_citations.extend(report.citations)
        
        if not completed_reports:
            raise ValueError("No completed reports to synthesize")
        
        # Create synthesis prompt
        reports_text = "\n\n---\n\n".join([
            f"## Report from {r['provider'].upper()}\n\n{r['content']}"
            for r in completed_reports
        ])
        
        system_prompt = """You are an expert research synthesizer. Your task is to analyze multiple research reports on the same topic and create a comprehensive master report that combines the best insights from each.

Guidelines:
- Create a cohesive, well-structured master report (2000-4000 words)
- Extract and combine the best insights from each report
- Eliminate redundancy while preserving unique perspectives
- Maintain all important citations
- Improve clarity and flow
- Use markdown formatting with clear sections
- Include an executive summary
- Conclude with comprehensive key findings"""

        user_prompt = f"""Original Research Query: {session.query}

I have {len(completed_reports)} research reports on this topic from different AI providers. Please synthesize them into a single, superior master report that captures the best insights from each.

{reports_text}

Create a master report that:
1. Combines the strongest points from each report
2. Eliminates redundancy
3. Maintains logical flow and structure
4. Preserves important citations
5. Provides the most comprehensive analysis"""

        # Generate synthesis based on provider type
        try:
            if synthesis_provider == ProviderType.OPENAI:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.openai_api_key)
                response = await client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                master_report = response.choices[0].message.content
                
            elif synthesis_provider == ProviderType.ANTHROPIC:
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=settings.anthropic_api_key)
                message = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                master_report = message.content[0].text
                
            elif synthesis_provider == ProviderType.XAI:
                import httpx
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.xai_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "grok-beta",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 4000
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    master_report = data["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Unknown provider: {synthesis_provider}")
            
            # Update session with master report
            session.master_report = master_report
            session.updated_at = datetime.utcnow()
            
            # Save to database
            await self._save_session(session_id, db)
            
            return master_report
            
        except Exception as e:
            raise Exception(f"Synthesis failed: {str(e)}")
    
    async def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Get a research session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Research session or None
        """
        return self.active_sessions.get(session_id)
    
    async def _save_session(self, session_id: str, db: AsyncSession):
        """Save session to database.
        
        Args:
            session_id: Session ID
            db: Database session
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        # Convert reports to dict for JSON storage
        reports_dict = {}
        for provider_name, report in session.reports.items():
            reports_dict[provider_name] = {
                "provider": report.provider.value,
                "status": report.status.value,
                "content": report.content,
                "citations": [c.model_dump() for c in report.citations],
                "error": report.error,
                "started_at": report.started_at.isoformat() if report.started_at else None,
                "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            }
        
        # Update database
        result = await db.execute(
            select(ResearchSessionDB).where(ResearchSessionDB.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        
        if db_session:
            db_session.status = session.status.value
            db_session.reports = reports_dict
            db_session.master_report = session.master_report
            db_session.updated_at = session.updated_at
            await db.commit()
    
    async def list_sessions(self, db: AsyncSession, limit: int = 50) -> list[ResearchSession]:
        """List recent research sessions.
        
        Args:
            db: Database session
            limit: Maximum number of sessions to return
            
        Returns:
            List of research sessions
        """
        result = await db.execute(
            select(ResearchSessionDB)
            .order_by(ResearchSessionDB.created_at.desc())
            .limit(limit)
        )
        db_sessions = result.scalars().all()
        
        sessions = []
        for db_session in db_sessions:
            # Reconstruct session from database
            reports = {}
            for provider_name, report_data in db_session.reports.items():
                reports[provider_name] = ProviderReport(
                    provider=ProviderType(report_data["provider"]),
                    status=ResearchStatus(report_data["status"]),
                    content=report_data.get("content", ""),
                    citations=[Citation(**c) for c in report_data.get("citations", [])],
                    error=report_data.get("error"),
                    started_at=datetime.fromisoformat(report_data["started_at"]) if report_data.get("started_at") else None,
                    completed_at=datetime.fromisoformat(report_data["completed_at"]) if report_data.get("completed_at") else None,
                )
            
            session = ResearchSession(
                session_id=db_session.id,
                query=db_session.query,
                providers=[ProviderType(p) for p in db_session.providers],
                status=ResearchStatus(db_session.status),
                reports=reports,
                master_report=db_session.master_report,
                created_at=db_session.created_at,
                updated_at=db_session.updated_at
            )
            sessions.append(session)
        
        return sessions


# Global service instance
research_service = ResearchService()

