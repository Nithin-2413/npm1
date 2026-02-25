from fastapi import APIRouter
import os
import logging
from datetime import datetime, timezone

from models import db

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """
    Comprehensive health check
    
    Checks:
    - API server
    - MongoDB connectivity
    - Playwright availability
    """
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": {"status": "healthy", "message": "API server running"},
            "database": {"status": "unknown"},
            "playwright": {"status": "unknown"}
        }
    }
    
    # Check MongoDB
    try:
        # Simple ping to verify connection
        db.command('ping')
        health_status["services"]["database"] = {
            "status": "healthy",
            "message": "MongoDB connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "message": f"MongoDB error: {str(e)}"
        }
        logger.error(f"Database health check failed: {e}")
    
    # Check Playwright
    try:
        from playwright.sync_api import sync_playwright
        health_status["services"]["playwright"] = {
            "status": "healthy",
            "message": "Playwright available"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["playwright"] = {
            "status": "degraded",
            "message": f"Playwright import warning: {str(e)}"
        }
    
    return health_status

@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for load balancers"""
    return {"status": "ok"}
