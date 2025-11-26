from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, get_db
from .services import llm_service
import asyncio

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

async def run_research(job_id: int, query: str, db: Session):
    job = db.query(models.ResearchJob).filter(models.ResearchJob.id == job_id).first()
    if not job:
        return
    
    job.status = models.JobStatus.PROCESSING
    db.commit()

    providers = ["openai", "anthropic", "groq"]
    tasks = [llm_service.generate_report(provider, query) for provider in providers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for provider, result in zip(providers, results):
        if isinstance(result, Exception):
            report_text = f"Error generating report from {provider}: {result}"
        else:
            report_text = result
        
        individual_report = models.IndividualReport(
            job_id=job_id,
            provider=provider,
            report_text=report_text
        )
        db.add(individual_report)
    
    job.status = models.JobStatus.COMPLETED
    db.commit()


@app.post("/api/research", response_model=schemas.ResearchJob)
def create_research_job(request: schemas.ResearchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = models.ResearchJob(query=request.query)
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(run_research, job.id, request.query, db)
    return job

@app.get("/api/research/{job_id}", response_model=schemas.ResearchJob)
def get_research_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.ResearchJob).filter(models.ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/synthesize", response_model=schemas.MasterReport)
async def synthesize_reports(request: schemas.SynthesisRequest, db: Session = Depends(get_db)):
    job = db.query(models.ResearchJob).filter(models.ResearchJob.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != models.JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Research job is not yet complete")

    individual_reports = [report.report_text for report in job.individual_reports]
    
    master_report_text = await llm_service.synthesize_reports(request.provider, individual_reports)

    master_report = models.MasterReport(
        job_id=request.job_id,
        report_text=master_report_text
    )
    db.add(master_report)
    db.commit()
    db.refresh(master_report)

    return master_report
