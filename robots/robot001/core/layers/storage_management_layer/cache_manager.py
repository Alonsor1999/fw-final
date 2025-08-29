"""
Gestor de Caché - Cuarta capa del sistema

Este componente se encarga de:
- Gestión de caché en memoria para acceso rápido
- Estrategias de caché (LRU, LFU, TTL)
- Optimización de rendimiento
- Gestión de memoria
"""

import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from collections import OrderedDict
import threading
import pickle


class CacheManager:
    """Gestor de caché para optimizar el acceso a datos"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = ttl  # segundos
        
        # Configuración del caché
        self.config = {
            'enable_cache': True,
            'cache_strategy': 'LRU',  # LRU, LFU, FIFO
            'enable_compression': True,
            'enable_persistence': False,
            'persistence_path': 'cache_data.pkl',
            'auto_cleanup': True,
            'cleanup_interval': 300,  # segundos
            'memory_limit': 100 * 1024 * 1024,  # 100MB
            'enable_statistics': True
        }
        
        # Estructuras de datos del caché
        self.cache = OrderedDict()  # Para LRU
        self.access_count = {}  # Para LFU
        self.expiry_times = {}
        self.cache_size = 0
        
        # Estadísticas del caché
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0,
            'cache_size': 0,
            'memory_usage': 0,
            'hit_rate': 0.0,
            'avg_access_time': 0.0
        }
        
        # Lock para thread safety
        self.lock = threading.Lock()
        
        # Inicializar limpieza automática
        if self.config['auto_cleanup']:
            self._start_cleanup_thread()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor del caché
        
        Args:
            key: Clave del elemento
            default: Valor por defecto si no se encuentra
            
        Returns:
            Valor almacenado o default
        """
        if not self.config['enable_cache']:
            return default
        
        start_time = time.time()
        
        with self.lock:
            # Verificar si existe y no ha expirado
            if key in self.cache:
                if self._is_expired(key):
                    self._remove_item(key)
                    self.stats['misses'] += 1
                else:
                    # Actualizar acceso
                    self._update_access(key)
                    self.stats['hits'] += 1
                    
                    # Calcular tiempo de acceso
                    access_time = time.time() - start_time
                    self._update_access_time_stats(access_time)
                    
                    return self.cache[key]['value']
            
            self.stats['misses'] += 1
            self.stats['total_requests'] += 1
            self._update_hit_rate()
            
            return default

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Almacena un valor en el caché
        
        Args:
            key: Clave del elemento
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos (None para usar default)
            
        Returns:
            True si se almacenó correctamente
        """
        if not self.config['enable_cache']:
            return False
        
        try:
            with self.lock:
                # Comprimir valor si está habilitado
                if self.config['enable_compression']:
                    compressed_value = self._compress_value(value)
                    storage_value = compressed_value
                else:
                    storage_value = value
                
                # Calcular tamaño del elemento
                item_size = self._calculate_item_size(key, storage_value)
                
                # Verificar si hay espacio
                if item_size > self.config['memory_limit']:
                    return False
                
                # Eliminar elementos si es necesario
                while (self.cache_size + item_size > self.config['memory_limit'] and 
                       len(self.cache) > 0):
                    self._evict_item()
                
                # Almacenar elemento
                expiry_time = time.time() + (ttl or self.default_ttl)
                
                self.cache[key] = {
                    'value': storage_value,
                    'size': item_size,
                    'compressed': self.config['enable_compression'],
                    'created_at': time.time()
                }
                
                self.expiry_times[key] = expiry_time
                self.access_count[key] = 0
                self.cache_size += item_size
                
                # Actualizar estadísticas
                self.stats['cache_size'] = len(self.cache)
                self.stats['memory_usage'] = self.cache_size
                
                return True
                
        except Exception as e:
            return False

    def delete(self, key: str) -> bool:
        """
        Elimina un elemento del caché
        
        Args:
            key: Clave del elemento a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        with self.lock:
            return self._remove_item(key)

    def clear(self) -> bool:
        """
        Limpia todo el caché
        
        Returns:
            True si se limpió correctamente
        """
        try:
            with self.lock:
                self.cache.clear()
                self.access_count.clear()
                self.expiry_times.clear()
                self.cache_size = 0
                
                # Actualizar estadísticas
                self.stats['cache_size'] = 0
                self.stats['memory_usage'] = 0
                
                return True
        except Exception as e:
            return False

    def exists(self, key: str) -> bool:
        """
        Verifica si una clave existe en el caché
        
        Args:
            key: Clave a verificar
            
        Returns:
            True si existe y no ha expirado
        """
        with self.lock:
            if key in self.cache:
                if self._is_expired(key):
                    self._remove_item(key)
                    return False
                return True
            return False

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Obtiene múltiples valores del caché
        
        Args:
            keys: Lista de claves
            
        Returns:
            Dict con claves y valores encontrados
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(self, items: Dict[str, Any], ttl: int = None) -> Dict[str, bool]:
        """
        Almacena múltiples valores en el caché
        
        Args:
            items: Dict con claves y valores
            ttl: Tiempo de vida en segundos
            
        Returns:
            Dict con resultados de almacenamiento
        """
        results = {}
        for key, value in items.items():
            results[key] = self.set(key, value, ttl)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché
        
        Returns:
            Dict con estadísticas completas
        """
        with self.lock:
            # Calcular elementos expirados
            expired_count = sum(1 for key in self.cache if self._is_expired(key))
            
            return {
                'total_items': len(self.cache),
                'cache_size': self.cache_size,
                'memory_usage': self.stats['memory_usage'],
                'memory_limit': self.config['memory_limit'],
                'expired_items': expired_count,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'total_requests': self.stats['total_requests'],
                'hit_rate': self.stats['hit_rate'],
                'avg_access_time': self.stats['avg_access_time'],
                'cache_strategy': self.config['cache_strategy'],
                'compression_enabled': self.config['enable_compression']
            }

    def optimize_cache(self) -> Dict[str, Any]:
        """
        Optimiza el caché eliminando elementos expirados y reorganizando
        
        Returns:
            Dict con información de la optimización
        """
        try:
            with self.lock:
                initial_size = len(self.cache)
                initial_memory = self.cache_size
                
                # Eliminar elementos expirados
                expired_keys = [key for key in self.cache if self._is_expired(key)]
                for key in expired_keys:
                    self._remove_item(key)
                
                # Reorganizar según la estrategia
                if self.config['cache_strategy'] == 'LRU':
                    self._reorganize_lru()
                elif self.config['cache_strategy'] == 'LFU':
                    self._reorganize_lfu()
                
                final_size = len(self.cache)
                final_memory = self.cache_size
                
                return {
                    'success': True,
                    'items_removed': initial_size - final_size,
                    'memory_freed': initial_memory - final_memory,
                    'expired_removed': len(expired_keys),
                    'optimization_time': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def save_cache(self, file_path: str = None) -> bool:
        """
        Guarda el caché en disco
        
        Args:
            file_path: Ruta del archivo (None para usar configuración)
            
        Returns:
            True si se guardó correctamente
        """
        if not self.config['enable_persistence']:
            return False
        
        try:
            with self.lock:
                cache_data = {
                    'cache': dict(self.cache),
                    'access_count': self.access_count.copy(),
                    'expiry_times': self.expiry_times.copy(),
                    'stats': self.stats.copy(),
                    'config': self.config.copy()
                }
                
                save_path = file_path or self.config['persistence_path']
                with open(save_path, 'wb') as f:
                    pickle.dump(cache_data, f)
                
                return True
                
        except Exception as e:
            return False

    def load_cache(self, file_path: str = None) -> bool:
        """
        Carga el caché desde disco
        
        Args:
            file_path: Ruta del archivo (None para usar configuración)
            
        Returns:
            True si se cargó correctamente
        """
        if not self.config['enable_persistence']:
            return False
        
        try:
            with self.lock:
                load_path = file_path or self.config['persistence_path']
                
                with open(load_path, 'rb') as f:
                    cache_data = pickle.load(f)
                
                self.cache = OrderedDict(cache_data['cache'])
                self.access_count = cache_data['access_count']
                self.expiry_times = cache_data['expiry_times']
                self.stats = cache_data['stats']
                
                # Recalcular tamaño
                self.cache_size = sum(item['size'] for item in self.cache.values())
                
                return True
                
        except Exception as e:
            return False

    def _is_expired(self, key: str) -> bool:
        """Verifica si un elemento ha expirado"""
        if key not in self.expiry_times:
            return True
        return time.time() > self.expiry_times[key]

    def _remove_item(self, key: str) -> bool:
        """Elimina un elemento del caché"""
        if key in self.cache:
            item_size = self.cache[key]['size']
            del self.cache[key]
            del self.expiry_times[key]
            if key in self.access_count:
                del self.access_count[key]
            self.cache_size -= item_size
            return True
        return False

    def _evict_item(self) -> bool:
        """Elimina un elemento según la estrategia de caché"""
        if len(self.cache) == 0:
            return False
        
        if self.config['cache_strategy'] == 'LRU':
            # Eliminar el elemento menos recientemente usado
            key = next(iter(self.cache))
        elif self.config['cache_strategy'] == 'LFU':
            # Eliminar el elemento menos frecuentemente usado
            if self.access_count:
                key = min(self.access_count, key=self.access_count.get)
            else:
                key = next(iter(self.cache))
        else:  # FIFO
            # Eliminar el primer elemento
            key = next(iter(self.cache))
        
        self._remove_item(key)
        self.stats['evictions'] += 1
        return True

    def _update_access(self, key: str):
        """Actualiza las estadísticas de acceso"""
        if key in self.access_count:
            self.access_count[key] += 1
        
        # Mover al final para LRU
        if self.config['cache_strategy'] == 'LRU':
            value = self.cache.pop(key)
            self.cache[key] = value

    def _update_access_time_stats(self, access_time: float):
        """Actualiza estadísticas de tiempo de acceso"""
        total_requests = self.stats['total_requests']
        current_avg = self.stats['avg_access_time']
        
        self.stats['avg_access_time'] = (
            (current_avg * total_requests + access_time) / (total_requests + 1)
        )
        self.stats['total_requests'] += 1

    def _update_hit_rate(self):
        """Actualiza la tasa de aciertos"""
        total = self.stats['hits'] + self.stats['misses']
        if total > 0:
            self.stats['hit_rate'] = self.stats['hits'] / total

    def _calculate_item_size(self, key: str, value: Any) -> int:
        """Calcula el tamaño aproximado de un elemento"""
        try:
            # Tamaño de la clave
            key_size = len(key.encode('utf-8'))
            
            # Tamaño del valor
            if isinstance(value, (str, bytes)):
                value_size = len(value)
            else:
                value_size = len(pickle.dumps(value))
            
            # Tamaño de metadatos
            metadata_size = 100  # Aproximación
            
            return key_size + value_size + metadata_size
        except:
            return 1024  # Tamaño por defecto

    def _compress_value(self, value: Any) -> bytes:
        """Comprime un valor"""
        try:
            return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            return pickle.dumps(str(value), protocol=pickle.HIGHEST_PROTOCOL)

    def _reorganize_lru(self):
        """Reorganiza el caché según LRU"""
        # El OrderedDict ya mantiene el orden LRU automáticamente
        pass

    def _reorganize_lfu(self):
        """Reorganiza el caché según LFU"""
        # Ordenar por frecuencia de acceso
        sorted_items = sorted(self.access_count.items(), key=lambda x: x[1])
        
        # Recrear OrderedDict
        new_cache = OrderedDict()
        for key, _ in sorted_items:
            if key in self.cache:
                new_cache[key] = self.cache[key]
        
        self.cache = new_cache

    def _start_cleanup_thread(self):
        """Inicia el hilo de limpieza automática"""
        def cleanup_worker():
            while True:
                time.sleep(self.config['cleanup_interval'])
                self._cleanup_expired_items()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def _cleanup_expired_items(self):
        """Limpia elementos expirados"""
        with self.lock:
            expired_keys = [key for key in self.cache if self._is_expired(key)]
            for key in expired_keys:
                self._remove_item(key)
