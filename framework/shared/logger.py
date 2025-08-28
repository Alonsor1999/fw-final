"""
Nombre del módulo: logger.py
Descripción: Este módulo es el encargado de escribir los logs de Audit y error.
Autor: Fabio A. Rojas A.
Fecha de creación: 2024
Última modificación: 2024
Versión: 1.0
Historial de modificaciones:
    - 1.0 (2024): Versión inicial.
"""

import logging
import os
import traceback
from datetime import datetime
from typing import Optional
from framework.config import settings


class Logger:
    """
    Clase Logger para manejar logs de auditoría y errores en el framework.
    Utiliza las configuraciones del framework para rutas y niveles de log.
    """

    # Configuración de directorios de logs
    LOG_BASE_DIR = "files/logs"
    AUDIT_LOG_DIR = os.path.join(LOG_BASE_DIR, "audit")
    ERROR_LOG_DIR = os.path.join(LOG_BASE_DIR, "error")

    @staticmethod
    def __set_logger(log_directory: str, log_filename: str) -> logging.Logger:
        """
        Configura un logger específico para un archivo de log.
        
        Args:
            log_directory: Directorio donde se guardará el archivo de log
            log_filename: Nombre del archivo de log
            
        Returns:
            Logger configurado
        """
        # Obtiene un logger con el nombre del archivo de log
        logger = logging.getLogger(log_filename)
        
        # Establece el nivel de log en DEBUG (registrará todos los mensajes DEBUG y superiores)
        logger.setLevel(logging.DEBUG)

        # Construye la ruta completa del archivo de log
        log_path = os.path.join(log_directory, log_filename)
        
        # Crea un manejador de archivos que escribirá los logs en el archivo especificado
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        
        # Establece el nivel de log del manejador en DEBUG
        file_handler.setLevel(logging.DEBUG)

        # Define el formato de los mensajes de log
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s', 
            "%Y-%m-%d %H:%M:%S"
        )
        
        # Asigna el formato al manejador
        file_handler.setFormatter(formatter)

        # Si el logger ya tiene manejadores, los elimina
        if logger.hasHandlers():
            logger.handlers.clear()

        # Agrega el manejador de archivos al logger
        logger.addHandler(file_handler)

        # Devuelve el logger configurado
        return logger

    @classmethod
    def write_file_log(cls, level: str, message: str, robot_id: Optional[str] = None, 
                      module_name: Optional[str] = None) -> None:
        """
        Escribe un mensaje de log en el archivo correspondiente según el nivel.
        
        Args:
            level: Nivel del log ("info", "error", "debug", "warn", "critical")
            message: Mensaje a escribir en el log
            robot_id: ID del robot (opcional, para logs específicos de robot)
            module_name: Nombre del módulo (opcional, para logs específicos de módulo)
        """
        try:
            # Genera un timestamp con el formato "ddmmyy"
            timestamp = datetime.now().strftime("%d%m%y")
            
            # Determina el directorio y nombre de archivo según el nivel
            if level == "info":
                log_directory = cls.AUDIT_LOG_DIR
                log_filename = f"LogAudit_{timestamp}.log"
            elif level == "error":
                log_directory = cls.ERROR_LOG_DIR
                log_filename = f"LogError_{timestamp}.log"
            else:
                # Para otros niveles (debug, warn, critical) usa el directorio de auditoría
                log_directory = cls.AUDIT_LOG_DIR
                log_filename = f"LogAudit_{timestamp}.log"

            # Si se especifica un robot_id, agrega el prefijo al nombre del archivo
            if robot_id:
                log_filename = f"Robot_{robot_id}_{log_filename}"
            
            # Si se especifica un module_name, agrega el prefijo al nombre del archivo
            if module_name:
                log_filename = f"Module_{module_name}_{log_filename}"

            # Si el directorio no existe, lo crea
            if not os.path.exists(log_directory):
                os.makedirs(log_directory)

            # Configura el logger con el directorio y nombre de archivo especificados
            logger = cls.__set_logger(log_directory, log_filename)

            # Registra el mensaje en el nivel correspondiente
            if level == "critical":
                logger.critical(message)
            elif level == "debug":
                logger.debug(message)
            elif level == "error":
                logger.error(message, stacklevel=2, exc_info=True)
            elif level == "info":
                logger.info(message, stacklevel=2)
            elif level == "warn":
                logger.warning(message)
                
        except Exception as ex:
            # Imprime el traceback y el mensaje de excepción si ocurre un error
            print(traceback.format_exc())
            print(f"Error en Logger.write_file_log: {ex}")

    @classmethod
    def info(cls, message: str, robot_id: Optional[str] = None, 
             module_name: Optional[str] = None) -> None:
        """Escribe un log de información."""
        cls.write_file_log("info", message, robot_id, module_name)

    @classmethod
    def error(cls, message: str, robot_id: Optional[str] = None, 
              module_name: Optional[str] = None) -> None:
        """Escribe un log de error."""
        cls.write_file_log("error", message, robot_id, module_name)

    @classmethod
    def debug(cls, message: str, robot_id: Optional[str] = None, 
              module_name: Optional[str] = None) -> None:
        """Escribe un log de debug."""
        cls.write_file_log("debug", message, robot_id, module_name)

    @classmethod
    def warning(cls, message: str, robot_id: Optional[str] = None, 
                module_name: Optional[str] = None) -> None:
        """Escribe un log de advertencia."""
        cls.write_file_log("warn", message, robot_id, module_name)

    @classmethod
    def critical(cls, message: str, robot_id: Optional[str] = None, 
                 module_name: Optional[str] = None) -> None:
        """Escribe un log crítico."""
        cls.write_file_log("critical", message, robot_id, module_name)

    @classmethod
    def robot_log(cls, robot_id: str, level: str, message: str, 
                  module_name: Optional[str] = None) -> None:
        """
        Método específico para logs de robots.
        
        Args:
            robot_id: ID del robot
            level: Nivel del log
            message: Mensaje a escribir
            module_name: Nombre del módulo (opcional)
        """
        cls.write_file_log(level, message, robot_id, module_name)

    @classmethod
    def module_log(cls, module_name: str, level: str, message: str, 
                   robot_id: Optional[str] = None) -> None:
        """
        Método específico para logs de módulos.
        
        Args:
            module_name: Nombre del módulo
            level: Nivel del log
            message: Mensaje a escribir
            robot_id: ID del robot (opcional)
        """
        cls.write_file_log(level, message, robot_id, module_name)

    @classmethod
    def framework_log(cls, level: str, message: str) -> None:
        """
        Método específico para logs del framework.
        
        Args:
            level: Nivel del log
            message: Mensaje a escribir
        """
        cls.write_file_log(level, message)

    @classmethod
    def get_log_paths(cls) -> dict:
        """
        Retorna las rutas de los directorios de logs.
        
        Returns:
            Diccionario con las rutas de los directorios de logs
        """
        return {
            "base_dir": cls.LOG_BASE_DIR,
            "audit_dir": cls.AUDIT_LOG_DIR,
            "error_dir": cls.ERROR_LOG_DIR
        }

    @classmethod
    def ensure_log_directories(cls) -> None:
        """Asegura que los directorios de logs existan."""
        directories = [cls.LOG_BASE_DIR, cls.AUDIT_LOG_DIR, cls.ERROR_LOG_DIR]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

def get_logger(name: str) -> logging.Logger:
    """
    Función simple para obtener un logger.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Si el logger ya tiene handlers, no agregar más
    if not logger.handlers:
        # Configurar handler básico
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
