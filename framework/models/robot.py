"""
Modelos para robots del Framework MVP
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from .base import TimestampedModel, PerformanceModel, ErrorModel


class RobotStatus(str, Enum):
    """Estados posibles de un robot"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class Priority(str, Enum):
    """Prioridades de procesamiento"""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProcessingTier(str, Enum):
    """Tiers de complejidad de procesamiento"""
    FAST = "FAST"
    STANDARD = "STANDARD"
    COMPLEX = "COMPLEX"
    BULK = "BULK"


class SecurityClassification(str, Enum):
    """Clasificaciones de seguridad"""
    STANDARD = "STANDARD"
    SENSITIVE = "SENSITIVE"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class Robot(TimestampedModel):
    """Modelo principal de robot - Registro simple"""
    robot_id: str = Field(..., description="Identificador único del robot")
    robot_name: str = Field(..., description="Nombre del robot")
    description: Optional[str] = Field(None, description="Descripción del robot")
    robot_type: Optional[str] = Field(None, description="Tipo de robot")
    status: str = Field(default="active", description="Estado del robot")
    
    # Configuración opcional
    config_data: Dict[str, Any] = Field(default_factory=dict, description="Datos de configuración")
    tags: List[str] = Field(default_factory=list, description="Etiquetas del robot")

    @validator('robot_id')
    def validate_robot_id(cls, v):
        """Validar formato del robot_id"""
        if not v or len(v) > 50:
            raise ValueError('robot_id debe tener entre 1 y 50 caracteres')
        return v

    def is_active(self) -> bool:
        """Verificar si el robot está activo"""
        return self.status == "active"

    def get_processing_time_ms(self) -> Optional[int]:
        """Obtener tiempo de procesamiento en ms"""
        if self.created_at and self.updated_at:
            return int((self.updated_at - self.created_at).total_seconds() * 1000)
        return None


class RobotCreate(BaseModel):
    """Modelo para crear un robot"""
    robot_name: str = Field(..., description="Nombre del robot")
    description: Optional[str] = Field(None, description="Descripción del robot")
    robot_type: Optional[str] = Field(None, description="Tipo de robot")
    config_data: Dict[str, Any] = Field(default_factory=dict, description="Datos de configuración")
    tags: List[str] = Field(default_factory=list, description="Etiquetas del robot")

    @validator('robot_name')
    def validate_robot_name(cls, v):
        """Validar nombre del robot"""
        if not v or len(v) > 100:
            raise ValueError('robot_name debe tener entre 1 y 100 caracteres')
        return v


class RobotUpdate(BaseModel):
    """Modelo para actualizar un robot"""
    robot_name: Optional[str] = Field(None, description="Nombre del robot")
    description: Optional[str] = Field(None, description="Descripción del robot")
    robot_type: Optional[str] = Field(None, description="Tipo de robot")
    status: Optional[str] = Field(None, description="Estado del robot")
    config_data: Optional[Dict[str, Any]] = Field(None, description="Datos de configuración")
    tags: Optional[List[str]] = Field(None, description="Etiquetas del robot")


class RobotResponse(BaseModel):
    """Respuesta de API para robots"""
    robot_id: str
    status: RobotStatus
    module_name: str
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    estimated_completion: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RobotListResponse(BaseModel):
    """Respuesta paginada de robots"""
    robots: List[RobotResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
