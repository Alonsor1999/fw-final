"""
Robot Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from framework.api.dependencies import get_orchestrator
from framework.models.robot import RobotCreate, Robot
from framework.core.orchestrator import Orchestrator

router = APIRouter()

@router.get("/")
async def get_robots():
    """Get all robots"""
    return {"message": "Robots endpoint", "robots": []}

@router.post("/", response_model=Dict[str, Any])
async def create_robot(robot_data: RobotCreate, orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Create a new robot"""
    try:
        # Crear el robot usando el orchestrator (sin validación de API key en desarrollo)
        result = await orchestrator.process_robot(robot_data, api_key="test_key_scraping")
        
        return {
            "success": True,
            "message": "Robot creado exitosamente",
            "robot_id": result["robot_id"],
            "status": result["status"],
            "module": result["module"],
            "processing_time_ms": result["processing_time_ms"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando robot: {str(e)}")

@router.get("/{robot_id}")
async def get_robot(robot_id: str):
    """Get robot by ID"""
    return {"message": f"Robot {robot_id}", "robot_id": robot_id}

@router.put("/{robot_id}")
async def update_robot(robot_id: str):
    """Update robot"""
    return {"message": f"Robot {robot_id} updated"}

@router.delete("/{robot_id}")
async def delete_robot(robot_id: str):
    """Delete robot"""
    return {"message": f"Robot {robot_id} deleted"}
