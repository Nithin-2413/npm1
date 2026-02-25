import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SelfHealer:
    """
    Self-healing mechanism for test failures
    Attempts to fix common issues before marking step as failed
    """
    
    MAX_ATTEMPTS = 2  # Max self-heal attempts per step
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and api_key != "your-groq-api-key-here":
            self.client = Groq(api_key=api_key)
            self.llm_available = True
        else:
            self.client = None
            self.llm_available = False
            logger.warning("GROQ_API_KEY not configured. Self-healing will use basic strategies only.")
        
        self.model = "llama-3.3-70b-versatile"
    
    async def attempt_heal(
        self,
        playwright_page,
        step: Dict[str, Any],
        error: Exception,
        attempt_number: int,
        screenshot_b64: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Attempt to self-heal a failed step
        
        Returns:
        (success: bool, method_used: str, result: dict | None)
        """
        
        if attempt_number > self.MAX_ATTEMPTS:
            logger.info(f"Max self-heal attempts ({self.MAX_ATTEMPTS}) reached")
            return False, "max_attempts_exceeded", None
        
        error_type = type(error).__name__
        error_message = str(error)
        
        logger.info(f"Self-heal attempt {attempt_number} for: {error_type} - {error_message}")
        
        # Strategy 1: Element not found → Try alternative selectors
        if "not found" in error_message.lower() or "timeout" in error_message.lower():
            success, result = await self._heal_element_not_found(
                playwright_page, step, error_message, screenshot_b64
            )
            if success:
                return True, "alternative_selector", result
        
        # Strategy 2: Timeout → Extend wait and retry
        if "timeout" in error_message.lower():
            success, result = await self._heal_timeout(
                playwright_page, step
            )
            if success:
                return True, "extended_wait", result
        
        # Strategy 3: Dropdown selection failed → JavaScript fallback
        if step.get('action') == 'select_dropdown':
            success, result = await self._heal_dropdown_selection(
                playwright_page, step
            )
            if success:
                return True, "javascript_selection", result
        
        # Strategy 4: Click failed → Force click or JavaScript click
        if step.get('action') in ['click_button', 'click']:
            success, result = await self._heal_click_failure(
                playwright_page, step
            )
            if success:
                return True, "force_click", result
        
        logger.warning(f"No self-healing strategy succeeded for: {error_type}")
        return False, "no_strategy_worked", None
    
    async def _heal_element_not_found(
        self,
        page,
        step: Dict[str, Any],
        error_message: str,
        screenshot_b64: Optional[str]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Try alternative selectors for element not found"""
        
        locator_strategies = step.get('locator_strategies', [])
        
        # Try remaining locator strategies in order of priority
        for strategy in locator_strategies[1:]:  # Skip first (already failed)
            try:
                selector_type = strategy.get('type')
                value = strategy.get('value') or strategy.get('name')
                
                logger.info(f"Trying alternative selector: {selector_type}={value}")
                
                # Attempt to find element
                if selector_type == 'selector':
                    element = page.locator(value)
                elif selector_type == 'text':
                    element = page.get_by_text(value)
                elif selector_type == 'role':
                    element = page.get_by_role("button", name=value)
                elif selector_type == 'label':
                    element = page.get_by_label(value)
                else:
                    continue
                
                # Check if element exists
                await element.wait_for(state='visible', timeout=5000)
                
                logger.info(f"Alternative selector worked: {selector_type}={value}")
                return True, {
                    'selector_type': selector_type,
                    'selector_value': value,
                    'element_found': True
                }
            
            except Exception as e:
                logger.debug(f"Alternative selector failed: {e}")
                continue
        
        # If LLM available, ask for intelligent suggestion
        if self.llm_available and screenshot_b64:
            return await self._llm_suggest_selector(step, error_message, screenshot_b64)
        
        return False, None
    
    async def _llm_suggest_selector(
        self,
        step: Dict[str, Any],
        error_message: str,
        screenshot_b64: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Ask LLM to suggest alternative selector based on screenshot"""
        
        try:
            system_prompt = """You are an expert at web element selection.
            
Given a failed step and screenshot, suggest an alternative Playwright selector.

Return JSON format:
{
  "suggested_selector": "button.submit-btn",
  "selector_type": "css" | "xpath" | "text" | "role",
  "confidence": 0.0-1.0,
  "reasoning": "Explanation"
}"""
            
            user_prompt = f"""Step failed: {step.get('step_description')}
Action: {step.get('action')}
Target: {step.get('target')}
Error: {error_message}

Suggest an alternative selector that might work. Return JSON only."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=256,
                response_format={"type": "json_object"}
            )
            
            suggestion = json.loads(response.choices[0].message.content)
            
            if suggestion.get('confidence', 0) > 0.6:
                logger.info(f"LLM suggested selector: {suggestion.get('suggested_selector')}")
                return True, suggestion
        
        except Exception as e:
            logger.error(f"LLM selector suggestion failed: {e}")
        
        return False, None
    
    async def _heal_timeout(
        self,
        page,
        step: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Extend wait time and retry"""
        
        try:
            logger.info("Extending wait time and retrying...")
            
            # Wait for page to be fully loaded
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Additional wait
            await asyncio.sleep(2)
            
            return True, {'wait_extended': True, 'additional_wait_ms': 2000}
        
        except Exception as e:
            logger.error(f"Extended wait failed: {e}")
            return False, None
    
    async def _heal_dropdown_selection(
        self,
        page,
        step: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Try JavaScript-based dropdown selection"""
        
        try:
            locator_strategies = step.get('locator_strategies', [])
            select_value = step.get('select_value')
            
            if not locator_strategies or not select_value:
                return False, None
            
            # Try to find dropdown
            selector = locator_strategies[0].get('value')
            
            logger.info(f"Attempting JavaScript dropdown selection: {selector}")
            
            # JavaScript approach
            js_code = f"""
            const select = document.querySelector('{selector}');
            if (select) {{
                select.value = '{select_value}';
                select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
            """
            
            result = await page.evaluate(js_code)
            
            if result:
                logger.info("JavaScript dropdown selection succeeded")
                return True, {'method': 'javascript', 'selector': selector}
        
        except Exception as e:
            logger.error(f"JavaScript dropdown selection failed: {e}")
        
        return False, None
    
    async def _heal_click_failure(
        self,
        page,
        step: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Try force click or JavaScript click"""
        
        try:
            locator_strategies = step.get('locator_strategies', [])
            
            if not locator_strategies:
                return False, None
            
            selector = locator_strategies[0].get('value') or locator_strategies[0].get('name')
            
            # Try force click (ignores actionability checks)
            try:
                logger.info(f"Attempting force click: {selector}")
                element = page.locator(selector)
                await element.click(force=True, timeout=5000)
                
                logger.info("Force click succeeded")
                return True, {'method': 'force_click', 'selector': selector}
            
            except:
                pass
            
            # Try JavaScript click
            try:
                logger.info(f"Attempting JavaScript click: {selector}")
                js_code = f"""
                const element = document.querySelector('{selector}');
                if (element) {{
                    element.click();
                    return true;
                }}
                return false;
                """
                
                result = await page.evaluate(js_code)
                
                if result:
                    logger.info("JavaScript click succeeded")
                    return True, {'method': 'javascript_click', 'selector': selector}
            
            except Exception as e:
                logger.error(f"JavaScript click failed: {e}")
        
        except Exception as e:
            logger.error(f"Click healing failed: {e}")
        
        return False, None


# Global instance
self_healer = SelfHealer()
