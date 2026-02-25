from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import logging

from models import create_test_run, get_test_run, test_runs_collection, serialize_doc
from core.flow_registry import flow_registry

router = APIRouter(prefix="/runs", tags=["Batch Execution"])
logger = logging.getLogger(__name__)

class BatchRunRequest(BaseModel):
    flow_id: str
    variables: Dict[str, Any]
    test_env_id: str = None

class BatchExecutionRequest(BaseModel):
    runs: List[BatchRunRequest]

@router.post("/batch")
async def execute_batch(
    request: BatchExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute multiple test runs in parallel
    
    Max parallel runs controlled by MAX_PARALLEL_RUNS env var
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
    
    # Create all test runs
    for run_request in request.runs:
        # Validate flow
        flow = flow_registry.get_flow(run_request.flow_id)
        if not flow:
            raise HTTPException(
                status_code=404,
                detail=f"Flow '{run_request.flow_id}' not found"
            )
        
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        create_test_run({
            "run_id": run_id,
            "flow_id": run_request.flow_id,
            "flow_name": flow['name'],
            "status": "pending",
            "variables_used": run_request.variables,
            "test_env_id": run_request.test_env_id
        })
        
        run_ids.append(run_id)
    
    # Start all runs in background
    for i, run_id in enumerate(run_ids):
        run_request = request.runs[i]
        background_tasks.add_task(
            execute_flow_background,
            run_id,
            run_request.flow_id,
            run_request.variables
        )
    
    return {
        "batch_id": batch_id,
        "status": "started",
        "total_runs": len(run_ids),
        "run_ids": run_ids,
        "max_parallel": max_parallel,
        "message": f"Batch execution started with {len(run_ids)} runs"
    }

async def execute_flow_background(run_id: str, flow_id: str, variables: dict):
    """Execute flow in background"""
    from routers.runs import execute_flow_async
    await execute_flow_async(run_id, flow_id, variables)

@router.get("/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """Get aggregated status for a batch of runs"""
    return {
        "batch_id": batch_id,
        "message": "Use individual run IDs to check status",
        "note": "Query GET /api/runs/{run_id}/status for each run_id from batch response"
    }
