import redis
import json
import os
from typing import Any, Dict, Optional
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class ContextStore:
    """Per-run context store backed by Redis"""
    
    def __init__(self, run_id: str, redis_url: Optional[str] = None):
        self.run_id = run_id
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = f"context:{run_id}"
        self.ttl = timedelta(hours=24)
    
    def set(self, key: str, value: Any) -> None:
        """Set a context value"""
        full_key = f"{self.key_prefix}:{key}"
        serialized = json.dumps(value)
        self.redis_client.set(full_key, serialized, ex=self.ttl)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value"""
        full_key = f"{self.key_prefix}:{key}"
        value = self.redis_client.get(full_key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all context values for this run"""
        pattern = f"{self.key_prefix}:*"
        keys = self.redis_client.keys(pattern)
        context = {}
        for key in keys:
            short_key = key.split(":", 2)[-1]
            value = self.redis_client.get(key)
            if value:
                try:
                    context[short_key] = json.loads(value)
                except json.JSONDecodeError:
                    context[short_key] = value
        return context
    
    def delete(self, key: str) -> None:
        """Delete a context value"""
        full_key = f"{self.key_prefix}:{key}"
        self.redis_client.delete(full_key)
    
    def clear(self) -> None:
        """Clear all context for this run"""
        pattern = f"{self.key_prefix}:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
    
    def extend_ttl(self) -> None:
        """Extend TTL for all keys in this context"""
        pattern = f"{self.key_prefix}:*"
        keys = self.redis_client.keys(pattern)
        for key in keys:
            self.redis_client.expire(key, self.ttl)