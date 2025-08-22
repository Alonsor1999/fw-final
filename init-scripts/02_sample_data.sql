-- Framework MVP Sample Data
-- Versión: 1.0 (MVP)
-- Fecha: 14 de Agosto, 2025

-- Insertar módulos de ejemplo
INSERT INTO module_registry (
    module_id,
    module_name,
    module_version,
    supported_robot_types,
    is_active,
    health_endpoint,
    registration_data,
    performance_score,
    performance_tier,
    health_status,
    security_level
) VALUES 
(
    'legal_module_v1.0_prod',
    'LegalModule',
    '1.0.0',
    ARRAY['legal_document_analysis', 'contract_review', 'compliance_check'],
    true,
    'http://legal-module:8080/health',
    '{"api_version": "v1", "features": ["ocr", "nlp", "classification"]}',
    0.95,
    'HIGH',
    'HEALTHY',
    'BASIC'
),
(
    'email_processor_v1.0_prod',
    'EmailProcessor',
    '1.0.0',
    ARRAY['email_classification', 'spam_detection', 'content_extraction'],
    true,
    'http://email-processor:8080/health',
    '{"api_version": "v1", "features": ["imap", "smtp", "filtering"]}',
    0.88,
    'HIGH',
    'HEALTHY',
    'BASIC'
),
(
    'ocr_engine_v1.0_prod',
    'OCREngine',
    '1.0.0',
    ARRAY['document_ocr', 'image_processing', 'text_extraction'],
    true,
    'http://ocr-engine:8080/health',
    '{"api_version": "v1", "features": ["tesseract", "image_preprocessing"]}',
    0.92,
    'HIGH',
    'HEALTHY',
    'BASIC'
),
(
    'data_analyzer_v1.0_prod',
    'DataAnalyzer',
    '1.0.0',
    ARRAY['data_analysis', 'report_generation', 'trend_analysis'],
    true,
    'http://data-analyzer:8080/health',
    '{"api_version": "v1", "features": ["pandas", "matplotlib", "statistics"]}',
    0.85,
    'MEDIUM',
    'HEALTHY',
    'BASIC'
),
(
    'web_scraper_v1.0_prod',
    'WebScraper',
    '1.0.0',
    ARRAY['web_scraping', 'data_extraction', 'link_following'],
    true,
    'http://web-scraper:8080/health',
    '{"api_version": "v1", "features": ["selenium", "beautifulsoup", "requests"]}',
    0.78,
    'MEDIUM',
    'DEGRADED',
    'BASIC'
);

-- Insertar robots de ejemplo
INSERT INTO robots (
    robot_id,
    robot_type,
    status,
    module_name,
    input_data,
    priority,
    processing_tier,
    completeness_score,
    confidence_score,
    source_reference,
    correlation_id
) VALUES 
(
    'robot_001_20241214_001',
    'legal_document_analysis',
    'COMPLETED',
    'LegalModule',
    '{"document_url": "https://example.com/contract.pdf", "analysis_type": "contract_review", "priority": "high"}',
    'HIGH',
    'STANDARD',
    0.95,
    0.92,
    'legal_department',
    'batch_001_20241214'
),
(
    'robot_002_20241214_002',
    'email_classification',
    'PROCESSING',
    'EmailProcessor',
    '{"email_id": "email_123", "sender": "client@example.com", "subject": "Contract Review Request"}',
    'NORMAL',
    'FAST',
    0.60,
    0.75,
    'email_system',
    'batch_001_20241214'
),
(
    'robot_003_20241214_003',
    'document_ocr',
    'PENDING',
    'OCREngine',
    '{"document_path": "/uploads/invoice.pdf", "language": "en", "quality": "high"}',
    'NORMAL',
    'STANDARD',
    0.00,
    0.00,
    'upload_system',
    'batch_001_20241214'
),
(
    'robot_004_20241214_004',
    'data_analysis',
    'FAILED',
    'DataAnalyzer',
    '{"dataset_path": "/data/sales_2024.csv", "analysis_type": "trend_analysis", "output_format": "pdf"}',
    'HIGH',
    'COMPLEX',
    0.30,
    0.45,
    'analytics_department',
    'batch_002_20241214'
),
(
    'robot_005_20241214_005',
    'web_scraping',
    'RETRYING',
    'WebScraper',
    '{"target_url": "https://competitor.com/pricing", "extract_fields": ["price", "features", "description"]}',
    'LOW',
    'STANDARD',
    0.20,
    0.30,
    'market_research',
    'batch_002_20241214'
);

