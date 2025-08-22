"""
Clase base para todos los módulos del framework
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path para importar el framework
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from framework.core.database_manager import DatabaseManager
from framework.shared.performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class BaseModule(ABC):
    """Clase base para todos los módulos del framework"""
    
    def __init__(self, module_id: str, robot_id: str, config: Dict[str, Any] = None):
        self.module_id = module_id
        self.robot_id = robot_id
        self.config = config or {}
        self.db_manager = DatabaseManager()
        self.performance_tracker = PerformanceTracker()
        self.is_initialized = False
        self.is_running = False
        self.start_time = None
        self.end_time = None
        self.results = []
        
    async def initialize(self):
        """Inicializar el módulo"""
        try:
            logger.info(f"Inicializando módulo {self.module_id} para robot {self.robot_id}")
            
            # Inicializar base de datos
            await self.db_manager.initialize()
            
            # Inicialización específica del módulo
            await self._initialize_module()
            
            self.is_initialized = True
            logger.info(f"Módulo {self.module_id} inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar módulo {self.module_id}: {e}")
            raise
    
    @abstractmethod
    async def _initialize_module(self):
        """Inicialización específica del módulo - debe ser implementado por subclases"""
        pass
    
    async def execute(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar el módulo"""
        try:
            if not self.is_initialized:
                raise Exception(f"Módulo {self.module_id} no está inicializado")
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info(f"Ejecutando módulo {self.module_id}")
            
            # Registrar evento de inicio
            await self.db_manager.insert_audit_event(self.robot_id, {
                'event_type': 'module_started',
                'event_source': self.module_id,
                'event_data': {
                    'start_time': self.start_time.isoformat(),
                    'params': params,
                    'config': self.config
                },
                'user_id': 'system'
            })
            
            # Ejecutar lógica específica del módulo
            result = await self._execute_module(params or {})
            
            # Guardar resultado
            self.results.append({
                'timestamp': datetime.now().isoformat(),
                'params': params,
                'result': result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error durante la ejecución del módulo {self.module_id}: {e}")
            
            # Registrar evento de error
            await self.db_manager.insert_audit_event(self.robot_id, {
                'event_type': 'module_error',
                'event_source': self.module_id,
                'event_data': {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                },
                'user_id': 'system'
            })
            
            raise
        finally:
            await self.stop()
    
    @abstractmethod
    async def _execute_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lógica específica del módulo - debe ser implementado por subclases"""
        pass
    
    async def stop(self):
        """Detener el módulo"""
        try:
            self.is_running = False
            self.end_time = datetime.now()
            
            logger.info(f"Deteniendo módulo {self.module_id}")
            
            # Calcular métricas de rendimiento
            if self.start_time and self.end_time:
                execution_time = (self.end_time - self.start_time).total_seconds()
                await self.performance_tracker.record_execution_time(
                    f"{self.robot_id}_{self.module_id}", execution_time
                )
            
            # Registrar evento de parada
            await self.db_manager.insert_audit_event(self.robot_id, {
                'event_type': 'module_stopped',
                'event_source': self.module_id,
                'event_data': {
                    'end_time': self.end_time.isoformat(),
                    'execution_time': execution_time if self.start_time and self.end_time else None
                },
                'user_id': 'system'
            })
            
            # Limpiar recursos
            await self._cleanup()
            
        except Exception as e:
            logger.error(f"Error al detener módulo {self.module_id}: {e}")
    
    async def _cleanup(self):
        """Limpieza de recursos - puede ser sobrescrito por subclases"""
        pass
    
    async def close(self):
        """Cerrar conexiones y liberar recursos"""
        try:
            await self.db_manager.close()
            logger.info(f"Módulo {self.module_id} cerrado correctamente")
        except Exception as e:
            logger.error(f"Error al cerrar módulo {self.module_id}: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del módulo"""
        return {
            'module_id': self.module_id,
            'robot_id': self.robot_id,
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            'results_count': len(self.results)
        }
    
    async def get_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener resultados del módulo"""
        return self.results[-limit:] if self.results else []
    
    @classmethod
    def get_module_info(cls) -> Dict[str, Any]:
        """Obtener información del módulo"""
        return {
            'name': cls.__name__,
            'description': cls.__doc__ or 'Sin descripción',
            'version': '1.0.0',
            'author': 'Framework Team'
        }
