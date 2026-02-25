import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class StepBuilder:
    """
    Build concrete executable steps from flow template + resolved variables
    - Replaces {{variable}} placeholders
    - Resolves conditional branches
    - Returns flat ordered list of steps
    
    NO LLM calls - pure logic
    """
    
    def build_steps(
        self,
        flow_template: Dict[str, Any],
        resolved_variables: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build executable step list from template
        
        Returns: List of concrete steps ready for Playwright execution
        """
        
        template_steps = flow_template.get('steps', [])
        concrete_steps = []
        
        for step in template_steps:
            # Check conditional execution
            if self._should_execute_step(step, resolved_variables):
                concrete_step = self._resolve_step(step, resolved_variables)
                concrete_steps.append(concrete_step)
                logger.debug(f"Step {concrete_step['step']}: {concrete_step['description']}")
            else:
                logger.debug(f"Skipping conditional step {step['step']}: {step['description']}")
        
        logger.info(f"Built {len(concrete_steps)} executable steps from {len(template_steps)} template steps")
        return concrete_steps
    
    def _should_execute_step(self, step: Dict[str, Any], variables: Dict[str, Any]) -> bool:
        """
        Check if step should be executed based on conditional logic
        
        Example: step.conditional = "customer" means only execute if customer variable exists
        """
        conditional = step.get('conditional')
        
        if not conditional:
            return True  # No condition, always execute
        
        # Simple conditional: check if variable exists and is not None
        if isinstance(conditional, str):
            return conditional in variables and variables[conditional] is not None
        
        # Complex conditional: dict with operators (future enhancement)
        if isinstance(conditional, dict):
            # e.g., {"user_type": "new"} - only execute if user_type == "new"
            for key, expected_value in conditional.items():
                actual_value = variables.get(key)
                if actual_value != expected_value:
                    return False
            return True
        
        return True
    
    def _resolve_step(self, step: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace all {{variable}} placeholders in step with actual values
        """
        
        # Deep copy to avoid modifying template
        concrete_step = {
            'step': step['step'],
            'description': self._replace_vars(step['description'], variables),
            'action': step['action'],
            'locator_strategies': self._resolve_locator_strategies(
                step.get('locator_strategies', []),
                variables
            )
        }
        
        # Copy other fields and replace variables
        for key in ['value', 'select_value', 'save_to_context', 'wait_before_ms', 
                    'duration_ms', 'max_wait_ms', 'select_by', 'extract_pattern',
                    'wait_for_element', 'wait_for_modal', 'conditional', 'human_reasoning']:
            if key in step:
                if isinstance(step[key], str):
                    concrete_step[key] = self._replace_vars(step[key], variables)
                else:
                    concrete_step[key] = step[key]
        
        return concrete_step
    
    def _resolve_locator_strategies(
        self,
        strategies: List[Dict[str, Any]],
        variables: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Replace variables in locator strategies
        """
        resolved = []
        
        for strategy in strategies:
            resolved_strategy = {
                'priority': strategy['priority'],
                'type': strategy['type']
            }
            
            # Replace variables in 'value' or 'name' fields
            for key in ['value', 'name']:
                if key in strategy:
                    resolved_strategy[key] = self._replace_vars(strategy[key], variables)
            
            resolved.append(resolved_strategy)
        
        return resolved
    
    def _replace_vars(self, text: str, variables: Dict[str, Any]) -> str:
        """
        Replace {{variable}} placeholders with actual values
        
        Example: "Login to {{url}}" with {"url": "https://example.com"}
                 becomes "Login to https://example.com"
        """
        if not isinstance(text, str):
            return text
        
        # Find all {{variable}} patterns
        pattern = r'{{(\w+)}}'
        
        def replace_match(match):
            var_name = match.group(1)
            value = variables.get(var_name)
            if value is not None:
                return str(value)
            else:
                logger.warning(f"Variable {var_name} not found in resolved variables")
                return match.group(0)  # Keep original if not found
        
        return re.sub(pattern, replace_match, text)


# Global instance
step_builder = StepBuilder()