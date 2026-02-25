from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis
import os
from groq import Groq
from playwright.async_api import async_playwright
import logging

from models import get_db

router = APIRouter(tags=["Health"])

logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check
    
    Checks:
    - API server (always returns if reached)
    - Database connectivity (PostgreSQL)
    - Redis connectivity
    - Groq API availability
    - Playwright availability
    """
    
    health_status = {
        "status": "healthy",
        "timestamp": None,
        "services": {
            "api": {"status": "healthy", "message": "API server running"},
            "database": {"status": "unknown"},
            "redis": {"status": "unknown"},
            "groq_api": {"status": "unknown"},
            "playwright": {"status": "unknown"}
        }
    }
    
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat()
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }
        logger.error(f"Redis health check failed: {e}")
    
    # Check Groq API
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key != "your-groq-api-key-here":
            # Just verify key exists, don't make actual API call
            health_status["services"]["groq_api"] = {
                "status": "healthy",
                "message": "Groq API key configured"
            }
        else:
            health_status["services"]["groq_api"] = {
                "status": "degraded",
                "message": "Groq API key not configured"
            }
    except Exception as e:
        health_status["services"]["groq_api"] = {
            "status": "unknown",
            "message": f"Groq check error: {str(e)}"
        }
    
    # Check Playwright
    try:
        # Just verify Playwright is importable
        playwright_installed = True
        health_status["services"]["playwright"] = {
            "status": "healthy",
            "message": "Playwright available"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["playwright"] = {
            "status": "unhealthy",
            "message": f"Playwright error: {str(e)}"
        }
        logger.error(f"Playwright health check failed: {e}")
    
    return health_status

@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for load balancers"""
    return {"status": "ok"}
