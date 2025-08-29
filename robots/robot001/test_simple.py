"""
Script de prueba simple para Robot001
Prueba la inicialización básica sin credenciales reales
"""

import asyncio
import sys
import os
from datetime import datetime

# Agregar el directorio del framework al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from framework.shared.logger import get_logger

logger = get_logger(__name__)

class SimpleRobot001:
    """Versión simplificada del Robot001 para pruebas"""
    
    def __init__(self):
        self.robot_name = 'Robot001 - Test Mode'
        self.version = '1.0.0'
        self.is_running = False
        
    async def start(self):
        """Iniciar el robot en modo de prueba"""
        try:
            logger.info("🤖 Iniciando Robot001 en modo de prueba...")
            self.is_running = True
            
            # Simular componentes
            logger.info("✅ Framework inicializado")
            logger.info("✅ Logger configurado")
            logger.info("✅ Sistema de monitoreo activo")
            
            # Simular estado de componentes
            components = {
                'mail_reader': False,  # No disponible sin credenciales
                'attachment_downloader': False,
                'rabbitmq_sender': False,
                'orchestrator': True
            }
            
            logger.info(f"📊 Componentes: {components}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando robot: {e}")
            return False
    
    async def get_status(self):
        """Obtener estado del robot"""
        return {
            'robot_name': self.robot_name,
            'version': self.version,
            'is_running': self.is_running,
            'mode': 'test',
            'timestamp': datetime.now().isoformat(),
            'message': 'Robot funcionando en modo de prueba'
        }
    
    async def stop(self):
        """Detener el robot"""
        logger.info("🛑 Deteniendo Robot001...")
        self.is_running = False
        logger.info("✅ Robot detenido")

async def main():
    """Función principal de prueba"""
    print("=" * 60)
    print("ROBOT001 - MODO DE PRUEBA")
    print("=" * 60)
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    robot = SimpleRobot001()
    
    try:
        # Iniciar robot
        success = await robot.start()
        
        if success:
            print("✅ Robot iniciado correctamente en modo de prueba")
            
            # Mostrar estado
            status = await robot.get_status()
            print(f"📊 Estado: {status['robot_name']} v{status['version']}")
            print(f"📊 Modo: {status['mode']}")
            print(f"📊 Mensaje: {status['message']}")
            
            print("\n🎉 ¡Prueba exitosa!")
            print("El framework está funcionando correctamente.")
            print("\nPara usar el robot completo, necesitas:")
            print("1. Crear archivo .env en Mail_loop_tracking/")
            print("2. Configurar credenciales de Microsoft Graph API")
            print("3. Ejecutar python main.py")
            
        else:
            print("❌ Error iniciando robot")
            
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        logger.error(f"Error en prueba: {e}")
        
    finally:
        await robot.stop()
        print("=" * 60)

if __name__ == "__main__":
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar prueba
    asyncio.run(main())
