"""
Main del Robot001 - Punto de entrada
"""
import asyncio
import sys
import os

# Agregar el framework al path para poder importar el logger
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from framework.shared.logger import Logger
from core.business import ScrapingBot

async def main():
    """Función principal - Muy corta y simple"""
    # ID del robot
    robot_id = "robot_001_20241220_001"
    
    try:
        # Crear y ejecutar el robot
        bot = ScrapingBot()
        results = await bot.run(robot_id)
        
        print(f"✅ Robot ejecutado exitosamente!")
        print(f"📊 Productos encontrados: {len(results)}")
        print(f"📁 Logs guardados en: files/logs/")
        
    except Exception as e:
        print(f"❌ Error ejecutando robot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
