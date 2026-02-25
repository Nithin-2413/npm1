from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging

from models import (
    create_test_environment, get_test_environment, 
    list_test_environments, update_test_environment,
    delete_test_environment
)

router = APIRouter(prefix="/secrets", tags=["Test Environments"])
logger = logging.getLogger(__name__)

class SecretCreate(BaseModel):
    test_env: str
    release_branch: Optional[str] = None
    url: str
    username: Optional[str] = None
    password: Optional[str] = None

class SecretResponse(BaseModel):
    id: str
    env_id: str
    test_env: str
    release_branch: Optional[str] = None
    url: str
    username: Optional[str] = None
    created_at: Optional[str] = None

@router.post("", response_model=SecretResponse)
async def create_secret(secret: SecretCreate):
    """Create a new test environment secret"""
    env_id = str(uuid.uuid4())
    
    result = create_test_environment({
        "env_id": env_id,
        "test_env": secret.test_env,
        "release_branch": secret.release_branch,
        "url": secret.url,
        "username": secret.username,
        "password": secret.password
    })
    
    return SecretResponse(
        id=result.get('id', env_id),
        env_id=env_id,
        test_env=secret.test_env,
        release_branch=secret.release_branch,
        url=secret.url,
        username=secret.username,
        created_at=result.get('created_at')
    )

@router.get("", response_model=List[SecretResponse])
async def list_secrets():
    """List all test environment secrets (without passwords)"""
    secrets = list_test_environments()
    return [
        SecretResponse(
            id=s.get('id', s.get('env_id', '')),
            env_id=s.get('env_id', ''),
            test_env=s.get('test_env', ''),
            release_branch=s.get('release_branch'),
            url=s.get('url', ''),
            username=s.get('username'),
            created_at=s.get('created_at')
        )
        for s in secrets
    ]

@router.get("/{env_id}", response_model=SecretResponse)
async def get_secret(env_id: str):
    """Get a specific test environment secret"""
    secret = get_test_environment(env_id)
    
    if not secret:
        raise HTTPException(status_code=404, detail=f"Secret '{env_id}' not found")
    
    return SecretResponse(
        id=secret.get('id', env_id),
        env_id=secret.get('env_id', env_id),
        test_env=secret.get('test_env', ''),
        release_branch=secret.get('release_branch'),
        url=secret.get('url', ''),
        username=secret.get('username'),
        created_at=secret.get('created_at')
    )

@router.put("/{env_id}", response_model=SecretResponse)
async def update_secret(env_id: str, secret: SecretCreate):
    """Update a test environment secret"""
    existing = get_test_environment(env_id)
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"Secret '{env_id}' not found")
    
    updates = {
        "test_env": secret.test_env,
        "release_branch": secret.release_branch,
        "url": secret.url,
        "username": secret.username
    }
    
    if secret.password:
        updates["password"] = secret.password
    
    result = update_test_environment(env_id, updates)
    
    return SecretResponse(
        id=result.get('id', env_id),
        env_id=env_id,
        test_env=secret.test_env,
        release_branch=secret.release_branch,
        url=secret.url,
        username=secret.username,
        created_at=result.get('created_at')
    )

@router.delete("/{env_id}")
async def delete_secret(env_id: str):
    """Delete a test environment secret"""
    existing = get_test_environment(env_id)
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"Secret '{env_id}' not found")
    
    delete_test_environment(env_id)
    
    return {"message": "Secret deleted successfully"}
