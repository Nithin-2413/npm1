from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import redis
import json
import os

from models import get_db, TestRun, TestEnvironment
from core.flow_registry import flow_registry
from core.llm.intent_parser import intent_parser
from core.llm.flow_selector import flow_selector
from core.llm.variable_resolver import variable_resolver
from tasks import execute_test_run

router = APIRouter(prefix="/runs", tags=["Test Runs"])

# Redis for clarification sessions
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url, decode_responses=True)

class StartRunRequest(BaseModel):
    flow_id: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    natural_language_input: Optional[str] = None
    test_env_id: Optional[str] = None

class ClarificationRequest(BaseModel):
    session_id: str
    user_response: str

class RunStatusResponse(BaseModel):
    run_id: str
    flow_id: Optional[str]
    flow_name: Optional[str]
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    variables_used: Optional[Dict[str, Any]]
    error_summary: Optional[str]
    progress: Optional[Dict[str, Any]] = None

@router.post("", response_model=Dict[str, Any])
async def start_test_run(
    request: StartRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a new test run with intelligent flow selection
    
    Supports three modes:
    1. flow_id + variables (traditional - skip NL parsing)
    2. natural_language_input only (AI parses intent + selects flow)
    3. both (use flow_id but extract variables from NL)
    """
    
    # Validate input
    if not request.flow_id and not request.natural_language_input:
        raise HTTPException(
            status_code=400, 
            detail="Either 'flow_id' or 'natural_language_input' must be provided"
        )
    
    # Get all available flows for parsing/selection
    available_flows = flow_registry.list_flows()
    
    final_flow_id = None
    final_variables = request.variables or {}
    confidence = 1.0
    reasoning = None
    
    # Mode 1: Natural language processing
    if request.natural_language_input:
        # Step 1: Intent parsing (extract variables)
        intent_result = await intent_parser.parse(
            request.natural_language_input,
            available_flows
        )
        
        # Check if clarification needed
        if intent_result.get('clarification_needed') and intent_result.get('confidence', 0) < 0.6:
            # Store in Redis for follow-up
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            redis_client.setex(
                f"clarification:{session_id}",
                3600,  # 1 hour TTL
                json.dumps({
                    'natural_language': request.natural_language_input,
                    'intent_result': intent_result,
                    'variables': final_variables,
                    'test_env_id': request.test_env_id
                })
            )
            
            return {
                'status': 'clarification_needed',
                'session_id': session_id,
                'question': intent_result['clarification_needed'],
                'parsed_flow': intent_result.get('flow_id'),
                'extracted_variables': intent_result.get('extracted_variables', {}),
                'missing_required': intent_result.get('missing_required', [])
            }
        
        # Merge LLM-extracted variables
        llm_vars = intent_result.get('extracted_variables', {})
        final_variables = {**llm_vars, **final_variables}  # form overrides LLM
        
        # Step 2: Flow selection (if not provided)
        if not request.flow_id:
            if intent_result.get('flow_id'):
                # Intent parser found a flow
                final_flow_id = intent_result['flow_id']
                confidence = intent_result.get('confidence', 0.8)
            else:
                # Use semantic search + LLM ranking
                selection_result = await flow_selector.select_flow(
                    request.natural_language_input,
                    available_flows
                )
                final_flow_id = selection_result['flow_id']
                confidence = selection_result['confidence']
                reasoning = selection_result.get('reasoning')
        else:
            final_flow_id = request.flow_id
    else:
        # Mode 2: Direct flow ID (traditional)
        final_flow_id = request.flow_id
    
    # Validate flow exists
    flow = flow_registry.get_flow(final_flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{final_flow_id}' not found")
    
    # Step 3: Variable resolution
    resolution_result = variable_resolver.resolve(
        flow=flow,
        form_overrides=final_variables,
        llm_extracted={}  # Already merged above
    )
    
    # Check for missing required variables
    if resolution_result['missing_required']:
        return {
            'status': 'missing_variables',
            'flow_id': final_flow_id,
            'flow_name': flow['name'],
            'missing_required': resolution_result['missing_required'],
            'resolved_variables': resolution_result['resolved'],
            'message': f"Missing required parameters: {', '.join(resolution_result['missing_required'])}"
        }
    
    final_variables = resolution_result['resolved']
    
    # Get test environment if provided
    if request.test_env_id:
        test_env = db.query(TestEnvironment).filter(TestEnvironment.id == request.test_env_id).first()
        if test_env:
            # Inject credentials
            final_variables['url'] = test_env.url
            final_variables['username'] = test_env.username
            final_variables['password'] = test_env.password
    
    # Generate unique run ID
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    
    # Create test run record
    test_run = TestRun(
        run_id=run_id,
        flow_id=final_flow_id,
        flow_name=flow['name'],
        status="pending",
        variables_used=final_variables,
        natural_language_input=request.natural_language_input,
        test_env_id=request.test_env_id,
        started_at=datetime.utcnow()
    )
    
    db.add(test_run)
    db.commit()
    db.refresh(test_run)
    
    # Start execution in background (Celery task)
    execute_test_run.delay(
        run_id=run_id,
        flow_id=final_flow_id,
        variables=final_variables,
        natural_language_input=request.natural_language_input,
        test_env_id=request.test_env_id
    )
    
    return {
        'status': 'started',
        'run_id': run_id,
        'flow_id': final_flow_id,
        'flow_name': flow['name'],
        'confidence': confidence,
        'reasoning': reasoning,
        'variables': final_variables,
        'auto_generated': resolution_result.get('auto_generated', {}),
        'message': 'Test run started successfully'
    }

@router.post("/clarify", response_model=Dict[str, Any])
async def handle_clarification(
    request: ClarificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle user response to clarification question
    Resume parsing with additional context
    """
    
    # Retrieve session from Redis
    session_key = f"clarification:{request.session_id}"
    session_data = redis_client.get(session_key)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    session = json.loads(session_data)
    
    # Combine original input with user response
    combined_input = f"{session['natural_language']}. {request.user_response}"
    
    # Re-parse with additional context
    available_flows = flow_registry.list_flows()
    intent_result = await intent_parser.parse(combined_input, available_flows)
    
    # Check if still need clarification
    if intent_result.get('clarification_needed') and intent_result.get('confidence', 0) < 0.6:
        # Update session
        session['intent_result'] = intent_result
        redis_client.setex(session_key, 3600, json.dumps(session))
        
        return {
            'status': 'clarification_needed',
            'session_id': request.session_id,
            'question': intent_result['clarification_needed'],
            'parsed_flow': intent_result.get('flow_id'),
            'extracted_variables': intent_result.get('extracted_variables', {})
        }
    
    # Clear session
    redis_client.delete(session_key)
    
    # Now start the run (similar logic to start_test_run)
    flow_id = intent_result.get('flow_id')
    if not flow_id:
        # Use flow selector
        selection_result = await flow_selector.select_flow(combined_input, available_flows)
        flow_id = selection_result['flow_id']
    
    flow = flow_registry.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
    
    # Merge variables
    variables = {**session.get('variables', {}), **intent_result.get('extracted_variables', {})}
    
    # Variable resolution
    resolution_result = variable_resolver.resolve(
        flow=flow,
        form_overrides=variables,
        llm_extracted={}
    )
    
    if resolution_result['missing_required']:
        return {
            'status': 'missing_variables',
            'flow_id': flow_id,
            'missing_required': resolution_result['missing_required'],
            'message': f"Still missing: {', '.join(resolution_result['missing_required'])}"
        }
    
    variables = resolution_result['resolved']
    
    # Create and start run
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    
    test_run = TestRun(
        run_id=run_id,
        flow_id=flow_id,
        flow_name=flow['name'],
        status="pending",
        variables_used=variables,
        natural_language_input=combined_input,
        test_env_id=session.get('test_env_id'),
        started_at=datetime.utcnow()
    )
    
    db.add(test_run)
    db.commit()
    
    execute_test_run.delay(
        run_id=run_id,
        flow_id=flow_id,
        variables=variables,
        natural_language_input=combined_input,
        test_env_id=session.get('test_env_id')
    )
    
    return {
        'status': 'started',
        'run_id': run_id,
        'flow_id': flow_id,
        'flow_name': flow['name'],
        'variables': variables,
        'message': 'Test run started successfully after clarification'
    }

@router.get("/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str, db: Session = Depends(get_db)):
    """
    Get current status of a test run
    """
    test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
    
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    # Get progress from context store or step logs
    from core.context_store import ContextStore
    context = ContextStore(run_id)
    progress_data = context.get("progress", {})
    
    return RunStatusResponse(
        run_id=test_run.run_id,
        flow_id=test_run.flow_id,
        flow_name=test_run.flow_name,
        status=test_run.status,
        started_at=test_run.started_at,
        finished_at=test_run.finished_at,
        variables_used=test_run.variables_used,
        error_summary=test_run.error_summary,
        progress=progress_data
    )

@router.post("/{run_id}/cancel")
async def cancel_test_run(run_id: str, db: Session = Depends(get_db)):
    """
    Cancel a running test
    """
    test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
    
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    if test_run.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel test run with status '{test_run.status}'"
        )
    
    # Update status to cancelled
    test_run.status = "cancelled"
    test_run.finished_at = datetime.utcnow()
    test_run.error_summary = "Test run cancelled by user"
    db.commit()
    
    # Set cancellation flag in context store
    from core.context_store import ContextStore
    context = ContextStore(run_id)
    context.set("cancelled", True)
    
    return {
        "run_id": run_id,
        "status": "cancelled",
        "message": "Test run cancelled successfully"
    }

@router.get("/{run_id}/logs")
async def get_run_logs(run_id: str, db: Session = Depends(get_db)):
    """
    Get step logs for a test run (for SSE streaming, this will be implemented separately)
    """
    from models import StepLog
    
    test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    
    logs = db.query(StepLog).filter(StepLog.run_id == run_id).order_by(StepLog.step_number).all()
    
    return [
        {
            "step_number": log.step_number,
            "description": log.step_description,
            "action": log.action,
            "target": log.target,
            "value": log.value,
            "status": log.status,
            "timestamp": log.timestamp.isoformat(),
            "duration_ms": log.duration_ms,
            "error_message": log.error_message,
            "screenshot_b64": log.screenshot_b64,
            "details": log.details
        }
        for log in logs
    ]