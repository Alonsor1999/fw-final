"""
Modelos de datos del Framework MVP
"""

from .base import BaseModel
from .robot import Robot, RobotCreate, RobotUpdate, RobotStatus
from .module import Module, ModuleCreate, ModuleUpdate, ModuleHealth
from .execution import RobotExecute, ExecutionState, StepCategory
from .performance import PerformanceMetrics, CacheMetrics

__all__ = [
    "BaseModel",
    "Robot", "RobotCreate", "RobotUpdate", "RobotStatus",
    "Module", "ModuleCreate", "ModuleUpdate", "ModuleHealth", 
    "RobotExecute", "ExecutionState", "StepCategory",
    "PerformanceMetrics", "CacheMetrics"
]
