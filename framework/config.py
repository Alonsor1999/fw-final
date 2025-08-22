"""
Configuración del Framework MVP
"""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os


class Settings(BaseSettings):
    """Configuración principal del framework MVP"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql://framework_user:framework_pass@postgres:5432/framework_db"
    DATABASE_POOL_MIN_SIZE: int = 2
    DATABASE_POOL_MAX_SIZE: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    
    # PostgreSQL specific settings (for DatabaseManager)
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "framework_user"
    POSTGRES_PASSWORD: str = "framework_pass"
    POSTGRES_DB: str = "framework_db"
    
    # Database settings from .env
    DB_HOST: str = "postgres"
    DB_PORT: str = "5432"
    DB_NAME: str = "framework_db"
    DB_USER: str = "framework_user"
    DB_PASSWORD: str = "framework_pass"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_POOL_MIN_SIZE: int = 5
    REDIS_POOL_MAX_SIZE: int = 20
    REDIS_DEFAULT_TTL: int = 1800
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY_LENGTH: int = 32
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_HEALTH: str = "1000/minute"
    
    # Performance
    MAX_CONCURRENT_ROBOTS: int = 1000
    ROBOT_TIMEOUT_SECONDS: int = 1800
    CACHE_HIT_RATE_TARGET: float = 0.8
    
    # Monitoring
    HEALTH_CHECK_INTERVAL: int = 300  # 5 minutes
    PERFORMANCE_CHECK_INTERVAL: int = 900  # 15 minutes
    METRICS_RETENTION_DAYS: int = 30
    
    # Backup
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_INTERVAL_HOURS: int = 6
    
    # Email & OCR
    EMAIL_BATCH_SIZE: int = 50
    OCR_TIMEOUT_SECONDS: int = 300
    MAX_FILE_SIZE_MB: int = 10
    
    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CIRCUIT_BREAKER_TIMEOUT: int = 30
    
    # Logging
    LOG_FILE_PATH: str = "logs/framework.log"
    LOG_MAX_SIZE: str = "10MB"
    LOG_BACKUP_COUNT: str = "5"
    
    # Gmail settings
    GMAIL_EMAIL: str = "tu_email@gmail.com"
    GMAIL_PASSWORD: str = "tu_password"
    GMAIL_APP_PASSWORD: str = "tu_app_password"
    GMAIL_CLIENT_ID: str = "tu_client_id"
    GMAIL_CLIENT_SECRET: str = "tu_client_secret"
    GMAIL_REFRESH_TOKEN: str = "tu_refresh_token"
    
    # Outlook settings
    OUTLOOK_EMAIL: str = "tu_email@outlook.com"
    OUTLOOK_PASSWORD: str = "tu_password"
    OUTLOOK_CLIENT_ID: str = "tu_client_id"
    OUTLOOK_CLIENT_SECRET: str = "tu_client_secret"
    OUTLOOK_TENANT_ID: str = "tu_tenant_id"
    OUTLOOK_REFRESH_TOKEN: str = "tu_refresh_token"
    
    # RabbitMQ settings
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: str = "5672"
    RABBITMQ_USERNAME: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_EXCHANGE: str = "robot_exchange"
    RABBITMQ_QUEUE: str = "robot_queue"
    RABBITMQ_ROUTING_KEY: str = "robot.routing"
    
    # Web automation settings
    WEBDRIVER_PATH: str = "/usr/local/bin/chromedriver"
    BROWSER_HEADLESS: str = "true"
    BROWSER_TIMEOUT: str = "30"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: str = "30"
    MAX_RETRIES: str = "3"
    
    # API settings
    API_KEY: str = "tu_api_key"
    NOTIFICATION_EMAIL: str = "admin@tuempresa.com"
    SLACK_WEBHOOK_URL: str = "https://hooks.slack.com/services/xxx/yyy/zzz"
    METRICS_ENABLED: str = "true"
    METRICS_PORT: str = "9090"
    API_PORT: str = "8000"
    API_HOST: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables extra en lugar de fallar


# Performance Configuration
PERFORMANCE_CONFIG = {
    "database": {
        "connection_pools": {
            "read_pool_size": {"min": 2, "max": 10},
            "write_pool_size": {"min": 1, "max": 5}
        },
        "query_timeout": 30,
        "transaction_timeout": 60
    },
    "cache": {
        "redis_pool_size": {"min": 5, "max": 20},
        "default_ttl": 1800,
        "smart_ttl": {
            "module_health": 300,
            "robot_status": 60,
            "performance_scores": 600
        }
    },
    "circuit_breaker": {
        "failure_threshold": 5,
        "recovery_timeout": 60,
        "timeout": 30
    }
}

# Security Configuration
SECURITY_CONFIG = {
    "api_key_length": 32,
    "hash_algorithm": "SHA-256",
    "rate_limits": {
        "default": "100/minute",
        "health_check": "1000/minute",
        "bulk_operations": "10/minute"
    },
    "input_validation": {
        "max_payload_size": "10MB",
        "allowed_content_types": ["application/json"],
        "sql_injection_protection": True,
        "xss_protection": True
    },
    "audit_logging": {
        "log_level": "INFO",
        "include_request_body": False,
        "include_response_body": False,
        "retention_days": 90
    }
}

# Cache TTL Configuration
CACHE_TTL_CONFIG = {
    "module_health": 300,      # 5 minutes
    "robot_status": 60,        # 1 minute
    "performance_scores": 600, # 10 minutes
    "routing_table": 300,      # 5 minutes
    "user_sessions": 3600,     # 1 hour
    "configuration": 1800,     # 30 minutes
    "default": 1800           # 30 minutes
}

# Target Performance Metrics
PERFORMANCE_TARGETS = {
    "robot_creation": 50,      # ms
    "status_update": 25,       # ms
    "module_selection": 15,    # ms
    "progress_tracking": 10,   # ms
    "health_check": 10,        # ms
    "database_query": 25,      # ms
    "cache_operation": 5       # ms
}

# Initialize settings
settings = Settings()
