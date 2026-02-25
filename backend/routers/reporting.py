from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta, timezone
import logging

from models import (
    test_runs_collection, step_logs_collection, rca_reports_collection,
    serialize_doc
)
from core.flow_registry import flow_registry

router = APIRouter(prefix="/reports", tags=["Reporting"])
logger = logging.getLogger(__name__)

@router.get("/runs")
async def get_run_history(
    limit: int = 50,
    offset: int = 0,
    flow_id: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """
    Get paginated run history with filters
    
    Filters:
    - flow_id: Filter by specific flow
    - status: pending|running|passed|failed|cancelled
    - from_date: ISO date string (e.g., 2025-01-01)
    - to_date: ISO date string
    """
    
    query = {}
    
    # Apply filters
    if flow_id:
        query["flow_id"] = flow_id
    
    if status:
        query["status"] = status
    
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            query["started_at"] = {"$gte": from_dt}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format: YYYY-MM-DD")
    
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            if "started_at" in query:
                query["started_at"]["$lte"] = to_dt
            else:
                query["started_at"] = {"$lte": to_dt}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format: YYYY-MM-DD")
    
    # Get total count
    total = test_runs_collection.count_documents(query)
    
    # Apply pagination
    runs = list(
        test_runs_collection.find(query)
        .sort("started_at", -1)
        .skip(offset)
        .limit(limit)
    )
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "runs": [
            {
                "run_id": run.get("run_id"),
                "flow_id": run.get("flow_id"),
                "flow_name": run.get("flow_name"),
                "status": run.get("status"),
                "started_at": run.get("started_at").isoformat() if run.get("started_at") else None,
                "finished_at": run.get("finished_at").isoformat() if run.get("finished_at") else None,
                "duration_seconds": (
                    (run.get("finished_at") - run.get("started_at")).total_seconds()
                    if run.get("finished_at") and run.get("started_at") else None
                ),
                "error_summary": run.get("error_summary"),
                "test_env_id": run.get("test_env_id")
            }
            for run in runs
        ]
    }

@router.get("/summary")
async def get_summary_stats(days: int = 7):
    """
    Get summary statistics
    
    Includes:
    - Success rates per flow
    - Average duration per flow
    - Flaky test detection
    - Total runs, passed, failed
    """
    
    # Calculate date range
    from_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get all runs in range
    runs = list(test_runs_collection.find({"started_at": {"$gte": from_date}}))
    
    total_runs = len(runs)
    passed_runs = len([r for r in runs if r.get('status') == 'passed'])
    failed_runs = len([r for r in runs if r.get('status') == 'failed'])
    cancelled_runs = len([r for r in runs if r.get('status') == 'cancelled'])
    
    overall_pass_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0
    
    # Per-flow statistics
    flow_stats = {}
    for run in runs:
        fid = run.get('flow_id')
        if not fid:
            continue
        
        if fid not in flow_stats:
            flow_stats[fid] = {
                'flow_id': fid,
                'flow_name': run.get('flow_name'),
                'total': 0,
                'passed': 0,
                'failed': 0,
                'durations': []
            }
        
        flow_stats[fid]['total'] += 1
        
        if run.get('status') == 'passed':
            flow_stats[fid]['passed'] += 1
        elif run.get('status') == 'failed':
            flow_stats[fid]['failed'] += 1
        
        started = run.get('started_at')
        finished = run.get('finished_at')
        if started and finished:
            duration = (finished - started).total_seconds()
            flow_stats[fid]['durations'].append(duration)
    
    # Calculate pass rates and detect flaky tests
    flaky_flows = []
    flow_summaries = []
    
    for fid, stats in flow_stats.items():
        total = stats['total']
        passed = stats['passed']
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        avg_duration = (
            sum(stats['durations']) / len(stats['durations'])
            if stats['durations'] else 0
        )
        
        # Flaky detection: pass rate between 20% and 80% with at least 5 runs
        is_flaky = (20 <= pass_rate <= 80) and total >= 5
        
        flow_summary = {
            'flow_id': fid,
            'flow_name': stats['flow_name'],
            'total_runs': total,
            'passed': passed,
            'failed': stats['failed'],
            'pass_rate': round(pass_rate, 2),
            'average_duration_seconds': round(avg_duration, 2),
            'is_flaky': is_flaky
        }
        
        flow_summaries.append(flow_summary)
        
        if is_flaky:
            flaky_flows.append(flow_summary)
    
    # Sort by total runs
    flow_summaries.sort(key=lambda x: x['total_runs'], reverse=True)
    
    return {
        "period_days": days,
        "from_date": from_date.isoformat(),
        "to_date": datetime.now(timezone.utc).isoformat(),
        "overall": {
            "total_runs": total_runs,
            "passed": passed_runs,
            "failed": failed_runs,
            "cancelled": cancelled_runs,
            "pass_rate": round(overall_pass_rate, 2)
        },
        "flows": flow_summaries,
        "flaky_flows": flaky_flows
    }

