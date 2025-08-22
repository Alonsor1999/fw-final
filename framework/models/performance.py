"""
Modelos para métricas de performance del Framework MVP
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MetricType(str, Enum):
    """Tipos de métricas"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    RESOURCE_USAGE = "resource_usage"
    SUCCESS_RATE = "success_rate"


class PerformanceMetrics(BaseModel):
    """Modelo para métricas de performance"""
    metric_type: MetricType
    value: float = Field(..., description="Valor de la métrica")
    unit: str = Field(..., description="Unidad de medida")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = Field(default_factory=dict, description="Contexto adicional")
    
    # Target performance
    target_value: Optional[float] = Field(None, description="Valor objetivo")
    threshold_warning: Optional[float] = Field(None, description="Umbral de advertencia")
    threshold_critical: Optional[float] = Field(None, description="Umbral crítico")
    
    # Analysis
    is_within_target: Optional[bool] = Field(None, description="¿Está dentro del objetivo?")
    performance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de performance")


class CacheMetrics(BaseModel):
    """Modelo para métricas de cache"""
    cache_key: str = Field(..., description="Clave de cache")
    hit_count: int = Field(default=0, ge=0, description="Número de hits")
    miss_count: int = Field(default=0, ge=0, description="Número de misses")
    total_requests: int = Field(default=0, ge=0, description="Total de requests")
    hit_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Tasa de hit")
    avg_response_time_ms: float = Field(default=0.0, ge=0.0, description="Tiempo promedio de respuesta")
    memory_usage_mb: Optional[float] = Field(None, ge=0.0, description="Uso de memoria")
    ttl_seconds: Optional[int] = Field(None, ge=0, description="TTL en segundos")
    last_accessed: Optional[datetime] = Field(None, description="Último acceso")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def calculate_hit_rate(self) -> float:
        """Calcular tasa de hit"""
        if self.total_requests > 0:
            return self.hit_count / self.total_requests
        return 0.0

    def update_metrics(self, is_hit: bool, response_time_ms: float):
        """Actualizar métricas de cache"""
        self.total_requests += 1
        if is_hit:
            self.hit_count += 1
        else:
            self.miss_count += 1
        
        # Actualizar tiempo promedio de respuesta
        if self.total_requests == 1:
            self.avg_response_time_ms = response_time_ms
        else:
            self.avg_response_time_ms = (
                (self.avg_response_time_ms * (self.total_requests - 1) + response_time_ms) / 
                self.total_requests
            )
        
        self.hit_rate = self.calculate_hit_rate()
        self.last_accessed = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class SystemMetrics(BaseModel):
    """Modelo para métricas del sistema"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # CPU metrics
    cpu_usage_percent: float = Field(ge=0.0, le=100.0, description="Uso de CPU")
    cpu_load_average: Optional[float] = Field(None, ge=0.0, description="Carga promedio de CPU")
    
    # Memory metrics
    memory_usage_mb: int = Field(ge=0, description="Uso de memoria en MB")
    memory_available_mb: int = Field(ge=0, description="Memoria disponible en MB")
    memory_usage_percent: float = Field(ge=0.0, le=100.0, description="Porcentaje de uso de memoria")
    
    # Disk metrics
    disk_usage_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Uso de disco")
    disk_io_read_mb: Optional[float] = Field(None, ge=0.0, description="I/O de lectura de disco")
    disk_io_write_mb: Optional[float] = Field(None, ge=0.0, description="I/O de escritura de disco")
    
    # Network metrics
    network_io_in_mb: Optional[float] = Field(None, ge=0.0, description="I/O de red entrada")
    network_io_out_mb: Optional[float] = Field(None, ge=0.0, description="I/O de red salida")
    
    # Application metrics
    active_connections: int = Field(default=0, ge=0, description="Conexiones activas")
    active_robots: int = Field(default=0, ge=0, description="Robots activos")
    active_modules: int = Field(default=0, ge=0, description="Módulos activos")
    
    # Performance metrics
    avg_response_time_ms: float = Field(default=0.0, ge=0.0, description="Tiempo promedio de respuesta")
    requests_per_second: float = Field(default=0.0, ge=0.0, description="Requests por segundo")
    error_rate_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Tasa de error")


class ModulePerformanceMetrics(BaseModel):
    """Modelo para métricas de performance de módulos"""
    module_name: str = Field(..., description="Nombre del módulo")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Processing metrics
    robots_processed: int = Field(default=0, ge=0, description="Robots procesados")
    avg_processing_time_ms: float = Field(default=0.0, ge=0.0, description="Tiempo promedio de procesamiento")
    success_rate: float = Field(default=100.0, ge=0.0, le=100.0, description="Tasa de éxito")
    error_count: int = Field(default=0, ge=0, description="Número de errores")
    
    # Capacity metrics
    capacity_utilization: float = Field(default=0.0, ge=0.0, le=1.0, description="Utilización de capacidad")
    queue_length: int = Field(default=0, ge=0, description="Longitud de cola")
    max_concurrent_robots: int = Field(default=0, ge=0, description="Máximo robots concurrentes")
    
    # Health metrics
    health_status: str = Field(default="UNKNOWN", description="Estado de salud")
    last_health_check: Optional[datetime] = Field(None, description="Último health check")
    consecutive_failures: int = Field(default=0, ge=0, description="Fallos consecutivos")
    
    # Performance score
    performance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Score de performance")
    performance_tier: str = Field(default="MEDIUM", description="Tier de performance")


class DatabaseMetrics(BaseModel):
    """Modelo para métricas de base de datos"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Connection metrics
    active_connections: int = Field(default=0, ge=0, description="Conexiones activas")
    idle_connections: int = Field(default=0, ge=0, description="Conexiones inactivas")
    max_connections: int = Field(default=0, ge=0, description="Máximo de conexiones")
    connection_utilization: float = Field(default=0.0, ge=0.0, le=1.0, description="Utilización de conexiones")
    
    # Query metrics
    queries_per_second: float = Field(default=0.0, ge=0.0, description="Queries por segundo")
    avg_query_time_ms: float = Field(default=0.0, ge=0.0, description="Tiempo promedio de query")
    slow_queries_count: int = Field(default=0, ge=0, description="Número de queries lentos")
    
    # Transaction metrics
    active_transactions: int = Field(default=0, ge=0, description="Transacciones activas")
    transactions_per_second: float = Field(default=0.0, ge=0.0, description="Transacciones por segundo")
    deadlocks_count: int = Field(default=0, ge=0, description="Número de deadlocks")
    
    # Cache metrics
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Tasa de hit de cache")
    cache_size_mb: Optional[float] = Field(None, ge=0.0, description="Tamaño de cache")


