import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

load_dotenv()

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM-based vision and reasoning"""
    
    def __init__(self, provider: str = "groq", model: str = "llama-3.3-70b-versatile"):
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
        
        # For Groq, we'll use OpenAI-compatible API
        # Note: Groq doesn't have native vision, so we'll use a workaround
        self.provider = provider
        self.model = model
        self.session_id = "qa_automation_session"
    
    async def analyze_screenshot_for_element(self, 
                                            screenshot_b64: str,
                                            target_description: str,
                                            failed_locator: str,
                                            step_description: str,
                                            context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze screenshot to find an element when standard locators fail
        
        Returns:
        {
            "element_visible": bool,
            "suggested_locator": str,
            "page_state": str,
            "next_action": str,
            "confidence": float
        }
        """
        
        # Create system prompt for QA expert
        system_message = """
You are an expert QA automation engineer analyzing a web page screenshot.
Your task is to help locate UI elements when standard locators fail.

Provide analysis in JSON format with:
- element_visible: true/false
- suggested_locator: Playwright locator suggestion (semantic if possible)
- page_state: description of current page state
- next_action: recommended next step
- confidence: 0-1 score
"""
        
        # Create user prompt
        user_prompt = f"""
Step: {step_description}
Target Element: {target_description}
Failed Locator: {failed_locator}

Context:
{self._format_context(context)}

Analyze the screenshot and:
1. Is the target element visible?
2. If yes, suggest a Playwright locator (prefer semantic: get_by_role, get_by_label, get_by_text)
3. Describe the current page state
4. Recommend the next action

Respond in JSON format only.
"""
        
        try:
            # Create LLM chat instance
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"{self.session_id}_vision",
                system_message=system_message
            )
            
            # Use OpenAI with vision (works with universal key)
            chat.with_model("openai", "gpt-5.2")
            
            # Create message with image
            image_content = ImageContent(image_base64=screenshot_b64)
            message = UserMessage(
                text=user_prompt,
                file_contents=[image_content]
            )
            
            response = await chat.send_message(message)
            
            # Parse JSON response
            import json
            result = json.loads(response)
            
            return result
        
        except Exception as e:
            logger.error(f"LLM vision analysis failed: {e}")
            return {
                "element_visible": False,
                "suggested_locator": "",
                "page_state": "Unable to analyze",
                "next_action": "retry_with_timeout",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def generate_rca_report(self,
                                 run_id: str,
                                 error_summary: str,
                                 failed_step: Dict[str, Any],
                                 screenshot_b64: str,
                                 network_logs: List[Dict],
                                 console_logs: List[Dict]) -> Dict[str, Any]:
        """
        Generate Root Cause Analysis report using LLM
        
        Returns:
        {
            "root_cause": str,
            "ai_explanation": str,
            "suggested_fix": str,
            "confidence_score": float
        }
        """
        
        system_message = """
You are an expert QA engineer performing root cause analysis on test failures.
Analyze the failure context and provide:
1. Root cause identification
2. Detailed explanation
3. Suggested fix
4. Confidence score (0-1)

Respond in JSON format.
"""
        
        user_prompt = f"""
Test Run ID: {run_id}
Error Summary: {error_summary}

Failed Step:
- Description: {failed_step.get('description')}
- Action: {failed_step.get('action')}
- Target: {failed_step.get('target')}
- Error: {failed_step.get('error')}

Network Errors:
{self._format_network_logs(network_logs)}

Console Errors:
{self._format_console_logs(console_logs)}

Provide root cause analysis in JSON format:
{{
  "root_cause": "brief summary",
  "ai_explanation": "detailed explanation",
  "suggested_fix": "actionable fix",
  "confidence_score": 0.0-1.0
}}
"""
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"{self.session_id}_rca",
                system_message=system_message
            )
            
            chat.with_model("openai", "gpt-5.2")
            
            # Include screenshot if available
            if screenshot_b64:
                image_content = ImageContent(image_base64=screenshot_b64)
                message = UserMessage(text=user_prompt, file_contents=[image_content])
            else:
                message = UserMessage(text=user_prompt)
            
            response = await chat.send_message(message)
            
            import json
            result = json.loads(response)
            
            return result
        
        except Exception as e:
            logger.error(f"LLM RCA generation failed: {e}")
            return {
                "root_cause": "Unable to determine",
                "ai_explanation": f"RCA generation failed: {str(e)}",
                "suggested_fix": "Manual investigation required",
                "confidence_score": 0.0
            }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for LLM prompt"""
        lines = []
        for key, value in context.items():
            if key not in ['screenshot', 'screenshot_b64']:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No context available"
    
    def _format_network_logs(self, logs: List[Dict]) -> str:
        """Format network logs for LLM prompt"""
        errors = [log for log in logs if log.get('status', 200) >= 400]
        if not errors:
            return "No network errors"
        
        lines = []
        for log in errors[:10]:  # Limit to last 10 errors
            lines.append(f"- {log.get('method')} {log.get('url')}: {log.get('status')}")
        return "\n".join(lines)
    
    def _format_console_logs(self, logs: List[Dict]) -> str:
        """Format console logs for LLM prompt"""
        errors = [log for log in logs if log.get('type') in ['error', 'warn']]
        if not errors:
            return "No console errors"
        
        lines = []
        for log in errors[:10]:  # Limit to last 10 errors
            lines.append(f"- [{log.get('type')}] {log.get('text')}")
        return "\n".join(lines)


# Global LLM service instance
llm_service = LLMService()