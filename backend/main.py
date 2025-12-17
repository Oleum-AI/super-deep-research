import asyncio
import io
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict

import uvicorn
from config import settings
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models import (
    Base,
    MasterReport,
    MasterReportResponse,
    MergeRequest,
    ProviderReport,
    ProviderReportResponse,
    ResearchProgress,
    ResearchRequest,
    ResearchSession,
    ResearchSessionResponse,
    ResearchStatus,
    WebSocketMessage,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker

# Create async engine
engine = create_async_engine(settings.database_url, echo=False, future=True)

# Create async session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Store active websocket connections
websocket_manager: Dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Deep Research API",
    version="0.1.0",
    description="Multi-provider AI research application with intelligent report merging",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get DB session
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# Import services
from services.models import get_all_models_by_provider
from services.pdf_export import PDFExporter
from services.report_merger import ReportMerger
from services.research_orchestrator import ResearchOrchestrator


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/api/models")
async def get_models():
    """Get all available models grouped by provider"""
    return get_all_models_by_provider()


@app.post("/api/research/start", response_model=ResearchSessionResponse)
async def start_research(request: ResearchRequest, db: AsyncSession = Depends(get_db)):
    """Start a new research session"""
    # Create new research session
    session_id = str(uuid.uuid4())
    research_session = ResearchSession(
        id=session_id, topic=request.topic, status=ResearchStatus.PENDING
    )

    # Create provider reports
    for provider in request.providers:
        provider_report = ProviderReport(
            session_id=session_id, provider=provider, status=ResearchStatus.PENDING
        )
        db.add(provider_report)

    db.add(research_session)
    await db.commit()
    await db.refresh(research_session)

    # Start async research tasks - pass the session maker, not the session
    orchestrator = ResearchOrchestrator(async_session, send_websocket_update)
    asyncio.create_task(
        orchestrator.start_research(
            session_id=session_id,
            topic=request.topic,
            providers=request.providers,
            provider_settings=request.provider_settings,
        )
    )

    return ResearchSessionResponse.model_validate(research_session)


@app.get("/api/research/{session_id}/status", response_model=ResearchProgress)
async def get_research_status(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get research session status"""
    result = await db.execute(
        select(ResearchSession)
        .options(selectinload(ResearchSession.provider_reports))
        .where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    providers_status = {}
    for report in session.provider_reports:
        providers_status[report.provider] = {
            "status": report.status,
            "has_content": bool(report.content),
            "error": report.error_message,
        }

    return ResearchProgress(
        session_id=session_id, overall_status=session.status, providers=providers_status
    )


@app.get("/api/research/{session_id}/reports")
async def get_provider_reports(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get all provider reports for a session"""
    result = await db.execute(
        select(ProviderReport)
        .where(ProviderReport.session_id == session_id)
        .order_by(ProviderReport.created_at)
    )
    reports = result.scalars().all()

    return [ProviderReportResponse.model_validate(report) for report in reports]


@app.post("/api/research/{session_id}/merge", response_model=MasterReportResponse)
async def merge_reports(
    session_id: str, request: MergeRequest, db: AsyncSession = Depends(get_db)
):
    """Generate master report by merging provider reports"""
    # Check if all provider reports are completed
    result = await db.execute(
        select(ProviderReport).where(ProviderReport.session_id == session_id)
    )
    reports = result.scalars().all()

    if not reports:
        raise HTTPException(status_code=404, detail="No provider reports found")

    incomplete_reports = [r for r in reports if r.status != ResearchStatus.COMPLETED]
    if incomplete_reports:
        raise HTTPException(
            status_code=400,
            detail=f"Some provider reports are not completed: {[r.provider for r in incomplete_reports]}",
        )

    # Implement report merging
    merger = ReportMerger(request.merge_provider)
    merged_content = await merger.merge_reports(reports)

    # Create master report
    master_report = MasterReport(session_id=session_id, content=merged_content)
    db.add(master_report)

    # Update session status
    await db.execute(
        update(ResearchSession)
        .where(ResearchSession.id == session_id)
        .values(status=ResearchStatus.MERGED)
    )

    await db.commit()
    await db.refresh(master_report)

    return MasterReportResponse.model_validate(master_report)


@app.get("/api/research/{session_id}/export/pdf")
async def export_to_pdf(session_id: str, db: AsyncSession = Depends(get_db)):
    """Export research report to PDF"""
    # Get master report
    result = await db.execute(
        select(MasterReport).where(MasterReport.session_id == session_id)
    )
    master_report = result.scalar_one_or_none()

    if not master_report:
        raise HTTPException(status_code=404, detail="Master report not found")

    # Implement PDF export
    exporter = PDFExporter()

    # Get the research topic for the title
    session_result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    session = session_result.scalar_one()

    pdf_bytes = await exporter.export_to_pdf(
        markdown_content=master_report.content,
        title=f"Research Report: {session.topic}",
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=research_report_{session_id}.pdf"
        },
    )


@app.websocket("/ws/research/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_manager[session_id] = websocket

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        del websocket_manager[session_id]


async def send_websocket_update(session_id: str, message: WebSocketMessage):
    """Send update to connected websocket client"""
    if session_id in websocket_manager:
        websocket = websocket_manager[session_id]
        try:
            await websocket.send_json(message.model_dump())
        except Exception:
            # Remove disconnected client
            del websocket_manager[session_id]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.backend_port, reload=True)
