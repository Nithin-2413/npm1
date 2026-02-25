from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to every request"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)")
        
        response.headers["X-Duration-Ms"] = str(duration_ms)
        
        return response

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
