import json
import uuid
import redis
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class NetworkMonitor:
    """
    Network and Console monitoring using Playwright's CDP
    Captures network events, console logs, and detects anomalies
    """
    
    def __init__(self, run_id: str, step_number: int = 0):
        self.run_id = run_id
        self.current_step = step_number
        
        # Redis for storage
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        
        self.network_key = f"run:{run_id}:network"
        self.console_key = f"run:{run_id}:console"
        
        # Event counters
        self.event_count = 0
        self.anomaly_count = 0
        
        # Filters for static assets
        self.static_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico',
            '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
            '.mp4', '.mp3', '.wav', '.pdf'
        }
        
        logger.info(f"Network monitor initialized for run {run_id}")
    
    def set_step(self, step_number: int) -> None:
        """Update current step number"""
        self.current_step = step_number
    
    def should_capture(self, url: str) -> bool:
        """
        Determine if this request should be captured
        Filter out static assets, only capture XHR/Fetch/API calls
        """
        # Skip data URLs
        if url.startswith('data:'):
            return False
        
        # Skip chrome-extension URLs
        if url.startswith('chrome-extension://'):
            return False
        
        # Check if it's a static asset by extension
        for ext in self.static_extensions:
            if ext in url.lower():
                return False
        
        # Capture if it looks like an API call
        api_indicators = ['/api/', '/v1/', '/v2/', '/graphql', '/rest/', '/services/']
        for indicator in api_indicators:
            if indicator in url:
                return True
        
        # Capture XHR/Fetch (will be determined by request type in handler)
        return True
    
    def capture_request(self, request_data: Dict[str, Any]) -> None:
        """Capture network request"""
        url = request_data.get('url', '')
        
        if not self.should_capture(url):
            return
        
        event = {
            'event_id': str(uuid.uuid4()),
            'run_id': self.run_id,
            'step_number': self.current_step,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'request',
            'method': request_data.get('method', 'GET'),
            'url': url,
            'request_headers': request_data.get('headers', {}),
            'request_body': request_data.get('postData'),
            'resource_type': request_data.get('resourceType'),
        }
        
        self._store_network_event(event)
        self.event_count += 1
        logger.debug(f"Captured request: {event['method']} {url}")
    
    def capture_response(self, response_data: Dict[str, Any]) -> None:
        """Capture network response"""
        url = response_data.get('url', '')
        
        if not self.should_capture(url):
            return
        
        status_code = response_data.get('status', 0)
        duration_ms = response_data.get('duration_ms', 0)
        
        # Detect anomalies
        is_anomaly = False
        anomaly_reason = None
        
        if status_code >= 400:
            is_anomaly = True
            anomaly_reason = f"HTTP {status_code} error"
            self.anomaly_count += 1
        elif duration_ms > 5000:
            is_anomaly = True
            anomaly_reason = f"Slow response ({duration_ms}ms)"
            self.anomaly_count += 1
        
        event = {
            'event_id': str(uuid.uuid4()),
            'run_id': self.run_id,
            'step_number': self.current_step,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'response',
            'method': response_data.get('method', 'GET'),
            'url': url,
            'status_code': status_code,
            'response_headers': response_data.get('headers', {}),
            'response_body': response_data.get('body'),
            'duration_ms': duration_ms,
            'is_anomaly': is_anomaly,
            'anomaly_reason': anomaly_reason
        }
        
        self._store_network_event(event)
        
        if is_anomaly:
            logger.warning(f"Network anomaly detected: {anomaly_reason} - {url}")
    
    def capture_failure(self, failure_data: Dict[str, Any]) -> None:
        """Capture network failure"""
        url = failure_data.get('url', '')
        
        if not self.should_capture(url):
            return
        
        event = {
            'event_id': str(uuid.uuid4()),
            'run_id': self.run_id,
            'step_number': self.current_step,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'failure',
            'method': failure_data.get('method', 'GET'),
            'url': url,
            'error_text': failure_data.get('errorText', 'Unknown error'),
            'is_anomaly': True,
            'anomaly_reason': f"Network failure: {failure_data.get('errorText')}"
        }
        
        self._store_network_event(event)
        self.anomaly_count += 1
        logger.error(f"Network failure: {event['error_text']} - {url}")
    
    def capture_console(self, console_data: Dict[str, Any]) -> None:
        """Capture console message"""
        console_type = console_data.get('type', 'log')
        text = console_data.get('text', '')
        
        # Detect if it's an error
        is_anomaly = console_type in ['error', 'warning']
        
        event = {
            'event_id': str(uuid.uuid4()),
            'run_id': self.run_id,
            'step_number': self.current_step,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'console',
            'console_type': console_type,
            'text': text,
            'location': console_data.get('location'),
            'is_anomaly': is_anomaly,
            'anomaly_reason': f"Console {console_type}" if is_anomaly else None
        }
        
        self._store_console_event(event)
        
        if is_anomaly:
            self.anomaly_count += 1
            logger.warning(f"Console {console_type}: {text}")
    
    def _store_network_event(self, event: Dict[str, Any]) -> None:
        """Store network event in Redis"""
        try:
            # Use Redis list to store events in order
            self.redis_client.rpush(self.network_key, json.dumps(event))
            # Set TTL to 7 days
            self.redis_client.expire(self.network_key, 604800)
        except Exception as e:
            logger.error(f"Failed to store network event: {e}")
    
    def _store_console_event(self, event: Dict[str, Any]) -> None:
        """Store console event in Redis"""
        try:
            self.redis_client.rpush(self.console_key, json.dumps(event))
            self.redis_client.expire(self.console_key, 604800)
        except Exception as e:
            logger.error(f"Failed to store console event: {e}")
    
    def get_all_network_events(self) -> List[Dict[str, Any]]:
        """Retrieve all network events for this run"""
        try:
            events = self.redis_client.lrange(self.network_key, 0, -1)
            return [json.loads(event) for event in events]
        except Exception as e:
            logger.error(f"Failed to retrieve network events: {e}")
            return []
    
    def get_all_console_events(self) -> List[Dict[str, Any]]:
        """Retrieve all console events for this run"""
        try:
            events = self.redis_client.lrange(self.console_key, 0, -1)
            return [json.loads(event) for event in events]
        except Exception as e:
            logger.error(f"Failed to retrieve console events: {e}")
            return []
    
    def get_anomalies(self) -> List[Dict[str, Any]]:
        """Get all anomalous events (network + console)"""
        network_events = self.get_all_network_events()
        console_events = self.get_all_console_events()
        
        all_events = network_events + console_events
        anomalies = [event for event in all_events if event.get('is_anomaly', False)]
        
        # Sort by timestamp
        anomalies.sort(key=lambda x: x.get('timestamp', ''))
        
        return anomalies
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        network_events = self.get_all_network_events()
        console_events = self.get_all_console_events()
        
        network_requests = [e for e in network_events if e['type'] == 'request']
        network_responses = [e for e in network_events if e['type'] == 'response']
        network_failures = [e for e in network_events if e['type'] == 'failure']
        
        console_errors = [e for e in console_events if e.get('console_type') == 'error']
        console_warnings = [e for e in console_events if e.get('console_type') == 'warning']
        
        return {
            'run_id': self.run_id,
            'total_network_events': len(network_events),
            'total_console_events': len(console_events),
            'network_requests': len(network_requests),
            'network_responses': len(network_responses),
            'network_failures': len(network_failures),
            'console_errors': len(console_errors),
            'console_warnings': len(console_warnings),
            'total_anomalies': self.anomaly_count,
            'anomalies': self.get_anomalies()
        }
    
    def clear(self) -> None:
        """Clear all stored events"""
        self.redis_client.delete(self.network_key)
        self.redis_client.delete(self.console_key)
        logger.info(f"Cleared network monitor data for run {self.run_id}")
