import os
import json
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RCAEngine:
    """
    Root Cause Analysis Engine using Groq LLM
    Analyzes test failures with network, console, and execution context
    """
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your-groq-api-key-here":
            raise ValueError("GROQ_API_KEY not configured for RCA")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.temperature = 0.3  # Slightly creative for analysis
        self.max_tokens = 2048
    
    async def analyze(
        self,
        run_id: str,
        failed_step: Dict[str, Any],
        recent_steps: List[Dict[str, Any]],
        network_anomalies: List[Dict[str, Any]],
        console_errors: List[Dict[str, Any]],
        screenshot_description: Optional[str],
        flow_name: str,
        variables: Dict[str, Any],
        streaming: bool = False
    ) -> Dict[str, Any]:
        """
        Perform root cause analysis
        
        If streaming=True, returns an async generator for token-by-token streaming
        Otherwise returns complete analysis
        """
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            failed_step=failed_step,
            recent_steps=recent_steps,
            network_anomalies=network_anomalies,
            console_errors=console_errors,
            screenshot_description=screenshot_description,
            flow_name=flow_name,
            variables=variables
        )
        
        if streaming:
            return self._analyze_streaming(system_prompt, user_prompt)
        else:
            return await self._analyze_complete(system_prompt, user_prompt, run_id)
    
    async def _analyze_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        run_id: str
    ) -> Dict[str, Any]:
        """Complete analysis (non-streaming)"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['run_id'] = run_id
            result['analysis_method'] = 'complete'
            
            logger.info(f"RCA complete for run {run_id}: {result.get('root_cause', 'Unknown')[:100]}")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse RCA JSON: {e}")
            return self._fallback_analysis(run_id, "JSON parse error")
        
        except Exception as e:
            logger.error(f"RCA analysis failed: {e}")
            return self._fallback_analysis(run_id, str(e))
    
    async def _analyze_streaming(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> AsyncIterator[str]:
        """Streaming analysis for real-time UX"""
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            # Collect tokens and yield for streaming
            collected_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    collected_text += token
                    yield token
            
            # Try to parse final result as JSON
            try:
                final_result = json.loads(collected_text)
                # Yield final JSON marker
                yield "\n[RCA_COMPLETE]" + json.dumps(final_result)
            except json.JSONDecodeError:
                logger.warning("Streaming RCA did not produce valid JSON")
                yield "\n[RCA_ERROR]Invalid JSON output"
        
        except Exception as e:
            logger.error(f"Streaming RCA failed: {e}")
            yield f"\n[RCA_ERROR]{str(e)}"
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for RCA"""
        
        return """You are an expert QA engineer performing root cause analysis on test failures.

Your job is to analyze:
1. The failed test step and error
2. Recent successful steps (context)
3. Network anomalies (HTTP errors, timeouts, failures)
4. Console errors and warnings
5. Screenshot state (if available)
6. Flow context (what the test was trying to do)

IMPORTANT: Return ONLY valid JSON in this exact format:
{
  "root_cause": "Clear, specific explanation of what went wrong",
  "affected_service": "Which service/API/component failed (if applicable)",
  "failure_category": "API Error" | "UI Element Missing" | "Timeout" | "Validation Error" | "Auth Error" | "Data Error" | "Network Error" | "JavaScript Error",
  "confidence": 0.0-1.0,
  "evidence": [
    "Specific piece of evidence 1",
    "Specific piece of evidence 2",
    "..."
  ],
  "suggested_fix": "Actionable suggestion to fix or workaround the issue",
  "severity": "critical" | "high" | "medium" | "low",
  "is_flaky": false | true,
  "flaky_reason": "Explanation if this appears to be a flaky test" | null
}

ANALYSIS GUIDELINES:
- Be specific: Don't say "API failed", say "Order Creation API returned 500 due to missing service_location_id"
- Use evidence: Reference specific HTTP status codes, console errors, timing
- Confidence scoring:
  - 0.9-1.0: Clear root cause with strong evidence
  - 0.7-0.9: Likely cause with good evidence
  - 0.5-0.7: Probable cause with some evidence
  - 0.3-0.5: Possible cause with weak evidence
  - 0.0-0.3: Uncertain
- Flaky detection: Mark as flaky if:
  - Timing-related issues (race conditions)
  - Intermittent network errors
  - Load-dependent failures
- Severity assessment:
  - critical: Blocker, cannot proceed with test
  - high: Major failure, test objective not met
  - medium: Partial failure, some functionality works
  - low: Minor issue, test mostly successful

Be concise but thorough. Always return valid JSON."""
    
    def _build_user_prompt(
        self,
        failed_step: Dict[str, Any],
        recent_steps: List[Dict[str, Any]],
        network_anomalies: List[Dict[str, Any]],
        console_errors: List[Dict[str, Any]],
        screenshot_description: Optional[str],
        flow_name: str,
        variables: Dict[str, Any]
    ) -> str:
        """Build user prompt with all context"""
        
        # Format recent steps
        recent_steps_text = "\n".join([
            f"Step {s['step_number']}: {s['step_description']} - {s['status']}"
            for s in recent_steps[-5:]  # Last 5 steps
        ])
        
        # Format network anomalies
        network_text = "\n".join([
            f"- {a.get('method', 'N/A')} {a.get('url', 'N/A')}: {a.get('anomaly_reason', 'Unknown')}"
            for a in network_anomalies[:10]  # Max 10
        ])
        
        # Format console errors
        console_text = "\n".join([
            f"- [{e.get('console_type', 'error')}] {e.get('text', 'Unknown')}"
            for e in console_errors[:10]  # Max 10
        ])
        
        prompt = f"""FAILURE ANALYSIS REQUEST

Flow: {flow_name}
Variables: {json.dumps(variables, indent=2)}

FAILED STEP:
Step {failed_step.get('step_number', 'N/A')}: {failed_step.get('step_description', 'Unknown')}
Action: {failed_step.get('action', 'N/A')}
Target: {failed_step.get('target', 'N/A')}
Error: {failed_step.get('error_message', 'Unknown error')}
Duration: {failed_step.get('duration_ms', 0)}ms

RECENT SUCCESSFUL STEPS (context):
{recent_steps_text if recent_steps_text else 'None'}

NETWORK ANOMALIES:
{network_text if network_text else 'None detected'}

CONSOLE ERRORS:
{console_text if console_text else 'None detected'}

SCREENSHOT STATE:
{screenshot_description if screenshot_description else 'Not available'}

Analyze this failure and provide root cause analysis in JSON format."""
        
        return prompt
    
    def _fallback_analysis(self, run_id: str, error: str) -> Dict[str, Any]:
        """Fallback analysis when LLM fails"""
        
        return {
            'run_id': run_id,
            'root_cause': f"Unable to determine root cause. Analysis error: {error}",
            'affected_service': 'Unknown',
            'failure_category': 'Unknown',
            'confidence': 0.0,
            'evidence': ['RCA analysis failed', f'Error: {error}'],
            'suggested_fix': 'Manual investigation required. Check logs and network activity.',
            'severity': 'high',
            'is_flaky': False,
            'flaky_reason': None,
            'analysis_method': 'fallback'
        }


# Global instance
rca_engine = RCAEngine()
