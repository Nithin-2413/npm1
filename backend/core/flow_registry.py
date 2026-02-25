import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

class FlowRegistry:
    """Manages flow templates loaded from JSON files"""
    
    def __init__(self, templates_dir: str = "/app/flows/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.flows: Dict[str, Dict[str, Any]] = {}
        self.load_all_flows()
    
    def load_all_flows(self) -> None:
        """Load all flow templates from JSON files"""
        if not self.templates_dir.exists():
            return
        
        for json_file in self.templates_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    flow_data = json.load(f)
                    flow_id = flow_data.get("id")
                    if flow_id:
                        self.flows[flow_id] = flow_data
            except Exception as e:
                print(f"Error loading flow {json_file}: {e}")
    
    def get_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific flow by ID"""
        return self.flows.get(flow_id)
    
    def list_flows(self) -> List[Dict[str, Any]]:
        """List all available flows (summary)"""
        return [
            {
                "id": flow["id"],
                "name": flow["name"],
                "category": flow.get("category", "general"),
                "description": flow.get("description", ""),
                "required_params": flow.get("required_params", []),
                "optional_params": flow.get("optional_params", []),
                "estimated_duration_seconds": flow.get("estimated_duration_seconds", 60)
            }
            for flow in self.flows.values()
        ]
    
    def save_flow(self, flow_data: Dict[str, Any]) -> None:
        """Save a flow template to JSON file"""
        flow_id = flow_data.get("id")
        if not flow_id:
            raise ValueError("Flow must have an 'id' field")
        
        filepath = self.templates_dir / f"{flow_id}.json"
        with open(filepath, 'w') as f:
            json.dump(flow_data, f, indent=2)
        
        self.flows[flow_id] = flow_data


# Global flow registry instance
flow_registry = FlowRegistry()