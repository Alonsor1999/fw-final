#!/usr/bin/env python3
"""
Script simple para probar el logger sin depender del framework completo
"""

import sys
import os
from datetime import datetime

# Agregar el framework al path
sys.path.append(os.path.dirname(__file__))

try:
    from framework.shared.logger import Logger
    print("✅ Logger importado correctamente")
    
    # Asegurar que los directorios de logs existan
    Logger.ensure_log_directories()
    print("✅ Directorios de logs creados")
    
    # Probar logging básico
    Logger.info("Test de información desde script simple")
    Logger.error("Test de error desde script simple")
    Logger.debug("Test de debug desde script simple")
    Logger.warning("Test de advertencia desde script simple")
    Logger.critical("Test crítico desde script simple")
    
    print("✅ Logs básicos escritos correctamente")
    
    # Probar logging con parámetros
    robot_id = "test_robot_001"
    Logger.info(
        "Test de información con parámetros",
        robot_id=robot_id,
        module_name="test_script"
    )
    
    Logger.error(
        "Test de error con parámetros",
        robot_id=robot_id,
        module_name="test_script"
    )
    
    print("✅ Logs con parámetros escritos correctamente")
    
    # Verificar archivos creados
    log_paths = Logger.get_log_paths()
    print(f"📁 Rutas de logs: {log_paths}")
    
    for name, path in log_paths.items():
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith('.log')]
            print(f"✅ {name}: {path} - {len(files)} archivos")
            for file in files:
                print(f"   📄 {file}")
        else:
            print(f"❌ {name}: {path} - NO EXISTE")
    
    print("\n🎉 ¡Prueba del logger completada exitosamente!")
    
except ImportError as e:
    print(f"❌ Error importando Logger: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error durante la prueba: {e}")
    import traceback
    traceback.print_exc()
