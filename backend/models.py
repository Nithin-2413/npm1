from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://qa_user:qa_password@localhost:5432/qa_automation")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestRun(Base):
    """Stores test run metadata"""
    __tablename__ = "test_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), unique=True, index=True, nullable=False)
    flow_id = Column(String(100), index=True)
    flow_name = Column(String(200))
    status = Column(String(50), default="pending")  # pending, running, passed, failed, cancelled
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    variables_used = Column(JSON, nullable=True)
    order_id_captured = Column(String(100), nullable=True)
    test_env_id = Column(String(100), nullable=True)  # Reference to secret/test environment
    error_summary = Column(Text, nullable=True)
    natural_language_input = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StepLog(Base):
    """Stores individual step execution logs"""
    __tablename__ = "step_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), index=True, nullable=False)
    step_number = Column(Integer, nullable=False)
    step_description = Column(Text, nullable=False)
    action = Column(String(50))  # click, fill, select, wait, etc.
    target = Column(Text)
    value = Column(Text, nullable=True)
    status = Column(String(50))  # pending, running, success, failure
    screenshot_b64 = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    details = Column(JSON, nullable=True)


class RCAReport(Base):
    """Stores Root Cause Analysis reports for failed tests"""
    __tablename__ = "rca_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), index=True, nullable=False)
    error_summary = Column(Text)
    root_cause = Column(Text)
    affected_step = Column(Integer)
    network_errors = Column(JSON, nullable=True)
    console_errors = Column(JSON, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TestEnvironment(Base):
    """Stores test environment secrets/credentials"""
    __tablename__ = "test_environments"
    
    id = Column(String(100), primary_key=True)
    test_env = Column(String(200), nullable=False)
    release_branch = Column(String(200), nullable=True)
    url = Column(Text, nullable=False)
    username = Column(String(200), nullable=True)
    password = Column(Text, nullable=True)  # Should be encrypted in production
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FlowTemplate(Base):
    """Stores flow templates in database (in addition to JSON files)"""
    __tablename__ = "flow_templates"
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    template_json = Column(JSON, nullable=False)
    estimated_duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Schedule(Base):
    """Scheduled test execution"""
    __tablename__ = "schedules"
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    flow_id = Column(String(100), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    variables = Column(JSON)
    test_env_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    total_runs = Column(Integer, default=0)


# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)