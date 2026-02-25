from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import uuid
import asyncio

from models import get_db, TestRun
from core.flow_registry import flow_registry
from tasks import execute_test_run
import os

router = APIRouter(prefix="/runs", tags=["Batch Execution"])

class BatchRunRequest(BaseModel):
    flow_id: str
    variables: Dict[str, Any]
    test_env_id: str = None

class BatchExecutionRequest(BaseModel):
    runs: List[BatchRunRequest]

@router.post("/batch")
async def execute_batch(
    request: BatchExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute multiple test runs in parallel
    
    Max parallel runs controlled by MAX_PARALLEL_RUNS env var
    Shared browser with isolated contexts for each run
    """
    
    max_parallel = int(os.getenv("MAX_PARALLEL_RUNS", "3"))
    
    if len(request.runs) > max_parallel:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute more than {max_parallel} runs in parallel. "
                   f"Split into multiple batches or increase MAX_PARALLEL_RUNS."
        )
    
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    run_ids = []
    
    # Create all test runs first
    for run_request in request.runs:
        # Validate flow
        flow = flow_registry.get_flow(run_request.flow_id)
        if not flow:
            raise HTTPException(
                status_code=404,
                detail=f"Flow '{run_request.flow_id}' not found"
            )
        
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        test_run = TestRun(
            run_id=run_id,
            flow_id=run_request.flow_id,
            flow_name=flow['name'],
            status="pending",
            variables_used=run_request.variables,
            test_env_id=run_request.test_env_id,
            started_at=datetime.utcnow()
        )
        
        db.add(test_run)
        run_ids.append(run_id)
    
    db.commit()
    
    # Start all runs in parallel (Celery will handle actual parallelization)
    for i, run_id in enumerate(run_ids):
        run_request = request.runs[i]
        execute_test_run.delay(
            run_id=run_id,
            flow_id=run_request.flow_id,
            variables=run_request.variables,
            natural_language_input=None,
            test_env_id=run_request.test_env_id
        )
    
    return {
        "batch_id": batch_id,
        "status": "started",
        "total_runs": len(run_ids),
        "run_ids": run_ids,
        "max_parallel": max_parallel,
        "message": f"Batch execution started with {len(run_ids)} runs"
    }

@router.get("/batch/{batch_id}/status")
async def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    """
    Get aggregated status for a batch of runs
    
    Note: batch_id is informational. We track by run_ids passed in response.
    """
    # In a full implementation, you'd store batch metadata
    # For now, return instructions
    return {
        "batch_id": batch_id,
        "message": "Use individual run IDs to check status",
        "note": "Query GET /api/runs/{run_id}/status for each run_id from batch response"
    }
