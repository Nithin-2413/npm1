import logging
import random
import string
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class VariableResolver:
    """
    Merge variables from multiple sources with priority:
    1. form_overrides (highest - from frontend form)
    2. llm_extracted (middle - from natural language)
    3. flow_defaults (lowest - from flow template)
    
    Also handles auto-generation of random values
    """
    
    def resolve(
        self,
        flow: Dict[str, Any],
        form_overrides: Optional[Dict[str, Any]] = None,
        llm_extracted: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve variables with priority merging
        
        Returns:
        {
            "resolved": {"var": "value", ...},
            "missing_required": ["var1", "var2", ...],
            "auto_generated": {"var": "value", ...}
        }
        """
        
        form_overrides = form_overrides or {}
        llm_extracted = llm_extracted or {}
        flow_defaults = flow.get('defaults', {})
        required_params = flow.get('required_params', [])
        
        resolved = {}
        auto_generated = {}
        
        # Step 1: Start with flow defaults
        resolved.update(flow_defaults)
        
        # Step 2: Override with LLM-extracted variables
        for key, value in llm_extracted.items():
            if value is not None:  # Only override if LLM found a value
                resolved[key] = value
        
        # Step 3: Override with form inputs (highest priority)
        for key, value in form_overrides.items():
            if value is not None:
                resolved[key] = value
        
        # Step 4: Auto-generate values for special fields
        auto_gen_fields = {
            'user_name': lambda: self._generate_random_name(),
            'mac_address': lambda: self._generate_mac_address(),
            'serial_number': lambda: self._generate_serial(),
            'phone_number': lambda: self._generate_phone_number(),
        }
        
        for field, generator in auto_gen_fields.items():
            if field in required_params and field not in resolved:
                resolved[field] = generator()
                auto_generated[field] = resolved[field]
                logger.info(f"Auto-generated {field}: {resolved[field]}")
        
        # Step 5: Check for missing required parameters
        missing_required = [
            param for param in required_params
            if param not in resolved or resolved[param] is None
        ]
        
        logger.info(
            f"Variable resolution complete: "
            f"resolved={len(resolved)}, missing={len(missing_required)}, auto_gen={len(auto_generated)}"
        )
        
        return {
            "resolved": resolved,
            "missing_required": missing_required,
            "auto_generated": auto_generated
        }
    
    def _generate_random_name(self, length: int = 5) -> str:
        """Generate random user name (5 char alpha)"""
        return 'User_' + ''.join(random.choices(string.ascii_uppercase, k=length))
    
    def _generate_mac_address(self) -> str:
        """Generate random MAC address (12 char hex)"""
        return ':'.join([
            ''.join(random.choices('0123456789ABCDEF', k=2))
            for _ in range(6)
        ])
    
    def _generate_serial(self) -> str:
        """Generate random serial number"""
        return 'SN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    def _generate_phone_number(self) -> str:
        """Generate random phone number"""
        area_code = random.randint(200, 999)
        exchange = random.randint(200, 999)
        subscriber = random.randint(1000, 9999)
        return f"+1-{area_code}-{exchange}-{subscriber}"


# Global instance
variable_resolver = VariableResolver()