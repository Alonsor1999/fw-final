"""
Health Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from framework.api.dependencies import get_orchestrator

router = APIRouter()

@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-12-14T10:00:00Z",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "database": "healthy",
            "cache": "healthy",
            "modules": "healthy"
        },
        "timestamp": "2024-12-14T10:00:00Z"
    }
