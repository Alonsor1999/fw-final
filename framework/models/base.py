"""
Modelo base para todos los modelos del framework MVP
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class BaseModelMVP(BaseModel):
    """Modelo base con funcionalidades comunes"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        validate_assignment = True


class TimestampedModel(BaseModelMVP):
    """Modelo con timestamps automáticos"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IdentifiableModel(BaseModelMVP):
    """Modelo con ID único"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class PerformanceModel(BaseModelMVP):
    """Modelo con métricas de performance"""
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: Optional[int] = None
    cache_hit: bool = False
    resource_usage_mb: Optional[int] = None


class ErrorModel(BaseModelMVP):
    """Modelo con manejo de errores"""
    error_details: Optional[Dict[str, Any]] = None
    error_category: Optional[str] = None
    retry_count: int = 0
    retry_limit: int = 3
    last_error_at: Optional[datetime] = None