@router.get("/runs/{run_id}/export")
async def export_run(run_id: str):
    """
    Export full run report as JSON
    """
    
    # Get run
    test_run = test_runs_collection.find_one({"run_id": run_id})
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    # Get step logs
    step_logs = list(step_logs_collection.find({"run_id": run_id}).sort("step_number", 1))
    
    # Get RCA report
    rca_report = rca_reports_collection.find_one({"run_id": run_id})
    
    started = test_run.get('started_at')
    finished = test_run.get('finished_at')
    
    report = {
        "run": {
            "run_id": test_run.get('run_id'),
            "flow_id": test_run.get('flow_id'),
            "flow_name": test_run.get('flow_name'),
            "status": test_run.get('status'),
            "started_at": started.isoformat() if started else None,
            "finished_at": finished.isoformat() if finished else None,
            "duration_seconds": (finished - started).total_seconds() if started and finished else None,
            "variables_used": test_run.get('variables_used'),
            "error_summary": test_run.get('error_summary'),
            "test_env_id": test_run.get('test_env_id')
        },
        "steps": [
            {
                "step_number": log.get("step_number"),
                "description": log.get("step_description"),
                "action": log.get("action"),
                "target": log.get("target"),
                "value": log.get("value"),
                "status": log.get("status"),
                "timestamp": log.get("timestamp").isoformat() if log.get("timestamp") else None,
                "duration_ms": log.get("duration_ms"),
                "error_message": log.get("error_message"),
                "screenshot_b64": log.get("screenshot_b64"),
                "retry_count": log.get("retry_count"),
                "details": log.get("details")
            }
            for log in step_logs
        ],
        "rca": {
            "root_cause": rca_report.get('root_cause') if rca_report else None,
            "ai_explanation": rca_report.get('ai_explanation') if rca_report else None,
            "suggested_fix": rca_report.get('suggested_fix') if rca_report else None,
            "confidence_score": rca_report.get('confidence_score') if rca_report else None
        } if rca_report else None,
        "export_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Return as downloadable JSON
    return JSONResponse(
        content=report,
        headers={
            "Content-Disposition": f"attachment; filename=run_{run_id}_report.json"
        }
    )

@router.get("/flows/{flow_id}/stats")
async def get_flow_stats(flow_id: str, days: int = 30):
    """Get detailed statistics for a specific flow"""
    
    # Validate flow exists
    flow = flow_registry.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    from_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    runs = list(test_runs_collection.find({
        "flow_id": flow_id,
        "started_at": {"$gte": from_date}
    }).sort("started_at", 1))
    
    if not runs:
        return {
            "flow_id": flow_id,
            "flow_name": flow['name'],
            "period_days": days,
            "total_runs": 0,
            "message": "No runs found in this period"
        }
    
    total = len(runs)
    passed = len([r for r in runs if r.get('status') == 'passed'])
    failed = len([r for r in runs if r.get('status') == 'failed'])
    
    durations = [
        (r.get('finished_at') - r.get('started_at')).total_seconds()
        for r in runs
        if r.get('started_at') and r.get('finished_at')
    ]
    
    # Trend data (last 10 runs)
    recent_runs = runs[-10:]
    trend = [
        {
            "run_id": r.get('run_id'),
            "status": r.get('status'),
            "started_at": r.get('started_at').isoformat() if r.get('started_at') else None,
            "duration_seconds": (
                (r.get('finished_at') - r.get('started_at')).total_seconds()
                if r.get('finished_at') and r.get('started_at') else None
            )
        }
        for r in recent_runs
    ]
    
    return {
        "flow_id": flow_id,
        "flow_name": flow['name'],
        "period_days": days,
        "total_runs": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round((passed / total * 100), 2),
        "average_duration_seconds": round(sum(durations) / len(durations), 2) if durations else 0,
        "min_duration_seconds": round(min(durations), 2) if durations else 0,
        "max_duration_seconds": round(max(durations), 2) if durations else 0,
        "recent_runs": trend
    }
