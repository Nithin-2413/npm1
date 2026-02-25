from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

from models import get_db, TestRun, StepLog, RCAReport
from core.flow_registry import flow_registry

router = APIRouter(prefix="/reports", tags=["Reporting"])

@router.get("/runs")
async def get_run_history(
    limit: int = 50,
    offset: int = 0,
    flow_id: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated run history with filters
    
    Filters:
    - flow_id: Filter by specific flow
    - status: pending|running|passed|failed|cancelled
    - from_date: ISO date string (e.g., 2025-01-01)
    - to_date: ISO date string
    """
    
    query = db.query(TestRun)
    
    # Apply filters
    if flow_id:
        query = query.filter(TestRun.flow_id == flow_id)
    
    if status:
        query = query.filter(TestRun.status == status)
    
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date)
            query = query.filter(TestRun.started_at >= from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format: YYYY-MM-DD")
    
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date)
            query = query.filter(TestRun.started_at <= to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format: YYYY-MM-DD")
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    runs = query.order_by(desc(TestRun.started_at)).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "runs": [
            {
                "run_id": run.run_id,
                "flow_id": run.flow_id,
                "flow_name": run.flow_name,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "duration_seconds": (
                    (run.finished_at - run.started_at).total_seconds()
                    if run.finished_at and run.started_at else None
                ),
                "error_summary": run.error_summary,
                "test_env_id": run.test_env_id
            }
            for run in runs
        ]
    }

@router.get("/summary")
async def get_summary_stats(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics
    
    Includes:
    - Success rates per flow
    - Average duration per flow
    - Flaky test detection
    - Total runs, passed, failed
    """
    
    # Calculate date range
    from_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all runs in range
    runs = db.query(TestRun).filter(TestRun.started_at >= from_date).all()
    
    total_runs = len(runs)
    passed_runs = len([r for r in runs if r.status == 'passed'])
    failed_runs = len([r for r in runs if r.status == 'failed'])
    cancelled_runs = len([r for r in runs if r.status == 'cancelled'])
    
    overall_pass_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0
    
    # Per-flow statistics
    flow_stats = {}
    for run in runs:
        if not run.flow_id:
            continue
        
        if run.flow_id not in flow_stats:
            flow_stats[run.flow_id] = {
                'flow_id': run.flow_id,
                'flow_name': run.flow_name,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'durations': []
            }
        
        flow_stats[run.flow_id]['total'] += 1
        
        if run.status == 'passed':
            flow_stats[run.flow_id]['passed'] += 1
        elif run.status == 'failed':
            flow_stats[run.flow_id]['failed'] += 1
        
        if run.started_at and run.finished_at:
            duration = (run.finished_at - run.started_at).total_seconds()
            flow_stats[run.flow_id]['durations'].append(duration)
    
    # Calculate pass rates and detect flaky tests
    flaky_flows = []
    flow_summaries = []
    
    for flow_id, stats in flow_stats.items():
        total = stats['total']
        passed = stats['passed']
        failed = stats['failed']
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        avg_duration = (
            sum(stats['durations']) / len(stats['durations'])
            if stats['durations'] else 0
        )
        
        # Flaky detection: pass rate between 20% and 80% with at least 5 runs
        is_flaky = (20 <= pass_rate <= 80) and total >= 5
        
        flow_summary = {
            'flow_id': flow_id,
            'flow_name': stats['flow_name'],
            'total_runs': total,
            'passed': passed,
            'failed': failed,
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
        "to_date": datetime.utcnow().isoformat(),
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
async def export_run(run_id: str, db: Session = Depends(get_db)):
    """
    Export full run report as JSON
    
    Includes:
    - Run metadata
    - All step logs with screenshots
    - Network events
    - Console logs
    - RCA report (if available)
    """
    
    # Get run
    test_run = db.query(TestRun).filter(TestRun.run_id == run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    # Get step logs
    step_logs = db.query(StepLog).filter(StepLog.run_id == run_id).order_by(StepLog.step_number).all()
    
    # Get RCA report
    rca_report = db.query(RCAReport).filter(RCAReport.run_id == run_id).first()
    
    # Get network data
    from core.network_monitor import NetworkMonitor
    monitor = NetworkMonitor(run_id)
    network_summary = monitor.get_summary()
    
    report = {
        "run": {
            "run_id": test_run.run_id,
            "flow_id": test_run.flow_id,
            "flow_name": test_run.flow_name,
            "status": test_run.status,
            "started_at": test_run.started_at.isoformat() if test_run.started_at else None,
            "finished_at": test_run.finished_at.isoformat() if test_run.finished_at else None,
            "duration_seconds": (
                (test_run.finished_at - test_run.started_at).total_seconds()
                if test_run.finished_at and test_run.started_at else None
            ),
            "variables_used": test_run.variables_used,
            "error_summary": test_run.error_summary,
            "test_env_id": test_run.test_env_id
        },
        "steps": [
            {
                "step_number": log.step_number,
                "description": log.step_description,
                "action": log.action,
                "target": log.target,
                "value": log.value,
                "status": log.status,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "duration_ms": log.duration_ms,
                "error_message": log.error_message,
                "screenshot_b64": log.screenshot_b64,
                "retry_count": log.retry_count,
                "details": log.details
            }
            for log in step_logs
        ],
        "network": {
            "summary": {
                "total_events": network_summary['total_network_events'],
                "total_anomalies": network_summary['total_anomalies'],
                "console_errors": network_summary['console_errors']
            },
            "anomalies": network_summary['anomalies']
        },
        "rca": {
            "root_cause": rca_report.root_cause if rca_report else None,
            "ai_explanation": rca_report.ai_explanation if rca_report else None,
            "suggested_fix": rca_report.suggested_fix if rca_report else None,
            "confidence_score": rca_report.confidence_score if rca_report else None
        } if rca_report else None,
        "export_timestamp": datetime.utcnow().isoformat()
    }
    
    # Return as downloadable JSON
    return JSONResponse(
        content=report,
        headers={
            "Content-Disposition": f"attachment; filename=run_{run_id}_report.json"
        }
    )

@router.get("/flows/{flow_id}/stats")
async def get_flow_stats(
    flow_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific flow"""
    
    # Validate flow exists
    flow = flow_registry.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    from_date = datetime.utcnow() - timedelta(days=days)
    
    runs = db.query(TestRun).filter(
        TestRun.flow_id == flow_id,
        TestRun.started_at >= from_date
    ).order_by(TestRun.started_at).all()
    
    if not runs:
        return {
            "flow_id": flow_id,
            "flow_name": flow['name'],
            "period_days": days,
            "total_runs": 0,
            "message": "No runs found in this period"
        }
    
    total = len(runs)
    passed = len([r for r in runs if r.status == 'passed'])
    failed = len([r for r in runs if r.status == 'failed'])
    
    durations = [
        (r.finished_at - r.started_at).total_seconds()
        for r in runs
        if r.started_at and r.finished_at
    ]
    
    # Trend data (last 10 runs)
    recent_runs = runs[-10:]
    trend = [
        {
            "run_id": r.run_id,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "duration_seconds": (
                (r.finished_at - r.started_at).total_seconds()
                if r.finished_at and r.started_at else None
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