class MetricsSummary(BaseModel):
    """Resumen de métricas del sistema"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # System health
    system_health_score: float = Field(ge=0.0, le=1.0, description="Score de salud del sistema")
    overall_performance_score: float = Field(ge=0.0, le=1.0, description="Score general de performance")
    
    # Key metrics
    avg_response_time_ms: float = Field(ge=0.0, description="Tiempo promedio de respuesta")
    throughput_robots_per_minute: float = Field(ge=0.0, description="Throughput de robots por minuto")
    error_rate_percent: float = Field(ge=0.0, le=100.0, description="Tasa de error")
    cache_hit_rate: float = Field(ge=0.0, le=1.0, description="Tasa de hit de cache")
    
    # Resource utilization
    cpu_utilization: float = Field(ge=0.0, le=100.0, description="Utilización de CPU")
    memory_utilization: float = Field(ge=0.0, le=100.0, description="Utilización de memoria")
    database_utilization: float = Field(ge=0.0, le=100.0, description="Utilización de base de datos")
    
    # Active components
    active_robots: int = Field(ge=0, description="Robots activos")
    active_modules: int = Field(ge=0, description="Módulos activos")
    healthy_modules: int = Field(ge=0, description="Módulos saludables")
    
    # Performance targets
    targets_met: int = Field(ge=0, description="Objetivos cumplidos")
    total_targets: int = Field(ge=0, description="Total de objetivos")
    performance_compliance: float = Field(ge=0.0, le=1.0, description="Cumplimiento de performance")
