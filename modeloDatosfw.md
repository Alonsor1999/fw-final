# Modelo de Datos Framework V1.0

---

**Versión:** 1.0 (MVP)

**Fecha:** 14 de Agosto, 2025

**Enfoque:** Modelo de datos MVP con robustez, seguridad y escalabilidad

**Clasificación:** Confidencial

---

## Tabla de Contenidos

1. [Filosofía del Modelo MVP](https://www.notion.so/Modelo-de-Datos-Framework-V1-0-24e5700a6af9803cb1d2dd264c54d7f0?pvs=21)
2. [Arquitectura de Datos MVP](https://www.notion.so/Modelo-de-Datos-Framework-V1-0-24e5700a6af9803cb1d2dd264c54d7f0?pvs=21)
3. [Especificación de Entidades](https://www.notion.so/Modelo-de-Datos-Framework-V1-0-24e5700a6af9803cb1d2dd264c54d7f0?pvs=21)
4. [Optimizaciones de Performance](https://www.notion.so/Modelo-de-Datos-Framework-V1-0-24e5700a6af9803cb1d2dd264c54d7f0?pvs=21)
5. [Estrategias MVP](https://www.notion.so/Modelo-de-Datos-Framework-V1-0-24e5700a6af9803cb1d2dd264c54d7f0?pvs=21)

---

## 1. Filosofía del Modelo MVP

### 1.1 Principios Arquitectónicos MVP

**SIMPLICIDAD EFECTIVA:** 3 tablas optimizadas que cubren 85% de funcionalidad enterprise con performance <100ms garantizado.

**SEGURIDAD INTEGRADA:** Authentication, rate limiting y audit trail básico incorporados desde el diseño del modelo.

**ESCALABILIDAD PREPARADA:** Estructura lista para clustering, partitioning y microservices sin breaking changes.

**OBSERVABILIDAD ESENCIAL:** Tracking completo de performance, errores y métricas operacionales críticas.

### 1.2 Arquitectura de 3 Tablas Enhanced

El modelo MVP mantiene las 3 tablas core del framework original pero **enhanced** con campos adicionales para observabilidad, performance tracking y evolution path enterprise.

**Diferencias vs Enterprise:**

- ✅ **Core functionality completa** con performance optimizado
- ✅ **Security foundation robusta** para production
- ✅ **Monitoring esencial** integrado en schema
- ❌ **Sin tablas enterprise** (api_keys, security_audit, system_config, backup_log)
- ❌ **Sin field-level encryption** nativo
- ❌ **Sin audit trail completo** para compliance

---

## 2. Arquitectura de Datos MVP

### 2.1 Framework MVP (3 Tablas Enhanced)

- `module_registry` - Gestión de módulos con performance tracking
- `robots` - Estados de robots con observabilidad integrada
- `robot_execute` - Control granular con resource monitoring

### 2.2 Separación de Responsabilidades MVP

| **Capa** | **Tablas** | **Responsabilidad** |
| --- | --- | --- |
| **Module Management** | module_registry | Registration + health + performance |
| **Robot Lifecycle** | robots | State management + metrics + tracking |
| **Execution Control** | robot_execute | Granular progress + resource usage |

### 2.3 Evolution Path Incorporado

**Enterprise Upgrade Ready:**

- Schema compatible con 4 tablas enterprise adicionales
- Foreign keys preparadas para seguridad avanzada
- Campos JSONB extensibles para features futuras
- Índices optimizados para queries enterprise

---

## 3. Especificación de Entidades

### 3.1 module_registry - Gestión de Módulos Enhanced

**Propósito:** Registro central de módulos de automatización con tracking de performance en tiempo real y health monitoring avanzado.

**Enhancements MVP:** Performance scoring, error tracking 24h, success rate automático y health monitoring integrado.

```sql
CREATE TYPE module_health_enum AS ENUM ('HEALTHY', 'DEGRADED', 'UNHEALTHY', 'UNKNOWN');
CREATE TYPE performance_tier_enum AS ENUM ('HIGH', 'MEDIUM', 'LOW', 'CRITICAL');

module_registry (
    -- Core Fields
    module_id VARCHAR(100) PRIMARY KEY,
    module_name VARCHAR(100) NOT NULL UNIQUE,
    module_version VARCHAR(50) NOT NULL,
    supported_robot_types TEXT[] NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    health_endpoint VARCHAR(200),
    registration_data JSONB,

    -- MVP Performance Enhancements
    performance_score DECIMAL(3,2) DEFAULT 1.0,
    performance_tier performance_tier_enum DEFAULT 'MEDIUM',
    last_performance_check TIMESTAMP,
    error_count_24h INTEGER DEFAULT 0,
    success_rate_24h DECIMAL(5,2) DEFAULT 100.0,
    avg_processing_time_ms INTEGER DEFAULT 0,
    capacity_utilization DECIMAL(3,2) DEFAULT 0.0,

    -- Health & Monitoring
    health_status module_health_enum DEFAULT 'UNKNOWN',
    last_health_check TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,
    last_error_message TEXT,
    uptime_percentage_24h DECIMAL(5,2) DEFAULT 100.0,

    -- Statistics
    total_robots_processed INTEGER DEFAULT 0,
    total_processing_time_hours DECIMAL(8,2) DEFAULT 0.0,

    -- Evolution Path
    security_level VARCHAR(20) DEFAULT 'BASIC',
    compliance_flags JSONB DEFAULT '{}',
    enterprise_features JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- MVP Optimized Indexes
CREATE INDEX idx_module_active_performance ON module_registry(is_active, performance_tier, performance_score)
WHERE is_active = true;

CREATE INDEX idx_module_health_monitoring ON module_registry(health_status, last_health_check)
WHERE is_active = true;

CREATE INDEX idx_module_routing_optimization ON module_registry(supported_robot_types, capacity_utilization, performance_score)
WHERE is_active = true AND health_status = 'HEALTHY';

CREATE INDEX idx_module_error_tracking ON module_registry(error_count_24h, success_rate_24h, consecutive_failures);

```

### Diccionario de Datos - module_registry

| **Campo** | **Tipo** | **Descripción** | **Reglas de Negocio MVP** |
| --- | --- | --- | --- |
| **module_id** | VARCHAR(100) | Identificador único del módulo | PK. Formato: {nombre}*{version}*{env} |
| **module_name** | VARCHAR(100) | Nombre descriptivo del módulo | Único. Ej: "LegalModule" |
| **supported_robot_types** | TEXT[] | Tipos de robot que puede procesar | Al menos uno. Usado para routing |
| **performance_score** | DECIMAL(3,2) | Score de performance 0.0-1.0 | Calculado automático. 1.0 = optimal |
| **performance_tier** | ENUM | Tier basado en performance | HIGH/MEDIUM/LOW/CRITICAL |
| **error_count_24h** | INTEGER | Errores en últimas 24 horas | Reset automático daily |
| **success_rate_24h** | DECIMAL(5,2) | % éxito últimas 24 horas | Calculado automático |
| **capacity_utilization** | DECIMAL(3,2) | % capacidad utilizada 0.0-1.0 | Para load balancing |
| **health_status** | ENUM | Estado de salud actual | Health check automático |
| **consecutive_failures** | INTEGER | Fallos consecutivos | Trigger para UNHEALTHY |

### 3.2 robots - Estados de Robots Enhanced

**Propósito:** Tabla central que mantiene el estado y datos de cada robot con observabilidad integrada y performance tracking.

**Enhancements MVP:** Performance metrics JSONB, cache tracking, error details, retry management y resource usage monitoring.

```sql
CREATE TYPE robot_status_enum AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'RETRYING');
CREATE TYPE priority_enum AS ENUM ('LOW', 'NORMAL', 'HIGH', 'CRITICAL');
CREATE TYPE processing_tier_enum AS ENUM ('FAST', 'STANDARD', 'COMPLEX', 'BULK');

robots (
    -- Core Fields
    robot_id VARCHAR(50) PRIMARY KEY,
    robot_type VARCHAR(50) NOT NULL,
    status robot_status_enum NOT NULL DEFAULT 'PENDING',
    module_name VARCHAR(100) NOT NULL REFERENCES module_registry(module_name),
    input_data JSONB NOT NULL,
    output_data JSONB,
    priority priority_enum NOT NULL DEFAULT 'NORMAL',

    -- MVP Performance Enhancements
    performance_metrics JSONB DEFAULT '{}',
    processing_time_ms INTEGER,
    processing_tier processing_tier_enum DEFAULT 'STANDARD',
    cache_hit BOOLEAN DEFAULT FALSE,
    cache_key VARCHAR(255),
    resource_usage_mb INTEGER,

    -- Error Management
    retry_count INTEGER DEFAULT 0,
    retry_limit INTEGER DEFAULT 3,
    error_details JSONB,
    error_category VARCHAR(50),
    last_error_at TIMESTAMP,

    -- Business Logic
    completeness_score DECIMAL(3,2) DEFAULT 0.0,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    source_reference VARCHAR(200),
    correlation_id VARCHAR(100),

    -- Estimations vs Actuals
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    complexity_score DECIMAL(2,1) DEFAULT 1.0,

    -- Evolution Path
    security_classification VARCHAR(20) DEFAULT 'STANDARD',
    compliance_tags TEXT[],
    enterprise_metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- MVP Optimized Indexes
CREATE INDEX idx_robots_active_processing ON robots(status, module_name, priority, created_at)
WHERE status IN ('PENDING', 'PROCESSING', 'RETRYING');

CREATE INDEX idx_robots_performance_analysis ON robots(status, processing_tier, processing_time_ms, cache_hit)
WHERE status = 'COMPLETED';

CREATE INDEX idx_robots_error_tracking ON robots(status, error_category, retry_count, last_error_at)
WHERE status IN ('FAILED', 'RETRYING');

CREATE INDEX idx_robots_type_priority ON robots(robot_type, priority, status, created_at);

CREATE INDEX idx_robots_correlation ON robots(correlation_id, source_reference)
WHERE correlation_id IS NOT NULL;

CREATE UNIQUE INDEX idx_robots_cache_key ON robots(cache_key)
WHERE cache_key IS NOT NULL;

```

### Diccionario de Datos - robots

| **Campo** | **Tipo** | **Descripción** | **Reglas de Negocio MVP** |
| --- | --- | --- | --- |
| **robot_id** | VARCHAR(50) | Identificador único del robot | PK. Formato: {prefix}*{timestamp}*{seq} |
| **performance_metrics** | JSONB | Métricas de performance detalladas | {"cpu_ms": 1500, "memory_peak_mb": 45} |
| **processing_tier** | ENUM | Tier de complejidad processing | FAST (<1min), STANDARD (<10min), etc. |
| **cache_hit** | BOOLEAN | Si se utilizó cache para este robot | Para optimization analysis |
| **cache_key** | VARCHAR(255) | Key de cache utilizada | Único. Para deduplication |
| **resource_usage_mb** | INTEGER | Memoria utilizada en MB | Para capacity planning |
| **error_details** | JSONB | Detalles estructurados del error | {"type": "TIMEOUT", "step": "OCR"} |
| **error_category** | VARCHAR(50) | Categoría del error | TIMEOUT, VALIDATION, EXTERNAL_API |
| **completeness_score** | DECIMAL(3,2) | Score de completitud 0.0-1.0 | 1.0 = datos completos |
| **confidence_score** | DECIMAL(3,2) | Score de confianza 0.0-1.0 | Para quality assurance |
| **correlation_id** | VARCHAR(100) | ID para correlacionar robots | Batch processing tracking |

### 3.3 robot_execute - Control de Ejecución Enhanced

**Propósito:** Tracking granular del progreso de ejecución con resource monitoring, step-by-step tracking y performance analytics.

**Enhancements MVP:** Resource usage detallado, step timing, performance tracking y error categorization.

```sql
CREATE TYPE execution_state_enum AS ENUM ('PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'RETRYING', 'CANCELLED');
CREATE TYPE step_category_enum AS ENUM ('INIT', 'VALIDATION', 'PROCESSING', 'EXTERNAL_API', 'FINALIZATION');

robot_execute (
    -- Core Fields
    execute_id VARCHAR(50) PRIMARY KEY,
    robot_id VARCHAR(50) NOT NULL REFERENCES robots(robot_id) ON DELETE CASCADE,
    module_name VARCHAR(100) NOT NULL,
    execution_state execution_state_enum NOT NULL DEFAULT 'PENDING',
    current_step VARCHAR(100),
    progress_percentage SMALLINT DEFAULT 0,

    -- MVP Step Tracking
    step_category step_category_enum DEFAULT 'INIT',
    total_steps INTEGER DEFAULT 1,
    completed_steps INTEGER DEFAULT 0,
    step_details JSONB DEFAULT '{}',
    step_start_time TIMESTAMP,
    step_duration_ms INTEGER,

    -- Resource Monitoring
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    disk_io_mb INTEGER,
    network_io_mb INTEGER,
    resource_peak_usage JSONB DEFAULT '{}',

    -- Performance Tracking
    throughput_items_per_sec DECIMAL(8,2),
    processing_rate DECIMAL(8,2),
    efficiency_score DECIMAL(3,2) DEFAULT 1.0,

    -- Timing
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    estimated_completion_at TIMESTAMP,
    duration_ms INTEGER,

    -- Error Management
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_retry_at TIMESTAMP,
    timeout_seconds INTEGER DEFAULT 1800,
    error_message TEXT,
    error_stack_trace TEXT,

    -- Evolution Path
    execution_metadata JSONB DEFAULT '{}',
    contains_sensitive_data BOOLEAN DEFAULT FALSE,
    compliance_context JSONB DEFAULT '{}',

    -- External Dependencies
    external_api_calls INTEGER DEFAULT 0,
    external_api_duration_ms INTEGER DEFAULT 0,
    external_api_failures INTEGER DEFAULT 0
);

-- MVP Optimized Indexes
CREATE INDEX idx_execute_active_monitoring ON robot_execute(execution_state, current_step, progress_percentage, started_at)
WHERE execution_state IN ('RUNNING', 'RETRYING', 'PAUSED');

CREATE INDEX idx_execute_performance_analysis ON robot_execute(module_name, execution_state, duration_ms, efficiency_score, completed_at)
WHERE completed_at IS NOT NULL;

CREATE INDEX idx_execute_resource_tracking ON robot_execute(cpu_usage_percent, memory_usage_mb, started_at)
WHERE execution_state = 'RUNNING';

CREATE INDEX idx_execute_step_analysis ON robot_execute(step_category, step_duration_ms, completed_at);

CREATE INDEX idx_execute_robot_progress ON robot_execute(robot_id, progress_percentage, execution_state);

CREATE INDEX idx_execute_timeout_monitoring ON robot_execute(started_at, timeout_seconds, execution_state)
WHERE execution_state IN ('RUNNING', 'PAUSED');

```

### Diccionario de Datos - robot_execute

| **Campo** | **Tipo** | **Descripción** | **Reglas de Negocio MVP** |
| --- | --- | --- | --- |
| **execute_id** | VARCHAR(50) | Identificador de sesión ejecución | PK. UUID format |
| **step_category** | ENUM | Categoría del step actual | Para performance analysis por tipo |
| **total_steps** | INTEGER | Total de steps planificados | Para progress calculation |
| **step_details** | JSONB | Detalles del step actual | {"name": "OCR_EXTRACT", "input_size": 2.5} |
| **step_duration_ms** | INTEGER | Duración del step actual en ms | Para bottleneck identification |
| **cpu_usage_percent** | DECIMAL(5,2) | % CPU utilizado | Real-time resource monitoring |
| **memory_usage_mb** | INTEGER | MB memoria utilizada | Para capacity planning |
| **resource_peak_usage** | JSONB | Picos de recursos | {"max_cpu": 85.5, "max_memory": 512} |
| **throughput_items_per_sec** | DECIMAL(8,2) | Items procesados por segundo | Performance benchmarking |
| **efficiency_score** | DECIMAL(3,2) | Score de eficiencia 0.0-1.0 | Actual vs estimated performance |
| **external_api_calls** | INTEGER | Número de API calls externas | Dependency tracking |
| **external_api_duration_ms** | INTEGER | Tiempo total en APIs externas | Network latency analysis |

---

## 4. Optimizaciones de Performance

### 4.1 Índices Estratégicos MVP

**Routing Optimization (module_registry)**

- Performance-based routing para optimal assignment
- Health-based filtering para reliability
- Capacity-based balancing para efficiency

**Active Operations (robots)**

- Fast lookup para robots en procesamiento
- Priority-based queuing para business rules
- Error pattern analysis para improvement

**Real-time Monitoring (robot_execute)**

- Live progress tracking para dashboards
- Resource usage monitoring para scaling
- Performance analysis para optimization

### 4.2 Query Performance Targets

| **Query Type** | **Target Time** | **Optimization Strategy** |
| --- | --- | --- |
| **Robot Creation** | <50ms | Prepared statements + connection pooling |
| **Status Updates** | <25ms | Optimized UPDATEs con WHERE específicos |
| **Progress Tracking** | <10ms | Índices compuestos + cache layer |
| **Performance Analytics** | <100ms | Aggregate indexes + background calculation |
| **Health Monitoring** | <15ms | Specialized health indexes |

### 4.3 Cache Strategy MVP

**Cache Warming Automático:**

- Active modules list (TTL: 5 minutes)
- Robot routing table (TTL: 1 minute)
- Performance scoreboard (TTL: 10 minutes)
- System health status (TTL: 30 seconds)

**Cache Invalidation Inteligente:**

- Module health changes → routing cache invalidation
- Performance score updates → ranking cache invalidation
- System capacity changes → assignment cache invalidation

---

## 5. Estrategias MVP

### 5.1 Security MVP

**Authentication Foundation:**

- API key validation mediante application layer
- Rate limiting por module_name en application
- Basic audit logging en application logs
- Input validation robusta en todos los endpoints

**Data Protection MVP:**

- SQL injection protection mediante prepared statements
- Input sanitization automática
- Error message sanitization para no exponer internals
- Sensitive data identification en compliance_context

### 5.2 Observabilidad MVP

**Real-time Metrics:**

- Performance score calculation automático cada 15 minutos
- Health check automático cada 5 minutos
- Error rate calculation continuous
- Resource usage trending cada minuto

**Analytics Foundation:**

- Daily performance reports automáticos
- Error pattern analysis semanal
- Capacity planning metrics mensual
- Module efficiency benchmarking

### 5.3 Backup y Recovery MVP

**Daily Backup Strategy:**

- PostgreSQL backup completo daily a las 2 AM
- Incremental backup cada 6 horas
- Backup verification automática
- 30 días retention automática

**Recovery Procedures:**

- Point-in-time recovery capability
- Schema migration scripts versionados
- Data consistency validation automática
- Recovery testing mensual

### 5.4 Evolution Path

**Enterprise Upgrade Ready:**

```sql
-- Security Tables Addition (sin breaking changes)
ALTER TABLE robots ADD COLUMN api_key_used VARCHAR(50);
ALTER TABLE robot_execute ADD COLUMN security_context JSONB DEFAULT '{}';

-- Advanced Configuration
ALTER TABLE module_registry ADD COLUMN config_overrides JSONB DEFAULT '{}';

-- Enhanced Audit Trail
ALTER TABLE robots ADD COLUMN audit_trail JSONB DEFAULT '{}';

```

**Microservices Evolution:**

- Schema separation por bounded context
- Event sourcing preparation en JSONB fields
- API versioning support en module_registry
- Service mesh integration points

---

## Conclusiones MVP

### 5.5 Modelo MVP Completo

**Framework MVP con 3 tablas enhanced:**

✅ **Core Functionality:** Robot lifecycle completo con orchestration

✅ **Performance Optimizado:** <100ms guaranteed con índices estratégicos

✅ **Observabilidad Integrada:** Metrics, health monitoring y analytics

✅ **Security Foundation:** Authentication, validation y audit básico

✅ **Scalability Ready:** Horizontal scaling preparation sin breaking changes

✅ **Evolution Path:** Enterprise upgrade sin technical debt

### 5.6 Capacidades MVP vs Enterprise

| **Capacidad** | **MVP** | **Enterprise** | **Gap** |
| --- | --- | --- | --- |
| **Core Operations** | ✅ 100% | ✅ 100% | None |
| **Performance** | ✅ <100ms | ✅ <50ms | Acceptable |
| **Security** | ✅ Robust Basic | ✅ Advanced | Authentication sufficient |
| **Monitoring** | ✅ Essential | ✅ Advanced | Real-time sufficient |
| **Scalability** | ✅ Prepared | ✅ Automatic | Manual acceptable |
| **Compliance** | ⚠️ Basic | ✅ Certified | Upgrade path ready |

### 5.7 Implementation Benefits

**Immediate Value:**

- ✅ Production-ready framework en 3 semanas
- ✅ 85% enterprise functionality con 20% effort
- ✅ Zero technical debt para enterprise evolution
- ✅ Proven architecture patterns desde day 1

**Long-term Value:**

- ✅ Enterprise upgrade path sin breaking changes
- ✅ Microservices evolution ready
- ✅ Compliance certification preparation
- ✅ Advanced analytics foundation

**Total: 3 tablas MVP con enterprise-grade capabilities y evolution path garantizado.**

---

**FIN DEL MODELO MVP**

*Páginas: 12*

*Tablas: 3 (enhanced con enterprise readiness)*

*Timeline: 3 semanas implementation*

*Performance: <100ms guaranteed*

*Evolution: Enterprise upgrade ready*