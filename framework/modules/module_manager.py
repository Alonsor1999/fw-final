"""
Gestor de Módulos - Permite a los robots usar módulos del framework
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Type
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path para importar el framework
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from framework.modules.base_module import BaseModule
from framework.modules.bot_modules.scraping_module import ScrapingModule
from framework.modules.bot_modules.email_module import EmailModule
from framework.modules.bot_modules.web_automation_module import WebAutomationModule
from framework.modules.bot_modules.rabbitmq_module import RabbitMQModule

logger = logging.getLogger(__name__)

class ModuleManager:
    """Gestor de módulos para robots"""
    
    def __init__(self, robot_id: str):
        self.robot_id = robot_id
        self.modules: Dict[str, BaseModule] = {}
        self.module_registry = {
            'scraping': ScrapingModule,
            'email': EmailModule,
            'web_automation': WebAutomationModule,
            'rabbitmq': RabbitMQModule
        }
    
    async def register_module(self, module_type: str, module_id: str, config: Dict[str, Any] = None) -> bool:
        """Registrar un módulo para el robot"""
        try:
            if module_type not in self.module_registry:
                raise ValueError(f"Tipo de módulo no soportado: {module_type}")
            
            if module_id in self.modules:
                logger.warning(f"Módulo {module_id} ya está registrado")
                return True
            
            # Crear instancia del módulo
            module_class = self.module_registry[module_type]
            module = module_class(module_id, self.robot_id, config)
            
            # Inicializar módulo
            await module.initialize()
            
            # Registrar módulo
            self.modules[module_id] = module
            
            logger.info(f"Módulo {module_type} registrado como {module_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar módulo {module_type}: {e}")
            return False
    
    async def execute_module(self, module_id: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar un módulo específico"""
        try:
            if module_id not in self.modules:
                raise ValueError(f"Módulo {module_id} no está registrado")
            
            module = self.modules[module_id]
            result = await module.execute(params or {})
            
            logger.info(f"Módulo {module_id} ejecutado exitosamente")
            return result
            
        except Exception as e:
            logger.error(f"Error al ejecutar módulo {module_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'module_id': module_id,
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_module_status(self, module_id: str) -> Dict[str, Any]:
        """Obtener estado de un módulo"""
        try:
            if module_id not in self.modules:
                return {'error': f'Módulo {module_id} no encontrado'}
            
            module = self.modules[module_id]
            return await module.get_status()
            
        except Exception as e:
            logger.error(f"Error al obtener estado del módulo {module_id}: {e}")
            return {'error': str(e)}
    
    async def get_all_modules_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los módulos"""
        try:
            status = {}
            for module_id, module in self.modules.items():
                status[module_id] = await module.get_status()
            
            return {
                'robot_id': self.robot_id,
                'total_modules': len(self.modules),
                'modules': status
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estado de módulos: {e}")
            return {'error': str(e)}
    
    async def get_module_results(self, module_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener resultados de un módulo"""
        try:
            if module_id not in self.modules:
                return []
            
            module = self.modules[module_id]
            return await module.get_results(limit)
            
        except Exception as e:
            logger.error(f"Error al obtener resultados del módulo {module_id}: {e}")
            return []
    
    async def get_module_stats(self, module_id: str) -> Dict[str, Any]:
        """Obtener estadísticas específicas de un módulo"""
        try:
            if module_id not in self.modules:
                return {'error': f'Módulo {module_id} no encontrado'}
            
            module = self.modules[module_id]
            
            # Obtener estadísticas específicas según el tipo de módulo
            if hasattr(module, 'get_scraping_stats'):
                return await module.get_scraping_stats()
            elif hasattr(module, 'get_email_stats'):
                return await module.get_email_stats()
            elif hasattr(module, 'get_rabbitmq_stats'):
                return await module.get_rabbitmq_stats()
            elif hasattr(module, 'get_automation_stats'):
                return await module.get_automation_stats()
            else:
                return await module.get_status()
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas del módulo {module_id}: {e}")
            return {'error': str(e)}
    
    def get_available_modules(self) -> List[Dict[str, Any]]:
        """Obtener lista de módulos disponibles"""
        available = []
        for module_type, module_class in self.module_registry.items():
            info = module_class.get_module_info()
            available.append({
                'type': module_type,
                'name': info['name'],
                'description': info['description'],
                'version': info['version']
            })
        return available
    
    def get_registered_modules(self) -> List[str]:
        """Obtener lista de módulos registrados"""
        return list(self.modules.keys())
    
    async def unregister_module(self, module_id: str) -> bool:
        """Desregistrar un módulo"""
        try:
            if module_id not in self.modules:
                logger.warning(f"Módulo {module_id} no está registrado")
                return True
            
            module = self.modules[module_id]
            await module.close()
            del self.modules[module_id]
            
            logger.info(f"Módulo {module_id} desregistrado")
            return True
            
        except Exception as e:
            logger.error(f"Error al desregistrar módulo {module_id}: {e}")
            return False
    
    async def close_all_modules(self):
        """Cerrar todos los módulos"""
        try:
            for module_id, module in self.modules.items():
                try:
                    await module.close()
                    logger.info(f"Módulo {module_id} cerrado")
                except Exception as e:
                    logger.error(f"Error al cerrar módulo {module_id}: {e}")
            
            self.modules.clear()
            logger.info("Todos los módulos cerrados")
            
        except Exception as e:
            logger.error(f"Error al cerrar módulos: {e}")
    
    async def execute_workflow(self, workflow: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ejecutar un flujo de trabajo con múltiples módulos"""
        try:
            results = []
            
            for step in workflow:
                module_id = step.get('module_id')
                params = step.get('params', {})
                wait_after = step.get('wait_after', 0)
                
                if not module_id:
                    logger.warning("Paso sin module_id, saltando...")
                    continue
                
                logger.info(f"Ejecutando paso con módulo: {module_id}")
                
                # Ejecutar módulo
                result = await self.execute_module(module_id, params)
                results.append({
                    'step': len(results) + 1,
                    'module_id': module_id,
                    'params': params,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Esperar si es necesario
                if wait_after > 0:
                    logger.info(f"Esperando {wait_after} segundos...")
                    await asyncio.sleep(wait_after)
            
            return results
            
        except Exception as e:
            logger.error(f"Error en workflow: {e}")
            return [{'error': str(e)}]
    
    def __del__(self):
        """Destructor para limpiar recursos"""
        try:
            # Intentar cerrar módulos si aún existen
            if hasattr(self, 'modules') and self.modules:
                asyncio.create_task(self.close_all_modules())
        except:
            pass
