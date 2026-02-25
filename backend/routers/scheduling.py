from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import logging

from models import schedules_collection, serialize_doc
from core.flow_registry import flow_registry

router = APIRouter(prefix="/schedules", tags=["Scheduling"])
logger = logging.getLogger(__name__)

# Request/Response models
class ScheduleCreate(BaseModel):
    name: str
    flow_id: str
    cron_expression: str  # e.g., "0 9 * * 1-5" (9 AM on weekdays)
    variables: Dict[str, Any]
    test_env_id: Optional[str] = None

class ScheduleResponse(BaseModel):
    id: str
    schedule_id: str
    name: str
    flow_id: str
    flow_name: str
    cron_expression: str
    variables: Dict[str, Any]
    test_env_id: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    total_runs: int = 0

@router.post("", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate):
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
    now = datetime.now(timezone.utc)
    
    doc = {
        "schedule_id": schedule_id,
        "name": schedule.name,
        "flow_id": schedule.flow_id,
        "cron_expression": schedule.cron_expression,
        "variables": schedule.variables,
        "test_env_id": schedule.test_env_id,
        "is_active": True,
        "created_at": now,
        "last_run_at": None,
        "next_run_at": None,
        "total_runs": 0
    }
    
    result = schedules_collection.insert_one(doc)
    
    return ScheduleResponse(
        id=str(result.inserted_id),
        schedule_id=schedule_id,
        name=schedule.name,
        flow_id=schedule.flow_id,
        flow_name=flow['name'],
        cron_expression=schedule.cron_expression,
        variables=schedule.variables,
        test_env_id=schedule.test_env_id,
        is_active=True,
        created_at=now.isoformat(),
        last_run_at=None,
        next_run_at=None,
        total_runs=0
    )

@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(active_only: bool = True):
    """List all scheduled tests"""
    
    query = {}
    if active_only:
        query["is_active"] = True
    
    schedules = list(schedules_collection.find(query).sort("created_at", -1))
    
    results = []
    for sched in schedules:
        flow = flow_registry.get_flow(sched.get('flow_id'))
        flow_name = flow['name'] if flow else "Unknown"
        
        results.append(ScheduleResponse(
            id=str(sched.get('_id', '')),
            schedule_id=sched.get('schedule_id', ''),
            name=sched.get('name', ''),
            flow_id=sched.get('flow_id', ''),
            flow_name=flow_name,
            cron_expression=sched.get('cron_expression', ''),
            variables=sched.get('variables', {}),
            test_env_id=sched.get('test_env_id'),
            is_active=sched.get('is_active', False),
            created_at=sched.get('created_at').isoformat() if sched.get('created_at') else None,
            last_run_at=sched.get('last_run_at').isoformat() if sched.get('last_run_at') else None,
            next_run_at=sched.get('next_run_at').isoformat() if sched.get('next_run_at') else None,
            total_runs=sched.get('total_runs', 0)
        ))
    
    return results

@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """Get specific schedule details"""
    
    schedule = schedules_collection.find_one({"schedule_id": schedule_id})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    flow = flow_registry.get_flow(schedule.get('flow_id'))
    flow_name = flow['name'] if flow else "Unknown"
    
    return ScheduleResponse(
        id=str(schedule.get('_id', '')),
        schedule_id=schedule.get('schedule_id', ''),
        name=schedule.get('name', ''),
        flow_id=schedule.get('flow_id', ''),
        flow_name=flow_name,
        cron_expression=schedule.get('cron_expression', ''),
        variables=schedule.get('variables', {}),
        test_env_id=schedule.get('test_env_id'),
        is_active=schedule.get('is_active', False),
        created_at=schedule.get('created_at').isoformat() if schedule.get('created_at') else None,
        last_run_at=schedule.get('last_run_at').isoformat() if schedule.get('last_run_at') else None,
        next_run_at=schedule.get('next_run_at').isoformat() if schedule.get('next_run_at') else None,
        total_runs=schedule.get('total_runs', 0)
    )

@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Remove a schedule"""
    
    result = schedules_collection.delete_one({"schedule_id": schedule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return {"message": "Schedule deleted successfully", "schedule_id": schedule_id}

@router.post("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str):
    """Enable/disable a schedule"""
    
    schedule = schedules_collection.find_one({"schedule_id": schedule_id})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    new_status = not schedule.get('is_active', False)
    schedules_collection.update_one(
        {"schedule_id": schedule_id},
        {"$set": {"is_active": new_status}}
    )
    
    status = "enabled" if new_status else "disabled"
    return {
        "message": f"Schedule {status}",
        "schedule_id": schedule_id,
        "is_active": new_status
    }
