-- Framework MVP Database Schema
-- Versión: 1.0 (MVP)
-- Fecha: 14 de Agosto, 2025

-- Crear tipos enumerados
CREATE TYPE module_health_enum AS ENUM ('HEALTHY', 'DEGRADED', 'UNHEALTHY', 'UNKNOWN');
CREATE TYPE performance_tier_enum AS ENUM ('HIGH', 'MEDIUM', 'LOW', 'CRITICAL');
CREATE TYPE robot_status_enum AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'RETRYING');
CREATE TYPE priority_enum AS ENUM ('LOW', 'NORMAL', 'HIGH', 'CRITICAL');
CREATE TYPE processing_tier_enum AS ENUM ('FAST', 'STANDARD', 'COMPLEX', 'BULK');
CREATE TYPE security_classification_enum AS ENUM ('STANDARD', 'SENSITIVE', 'CONFIDENTIAL', 'RESTRICTED');
CREATE TYPE security_level_enum AS ENUM ('BASIC', 'STANDARD', 'ENHANCED', 'ENTERPRISE');
CREATE TYPE execution_state_enum AS ENUM ('PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'RETRYING', 'CANCELLED');
CREATE TYPE step_category_enum AS ENUM ('INIT', 'VALIDATION', 'PROCESSING', 'EXTERNAL_API', 'FINALIZATION');

-- Tabla: module_registry
CREATE TABLE module_registry (
    -- Core Fields
    module_id VARCHAR(100) PRIMARY KEY,
    module_name VARCHAR(100) NOT NULL UNIQUE,
    module_version VARCHAR(50) NOT NULL,
    supported_robot_types TEXT[] NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    health_endpoint VARCHAR(200),
    registration_data JSONB DEFAULT '{}',

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
    security_level security_level_enum DEFAULT 'BASIC',
    compliance_flags JSONB DEFAULT '{}',
    enterprise_features JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tabla: robots (Registro simple de robots)
CREATE TABLE robots (
    -- Core Fields
    robot_id VARCHAR(50) PRIMARY KEY,
    robot_name VARCHAR(100) NOT NULL,
    description TEXT,
    robot_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    
    -- Configuración opcional
    config_data JSONB DEFAULT '{}',
    tags TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tabla: robot_execute
CREATE TABLE robot_execute (
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

-- Índices optimizados para MVP
-- module_registry indexes
CREATE INDEX idx_module_active_performance ON module_registry(is_active, performance_tier, performance_score)
WHERE is_active = true;

CREATE INDEX idx_module_health_monitoring ON module_registry(health_status, last_health_check)
WHERE is_active = true;

CREATE INDEX idx_module_routing_optimization ON module_registry(supported_robot_types, capacity_utilization, performance_score)
WHERE is_active = true AND health_status = 'HEALTHY';

CREATE INDEX idx_module_error_tracking ON module_registry(error_count_24h, success_rate_24h, consecutive_failures);

-- robots indexes
CREATE INDEX idx_robots_status ON robots(status, created_at);

CREATE INDEX idx_robots_type ON robots(robot_type, status, created_at);

CREATE INDEX idx_robots_name ON robots(robot_name);

-- robot_execute indexes
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

-- Triggers para actualización automática de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_module_registry_updated_at BEFORE UPDATE ON module_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_robots_updated_at BEFORE UPDATE ON robots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Función para calcular performance score automáticamente
CREATE OR REPLACE FUNCTION calculate_performance_score(
    p_success_rate DECIMAL,
    p_avg_processing_time_ms INTEGER,
    p_error_count_24h INTEGER
) RETURNS DECIMAL AS $$
DECLARE
    score DECIMAL;
BEGIN
    -- Base score from success rate (0.0 to 1.0)
    score := p_success_rate / 100.0;
    
    -- Penalty for high processing time (normalize to 0-1, where lower is better)
    IF p_avg_processing_time_ms > 0 THEN
        score := score * (1.0 - LEAST(p_avg_processing_time_ms / 10000.0, 0.3));
    END IF;
    
    -- Penalty for errors (max 20% penalty)
    IF p_error_count_24h > 0 THEN
        score := score * (1.0 - LEAST(p_error_count_24h / 100.0, 0.2));
    END IF;
    
    RETURN GREATEST(score, 0.0);
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar performance tier
CREATE OR REPLACE FUNCTION update_performance_tier(p_score DECIMAL)
RETURNS performance_tier_enum AS $$
BEGIN
    IF p_score >= 0.8 THEN
        RETURN 'HIGH';
    ELSIF p_score >= 0.6 THEN
        RETURN 'MEDIUM';
    ELSIF p_score >= 0.4 THEN
        RETURN 'LOW';
    ELSE
        RETURN 'CRITICAL';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Comentarios para documentación
COMMENT ON TABLE module_registry IS 'Registro central de módulos de automatización con tracking de performance en tiempo real';
COMMENT ON TABLE robots IS 'Registro simple de robots con configuración básica';
COMMENT ON TABLE robot_execute IS 'Control granular de ejecución con resource monitoring y step-by-step tracking';

COMMENT ON COLUMN module_registry.performance_score IS 'Score de performance 0.0-1.0 calculado automáticamente';
COMMENT ON COLUMN module_registry.capacity_utilization IS '% capacidad utilizada 0.0-1.0 para load balancing';
COMMENT ON COLUMN robots.robot_name IS 'Nombre descriptivo del robot';
COMMENT ON COLUMN robots.config_data IS 'Configuración JSON del robot';
COMMENT ON COLUMN robot_execute.efficiency_score IS 'Score de eficiencia 0.0-1.0 actual vs estimated performance';
