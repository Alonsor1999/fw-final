"""
Configuración para RabbitMQ
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de RabbitMQ
RABBITMQ_CONFIG = {
    'host': os.getenv('RABBITMQ_HOST', 'localhost'),
    'port': int(os.getenv('RABBITMQ_PORT', 5672)),
    'username': os.getenv('RABBITMQ_USERNAME', 'guest'),
    'password': os.getenv('RABBITMQ_PASSWORD', 'guest'),
    'virtual_host': os.getenv('RABBITMQ_VHOST', '/'),
    'queue_name': os.getenv('RABBITMQ_QUEUE', 'pdf_processing_queue'),
    'exchange': os.getenv('RABBITMQ_EXCHANGE', ''),
    'routing_key': os.getenv('RABBITMQ_ROUTING_KEY', 'pdf_processing_queue'),
    'summary_queue': os.getenv('RABBITMQ_SUMMARY_QUEUE', 'email_summary_queue')
}

# Configuración de conexión
RABBITMQ_CONNECTION_CONFIG = {
    'host': RABBITMQ_CONFIG['host'],
    'port': RABBITMQ_CONFIG['port'],
    'username': RABBITMQ_CONFIG['username'],
    'password': RABBITMQ_CONFIG['password'],
    'virtual_host': RABBITMQ_CONFIG['virtual_host']
}

def get_rabbitmq_config():
    """Obtener configuración de RabbitMQ"""
    return RABBITMQ_CONFIG.copy()

def get_connection_config():
    """Obtener configuración de conexión"""
    return RABBITMQ_CONNECTION_CONFIG.copy()

def validate_rabbitmq_config():
    """Validar configuración de RabbitMQ"""
    required_fields = ['host', 'port', 'username', 'password', 'queue_name']
    
    for field in required_fields:
        if not RABBITMQ_CONFIG.get(field):
            raise ValueError(f"Campo requerido faltante en configuración RabbitMQ: {field}")
    
    return True
