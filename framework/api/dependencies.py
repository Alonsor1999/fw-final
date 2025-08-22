"""
Dependencias de la API del Framework MVP
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header
from framework.core.orchestrator import Orchestrator

# Global orchestrator instance (will be set by main.py)
_orchestrator: Optional[Orchestrator] = None


def set_orchestrator(orchestrator: Orchestrator):
    """Set global orchestrator instance"""
    global _orchestrator
    _orchestrator = orchestrator


async def get_orchestrator() -> Orchestrator:
    """Dependency to get orchestrator instance"""
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _orchestrator


async def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication")):
    """Verify API key"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key is required")
    
    # For MVP, we'll use simple validation
    # In production, this would validate against a database
    valid_keys = [
        "test_key_legal",
        "test_key_email", 
        "test_key_ocr"
    ]
    
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key


async def get_current_user(api_key: str = Depends(verify_api_key)):
    """Get current user from API key"""
    # For MVP, we'll return a simple user object
    # In production, this would decode the API key and get user info
    return {
        "api_key": api_key,
        "module_name": api_key.replace("test_key_", "").title(),
        "permissions": ["read", "write"]
    }
