"""
Modelos para ejecución de robots del Framework MVP
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from .base import TimestampedModel, PerformanceModel, ErrorModel


class ExecutionState(str, Enum):
    """Estados de ejecución"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class StepCategory(str, Enum):
    """Categorías de pasos de ejecución"""
    INIT = "INIT"
    VALIDATION = "VALIDATION"
    PROCESSING = "PROCESSING"
    EXTERNAL_API = "EXTERNAL_API"
    FINALIZATION = "FINALIZATION"


class RobotExecute(TimestampedModel, PerformanceModel, ErrorModel):
    """Modelo principal de ejecución de robot"""
    execute_id: str = Field(..., description="Identificador de sesión ejecución")
    robot_id: str = Field(..., description="ID del robot asociado")
    module_name: str = Field(..., description="Nombre del módulo ejecutando")
    execution_state: ExecutionState = Field(default=ExecutionState.PENDING, description="Estado de ejecución")
    current_step: Optional[str] = Field(None, description="Paso actual")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="Porcentaje de progreso")
    
    # MVP Step Tracking
    step_category: StepCategory = Field(default=StepCategory.INIT, description="Categoría del step actual")
    total_steps: int = Field(default=1, ge=1, description="Total de steps planificados")
    completed_steps: int = Field(default=0, ge=0, description="Steps completados")
    step_details: Dict[str, Any] = Field(default_factory=dict, description="Detalles del step actual")
    step_start_time: Optional[datetime] = Field(None, description="Tiempo de inicio del step")
    step_duration_ms: Optional[int] = Field(None, ge=0, description="Duración del step actual en ms")
    
    # Resource Monitoring
    cpu_usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="% CPU utilizado")
    memory_usage_mb: Optional[int] = Field(None, ge=0, description="MB memoria utilizada")
    disk_io_mb: Optional[int] = Field(None, ge=0, description="MB de I/O de disco")
    network_io_mb: Optional[int] = Field(None, ge=0, description="MB de I/O de red")
    resource_peak_usage: Dict[str, Any] = Field(default_factory=dict, description="Picos de recursos")
    
    # Performance Tracking
    throughput_items_per_sec: Optional[float] = Field(None, ge=0.0, description="Items procesados por segundo")
    processing_rate: Optional[float] = Field(None, ge=0.0, description="Tasa de procesamiento")
    efficiency_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Score de eficiencia")
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Tiempo de inicio")
    completed_at: Optional[datetime] = Field(None, description="Tiempo de finalización")
    estimated_completion_at: Optional[datetime] = Field(None, description="Estimación de finalización")
    duration_ms: Optional[int] = Field(None, ge=0, description="Duración total en ms")
    
    # Error Management
    max_retries: int = Field(default=3, ge=0, description="Máximo número de reintentos")
    last_retry_at: Optional[datetime] = Field(None, description="Último reintento")
    timeout_seconds: int = Field(default=1800, ge=1, description="Timeout en segundos")
    error_message: Optional[str] = Field(None, description="Mensaje de error")
    error_stack_trace: Optional[str] = Field(None, description="Stack trace del error")
    
    # Evolution Path
    execution_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos de ejecución")
    contains_sensitive_data: bool = Field(default=False, description="Contiene datos sensibles")
    compliance_context: Dict[str, Any] = Field(default_factory=dict, description="Contexto de compliance")
    
    # External Dependencies
    external_api_calls: int = Field(default=0, ge=0, description="Número de API calls externas")
    external_api_duration_ms: int = Field(default=0, ge=0, description="Tiempo total en APIs externas")
    external_api_failures: int = Field(default=0, ge=0, description="Fallos en APIs externas")

    @validator('execute_id')
    def validate_execute_id(cls, v):
        """Validar formato del execute_id"""
        if not v or len(v) > 50:
            raise ValueError('execute_id debe tener entre 1 y 50 caracteres')
        return v

    @validator('progress_percentage')
    def validate_progress(cls, v):
        """Validar porcentaje de progreso"""
        if not 0 <= v <= 100:
            raise ValueError('progress_percentage debe estar entre 0 y 100')
        return v

    @validator('efficiency_score')
    def validate_efficiency(cls, v):
        """Validar score de eficiencia"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('efficiency_score debe estar entre 0.0 y 1.0')
        return v

    @validator('cpu_usage_percent')
    def validate_cpu_usage(cls, v):
        """Validar uso de CPU"""
        if v is not None and not 0.0 <= v <= 100.0:
            raise ValueError('cpu_usage_percent debe estar entre 0.0 y 100.0')
        return v

    def is_active(self) -> bool:
        """Verificar si la ejecución está activa"""
        return self.execution_state in [
            ExecutionState.PENDING, 
            ExecutionState.RUNNING, 
            ExecutionState.RETRYING,
            ExecutionState.PAUSED
        ]

    def is_completed(self) -> bool:
        """Verificar si la ejecución está completada"""
        return self.execution_state in [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED]

    def can_retry(self) -> bool:
        """Verificar si puede reintentarse"""
        return (
            self.retry_count < self.max_retries and 
            self.execution_state in [ExecutionState.FAILED, ExecutionState.RETRYING]
        )

    def get_elapsed_time_ms(self) -> Optional[int]:
        """Obtener tiempo transcurrido en ms"""
        if self.started_at:
            if self.completed_at:
                return int((self.completed_at - self.started_at).total_seconds() * 1000)
            else:
                return int((datetime.utcnow() - self.started_at).total_seconds() * 1000)
        return None

    def get_step_progress(self) -> float:
        """Obtener progreso basado en steps completados"""
        if self.total_steps > 0:
            return (self.completed_steps / self.total_steps) * 100
        return 0.0

    def update_progress(self, completed_steps: int, current_step: str = None):
        """Actualizar progreso de ejecución"""
        self.completed_steps = min(completed_steps, self.total_steps)
        self.progress_percentage = int(self.get_step_progress())
        if current_step:
            self.current_step = current_step
        self.updated_at = datetime.utcnow()

    def add_step_detail(self, key: str, value: Any):
        """Agregar detalle al step actual"""
        self.step_details[key] = value
        self.updated_at = datetime.utcnow()

    def record_resource_usage(self, cpu_percent: float, memory_mb: int, disk_io_mb: int = 0, network_io_mb: int = 0):
        """Registrar uso de recursos"""
        self.cpu_usage_percent = cpu_percent
        self.memory_usage_mb = memory_mb
        self.disk_io_mb = disk_io_mb
        self.network_io_mb = network_io_mb
        
        # Actualizar picos de recursos
        if 'max_cpu' not in self.resource_peak_usage or cpu_percent > self.resource_peak_usage['max_cpu']:
            self.resource_peak_usage['max_cpu'] = cpu_percent
        if 'max_memory' not in self.resource_peak_usage or memory_mb > self.resource_peak_usage['max_memory']:
            self.resource_peak_usage['max_memory'] = memory_mb
        
        self.updated_at = datetime.utcnow()


class ExecutionCreate(BaseModel):
    """Modelo para crear una ejecución"""
    robot_id: str = Field(..., description="ID del robot a ejecutar")
    module_name: str = Field(..., description="Nombre del módulo")
    total_steps: int = Field(default=1, ge=1, description="Total de steps planificados")
    timeout_seconds: int = Field(default=1800, ge=1, description="Timeout en segundos")
    max_retries: int = Field(default=3, ge=0, description="Máximo número de reintentos")
    contains_sensitive_data: bool = Field(default=False, description="Contiene datos sensibles")
    compliance_context: Dict[str, Any] = Field(default_factory=dict, description="Contexto de compliance")

    @validator('robot_id')
    def validate_robot_id(cls, v):
        """Validar ID del robot"""
        if not v or len(v) > 50:
            raise ValueError('robot_id debe tener entre 1 y 50 caracteres')
        return v


class ExecutionUpdate(BaseModel):
    """Modelo para actualizar una ejecución"""
    execution_state: Optional[ExecutionState] = None
    current_step: Optional[str] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    step_category: Optional[StepCategory] = None
    completed_steps: Optional[int] = Field(None, ge=0)
    step_details: Optional[Dict[str, Any]] = None
    step_duration_ms: Optional[int] = Field(None, ge=0)
    cpu_usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_usage_mb: Optional[int] = Field(None, ge=0)
    efficiency_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    error_message: Optional[str] = None
    error_stack_trace: Optional[str] = None


class ExecutionResponse(BaseModel):
    """Respuesta de API para ejecuciones"""
    execute_id: str
    robot_id: str
    module_name: str
    execution_state: ExecutionState
    progress_percentage: int
    current_step: Optional[str]
    step_category: StepCategory
    completed_steps: int
    total_steps: int
    started_at: datetime
    estimated_completion_at: Optional[datetime]
    duration_ms: Optional[int]
    efficiency_score: float
    created_at: datetime
    updated_at: datetime


class ExecutionListResponse(BaseModel):
    """Respuesta paginada de ejecuciones"""
    executions: List[ExecutionResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
