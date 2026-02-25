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
import redis
import asyncio
import structlog

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Initialize database
from models import init_db
try:
    init_db()
    logger.info("database_initialized")
except Exception as e:
    logger.error("database_initialization_failed", error=str(e))

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
api_router.include_router(health.router)  # Health at top level
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
        "version": "1.0.0"
    }

# SSE endpoint for real-time logs
@api_router.get("/runs/{run_id}/stream")
async def stream_run_logs(run_id: str):
    """
    Server-Sent Events (SSE) endpoint for real-time test run logs
    """
    async def event_generator():
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        
        channel = f"test_run:{run_id}:events"
        pubsub.subscribe(channel)
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'event': 'connected', 'run_id': run_id})}\n\n"
            
            # Listen for events
            for message in pubsub.listen():
                if message['type'] == 'message':
                    data = message['data']
                    yield f"data: {data}\n\n"
                    
                    # Check if run is complete
                    try:
                        event_data = json.loads(data)
                        if event_data.get('event_type') in ['run_complete', 'run_failed', 'run_cancelled']:
                            break
                    except json.JSONDecodeError:
                        pass
                
                await asyncio.sleep(0.1)
        
        finally:
            pubsub.unsubscribe(channel)
            redis_client.close()
    
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
    logger.info("api_startup", version="2.0.0")
    
    # Load flow templates
    from core.flow_registry import flow_registry
    flow_registry.load_all_flows()
    logger.info("flows_loaded", count=len(flow_registry.flows))
    
    # Embed flows into ChromaDB for semantic search
    try:
        from core.llm.flow_selector import flow_selector
        flows_list = flow_registry.list_flows()
        flow_selector.embed_flows(flows_list)
        logger.info("flows_embedded", count=len(flows_list))
    except Exception as e:
        logger.warning("flow_embedding_failed", error=str(e))

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("api_shutdown", message="Graceful shutdown initiated")
