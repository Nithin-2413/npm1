from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
import logging
from pathlib import Path
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
from models import init_db
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Create the main app
app = FastAPI(
    title="QA Automation API",
    description="AI-powered QA test automation platform with self-healing and network monitoring",
    version="2.0.0"
)

# Add middleware
from middleware import RequestIDMiddleware, LoggingMiddleware, limiter

app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import routers
from routers import runs, flows, secrets, network_rca, batch, scheduling, reporting, health

# Include routers
api_router.include_router(health.router)
api_router.include_router(runs.router)
api_router.include_router(flows.router)
api_router.include_router(secrets.router)
api_router.include_router(network_rca.router)
api_router.include_router(batch.router)
api_router.include_router(scheduling.router)
api_router.include_router(reporting.router)

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "qa-automation-api",
        "version": "2.0.0"
    }

# SSE endpoint for real-time logs
@api_router.get("/runs/{run_id}/stream")
async def stream_run_logs(run_id: str):
    """Server-Sent Events (SSE) endpoint for real-time test run logs"""
    async def event_generator():
        # Send initial connection message
        yield f"data: {json.dumps({'event': 'connected', 'run_id': run_id})}\n\n"
        
        # For now, just send a placeholder - real implementation would use Redis pubsub
        for i in range(10):
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'event': 'heartbeat', 'run_id': run_id, 'count': i})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Include the API router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("API startup - QA Automation v2.0.0")
    
    # Load flow templates
    try:
        from core.flow_registry import flow_registry
        flow_registry.load_all_flows()
        logger.info(f"Loaded {len(flow_registry.flows)} flow templates")
    except Exception as e:
        logger.warning(f"Failed to load flow templates: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("API shutdown - Graceful shutdown initiated")
