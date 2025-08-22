"""
Modelos para módulos del Framework MVP
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from .base import TimestampedModel, PerformanceModel, ErrorModel


class ModuleHealth(str, Enum):
    """Estados de salud de un módulo"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class PerformanceTier(str, Enum):
    """Tiers de performance"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CRITICAL = "CRITICAL"


class SecurityLevel(str, Enum):
    """Niveles de seguridad"""
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    ENHANCED = "ENHANCED"
    ENTERPRISE = "ENTERPRISE"


class Module(TimestampedModel, PerformanceModel, ErrorModel):
    """Modelo principal de módulo"""
    module_id: str = Field(..., description="Identificador único del módulo")
    module_name: str = Field(..., description="Nombre descriptivo del módulo")
    module_version: str = Field(..., description="Versión del módulo")
    supported_robot_types: List[str] = Field(..., description="Tipos de robot soportados")
    is_active: bool = Field(default=True, description="Estado activo del módulo")
    health_endpoint: Optional[str] = Field(None, description="Endpoint de health check")
    registration_data: Dict[str, Any] = Field(default_factory=dict, description="Datos de registro")
    
    # MVP Performance Enhancements
    performance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Score de performance 0.0-1.0")
    performance_tier: PerformanceTier = Field(default=PerformanceTier.MEDIUM, description="Tier basado en performance")
    last_performance_check: Optional[datetime] = Field(None, description="Última verificación de performance")
    error_count_24h: int = Field(default=0, ge=0, description="Errores en últimas 24 horas")
    success_rate_24h: float = Field(default=100.0, ge=0.0, le=100.0, description="% éxito últimas 24 horas")
    avg_processing_time_ms: int = Field(default=0, ge=0, description="Tiempo promedio de procesamiento")
    capacity_utilization: float = Field(default=0.0, ge=0.0, le=1.0, description="% capacidad utilizada")
    
    # Health & Monitoring
    health_status: ModuleHealth = Field(default=ModuleHealth.UNKNOWN, description="Estado de salud actual")
    last_health_check: Optional[datetime] = Field(None, description="Último health check")
    consecutive_failures: int = Field(default=0, ge=0, description="Fallos consecutivos")
    last_error_message: Optional[str] = Field(None, description="Último mensaje de error")
    uptime_percentage_24h: float = Field(default=100.0, ge=0.0, le=100.0, description="% uptime últimas 24h")
    
    # Statistics
    total_robots_processed: int = Field(default=0, ge=0, description="Total robots procesados")
    total_processing_time_hours: float = Field(default=0.0, ge=0.0, description="Tiempo total de procesamiento")
    
    # Evolution Path
    security_level: SecurityLevel = Field(default=SecurityLevel.BASIC, description="Nivel de seguridad")
    compliance_flags: Dict[str, Any] = Field(default_factory=dict, description="Flags de compliance")
    enterprise_features: Dict[str, Any] = Field(default_factory=dict, description="Features enterprise")

    @validator('module_id')
    def validate_module_id(cls, v):
        """Validar formato del module_id"""
        if not v or len(v) > 100:
            raise ValueError('module_id debe tener entre 1 y 100 caracteres')
        return v

    @validator('module_name')
    def validate_module_name(cls, v):
        """Validar nombre del módulo"""
        if not v or len(v) > 100:
            raise ValueError('module_name debe tener entre 1 y 100 caracteres')
        return v

    @validator('supported_robot_types')
    def validate_robot_types(cls, v):
        """Validar tipos de robot soportados"""
        if not v or len(v) == 0:
            raise ValueError('Debe soportar al menos un tipo de robot')
        return v

    @validator('performance_score')
    def validate_performance_score(cls, v):
        """Validar score de performance"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('performance_score debe estar entre 0.0 y 1.0')
        return v

    @validator('success_rate_24h', 'uptime_percentage_24h')
    def validate_percentages(cls, v):
        """Validar porcentajes"""
        if not 0.0 <= v <= 100.0:
            raise ValueError('Porcentaje debe estar entre 0.0 y 100.0')
        return v

    def is_healthy(self) -> bool:
        """Verificar si el módulo está saludable"""
        return self.health_status == "HEALTHY"

    def is_available(self) -> bool:
        """Verificar si el módulo está disponible"""
        return self.is_active and self.is_healthy()

    def can_process_robot_type(self, robot_type: str) -> bool:
        """Verificar si puede procesar un tipo de robot"""
        return robot_type in self.supported_robot_types

    def get_capacity_score(self) -> float:
        """Obtener score de capacidad (inverso de utilización)"""
        return 1.0 - self.capacity_utilization

    def get_overall_score(self) -> float:
        """Obtener score general para routing"""
        return (
            self.performance_score * 0.5 +
            self.get_capacity_score() * 0.3 +
            (1.0 if self.is_healthy() else 0.0) * 0.2
        )


class ModuleCreate(BaseModel):
    """Modelo para crear un módulo"""
    module_name: str = Field(..., description="Nombre descriptivo del módulo")
    module_version: str = Field(..., description="Versión del módulo")
    supported_robot_types: List[str] = Field(..., description="Tipos de robot soportados")
    health_endpoint: Optional[str] = Field(None, description="Endpoint de health check")
    registration_data: Dict[str, Any] = Field(default_factory=dict, description="Datos de registro")
    security_level: SecurityLevel = Field(default=SecurityLevel.BASIC, description="Nivel de seguridad")

    @validator('module_name')
    def validate_module_name(cls, v):
        """Validar nombre del módulo"""
        if not v or len(v) > 100:
            raise ValueError('module_name debe tener entre 1 y 100 caracteres')
        return v

    @validator('supported_robot_types')
    def validate_robot_types(cls, v):
        """Validar tipos de robot soportados"""
        if not v or len(v) == 0:
            raise ValueError('Debe soportar al menos un tipo de robot')
        return v


class ModuleUpdate(BaseModel):
    """Modelo para actualizar un módulo"""
    is_active: Optional[bool] = None
    health_endpoint: Optional[str] = None
    registration_data: Optional[Dict[str, Any]] = None
    supported_robot_types: Optional[List[str]] = None
    security_level: Optional[SecurityLevel] = None
    compliance_flags: Optional[Dict[str, Any]] = None
    enterprise_features: Optional[Dict[str, Any]] = None


class ModuleHealth(BaseModel):
    """Modelo para health check de módulo"""
    module_name: str
    health_status: ModuleHealth
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)
    consecutive_failures: int = Field(default=0, ge=0)


class ModulePerformance(BaseModel):
    """Modelo para métricas de performance de módulo"""
    module_name: str
    performance_score: float = Field(ge=0.0, le=1.0)
    performance_tier: PerformanceTier
    avg_processing_time_ms: int = Field(ge=0)
    success_rate_24h: float = Field(ge=0.0, le=100.0)
    error_count_24h: int = Field(ge=0)
    capacity_utilization: float = Field(ge=0.0, le=1.0)
    total_robots_processed: int = Field(ge=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ModuleResponse(BaseModel):
    """Respuesta de API para módulos"""
    module_id: str
    module_name: str
    module_version: str
    is_active: bool
    health_status: ModuleHealth
    performance_score: float
    performance_tier: PerformanceTier
    supported_robot_types: List[str]
    capacity_utilization: float
    total_robots_processed: int
    created_at: datetime
    updated_at: datetime


class ModuleListResponse(BaseModel):
    """Respuesta paginada de módulos"""
    modules: List[ModuleResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
