from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from models import get_db, TestEnvironment

router = APIRouter(prefix="/secrets", tags=["Test Environments"])

class SecretCreate(BaseModel):
    test_env: str
    release_branch: Optional[str] = None
    url: str
    username: Optional[str] = None
    password: Optional[str] = None

class SecretResponse(BaseModel):
    id: str
    test_env: str
    release_branch: Optional[str]
    url: str
    username: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("", response_model=SecretResponse)
async def create_secret(secret: SecretCreate, db: Session = Depends(get_db)):
    """
    Create a new test environment secret
    """
    secret_id = str(uuid.uuid4())
    
    db_secret = TestEnvironment(
        id=secret_id,
        test_env=secret.test_env,
        release_branch=secret.release_branch,
        url=secret.url,
        username=secret.username,
        password=secret.password  # Should be encrypted in production
    )
    
    db.add(db_secret)
    db.commit()
    db.refresh(db_secret)
    
    return db_secret

@router.get("", response_model=List[SecretResponse])
async def list_secrets(db: Session = Depends(get_db)):
    """
    List all test environment secrets (without passwords)
    """
    secrets = db.query(TestEnvironment).all()
    return secrets

@router.get("/{secret_id}", response_model=SecretResponse)
async def get_secret(secret_id: str, db: Session = Depends(get_db)):
    """
    Get a specific test environment secret
    """
    secret = db.query(TestEnvironment).filter(TestEnvironment.id == secret_id).first()
    
    if not secret:
        raise HTTPException(status_code=404, detail=f"Secret '{secret_id}' not found")
    
    return secret

@router.put("/{secret_id}", response_model=SecretResponse)
async def update_secret(secret_id: str, secret: SecretCreate, db: Session = Depends(get_db)):
    """
    Update a test environment secret
    """
    db_secret = db.query(TestEnvironment).filter(TestEnvironment.id == secret_id).first()
    
    if not db_secret:
        raise HTTPException(status_code=404, detail=f"Secret '{secret_id}' not found")
    
    db_secret.test_env = secret.test_env
    db_secret.release_branch = secret.release_branch
    db_secret.url = secret.url
    db_secret.username = secret.username
    if secret.password:
        db_secret.password = secret.password
    db_secret.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_secret)
    
    return db_secret

@router.delete("/{secret_id}")
async def delete_secret(secret_id: str, db: Session = Depends(get_db)):
    """
    Delete a test environment secret
    """
    db_secret = db.query(TestEnvironment).filter(TestEnvironment.id == secret_id).first()
    
    if not db_secret:
        raise HTTPException(status_code=404, detail=f"Secret '{secret_id}' not found")
    
    db.delete(db_secret)
    db.commit()
    
    return {"message": "Secret deleted successfully"}