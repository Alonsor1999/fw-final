#!/usr/bin/env python3
"""
Script de prueba para el sistema de logging del framework
"""

import sys
import os
import asyncio
from datetime import datetime

# Agregar el framework al path
sys.path.append(os.path.dirname(__file__))

from framework.shared.logger import Logger

def test_basic_logging():
    """Prueba logging básico"""
    print("🧪 Probando logging básico...")
    
    # Asegurar que los directorios existan
    Logger.ensure_log_directories()
    
    # Logs básicos
    Logger.info("Mensaje de información de prueba")
    Logger.error("Mensaje de error de prueba")
    Logger.debug("Mensaje de debug de prueba")
    Logger.warning("Mensaje de advertencia de prueba")
    Logger.critical("Mensaje crítico de prueba")
    
    print("✅ Logging básico completado")

def test_robot_logging():
    """Prueba logging específico de robot"""
    print("🧪 Probando logging de robot...")
    
    robot_id = "robot_001"
    
    # Logs específicos de robot
    Logger.robot_log(robot_id, "info", "Robot iniciando proceso de scraping")
    Logger.robot_log(robot_id, "error", "Error en el módulo de scraping")
    Logger.robot_log(robot_id, "debug", "Configuración de scraping aplicada")
    
    # Logs con parámetros opcionales
    Logger.info(
        "Mensaje de información del robot",
        robot_id=robot_id,
        module_name="scraping_module"
    )
    
    Logger.error(
        "Error en el proceso de scraping",
        robot_id=robot_id,
        module_name="scraping_module"
    )
    
    print("✅ Logging de robot completado")

def test_module_logging():
    """Prueba logging específico de módulo"""
    print("🧪 Probando logging de módulo...")
    
    module_name = "scraping_module"
    
    # Logs específicos de módulo
    Logger.module_log(module_name, "info", "Módulo de scraping cargado")
    Logger.module_log(module_name, "debug", "Configuración de scraping aplicada")
    Logger.module_log(module_name, "error", "Error en el módulo de scraping")
    
    print("✅ Logging de módulo completado")

def test_framework_logging():
    """Prueba logging del framework"""
    print("🧪 Probando logging del framework...")
    
    # Logs del framework
    Logger.framework_log("info", "Framework iniciado correctamente")
    Logger.framework_log("error", "Error de conexión a la base de datos")
    Logger.framework_log("debug", "Configuración del framework cargada")
    
    print("✅ Logging del framework completado")

def test_log_paths():
    """Prueba obtención de rutas de logs"""
    print("🧪 Probando rutas de logs...")
    
    log_paths = Logger.get_log_paths()
    print(f"📁 Rutas de logs: {log_paths}")
    
    # Verificar que los directorios existen
    for name, path in log_paths.items():
        if os.path.exists(path):
            print(f"✅ Directorio {name}: {path} - EXISTE")
        else:
            print(f"❌ Directorio {name}: {path} - NO EXISTE")
    
    print("✅ Verificación de rutas completada")

def test_file_creation():
    """Prueba creación de archivos de log"""
    print("🧪 Probando creación de archivos de log...")
    
    # Generar algunos logs para crear archivos
    timestamp = datetime.now().strftime("%d%m%y")
    
    Logger.info("Test de creación de archivo de auditoría")
    Logger.error("Test de creación de archivo de error")
    
    # Verificar archivos creados
    audit_dir = Logger.AUDIT_LOG_DIR
    error_dir = Logger.ERROR_LOG_DIR
    
    audit_files = [f for f in os.listdir(audit_dir) if f.endswith('.log')] if os.path.exists(audit_dir) else []
    error_files = [f for f in os.listdir(error_dir) if f.endswith('.log')] if os.path.exists(error_dir) else []
    
    print(f"📄 Archivos de auditoría creados: {audit_files}")
    print(f"📄 Archivos de error creados: {error_files}")
    
    # Verificar contenido de un archivo
    if audit_files:
        audit_file_path = os.path.join(audit_dir, audit_files[0])
        with open(audit_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📝 Contenido del archivo de auditoría ({audit_files[0]}):")
            print(content[:500] + "..." if len(content) > 500 else content)
    
    print("✅ Verificación de archivos completada")

async def test_async_logging():
    """Prueba logging en contexto asíncrono"""
    print("🧪 Probando logging asíncrono...")
    
    robot_id = "robot_async_001"
    
    Logger.info(
        "Iniciando proceso asíncrono",
        robot_id=robot_id,
        module_name="async_test"
    )
    
    # Simular trabajo asíncrono
    await asyncio.sleep(1)
    
    Logger.info(
        "Proceso asíncrono completado",
        robot_id=robot_id,
        module_name="async_test"
    )
    
    print("✅ Logging asíncrono completado")

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del sistema de logging...")
    print("=" * 50)
    
    try:
        # Ejecutar todas las pruebas
        test_basic_logging()
        print()
        
        test_robot_logging()
        print()
        
        test_module_logging()
        print()
        
        test_framework_logging()
        print()
        
        test_log_paths()
        print()
        
        test_file_creation()
        print()
        
        # Prueba asíncrona
        asyncio.run(test_async_logging())
        print()
        
        print("🎉 ¡Todas las pruebas completadas exitosamente!")
        print("📁 Revisa los archivos de log en la carpeta 'files/logs/'")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
