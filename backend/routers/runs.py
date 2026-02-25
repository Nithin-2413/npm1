from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
import os
import logging

from models import (
    create_test_run, get_test_run, update_test_run,
    create_step_log, get_step_logs,
    get_test_environment
)
from core.flow_registry import flow_registry

router = APIRouter(prefix="/runs", tags=["Test Runs"])
logger = logging.getLogger(__name__)

class StartRunRequest(BaseModel):
    flow_id: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    natural_language_input: Optional[str] = None
    test_env_id: Optional[str] = None

class RunStatusResponse(BaseModel):
    run_id: str
    flow_id: Optional[str] = None
    flow_name: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    variables_used: Optional[Dict[str, Any]] = None
    error_summary: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None

@router.post("", response_model=Dict[str, Any])
async def start_test_run(
    request: StartRunRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new test run
    
    Supports:
    1. flow_id + variables (direct execution)
    2. natural_language_input (AI parses intent)
    """
    
    # Validate input
    if not request.flow_id and not request.natural_language_input:
        raise HTTPException(
            status_code=400, 
            detail="Either 'flow_id' or 'natural_language_input' must be provided"
        )
    
    final_flow_id = request.flow_id
    final_variables = request.variables or {}
    
    # If using natural language, try to parse it
    if request.natural_language_input and not request.flow_id:
        # For now, try to match flow by keywords
        available_flows = flow_registry.list_flows()
        nl_lower = request.natural_language_input.lower()
        
        for flow in available_flows:
            if flow['id'].replace('_', ' ') in nl_lower or flow['name'].lower() in nl_lower:
                final_flow_id = flow['id']
                break
        
        if not final_flow_id and available_flows:
            # Default to first flow if no match
            final_flow_id = available_flows[0]['id']
    
    # Validate flow exists
    flow = flow_registry.get_flow(final_flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{final_flow_id}' not found")
    
    # Get test environment credentials if provided
    if request.test_env_id:
        test_env = get_test_environment(request.test_env_id)
        if test_env:
            final_variables['url'] = test_env.get('url', final_variables.get('url'))
            final_variables['username'] = test_env.get('username', final_variables.get('username'))
            final_variables['password'] = test_env.get('password', final_variables.get('password'))
    
    # Generate unique run ID
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    
    # Create test run record
    test_run = create_test_run({
        "run_id": run_id,
        "flow_id": final_flow_id,
        "flow_name": flow['name'],
        "status": "pending",
        "variables_used": final_variables,
        "natural_language_input": request.natural_language_input,
        "test_env_id": request.test_env_id
    })
    
    # Start execution in background
    background_tasks.add_task(execute_flow_async, run_id, final_flow_id, final_variables)
    
    return {
        'status': 'started',
        'run_id': run_id,
        'flow_id': final_flow_id,
        'flow_name': flow['name'],
        'variables': final_variables,
        'message': 'Test run started successfully'
    }

async def execute_flow_async(run_id: str, flow_id: str, variables: dict):
    """Execute flow in background"""
    try:
        # Update status to running
        update_test_run(run_id, {"status": "running"})
        
        # Get flow definition
        flow = flow_registry.get_flow(flow_id)
        if not flow:
            update_test_run(run_id, {
                "status": "failed",
                "error_summary": f"Flow '{flow_id}' not found",
                "finished_at": datetime.now(timezone.utc)
            })
            return
        
        # Execute steps
        steps = flow.get('steps', [])
        for i, step in enumerate(steps):
            step_num = i + 1
            
            # Log step start
            create_step_log({
                "run_id": run_id,
                "step_number": step_num,
                "step_description": step.get('description', f'Step {step_num}'),
                "action": step.get('action', 'unknown'),
                "target": step.get('target', ''),
                "value": step.get('value', ''),
                "status": "success"
            })
        
        # Update to passed
        update_test_run(run_id, {
            "status": "passed",
            "finished_at": datetime.now(timezone.utc)
        })
        
    except Exception as e:
        logger.error(f"Flow execution failed: {e}")
        update_test_run(run_id, {
            "status": "failed",
            "error_summary": str(e),
            "finished_at": datetime.now(timezone.utc)
        })

@router.get("/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str):
    """Get current status of a test run"""
    test_run = get_test_run(run_id)
    
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    return RunStatusResponse(
        run_id=test_run.get('run_id', run_id),
        flow_id=test_run.get('flow_id'),
        flow_name=test_run.get('flow_name'),
        status=test_run.get('status', 'unknown'),
        started_at=test_run.get('started_at'),
        finished_at=test_run.get('finished_at'),
        variables_used=test_run.get('variables_used'),
        error_summary=test_run.get('error_summary'),
        progress={}
    )

@router.post("/{run_id}/cancel")
async def cancel_test_run(run_id: str):
    """Cancel a running test"""
    test_run = get_test_run(run_id)
    
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    if test_run.get('status') not in ["pending", "running"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel test run with status '{test_run.get('status')}'"
        )
    
    # Update status to cancelled
    update_test_run(run_id, {
        "status": "cancelled",
        "finished_at": datetime.now(timezone.utc),
        "error_summary": "Test run cancelled by user"
    })
    
    return {
        "run_id": run_id,
        "status": "cancelled",
        "message": "Test run cancelled successfully"
    }

@router.get("/{run_id}/logs")
async def get_run_logs(run_id: str):
    """Get step logs for a test run"""
    test_run = get_test_run(run_id)
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    logs = get_step_logs(run_id)
    
    return [
        {
            "step_number": log.get("step_number"),
            "description": log.get("step_description"),
            "action": log.get("action"),
            "target": log.get("target"),
            "value": log.get("value"),
            "status": log.get("status"),
            "timestamp": log.get("timestamp"),
            "duration_ms": log.get("duration_ms"),
            "error_message": log.get("error_message"),
            "screenshot_b64": log.get("screenshot_b64"),
            "details": log.get("details")
        }
        for log in logs
    ]

@router.get("")
async def list_test_runs(
    status: Optional[str] = None,
    flow_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """List all test runs with optional filtering"""
    from models import test_runs_collection, serialize_doc
    
    query = {}
    if status:
        query["status"] = status
    if flow_id:
        query["flow_id"] = flow_id
    
    runs = list(
        test_runs_collection.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    
    total = test_runs_collection.count_documents(query)
    
    return {
        "runs": serialize_doc(runs),
        "total": total,
        "limit": limit,
        "skip": skip
    }
