import asyncio
import base64
import json
import os
import logging
from typing import Optional, Dict, Any, Literal
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, ElementHandle
from datetime import datetime
import redis
from dotenv import load_dotenv
from core.network_monitor import NetworkMonitor

load_dotenv()

logger = logging.getLogger(__name__)

class PlaywrightEngine:
    """Core Playwright automation engine with built-in retry and screenshot capabilities"""
    
    def __init__(self, run_id: str, headless: bool = True):
        self.run_id = run_id
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Redis for pub-sub events
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        self.pubsub_channel = f"test_run:{run_id}:events"
        
        # Network monitor
        self.network_monitor = NetworkMonitor(run_id)
        
        # Request/response tracking
        self.pending_requests = {}
        
        # Retry config
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    async def initialize(self) -> None:
        """Initialize Playwright browser and context"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        # Enable network and console monitoring
        self.context.on("request", self._handle_request)
        self.context.on("response", self._handle_response)
        
        self.page = await self.context.new_page()
        self.page.on("console", self._handle_console)
        
        logger.info(f"Playwright initialized for run {self.run_id}")
        await self._emit_event("playwright_initialized", {"headless": self.headless})
    
    async def close(self) -> None:
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info(f"Playwright closed for run {self.run_id}")
    
    def _handle_request(self, request) -> None:
        """Capture network requests"""
        self.network_logs.append({
            "type": "request",
            "method": request.method,
            "url": request.url,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _handle_response(self, response) -> None:
        """Capture network responses"""
        self.network_logs.append({
            "type": "response",
            "method": response.request.method,
            "url": response.url,
            "status": response.status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _handle_console(self, msg) -> None:
        """Capture console messages"""
        self.console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event to Redis pub-sub for SSE streaming"""
        event = {
            "run_id": self.run_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.redis_client.publish(self.pubsub_channel, json.dumps(event))
    
    async def get_screenshot(self, full_page: bool = False) -> str:
        """Take screenshot and return base64 encoded string"""
        if not self.page:
            return ""
        
        try:
            screenshot_bytes = await self.page.screenshot(full_page=full_page)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ""
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry a function with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
    
    async def login(self, url: str, username: str, password: str, 
                   username_selector: str = "input[name='username']",
                   password_selector: str = "input[name='password']",
                   submit_selector: str = "button[type='submit']") -> Dict[str, Any]:
        """Login to application"""
        start_time = datetime.utcnow()
        await self._emit_event("step_start", {
            "action": "login",
            "url": url,
            "username": username
        })
        
        try:
            # Navigate
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)
            
            # Fill username
            await self.page.fill(username_selector, username)
            await asyncio.sleep(0.3)
            
            # Fill password
            await self.page.fill(password_selector, password)
            await asyncio.sleep(0.3)
            
            # Click submit
            await self.page.click(submit_selector)
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_complete", {
                "action": "login",
                "status": "success",
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return {
                "status": "success",
                "screenshot_b64": screenshot,
                "duration_ms": duration_ms
            }
        except Exception as e:
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_error", {
                "action": "login",
                "error": str(e),
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            raise
    
    async def click_button(self, label_or_selector: str, timeout: int = 30000, 
                          use_role: bool = True) -> Dict[str, Any]:
        """Click a button using semantic locator or selector"""
        start_time = datetime.utcnow()
        await self._emit_event("step_start", {
            "action": "click",
            "target": label_or_selector
        })
        
        try:
            async def _click():
                if use_role:
                    # Try semantic locator first
                    try:
                        button = self.page.get_by_role("button", name=label_or_selector)
                        await button.click(timeout=timeout)
                    except:
                        # Fallback to selector
                        await self.page.click(label_or_selector, timeout=timeout)
                else:
                    await self.page.click(label_or_selector, timeout=timeout)
                
                await asyncio.sleep(0.5)  # Wait for action to complete
            
            await self._retry_with_backoff(_click)
            
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_complete", {
                "action": "click",
                "target": label_or_selector,
                "status": "success",
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return {
                "status": "success",
                "screenshot_b64": screenshot,
                "duration_ms": duration_ms
            }
        except Exception as e:
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_error", {
                "action": "click",
                "target": label_or_selector,
                "error": str(e),
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            raise
    
    async def fill_field(self, field_label: str, value: str, 
                        timeout: int = 30000, use_label: bool = True) -> Dict[str, Any]:
        """Fill an input field using semantic locator"""
        start_time = datetime.utcnow()
        await self._emit_event("step_start", {
            "action": "fill",
            "target": field_label,
            "value": value
        })
        
        try:
            async def _fill():
                if use_label:
                    try:
                        field = self.page.get_by_label(field_label)
                        await field.fill(value, timeout=timeout)
                    except:
                        # Fallback to selector
                        await self.page.fill(field_label, value, timeout=timeout)
                else:
                    await self.page.fill(field_label, value, timeout=timeout)
                
                await asyncio.sleep(0.3)
            
            await self._retry_with_backoff(_fill)
            
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_complete", {
                "action": "fill",
                "target": field_label,
                "value": value,
                "status": "success",
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return {
                "status": "success",
                "screenshot_b64": screenshot,
                "duration_ms": duration_ms
            }
        except Exception as e:
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_error", {
                "action": "fill",
                "target": field_label,
                "error": str(e),
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            raise
    
    async def select_dropdown(self, dropdown_label: str, value: str, 
                             by: Literal['text', 'value', 'index'] = 'text',
                             timeout: int = 30000) -> Dict[str, Any]:
        """Select option from dropdown"""
        start_time = datetime.utcnow()
        await self._emit_event("step_start", {
            "action": "select",
            "target": dropdown_label,
            "value": value,
            "select_by": by
        })
        
        try:
            async def _select():
                # Try to find dropdown by label
                try:
                    dropdown = self.page.get_by_label(dropdown_label)
                except:
                    dropdown = self.page.locator(dropdown_label)
                
                if by == 'text':
                    await dropdown.select_option(label=value, timeout=timeout)
                elif by == 'value':
                    await dropdown.select_option(value=value, timeout=timeout)
                elif by == 'index':
                    await dropdown.select_option(index=int(value), timeout=timeout)
                
                await asyncio.sleep(0.5)
            
            await self._retry_with_backoff(_select)
            
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_complete", {
                "action": "select",
                "target": dropdown_label,
                "value": value,
                "status": "success",
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return {
                "status": "success",
                "screenshot_b64": screenshot,
                "duration_ms": duration_ms
            }
        except Exception as e:
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_error", {
                "action": "select",
                "target": dropdown_label,
                "error": str(e),
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            raise
    
    async def wait_for_element(self, description: str, selector: str = None, 
                               timeout: int = 30000) -> Dict[str, Any]:
        """Wait for an element to appear"""
        start_time = datetime.utcnow()
        await self._emit_event("step_start", {
            "action": "wait",
            "target": description
        })
        
        try:
            if selector:
                await self.page.wait_for_selector(selector, timeout=timeout, state='visible')
            else:
                # Wait for page to be idle
                await self.page.wait_for_load_state('networkidle', timeout=timeout)
            
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_complete", {
                "action": "wait",
                "target": description,
                "status": "success",
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return {
                "status": "success",
                "screenshot_b64": screenshot,
                "duration_ms": duration_ms
            }
        except Exception as e:
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_error", {
                "action": "wait",
                "target": description,
                "error": str(e),
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            raise
    
    async def double_click_field(self, label: str, timeout: int = 30000) -> Dict[str, Any]:
        """Double-click a field (useful for clearing and selecting text)"""
        start_time = datetime.utcnow()
        await self._emit_event("step_start", {
            "action": "double_click",
            "target": label
        })
        
        try:
            async def _double_click():
                try:
                    field = self.page.get_by_label(label)
                    await field.dblclick(timeout=timeout)
                except:
                    await self.page.dblclick(label, timeout=timeout)
                
                await asyncio.sleep(0.3)
            
            await self._retry_with_backoff(_double_click)
            
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_complete", {
                "action": "double_click",
                "target": label,
                "status": "success",
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return {
                "status": "success",
                "screenshot_b64": screenshot,
                "duration_ms": duration_ms
            }
        except Exception as e:
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_error", {
                "action": "double_click",
                "target": label,
                "error": str(e),
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            raise
    
    async def extract_text(self, element_description: str, selector: str = None) -> str:
        """Extract text from an element"""
        start_time = datetime.utcnow()
        await self._emit_event("step_start", {
            "action": "extract_text",
            "target": element_description
        })
        
        try:
            if selector:
                element = await self.page.wait_for_selector(selector, timeout=10000)
                text = await element.text_content()
            else:
                # Try to find by text content
                text = await self.page.text_content(f":text('{element_description}')")
            
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_complete", {
                "action": "extract_text",
                "target": element_description,
                "extracted_value": text,
                "status": "success",
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return text or ""
        except Exception as e:
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_error", {
                "action": "extract_text",
                "target": element_description,
                "error": str(e),
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return ""
    
    async def navigate(self, url: str, wait_until: str = 'networkidle') -> Dict[str, Any]:
        """Navigate to a URL"""
        start_time = datetime.utcnow()
        await self._emit_event("step_start", {
            "action": "navigate",
            "url": url
        })
        
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=30000)
            await asyncio.sleep(1)
            
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_complete", {
                "action": "navigate",
                "url": url,
                "status": "success",
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            return {
                "status": "success",
                "screenshot_b64": screenshot,
                "duration_ms": duration_ms
            }
        except Exception as e:
            screenshot = await self.get_screenshot()
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self._emit_event("step_error", {
                "action": "navigate",
                "url": url,
                "error": str(e),
                "duration_ms": duration_ms,
                "screenshot_b64": screenshot
            })
            
            raise
    
    def get_network_logs(self) -> list:
        """Get all network logs"""
        return self.network_logs
    
    def get_console_logs(self) -> list:
        """Get all console logs"""
        return self.console_logs
