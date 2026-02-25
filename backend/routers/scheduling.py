from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from models import get_db, Base
from core.flow_registry import flow_registry

router = APIRouter(prefix="/schedules", tags=["Scheduling"])

# Database model for schedules
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

# Request/Response models
class ScheduleCreate(BaseModel):
    name: str
    flow_id: str
    cron_expression: str  # e.g., "0 9 * * 1-5" (9 AM on weekdays)
    variables: Dict[str, Any]
    test_env_id: Optional[str] = None

class ScheduleResponse(BaseModel):
    id: str
    name: str
    flow_id: str
    flow_name: str
    cron_expression: str
    variables: Dict[str, Any]
    test_env_id: Optional[str]
    is_active: bool
    created_at: datetime
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    total_runs: int
    
    class Config:
        from_attributes = True

@router.post("", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """
    Create a scheduled test execution
    
    Cron expression format:
    * * * * * (minute hour day month day_of_week)
    
    Examples:
    - "0 9 * * 1-5" - 9 AM on weekdays
    - "0 */4 * * *" - Every 4 hours
    - "0 0 * * 0" - Midnight on Sundays
    """
    
    # Validate flow exists
    flow = flow_registry.get_flow(schedule.flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{schedule.flow_id}' not found")
    
    # Validate cron expression (basic validation)
    parts = schedule.cron_expression.split()
    if len(parts) != 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression. Format: minute hour day month day_of_week"
        )
    
    schedule_id = str(uuid.uuid4())
    
    db_schedule = Schedule(
        id=schedule_id,
        name=schedule.name,
        flow_id=schedule.flow_id,
        cron_expression=schedule.cron_expression,
        variables=schedule.variables,
        test_env_id=schedule.test_env_id,
        is_active=True
    )
    
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    # TODO: Register with Celery Beat dynamically
    # For now, schedules are stored but need Celery Beat restart to pick up
    
    return ScheduleResponse(
        id=db_schedule.id,
        name=db_schedule.name,
        flow_id=db_schedule.flow_id,
        flow_name=flow['name'],
        cron_expression=db_schedule.cron_expression,
        variables=db_schedule.variables,
        test_env_id=db_schedule.test_env_id,
        is_active=db_schedule.is_active,
        created_at=db_schedule.created_at,
        last_run_at=db_schedule.last_run_at,
        next_run_at=db_schedule.next_run_at,
        total_runs=db_schedule.total_runs
    )

@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all scheduled tests"""
    
    query = db.query(Schedule)
    if active_only:
        query = query.filter(Schedule.is_active == True)
    
    schedules = query.order_by(Schedule.created_at.desc()).all()
    
    results = []
    for sched in schedules:
        flow = flow_registry.get_flow(sched.flow_id)
        flow_name = flow['name'] if flow else "Unknown"
        
        results.append(ScheduleResponse(
            id=sched.id,
            name=sched.name,
            flow_id=sched.flow_id,
            flow_name=flow_name,
            cron_expression=sched.cron_expression,
            variables=sched.variables,
            test_env_id=sched.test_env_id,
            is_active=sched.is_active,
            created_at=sched.created_at,
            last_run_at=sched.last_run_at,
            next_run_at=sched.next_run_at,
            total_runs=sched.total_runs
        ))
    
    return results

@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Get specific schedule details"""
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    flow = flow_registry.get_flow(schedule.flow_id)
    flow_name = flow['name'] if flow else "Unknown"
    
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        flow_id=schedule.flow_id,
        flow_name=flow_name,
        cron_expression=schedule.cron_expression,
        variables=schedule.variables,
        test_env_id=schedule.test_env_id,
        is_active=schedule.is_active,
        created_at=schedule.created_at,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        total_runs=schedule.total_runs
    )

@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Remove a schedule"""
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    
    return {"message": "Schedule deleted successfully", "schedule_id": schedule_id}

@router.post("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Enable/disable a schedule"""
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.is_active = not schedule.is_active
    db.commit()
    
    status = "enabled" if schedule.is_active else "disabled"
    return {
        "message": f"Schedule {status}",
        "schedule_id": schedule_id,
        "is_active": schedule.is_active
    }
