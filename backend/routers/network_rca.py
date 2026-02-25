from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json

from models import get_db, TestRun, StepLog, RCAReport
from core.network_monitor import NetworkMonitor
from core.llm.rca_engine import rca_engine

router = APIRouter(prefix="/runs", tags=["Network & RCA"])

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
async def get_network_events(run_id: str, db: Session = Depends(get_db)):
    """
    Get all captured network events for a test run
    """
    # Verify run exists
    test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    # Get network monitor data
    monitor = NetworkMonitor(run_id)
    summary = monitor.get_summary()
    
    return {
        "run_id": run_id,
        "summary": {
            "total_network_events": summary['total_network_events'],
            "total_console_events": summary['total_console_events'],
            "network_failures": summary['network_failures'],
            "console_errors": summary['console_errors'],
            "console_warnings": summary['console_warnings'],
            "total_anomalies": summary['total_anomalies']
        },
        "network_events": monitor.get_all_network_events(),
        "console_events": monitor.get_all_console_events(),
        "anomalies": summary['anomalies']
    }

@router.post("/{run_id}/network-events")
async def receive_network_events(
    run_id: str,
    events: List[NetworkEventCreate],
    db: Session = Depends(get_db)
):
    """
    Receive network/console events captured by frontend
    Merges with Playwright-captured events
    """
    # Verify run exists
    test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    monitor = NetworkMonitor(run_id)
    
    # Process each event
    for event in events:
        if event.event_type == 'request':
            monitor.capture_request({
                'url': event.url,
                'method': event.method,
                'timestamp': event.timestamp
            })
        elif event.event_type == 'response':
            monitor.capture_response({
                'url': event.url,
                'method': event.method,
                'status': event.status_code,
                'duration_ms': event.duration_ms,
                'timestamp': event.timestamp
            })
        elif event.event_type == 'failure':
            monitor.capture_failure({
                'url': event.url,
                'method': event.method,
                'errorText': event.error_text,
                'timestamp': event.timestamp
            })
        elif event.event_type == 'console':
            monitor.capture_console({
                'type': event.console_type,
                'text': event.console_text,
                'timestamp': event.timestamp
            })
    
    return {
        "message": f"Received {len(events)} events",
        "run_id": run_id
    }

@router.get("/{run_id}/rca")
async def get_rca_report(run_id: str, db: Session = Depends(get_db)):
    """
    Get RCA report for a failed test run
    """
    # Get existing RCA report
    rca_report = db.query(RCAReport).filter(RCAReport.run_id == run_id).first()
    
    if not rca_report:
        raise HTTPException(
            status_code=404,
            detail=f"No RCA report found for run '{run_id}'. Trigger analysis with POST /api/runs/{run_id}/rca/trigger"
        )
    
    return {
        "run_id": rca_report.run_id,
        "root_cause": rca_report.root_cause,
        "affected_service": rca_report.affected_step,  # Using affected_step as proxy
        "error_summary": rca_report.error_summary,
        "ai_explanation": rca_report.ai_explanation,
        "suggested_fix": rca_report.suggested_fix,
        "confidence_score": rca_report.confidence_score,
        "network_errors": rca_report.network_errors,
        "console_errors": rca_report.console_errors,
        "created_at": rca_report.created_at.isoformat()
    }

@router.post("/{run_id}/rca/trigger")
async def trigger_rca(run_id: str, streaming: bool = False, db: Session = Depends(get_db)):
    """
    Manually trigger RCA analysis (works for both passed and failed runs)
    
    Set streaming=true for token-by-token SSE streaming
    """
    # Get test run
    test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    # Get step logs
    step_logs = db.query(StepLog).filter(StepLog.run_id == run_id).order_by(StepLog.step_number).all()
    
    if not step_logs:
        raise HTTPException(status_code=400, detail="No step logs found for this run")
    
    # Find failed step (or last step if all passed)
    failed_steps = [log for log in step_logs if log.status == 'failure']
    failed_step = failed_steps[0] if failed_steps else step_logs[-1]
    
    # Get recent steps for context
    failed_step_num = failed_step.step_number
    recent_steps = [
        {
            'step_number': log.step_number,
            'step_description': log.step_description,
            'action': log.action,
            'status': log.status,
            'duration_ms': log.duration_ms
        }
        for log in step_logs
        if log.step_number < failed_step_num
    ][-5:]  # Last 5 steps before failure
    
    # Get network and console data
    monitor = NetworkMonitor(run_id)
    network_anomalies = monitor.get_anomalies()
    console_events = monitor.get_all_console_events()
    console_errors = [e for e in console_events if e.get('console_type') in ['error', 'warning']]
    
    # Prepare failed step data
    failed_step_data = {
        'step_number': failed_step.step_number,
        'step_description': failed_step.step_description,
        'action': failed_step.action,
        'target': failed_step.target,
        'error_message': failed_step.error_message or 'No error message',
        'duration_ms': failed_step.duration_ms
    }
    
    # Screenshot description (could be enhanced with vision model)
    screenshot_desc = "Screenshot available but not analyzed" if failed_step.screenshot_b64 else None
    
    # Perform RCA
    if streaming:
        # Return SSE stream
        async def generate_stream():
            try:
                async for token in await rca_engine.analyze(
                    run_id=run_id,
                    failed_step=failed_step_data,
                    recent_steps=recent_steps,
                    network_anomalies=network_anomalies,
                    console_errors=console_errors,
                    screenshot_description=screenshot_desc,
                    flow_name=test_run.flow_name or "Unknown",
                    variables=test_run.variables_used or {},
                    streaming=True
                ):
                    yield f"data: {json.dumps({'token': token})}\n\n"
                    await asyncio.sleep(0.01)  # Small delay for better streaming UX
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Complete analysis
        rca_result = await rca_engine.analyze(
            run_id=run_id,
            failed_step=failed_step_data,
            recent_steps=recent_steps,
            network_anomalies=network_anomalies,
            console_errors=console_errors,
            screenshot_description=screenshot_desc,
            flow_name=test_run.flow_name or "Unknown",
            variables=test_run.variables_used or {},
            streaming=False
        )
        
        # Save to database
        existing_rca = db.query(RCAReport).filter(RCAReport.run_id == run_id).first()
        
        if existing_rca:
            # Update existing
            existing_rca.root_cause = rca_result.get('root_cause')
            existing_rca.error_summary = rca_result.get('root_cause')
            existing_rca.ai_explanation = json.dumps(rca_result)
            existing_rca.suggested_fix = rca_result.get('suggested_fix')
            existing_rca.confidence_score = rca_result.get('confidence')
        else:
            # Create new
            rca_report = RCAReport(
                run_id=run_id,
                error_summary=rca_result.get('root_cause'),
                root_cause=rca_result.get('root_cause'),
                affected_step=failed_step.step_number,
                network_errors={'anomalies': [a for a in network_anomalies if a.get('type') != 'console']},
                console_errors={'errors': console_errors},
                ai_explanation=json.dumps(rca_result),
                suggested_fix=rca_result.get('suggested_fix'),
                confidence_score=rca_result.get('confidence', 0.0)
            )
            db.add(rca_report)
        
        db.commit()
        
        return {
            "message": "RCA analysis complete",
            "run_id": run_id,
            "rca": rca_result
        }
