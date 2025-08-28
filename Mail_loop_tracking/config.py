# config.py
"""
Configuración centralizada para el sistema Mail Loop Tracking.

Este módulo maneja la carga y validación de variables de entorno
necesarias para la autenticación con Microsoft Graph API.
"""
import os
from typing import List
from dotenv import load_dotenv
from utils.logger_config import setup_logger

# Configurar logger para este módulo
logger = setup_logger("config")

# Cargar variables de entorno
load_dotenv()
logger.debug("Archivo .env cargado correctamente")

# Variables de configuración de Microsoft Graph API
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GRAPH_SCOPE = [os.getenv("GRAPH_SCOPE", "https://graph.microsoft.com/.default")]
MAIL_USER = os.getenv("MAIL_USER")

# Configuración de endpoints y directorios
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, ".", "logs/attachments")
LOG_DIR = os.path.abspath(LOG_DIR)
DOWNLOAD_DIR = LOG_DIR
ATTACHMENTS_DIR = LOG_DIR
AUTHORITY_URL = f"https://login.microsoftonline.com/{TENANT_ID}" if TENANT_ID else None

def validate_config() -> bool:
    """
    Valida que todas las variables de configuración requeridas estén presentes.
    
    Returns:
        bool: True si la configuración es válida, False en caso contrario
        
    Raises:
        EnvironmentError: Si faltan variables obligatorias
    """
    logger.info("Iniciando validación de configuración...")
    
    # Lista de variables obligatorias
    required_vars = {
        "TENANT_ID": TENANT_ID,
        "CLIENT_ID": CLIENT_ID,
        "CLIENT_SECRET": CLIENT_SECRET,
        "MAIL_USER": MAIL_USER
    }
    
    # Verificar variables faltantes
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        error_msg = f"Variables de entorno obligatorias faltantes: {', '.join(missing_vars)}"
        logger.error(f"❌ {error_msg}")
        logger.error("Por favor, verifica tu archivo .env")
        raise EnvironmentError(error_msg)
    
    # Validaciones adicionales
    if not MAIL_USER or '@' not in MAIL_USER:
        error_msg = "MAIL_USER debe ser un email válido"
        logger.error(f"❌ {error_msg}")
        raise EnvironmentError(error_msg)
    
    if not CLIENT_SECRET or len(CLIENT_SECRET) < 10:
        error_msg = "CLIENT_SECRET debe tener al menos 10 caracteres"
        logger.error(f"❌ {error_msg}")
        raise EnvironmentError(error_msg)
    
    logger.info("✅ Configuración validada correctamente")
    logger.debug(f"Usuario configurado: {MAIL_USER}")
    logger.debug(f"Tenant ID: {TENANT_ID}")
    logger.debug(f"Graph API Endpoint: {GRAPH_API_ENDPOINT}")
    
    return True

def get_config_summary() -> dict:
    """
    Obtiene un resumen de la configuración actual (sin datos sensibles).
    
    Returns:
        dict: Resumen de la configuración
    """
    return {
        "mail_user": MAIL_USER,
        "tenant_id": TENANT_ID,
        "graph_api_endpoint": GRAPH_API_ENDPOINT,
        "attachments_dir": ATTACHMENTS_DIR,
        "graph_scope": GRAPH_SCOPE,
        "authority_url": AUTHORITY_URL
    }

def create_directories() -> None:
    """
    Crea los directorios necesarios para el funcionamiento del sistema.
    """
    logger.info("Creando directorios necesarios...")
    
    directories = [
        ATTACHMENTS_DIR,
        "logs",
        "credentials"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"✅ Directorio creado/verificado: {directory}")
        except Exception as e:
            logger.error(f"❌ Error creando directorio {directory}: {e}")
            raise

# Validación automática al importar el módulo
try:
    validate_config()
    create_directories()
except EnvironmentError as e:
    logger.critical(f"Error crítico de configuración: {e}")
    raise
except Exception as e:
    logger.critical(f"Error inesperado durante la configuración: {e}")
    raise