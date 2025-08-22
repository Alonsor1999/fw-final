"""
CacheManager MVP - Sistema de cache distribuido con intelligent TTL management
"""
import asyncio
import json
import logging
import hashlib
from typing import Optional, Dict, Any, List, Callable, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import redis.asyncio as redis
from framework.config import settings, CACHE_TTL_CONFIG

logger = logging.getLogger(__name__)


class CacheWarmerMVP:
    """Cache warming engine para precarga de datos críticos"""
    
    def __init__(self, cache_manager: 'CacheManager'):
        self.cache_manager = cache_manager
        self.warming_tasks: Dict[str, asyncio.Task] = {}

    async def warm_critical_caches(self):
        """Warm critical caches automáticamente"""
        try:
            # Warm active modules (TTL: 5 minutes)
            await self.warm_active_modules()
            
            # Warm performance scores (TTL: 10 minutes)
            await self.warm_performance_scores()
            
            # Warm health status (TTL: 30 seconds)
            await self.warm_health_status()
            
            # Warm robot routing table (TTL: 1 minute)
            await self.warm_robot_routing_table()
            
            logger.info("Critical caches warmed successfully")
            
        except Exception as e:
            logger.error(f"Failed to warm critical caches: {e}")

    async def warm_active_modules(self):
        """Warm active modules cache"""
        cache_key = "active_modules"
        try:
            # This would typically fetch from StateManager
            # For now, we'll use a placeholder
            modules_data = {
                "modules": [
                    {"name": "LegalModule", "performance_score": 0.95},
                    {"name": "EmailProcessor", "performance_score": 0.88},
                    {"name": "OCREngine", "performance_score": 0.92}
                ],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            await self.cache_manager.set(
                cache_key, 
                modules_data, 
                ttl=CACHE_TTL_CONFIG["module_health"]
            )
            
        except Exception as e:
            logger.error(f"Failed to warm active modules: {e}")

    async def warm_performance_scores(self):
        """Warm performance scores cache"""
        cache_key = "performance_scores"
        try:
            scores_data = {
                "scores": {
                    "LegalModule": 0.95,
                    "EmailProcessor": 0.88,
                    "OCREngine": 0.92,
                    "DataAnalyzer": 0.85,
                    "WebScraper": 0.78
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
            await self.cache_manager.set(
                cache_key, 
                scores_data, 
                ttl=CACHE_TTL_CONFIG["performance_scores"]
            )
            
        except Exception as e:
            logger.error(f"Failed to warm performance scores: {e}")

    async def warm_health_status(self):
        """Warm health status cache"""
        cache_key = "system_health"
        try:
            health_data = {
                "overall_status": "HEALTHY",
                "modules": {
                    "LegalModule": "HEALTHY",
                    "EmailProcessor": "HEALTHY",
                    "OCREngine": "HEALTHY",
                    "DataAnalyzer": "DEGRADED",
                    "WebScraper": "UNHEALTHY"
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
            await self.cache_manager.set(
                cache_key, 
                health_data, 
                ttl=CACHE_TTL_CONFIG["module_health"]
            )
            
        except Exception as e:
            logger.error(f"Failed to warm health status: {e}")

    async def warm_robot_routing_table(self):
        """Warm robot routing table cache"""
        cache_key = "robot_routing_table"
        try:
            routing_data = {
                "legal_document_analysis": ["LegalModule"],
                "email_classification": ["EmailProcessor"],
                "document_ocr": ["OCREngine"],
                "data_analysis": ["DataAnalyzer"],
                "web_scraping": ["WebScraper"]
            }
            
            await self.cache_manager.set(
                cache_key, 
                routing_data, 
                ttl=CACHE_TTL_CONFIG["routing_table"]
            )
            
        except Exception as e:
            logger.error(f"Failed to warm robot routing table: {e}")


class CacheManager:
    """Sistema de cache distribuido con intelligent TTL management y graceful fallback"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.cache_warmer = CacheWarmerMVP(self)
        self._initialized = False
        self._connection_pool: Optional[redis.ConnectionPool] = None

    async def initialize(self):
        """Inicializar conexión Redis"""
        if self._initialized:
            return

        try:
            # Create Redis client with connection pool
            self.redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=settings.REDIS_POOL_MAX_SIZE
            )
            
            # Test connection
            await self.redis.ping()
            
            self._initialized = True
            logger.info("CacheManager initialized successfully")
            
            # Start cache warming
            asyncio.create_task(self._start_cache_warming())
            
        except Exception as e:
            logger.error(f"Failed to initialize CacheManager: {e}")
            raise

    async def close(self):
        """Cerrar conexión Redis"""
        if self.redis:
            await self.redis.close()
        logger.info("CacheManager closed")

    async def _start_cache_warming(self):
        """Iniciar cache warming automático"""
        while self._initialized:
            try:
                await self.cache_warmer.warm_critical_caches()
                # Wait 5 minutes before next warming
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Cache warming failed: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute

    def calculate_smart_ttl(self, key: str, data: Any) -> int:
        """Calcular TTL inteligente basado en tipo de datos"""
        # Smart TTL based on data volatility
        if 'module_health' in key:
            return CACHE_TTL_CONFIG["module_health"]
        elif 'robot_status' in key:
            return CACHE_TTL_CONFIG["robot_status"]
        elif 'performance_score' in key:
            return CACHE_TTL_CONFIG["performance_scores"]
        elif 'routing_table' in key:
            return CACHE_TTL_CONFIG["routing_table"]
        elif 'user_session' in key:
            return CACHE_TTL_CONFIG["user_sessions"]
        elif 'configuration' in key:
            return CACHE_TTL_CONFIG["configuration"]
        else:
            return CACHE_TTL_CONFIG["default"]

    def generate_cache_key(self, prefix: str, *args) -> str:
        """Generar clave de cache consistente"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if not self._initialized:
            await self.initialize()

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Establecer valor en cache"""
        if not self._initialized:
            await self.initialize()

        try:
            # Use smart TTL if not provided
            if ttl is None:
                ttl = self.calculate_smart_ttl(key, value)
            
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Eliminar clave del cache"""
        if not self._initialized:
            await self.initialize()

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Verificar si clave existe en cache"""
        if not self._initialized:
            await self.initialize()

        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False

    async def get_with_fallback(self, key: str, fallback_func: Callable, ttl: Optional[int] = None) -> Any:
        """Obtener con fallback a función"""
        # Try cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_value

        # Fallback to function
        logger.debug(f"Cache miss for key: {key}, calling fallback function")
        try:
            value = await fallback_func()
            
            # Cache the result
            await self.set(key, value, ttl)
            
            return value
        except Exception as e:
            logger.error(f"Fallback function failed for key {key}: {e}")
            raise

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidar claves que coincidan con patrón"""
        if not self._initialized:
            await self.initialize()

        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {e}")
            return 0

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Obtener múltiples valores del cache"""
        if not self._initialized:
            await self.initialize()

        try:
            values = await self.redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Failed to get many cache keys: {e}")
            return {}

    async def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Establecer múltiples valores en cache"""
        if not self._initialized:
            await self.initialize()

        try:
            pipeline = self.redis.pipeline()
            for key, value in data.items():
                if ttl is None:
                    ttl = self.calculate_smart_ttl(key, value)
                serialized_value = json.dumps(value, default=str)
                pipeline.setex(key, ttl, serialized_value)
            
            await pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Failed to set many cache keys: {e}")
            return False

    # Robot-specific cache methods
    async def get_robot_status(self, robot_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de robot del cache"""
        cache_key = self.generate_cache_key("robot_status", robot_id)
        return await self.get(cache_key)

    async def set_robot_status(self, robot_id: str, status_data: Dict[str, Any]) -> bool:
        """Establecer estado de robot en cache"""
        cache_key = self.generate_cache_key("robot_status", robot_id)
        return await self.set(cache_key, status_data, CACHE_TTL_CONFIG["robot_status"])

    async def invalidate_robot_cache(self, robot_id: str):
        """Invalidar cache de robot específico"""
        pattern = f"robot_status:{robot_id}*"
        await self.invalidate_pattern(pattern)

    # Module-specific cache methods
    async def get_module_health(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Obtener salud de módulo del cache"""
        cache_key = self.generate_cache_key("module_health", module_name)
        return await self.get(cache_key)

    async def set_module_health(self, module_name: str, health_data: Dict[str, Any]) -> bool:
        """Establecer salud de módulo en cache"""
        cache_key = self.generate_cache_key("module_health", module_name)
        return await self.set(cache_key, health_data, CACHE_TTL_CONFIG["module_health"])

    async def get_module_performance(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Obtener performance de módulo del cache"""
        cache_key = self.generate_cache_key("module_performance", module_name)
        return await self.get(cache_key)

    async def set_module_performance(self, module_name: str, performance_data: Dict[str, Any]) -> bool:
        """Establecer performance de módulo en cache"""
        cache_key = self.generate_cache_key("module_performance", module_name)
        return await self.set(cache_key, performance_data, CACHE_TTL_CONFIG["performance_scores"])

    async def invalidate_module_cache(self, module_name: str):
        """Invalidar cache de módulo específico"""
        pattern = f"module_*:{module_name}*"
        await self.invalidate_pattern(pattern)

    # Routing cache methods
    async def get_routing_table(self) -> Optional[Dict[str, List[str]]]:
        """Obtener tabla de routing del cache"""
        cache_key = "robot_routing_table"
        return await self.get(cache_key)

    async def set_routing_table(self, routing_data: Dict[str, List[str]]) -> bool:
        """Establecer tabla de routing en cache"""
        cache_key = "robot_routing_table"
        return await self.set(cache_key, routing_data, CACHE_TTL_CONFIG["routing_table"])

    async def get_optimal_module(self, robot_type: str) -> Optional[str]:
        """Obtener módulo óptimo para tipo de robot"""
        routing_table = await self.get_routing_table()
        if routing_table and robot_type in routing_table:
            modules = routing_table[robot_type]
            if modules:
                return modules[0]  # Return first available module
        return None

    # Performance cache methods
    async def get_performance_metrics(self, metric_type: str, time_range: str = "24h") -> Optional[Dict[str, Any]]:
        """Obtener métricas de performance del cache"""
        cache_key = self.generate_cache_key("performance_metrics", metric_type, time_range)
        return await self.get(cache_key)

    async def set_performance_metrics(self, metric_type: str, metrics_data: Dict[str, Any], 
                                    time_range: str = "24h") -> bool:
        """Establecer métricas de performance en cache"""
        cache_key = self.generate_cache_key("performance_metrics", metric_type, time_range)
        return await self.set(cache_key, metrics_data, CACHE_TTL_CONFIG["performance_scores"])

    # Cache statistics
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        if not self._initialized:
            await self.initialize()

        try:
            info = await self.redis.info()
            return {
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    async def get_hit_rate(self) -> float:
        """Calcular tasa de hit del cache"""
        stats = await self.get_cache_stats()
        hits = stats.get("keyspace_hits", 0)
        misses = stats.get("keyspace_misses", 0)
        total = hits + misses
        
        if total > 0:
            return hits / total
        return 0.0

    # Cache warming methods
    async def warm_cache(self, cache_type: str):
        """Warm specific cache type"""
        if cache_type == "modules":
            await self.cache_warmer.warm_active_modules()
        elif cache_type == "performance":
            await self.cache_warmer.warm_performance_scores()
        elif cache_type == "health":
            await self.cache_warmer.warm_health_status()
        elif cache_type == "routing":
            await self.cache_warmer.warm_robot_routing_table()
        else:
            logger.warning(f"Unknown cache type for warming: {cache_type}")

    # Cache cleanup
    async def cleanup_expired_keys(self) -> int:
        """Limpiar claves expiradas"""
        if not self._initialized:
            await self.initialize()

        try:
            # Redis automatically handles expired keys
            # This method is for monitoring purposes
            info = await self.redis.info()
            expired_keys = info.get("expired_keys", 0)
            logger.info(f"Expired keys cleaned: {expired_keys}")
            return expired_keys
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0

    # Health check
    async def health_check(self) -> bool:
        """Verificar salud del cache"""
        if not self._initialized:
            return False

        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False
