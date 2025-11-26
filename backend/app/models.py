from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum

from .database import Base

class JobStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)

    individual_reports = relationship("IndividualReport", back_populates="job")
    master_report = relationship("MasterReport", uselist=False, back_populates="job")


class IndividualReport(Base):
    __tablename__ = "individual_reports"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("research_jobs.id"))
    provider = Column(String)
    report_text = Column(Text)

    job = relationship("ResearchJob", back_populates="individual_reports")


class MasterReport(Base):
    __tablename__ = "master_reports"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("research_jobs.id"))
    report_text = Column(Text)
    
    job = relationship("ResearchJob", back_populates="master_report")
