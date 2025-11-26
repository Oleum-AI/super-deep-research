from pydantic import BaseModel
from typing import List, Optional
from .models import JobStatus

class ResearchRequest(BaseModel):
    query: str

class IndividualReport(BaseModel):
    id: int
    provider: str
    report_text: str

    class Config:
        orm_mode = True

class MasterReport(BaseModel):
    id: int
    report_text: str

    class Config:
        orm_mode = True

class ResearchJob(BaseModel):
    id: int
    query: str
    status: JobStatus
    individual_reports: List[IndividualReport] = []
    master_report: Optional[MasterReport] = None

    class Config:
        orm_mode = True

class SynthesisRequest(BaseModel):
    job_id: int
    provider: str
