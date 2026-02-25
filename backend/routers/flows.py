from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from core.flow_registry import flow_registry

router = APIRouter(prefix="/flows", tags=["Flow Templates"])
logger = logging.getLogger(__name__)

class FlowSummary(BaseModel):
    id: str
    name: str
    category: str
    description: str
    required_params: List[str] = []
    optional_params: List[str] = []
    estimated_duration_seconds: int = 60

class FlowDetail(BaseModel):
    id: str
    name: str
    category: str
    description: str
    required_params: List[str] = []
    optional_params: List[str] = []
    defaults: Dict[str, Any] = {}
    estimated_duration_seconds: int = 60
    steps: List[Dict[str, Any]] = []

@router.get("", response_model=List[FlowSummary])
async def list_flows():
    """List all available flow templates"""
    flows = flow_registry.list_flows()
    return [
        FlowSummary(
            id=f.get('id', ''),
            name=f.get('name', ''),
            category=f.get('category', 'general'),
            description=f.get('description', ''),
            required_params=f.get('required_params', []),
            optional_params=f.get('optional_params', []),
            estimated_duration_seconds=f.get('estimated_duration_seconds', 60)
        )
        for f in flows
    ]

@router.get("/{flow_id}", response_model=FlowDetail)
async def get_flow_detail(flow_id: str):
    """Get detailed information about a specific flow template"""
    flow = flow_registry.get_flow(flow_id)
    
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
    
    return FlowDetail(
        id=flow.get('id', flow_id),
        name=flow.get('name', ''),
        category=flow.get('category', 'general'),
        description=flow.get('description', ''),
        required_params=flow.get('required_params', []),
        optional_params=flow.get('optional_params', []),
        defaults=flow.get('defaults', {}),
        estimated_duration_seconds=flow.get('estimated_duration_seconds', 60),
        steps=flow.get('steps', [])
    )

@router.post("", response_model=Dict[str, str])
async def create_flow(flow_data: FlowDetail):
    """Create a new flow template"""
    # Check if flow already exists
    existing = flow_registry.get_flow(flow_data.id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Flow '{flow_data.id}' already exists")
    
    # Save to flow registry (JSON file)
    flow_registry.save_flow(flow_data.model_dump())
    
    return {
        "flow_id": flow_data.id,
        "message": "Flow template created successfully"
    }

@router.put("/{flow_id}", response_model=Dict[str, str])
async def update_flow(flow_id: str, flow_data: FlowDetail):
    """Update an existing flow template"""
    existing = flow_registry.get_flow(flow_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
    
    # Update flow
    flow_dict = flow_data.model_dump()
    flow_dict['id'] = flow_id  # Ensure ID matches
    flow_registry.save_flow(flow_dict)
    
    return {
        "flow_id": flow_id,
        "message": "Flow template updated successfully"
    }

@router.delete("/{flow_id}")
async def delete_flow(flow_id: str):
    """Delete a flow template"""
    existing = flow_registry.get_flow(flow_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
    
    # Delete from registry
    flow_registry.delete_flow(flow_id)
    
    return {
        "flow_id": flow_id,
        "message": "Flow template deleted successfully"
    }
