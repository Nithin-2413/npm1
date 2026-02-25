from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from models import get_db, FlowTemplate
from core.flow_registry import flow_registry

router = APIRouter(prefix="/flows", tags=["Flow Templates"])

class FlowSummary(BaseModel):
    id: str
    name: str
    category: str
    description: str
    required_params: List[str]
    optional_params: List[str]
    estimated_duration_seconds: int

class FlowDetail(BaseModel):
    id: str
    name: str
    category: str
    description: str
    required_params: List[str]
    optional_params: List[str]
    defaults: Dict[str, Any]
    estimated_duration_seconds: int
    steps: List[Dict[str, Any]]

@router.get("", response_model=List[FlowSummary])
async def list_flows():
    """
    List all available flow templates
    """
    flows = flow_registry.list_flows()
    return flows

@router.get("/{flow_id}", response_model=FlowDetail)
async def get_flow_detail(flow_id: str):
    """
    Get detailed information about a specific flow template
    """
    flow = flow_registry.get_flow(flow_id)
    
    if not flow:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
    
    return FlowDetail(**flow)

@router.post("", response_model=Dict[str, str])
async def create_flow(flow_data: FlowDetail, db: Session = Depends(get_db)):
    """
    Create a new flow template
    """
    # Check if flow already exists
    existing = flow_registry.get_flow(flow_data.id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Flow '{flow_data.id}' already exists")
    
    # Save to flow registry (JSON file)
    flow_registry.save_flow(flow_data.dict())
    
    # Also save to database
    db_flow = FlowTemplate(
        id=flow_data.id,
        name=flow_data.name,
        category=flow_data.category,
        description=flow_data.description,
        template_json=flow_data.dict(),
        estimated_duration_seconds=flow_data.estimated_duration_seconds,
        is_active=True
    )
    db.add(db_flow)
    db.commit()
    
    return {
        "flow_id": flow_data.id,
        "message": "Flow template created successfully"
    }