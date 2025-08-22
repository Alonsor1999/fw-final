"""
Función simple para leer archivos JSON
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Función simple para leer un archivo JSON
    
    Args:
        file_path: Ruta del archivo JSON (puede ser relativa o absoluta)
        
    Returns:
        Dict con el contenido del archivo JSON
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        json.JSONDecodeError: Si el archivo no es un JSON válido
    """
    try:
        # Convertir a Path para manejo de rutas
        path = Path(file_path)
        
        # Verificar si el archivo existe
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Verificar si es un archivo
        if not path.is_file():
            raise FileNotFoundError(f"No es un archivo válido: {file_path}")
        
        # Leer el archivo JSON
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Archivo JSON leído exitosamente: {file_path}")
        return data
        
    except FileNotFoundError as e:
        logger.error(f"Error de archivo: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error de formato JSON en {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado leyendo {file_path}: {e}")
        raise

def read_json_from_config_dir(filename: str, config_dir: str = "config") -> Dict[str, Any]:
    """
    Leer archivo JSON desde el directorio de configuración
    
    Args:
        filename: Nombre del archivo JSON (ej: "YOGUIBOT_config.json")
        config_dir: Directorio de configuración (por defecto "config")
        
    Returns:
        Dict con el contenido del archivo JSON
    """
    file_path = os.path.join(config_dir, filename)
    return read_json_file(file_path)

def read_bot_config(bot_name: str, config_dir: str = "config") -> Dict[str, Any]:
    """
    Leer configuración específica de un bot
    
    Args:
        bot_name: Nombre del bot (ej: "YOGUIBOT")
        config_dir: Directorio de configuración (por defecto "config")
        
    Returns:
        Dict con la configuración del bot
    """
    filename = f"{bot_name}_config.json"
    return read_json_from_config_dir(filename, config_dir)

def list_json_files(config_dir: str = "config") -> list:
    """
    Listar todos los archivos JSON en el directorio de configuración
    
    Args:
        config_dir: Directorio de configuración (por defecto "config")
        
    Returns:
        Lista de nombres de archivos JSON
    """
    try:
        config_path = Path(config_dir)
        if not config_path.exists():
            return []
        
        json_files = list(config_path.glob("*.json"))
        return [f.name for f in json_files]
        
    except Exception as e:
        logger.error(f"Error listando archivos JSON en {config_dir}: {e}")
        return []

def get_json_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Obtener un valor específico de un JSON usando una ruta de claves
    
    Args:
        data: Diccionario JSON
        key_path: Ruta de claves separadas por puntos (ej: "BotConfig.Inputs.MaxRetries")
        default: Valor por defecto si no se encuentra la clave
        
    Returns:
        Valor encontrado o el valor por defecto
    """
    try:
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
        
    except Exception as e:
        logger.error(f"Error obteniendo valor de {key_path}: {e}")
        return default

def validate_json_structure(data: Dict[str, Any], required_keys: list) -> bool:
    """
    Validar que el JSON tenga las claves requeridas
    
    Args:
        data: Diccionario JSON a validar
        required_keys: Lista de claves requeridas
        
    Returns:
        True si todas las claves están presentes
    """
    try:
        for key in required_keys:
            if key not in data:
                logger.error(f"Clave requerida faltante: {key}")
                return False
        return True
        
    except Exception as e:
        logger.error(f"Error validando estructura JSON: {e}")
        return False

# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Ejemplo 1: Leer archivo JSON específico
        print("=== Ejemplo 1: Leer archivo JSON específico ===")
        config_data = read_json_file("YOGUIBOT_config.json")
        print(f"Configuración cargada: {len(config_data)} secciones")
        
        # Ejemplo 2: Leer configuración de bot
        print("\n=== Ejemplo 2: Leer configuración de bot ===")
        bot_config = read_bot_config("YOGUIBOT")
        print(f"Bot config cargado: {len(bot_config)} secciones")
        
        # Ejemplo 3: Obtener valor específico
        print("\n=== Ejemplo 3: Obtener valor específico ===")
        max_retries = get_json_value(bot_config, "BotConfig.Inputs.MaxRetries")
        server_rpa = get_json_value(bot_config, "BotConfig.Inputs.serverRPA")
        print(f"MaxRetries: {max_retries}")
        print(f"Server RPA: {server_rpa}")
        
        # Ejemplo 4: Listar archivos JSON
        print("\n=== Ejemplo 4: Listar archivos JSON ===")
        json_files = list_json_files()
        print(f"Archivos JSON encontrados: {json_files}")
        
        # Ejemplo 5: Validar estructura
        print("\n=== Ejemplo 5: Validar estructura ===")
        is_valid = validate_json_structure(bot_config, ["BotConfig"])
        print(f"Estructura válida: {is_valid}")
        
    except Exception as e:
        print(f"Error en ejemplo: {e}")
