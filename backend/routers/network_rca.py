from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging

from models import (
    get_test_run, get_step_logs, create_rca_report, get_rca_report,
    test_runs_collection, rca_reports_collection
)

router = APIRouter(prefix="/runs", tags=["Network & RCA"])
logger = logging.getLogger(__name__)

class NetworkEventCreate(BaseModel):
    """Frontend-captured network event"""
    event_type: str  # request, response, failure, console
    timestamp: str
    method: Optional[str] = None
    url: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[int] = None
    error_text: Optional[str] = None
    console_type: Optional[str] = None
    console_text: Optional[str] = None

@router.get("/{run_id}/network")
async def get_network_events(run_id: str):
    """Get all captured network events for a test run"""
    # Verify run exists
    test_run = get_test_run(run_id)
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    # For now, return empty network data (real implementation would store this)
    return {
        "run_id": run_id,
        "summary": {
            "total_network_events": 0,
            "total_console_events": 0,
            "network_failures": 0,
            "console_errors": 0,
            "console_warnings": 0,
            "total_anomalies": 0
        },
        "network_events": [],
        "console_events": [],
        "anomalies": []
    }

@router.post("/{run_id}/network-events")
async def receive_network_events(run_id: str, events: List[NetworkEventCreate]):
    """Receive network/console events captured by frontend"""
    # Verify run exists
    test_run = get_test_run(run_id)
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    # Process events (store in DB in real implementation)
    logger.info(f"Received {len(events)} network events for run {run_id}")
    
    return {
        "message": f"Received {len(events)} events",
        "run_id": run_id
    }

@router.get("/{run_id}/rca")
async def get_rca_report_endpoint(run_id: str):
    """Get RCA report for a failed test run"""
    rca_report = get_rca_report(run_id)
    
    if not rca_report:
        raise HTTPException(
            status_code=404,
            detail=f"No RCA report found for run '{run_id}'. Trigger analysis with POST /api/runs/{run_id}/rca/trigger"
        )
    
    return {
        "run_id": rca_report.get('run_id'),
        "root_cause": rca_report.get('root_cause'),
        "affected_step": rca_report.get('affected_step'),
        "error_summary": rca_report.get('error_summary'),
        "ai_explanation": rca_report.get('ai_explanation'),
        "suggested_fix": rca_report.get('suggested_fix'),
        "confidence_score": rca_report.get('confidence_score'),
        "network_errors": rca_report.get('network_errors'),
        "console_errors": rca_report.get('console_errors'),
        "created_at": rca_report.get('created_at')
    }

@router.post("/{run_id}/rca/trigger")
async def trigger_rca(run_id: str, streaming: bool = False):
    """Manually trigger RCA analysis"""
    # Get test run
    test_run = get_test_run(run_id)
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    # Get step logs
    step_logs = get_step_logs(run_id)
    
    if not step_logs:
        raise HTTPException(status_code=400, detail="No step logs found for this run")
    
    # Find failed step (or last step if all passed)
    failed_steps = [log for log in step_logs if log.get('status') == 'failure']
    failed_step = failed_steps[0] if failed_steps else step_logs[-1]
    
    # Generate simple RCA (real implementation would use LLM)
    error_msg = failed_step.get('error_message', 'No error message')
    flow_name = test_run.get('flow_name', 'Unknown')
    
    rca_result = {
        "root_cause": f"Step {failed_step.get('step_number')}: {failed_step.get('step_description', 'Unknown step')}",
        "failure_category": "execution_error",
        "affected_service": "playwright",
        "confidence": 0.75,
        "evidence": [error_msg] if error_msg else [],
        "suggested_fix": f"Review step {failed_step.get('step_number')} in flow '{flow_name}' and verify selectors/actions",
        "next_steps": [
            "Check if selectors are valid",
            "Verify page load timing",
            "Review network requests"
        ]
    }
    
    # Save to database
    create_rca_report({
        "run_id": run_id,
        "error_summary": error_msg,
        "root_cause": rca_result["root_cause"],
        "affected_step": failed_step.get('step_number'),
        "network_errors": [],
        "console_errors": [],
        "ai_explanation": json.dumps(rca_result),
        "suggested_fix": rca_result["suggested_fix"],
        "confidence_score": rca_result["confidence"]
    })
    
    return {
        "message": "RCA analysis complete",
        "run_id": run_id,
        "rca": rca_result
    }
