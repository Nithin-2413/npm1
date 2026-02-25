import os
import json
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class IntentParser:
    """
    Parse natural language input to extract flow intent and variables
    Uses Groq API with llama-3.3-70b-versatile
    """
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your-groq-api-key-here":
            raise ValueError("GROQ_API_KEY not configured. Please set it in .env file")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.temperature = 0.1  # Deterministic
        self.max_tokens = 512
    
    async def parse(self, natural_language: str, available_flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse natural language to extract flow and variables
        
        Returns:
        {
            "flow_id": str | null,
            "confidence": 0.0-1.0,
            "extracted_variables": {...},
            "missing_required": [...],
            "clarification_needed": str | null
        }
        """
        
        system_prompt = self._build_system_prompt(available_flows)
        user_prompt = f"""Parse this test command:

"{natural_language}"

Extract the flow ID and all variables. Return JSON only."""
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Validate and add confidence check
            if result.get('confidence', 0) < 0.6:
                result['clarification_needed'] = result.get(
                    'clarification_needed',
                    "I'm not confident about understanding your request. Could you please provide more details?"
                )
            
            logger.info(f"Intent parsed: flow={result.get('flow_id')}, confidence={result.get('confidence')}")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Retry with stricter prompt
            return await self._retry_parse(natural_language, available_flows)
        
        except Exception as e:
            logger.error(f"Intent parsing failed: {e}")
            return {
                "flow_id": None,
                "confidence": 0.0,
                "extracted_variables": {},
                "missing_required": [],
                "clarification_needed": f"Failed to parse your request. Please try rephrasing. Error: {str(e)}"
            }
    
    def _build_system_prompt(self, flows: List[Dict[str, Any]]) -> str:
        """Build system prompt with flow descriptions"""
        
        flows_summary = "\n".join([
            f"- {flow['id']}: {flow['name']} - {flow.get('description', '')} (params: {', '.join(flow.get('required_params', []))})"
            for flow in flows
        ])
        
        return f"""You are an expert QA automation assistant. Your job is to parse natural language test commands and extract:
1. The best matching flow ID from the available flows
2. All variables mentioned in the command
3. Missing required parameters
4. Clarification questions if needed

AVAILABLE FLOWS:
{flows_summary}

VARIABLES TO EXTRACT (if mentioned):
- customer: Customer name (e.g., "Lumen-Demo", "Acme Corp")
- service_location: Location/address (e.g., "Dallas Office", "123 Main St")
- quantity: Number/quantity (integer)
- order_type: Type of order (e.g., "Add New Phone Numbers", "Port Numbers")
- user_type: "existing" or "new"
- router_type: "4G" or "5G"
- equipment_type: "lumen_leased", "byod", or "none"
- order_id: Existing order ID for cancel/edit operations
- cancellation_reason: Reason for cancellation

RETURN FORMAT (JSON):
{{
  "flow_id": "flow_id_here" or null,
  "confidence": 0.0-1.0,
  "extracted_variables": {{
    "variable_name": "value"
  }},
  "missing_required": ["list", "of", "missing", "params"],
  "clarification_needed": "question for user" or null
}}

EXAMPLES:

Input: "Create an order for Dallas Office with 3 phone numbers"
Output:
{{
  "flow_id": "create_order_single_tn",
  "confidence": 0.9,
  "extracted_variables": {{
    "service_location": "Dallas Office",
    "quantity": 3
  }},
  "missing_required": [],
  "clarification_needed": null
}}

Input: "Login to the system"
Output:
{{
  "flow_id": "login_customer_selection",
  "confidence": 0.95,
  "extracted_variables": {{}},
  "missing_required": ["url", "username", "password"],
  "clarification_needed": "Please provide login credentials (URL, username, password) or select a test environment."
}}

Input: "Cancel order 12345 because testing is complete"
Output:
{{
  "flow_id": "cancel_order",
  "confidence": 0.95,
  "extracted_variables": {{
    "order_id": "12345",
    "cancellation_reason": "testing is complete"
  }},
  "missing_required": [],
  "clarification_needed": null
}}

Be strict with variable extraction - only extract if explicitly mentioned. Always return valid JSON."""
    
    async def _retry_parse(self, natural_language: str, available_flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Retry with stricter prompt"""
        logger.info("Retrying intent parsing with stricter prompt")
        
        system_prompt = self._build_system_prompt(available_flows)
        user_prompt = f"""Parse this command and return ONLY valid JSON, nothing else:

"{natural_language}"

Return format:
{{
  "flow_id": "id_or_null",
  "confidence": 0.8,
  "extracted_variables": {{}},
  "missing_required": [],
  "clarification_needed": null
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,  # Even more deterministic
                max_tokens=512,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        
        except Exception as e:
            logger.error(f"Retry failed: {e}")
            return {
                "flow_id": None,
                "confidence": 0.0,
                "extracted_variables": {},
                "missing_required": [],
                "clarification_needed": "I couldn't understand your request. Please try again with more specific details."
            }


# Global instance
intent_parser = IntentParser()