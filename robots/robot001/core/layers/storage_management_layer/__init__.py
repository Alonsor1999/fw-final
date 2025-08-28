"""
Capa de Almacenamiento y Gestión de Datos - Cuarta capa del sistema de procesamiento de documentos

Esta capa se encarga de:
- Almacenamiento persistente de documentos procesados
- Gestión de índices para búsqueda rápida
- Sistema de caché para optimizar rendimiento
- Backup y recuperación de datos
"""

from .data_storage_manager import DataStorageManager
from .index_manager import IndexManager
from .cache_manager import CacheManager
from .storage_management_coordinator import StorageManagementCoordinator

__all__ = [
    'DataStorageManager', 
    'IndexManager', 
    'CacheManager', 
    'StorageManagementCoordinator'
]