-- Insertar ejecuciones de ejemplo
INSERT INTO robot_execute (
    execute_id,
    robot_id,
    module_name,
    execution_state,
    current_step,
    progress_percentage,
    step_category,
    total_steps,
    completed_steps,
    step_details,
    cpu_usage_percent,
    memory_usage_mb,
    efficiency_score,
    started_at,
    timeout_seconds
) VALUES 
(
    'exec_001_20241214_001',
    'robot_001_20241214_001',
    'LegalModule',
    'COMPLETED',
    'FINALIZATION',
    100,
    'FINALIZATION',
    5,
    5,
    '{"final_step": "report_generation", "output_size": "2.5MB", "processing_time": "45s"}',
    25.5,
    128,
    0.95,
    '2024-12-14 10:00:00',
    1800
),
(
    'exec_002_20241214_002',
    'robot_002_20241214_002',
    'EmailProcessor',
    'RUNNING',
    'PROCESSING',
    60,
    'PROCESSING',
    4,
    2,
    '{"current_step": "content_analysis", "words_processed": 1500, "confidence": 0.85}',
    45.2,
    256,
    0.88,
    '2024-12-14 10:15:00',
    1800
),
(
    'exec_003_20241214_003',
    'robot_003_20241214_003',
    'OCREngine',
    'PENDING',
    'INIT',
    0,
    'INIT',
    3,
    0,
    '{"status": "waiting_for_resources", "estimated_duration": "30s"}',
    0.0,
    0,
    1.0,
    '2024-12-14 10:30:00',
    1800
),
(
    'exec_004_20241214_004',
    'robot_004_20241214_004',
    'DataAnalyzer',
    'FAILED',
    'EXTERNAL_API',
    30,
    'EXTERNAL_API',
    6,
    2,
    '{"error": "dataset_not_found", "attempt": 3, "last_error": "File not found: /data/sales_2024.csv"}',
    65.8,
    512,
    0.45,
    '2024-12-14 09:45:00',
    1800
),
(
    'exec_005_20241214_005',
    'robot_005_20241214_005',
    'WebScraper',
    'RETRYING',
    'VALIDATION',
    10,
    'VALIDATION',
    4,
    0,
    '{"retry_reason": "connection_timeout", "retry_count": 2, "max_retries": 3}',
    15.3,
    64,
    0.30,
    '2024-12-14 10:20:00',
    1800
);

-- Actualizar robots con datos de ejecución
UPDATE robots SET 
    started_at = '2024-12-14 10:00:00',
    completed_at = '2024-12-14 10:00:45',
    processing_time_ms = 45000,
    performance_metrics = '{"cpu_peak": 25.5, "memory_peak": 128, "io_operations": 150}',
    cache_hit = false
WHERE robot_id = 'robot_001_20241214_001';

UPDATE robots SET 
    started_at = '2024-12-14 10:15:00',
    performance_metrics = '{"cpu_peak": 45.2, "memory_peak": 256, "io_operations": 75}',
    cache_hit = true,
    cache_key = 'email_classification_client_example_com_20241214'
WHERE robot_id = 'robot_002_20241214_002';

UPDATE robots SET 
    error_details = '{"type": "FILE_NOT_FOUND", "message": "Dataset file not found", "path": "/data/sales_2024.csv"}',
    error_category = 'DATA_ERROR',
    last_error_at = '2024-12-14 09:50:00',
    retry_count = 3
WHERE robot_id = 'robot_004_20241214_004';

UPDATE robots SET 
    error_details = '{"type": "CONNECTION_TIMEOUT", "message": "Target website not responding", "url": "https://competitor.com/pricing"}',
    error_category = 'NETWORK_ERROR',
    last_error_at = '2024-12-14 10:25:00',
    retry_count = 2
WHERE robot_id = 'robot_005_20241214_005';

-- Actualizar módulos con estadísticas
UPDATE module_registry SET 
    total_robots_processed = 150,
    total_processing_time_hours = 25.5,
    avg_processing_time_ms = 45000,
    capacity_utilization = 0.65,
    last_performance_check = NOW(),
    last_health_check = NOW()
WHERE module_name = 'LegalModule';

UPDATE module_registry SET 
    total_robots_processed = 320,
    total_processing_time_hours = 18.2,
    avg_processing_time_ms = 12000,
    capacity_utilization = 0.45,
    last_performance_check = NOW(),
    last_health_check = NOW()
WHERE module_name = 'EmailProcessor';

UPDATE module_registry SET 
    total_robots_processed = 89,
    total_processing_time_hours = 12.8,
    avg_processing_time_ms = 30000,
    capacity_utilization = 0.30,
    last_performance_check = NOW(),
    last_health_check = NOW()
WHERE module_name = 'OCREngine';

UPDATE module_registry SET 
    total_robots_processed = 45,
    total_processing_time_hours = 8.5,
    avg_processing_time_ms = 90000,
    capacity_utilization = 0.20,
    last_performance_check = NOW(),
    last_health_check = NOW(),
    error_count_24h = 3,
    success_rate_24h = 85.0,
    consecutive_failures = 2,
    last_error_message = 'Dataset file not found'
WHERE module_name = 'DataAnalyzer';

UPDATE module_registry SET 
    total_robots_processed = 67,
    total_processing_time_hours = 15.3,
    avg_processing_time_ms = 60000,
    capacity_utilization = 0.35,
    last_performance_check = NOW(),
    last_health_check = NOW(),
    error_count_24h = 8,
    success_rate_24h = 78.0,
    consecutive_failures = 3,
    last_error_message = 'Connection timeout to target website'
WHERE module_name = 'WebScraper';
