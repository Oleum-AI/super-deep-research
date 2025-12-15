from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import enum
import uuid

Base = declarative_base()

class ResearchStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    MERGED = "merged"

class Provider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"

# SQLAlchemy Models
class ResearchSession(Base):
    __tablename__ = "research_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(Text, nullable=False)
    status = Column(SQLEnum(ResearchStatus), default=ResearchStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    provider_reports = relationship("ProviderReport", back_populates="session", cascade="all, delete-orphan")
    master_report = relationship("MasterReport", back_populates="session", uselist=False, cascade="all, delete-orphan")

class ProviderReport(Base):
    __tablename__ = "provider_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("research_sessions.id"))
    provider = Column(SQLEnum(Provider), nullable=False)
    content = Column(Text)
    thinking = Column(Text, nullable=True)  # Stores LLM reasoning/metadata separately
    status = Column(SQLEnum(ResearchStatus), default=ResearchStatus.PENDING)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="provider_reports")

class MasterReport(Base):
    __tablename__ = "master_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("research_sessions.id"), unique=True)
    content = Column(Text)
    thinking = Column(Text, nullable=True)  # Stores LLM reasoning/metadata separately
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="master_report")

# Pydantic Models for API
class ResearchRequest(BaseModel):
    topic: str
    providers: List[Provider] = Field(default=[Provider.OPENAI, Provider.ANTHROPIC, Provider.XAI])
    max_tokens: Optional[int] = Field(default=4096, ge=1000, le=16384)
    include_web_search: bool = Field(default=True)

class ResearchSessionResponse(BaseModel):
    id: str
    topic: str
    status: ResearchStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProviderReportResponse(BaseModel):
    id: int
    provider: Provider
    content: Optional[str]
    thinking: Optional[str] = None  # LLM reasoning/metadata shown separately
    status: ResearchStatus
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MasterReportResponse(BaseModel):
    id: int
    content: str
    thinking: Optional[str] = None  # LLM reasoning/metadata shown separately
    created_at: datetime
    
    class Config:
        from_attributes = True

class ResearchProgress(BaseModel):
    session_id: str
    overall_status: ResearchStatus
    providers: Dict[str, Dict[str, Any]]
    
class MergeRequest(BaseModel):
    merge_provider: Provider = Field(default=Provider.OPENAI)
    
class WebSocketMessage(BaseModel):
    type: str
    session_id: str
    provider: Optional[str]
    status: Optional[str]
    content: Optional[str]
    error: Optional[str]
    progress: Optional[float]
