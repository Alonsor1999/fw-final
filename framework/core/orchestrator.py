"""
Orchestrator MVP - Coordinador central del framework
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from framework.config import settings, PERFORMANCE_TARGETS
from framework.core.state_manager import StateManager
from framework.core.cache_manager import CacheManager
from framework.core.database_manager import DatabaseManager
from framework.models.robot import Robot, RobotCreate, RobotUpdate, RobotStatus, Priority
from framework.models.module import Module, ModuleCreate, ModuleHealth
from framework.models.execution import RobotExecute, ExecutionCreate, ExecutionUpdate, ExecutionState
from framework.shared.load_balancer import LoadBalancerMVP
from framework.shared.security_validator import SecurityValidatorMVP
from framework.shared.performance_tracker import PerformanceTrackerMVP

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrator MVP - Punto de entrada único que coordina todo el ciclo de vida de robots"""
    
    def __init__(self):
        self.state_manager = StateManager()
        self.cache_manager = CacheManager()
        self.database_manager = DatabaseManager()
        self.load_balancer = LoadBalancerMVP()
        self.security_validator = SecurityValidatorMVP()
        self.performance_tracker = PerformanceTrackerMVP()
        
        # Internal caches
        self.module_cache: Dict[str, Module] = {}
        self.performance_cache: Dict[str, float] = {}
        self._initialized = False

    async def initialize(self):
        """Inicializar todos los componentes"""
        if self._initialized:
            return

        try:
            # Initialize core components
            await self.state_manager.initialize()
            await self.cache_manager.initialize()
            await self.database_manager.initialize()
            
            # Start background tasks
            asyncio.create_task(self._health_monitor_loop())
            asyncio.create_task(self._performance_update_loop())
            asyncio.create_task(self._cleanup_loop())
            
            self._initialized = True
            logger.info("Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Orchestrator: {e}")
            raise

    async def close(self):
        """Cerrar todos los componentes"""
        await self.state_manager.close()
        await self.cache_manager.close()
        await self.database_manager.close()
        logger.info("Orchestrator closed")

    # Main Robot Processing Methods
    async def process_robot(self, robot_data: RobotCreate, api_key: str) -> Dict[str, Any]:
        """Procesar robot con performance tracking y security validation"""
        start_time = time.time()
        
        try:
            # 1. Security validation (5-10ms)
            module_name = await self.security_validator.validate_request(robot_data, api_key)
            
            # 2. Optimal module selection (10-15ms)
            module = await self.select_optimal_module(robot_data.robot_type)
            
            # 3. Robot creation + routing (20-30ms)
            robot = await self.state_manager.create_robot(robot_data)
            
            # 4. Performance tracking start
            execution = await self.start_execution(robot.robot_id, module.module_name)
            
            # 5. Cache robot status
            await self.cache_manager.set_robot_status(robot.robot_id, {
                "status": robot.status,
                "module_name": module.module_name,
                "progress": 0,
                "created_at": robot.created_at.isoformat()
            })
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Robot processed in {processing_time:.2f}ms: {robot.robot_id}")
            
            # Track performance
            await self.performance_tracker.record_operation(
                "robot_creation", processing_time, "success"
            )
            
            return {
                "robot_id": robot.robot_id,
                "module": module.module_name,
                "status": robot.status,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            await self.performance_tracker.record_operation(
                "robot_creation", processing_time, "error", str(e)
            )
            logger.error(f"Failed to process robot: {e}")
            raise

    async def select_optimal_module(self, robot_type: str) -> Module:
        """Seleccionar módulo óptimo con intelligent load balancing"""
        start_time = time.time()
        
        try:
            # Try cache first
            cached_module = await self.cache_manager.get_optimal_module(robot_type)
            if cached_module:
                module = await self.state_manager.get_module(cached_module)
                if module and module.is_available():
                    selection_time = (time.time() - start_time) * 1000
                    logger.debug(f"Module selected from cache in {selection_time:.2f}ms: {module.module_name}")
                    return module
            
            # Get available modules
            available_modules = await self.state_manager.get_active_modules()
            
            # Filter by robot type support
            supported_modules = [
                module for module in available_modules 
                if module.can_process_robot_type(robot_type)
            ]
            
            if not supported_modules:
                raise Exception(f"No available modules for robot type: {robot_type}")
            
            # Use load balancer for optimal selection
            optimal_module = self.load_balancer.select_best_module(supported_modules)
            
            # Cache the selection
            await self.cache_manager.set_routing_table({
                robot_type: [optimal_module.module_name]
            })
            
            selection_time = (time.time() - start_time) * 1000
            logger.debug(f"Module selected in {selection_time:.2f}ms: {optimal_module.module_name}")
            
            return optimal_module
            
        except Exception as e:
            selection_time = (time.time() - start_time) * 1000
            logger.error(f"Module selection failed in {selection_time:.2f}ms: {e}")
            raise

    async def start_execution(self, robot_id: str, module_name: str) -> RobotExecute:
        """Iniciar ejecución de robot"""
        execution_data = ExecutionCreate(
            robot_id=robot_id,
            module_name=module_name,
            total_steps=5,  # Default steps
            timeout_seconds=settings.ROBOT_TIMEOUT_SECONDS,
            max_retries=3
        )
        
        execution = await self.state_manager.create_execution(execution_data)
        
        # Update robot status to processing
        await self.state_manager.update_robot(robot_id, RobotUpdate(
            status=RobotStatus.PROCESSING
        ))
        
        logger.info(f"Execution started: {execution.execute_id} for robot: {robot_id}")
        return execution

    async def update_robot_progress(self, robot_id: str, progress_data: Dict[str, Any]) -> Robot:
        """Actualizar progreso de robot con batch optimization"""
        try:
            # Update execution
            execution_update = ExecutionUpdate(
                progress_percentage=progress_data.get("progress_percentage", 0),
                current_step=progress_data.get("current_step"),
                completed_steps=progress_data.get("completed_steps"),
                cpu_usage_percent=progress_data.get("cpu_usage_percent"),
                memory_usage_mb=progress_data.get("memory_usage_mb"),
                efficiency_score=progress_data.get("efficiency_score", 1.0)
            )
            
            execution = await self.state_manager.update_execution(
                progress_data.get("execute_id"), execution_update
            )
            
            # Update robot
            robot_update = RobotUpdate(
                completeness_score=progress_data.get("completeness_score"),
                confidence_score=progress_data.get("confidence_score"),
                performance_metrics=progress_data.get("performance_metrics"),
                processing_time_ms=progress_data.get("processing_time_ms"),
                cache_hit=progress_data.get("cache_hit", False),
                resource_usage_mb=progress_data.get("resource_usage_mb")
            )
            
            robot = await self.state_manager.update_robot(robot_id, robot_update)
            
            # Update cache
            await self.cache_manager.set_robot_status(robot_id, {
                "status": robot.status.value,
                "progress": progress_data.get("progress_percentage", 0),
                "module_name": robot.module_name,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            return robot
            
        except Exception as e:
            logger.error(f"Failed to update robot progress: {e}")
            raise

    async def complete_robot(self, robot_id: str, output_data: Dict[str, Any]) -> Robot:
        """Completar robot con output data"""
        try:
            # Update robot with completion data
            robot_update = RobotUpdate(
                status=RobotStatus.COMPLETED,
                output_data=output_data,
                completeness_score=1.0,
                confidence_score=output_data.get("confidence_score", 1.0),
                actual_duration_minutes=output_data.get("duration_minutes")
            )
            
            robot = await self.state_manager.update_robot(robot_id, robot_update)
            
            # Update execution
            execution = await self.state_manager.get_execution(
                output_data.get("execute_id")
            )
            if execution:
                await self.state_manager.update_execution(execution.execute_id, ExecutionUpdate(
                    execution_state=ExecutionState.COMPLETED,
                    progress_percentage=100,
                    completed_steps=execution.total_steps
                ))
            
            # Update module performance
            await self.update_module_performance(robot.module_name, {
                "success_count": 1,
                "processing_time_ms": output_data.get("processing_time_ms", 0)
            })
            
            # Update cache
            await self.cache_manager.set_robot_status(robot_id, {
                "status": "COMPLETED",
                "progress": 100,
                "output_data": output_data,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Robot completed: {robot_id}")
            return robot
            
        except Exception as e:
            logger.error(f"Failed to complete robot: {e}")
            raise

    async def fail_robot(self, robot_id: str, error_data: Dict[str, Any]) -> Robot:
        """Marcar robot como fallido con error details"""
        try:
            # Update robot with error data
            robot_update = RobotUpdate(
                status=RobotStatus.FAILED,
                error_details=error_data,
                error_category=error_data.get("category", "UNKNOWN"),
                last_error_at=datetime.utcnow()
            )
            
            robot = await self.state_manager.update_robot(robot_id, robot_update)
            
            # Update execution
            execution = await self.state_manager.get_execution(
                error_data.get("execute_id")
            )
            if execution:
                await self.state_manager.update_execution(execution.execute_id, ExecutionUpdate(
                    execution_state=ExecutionState.FAILED,
                    error_message=error_data.get("message"),
                    error_stack_trace=error_data.get("stack_trace")
                ))
            
            # Update module performance (failure)
            await self.update_module_performance(robot.module_name, {
                "error_count": 1,
                "error_category": error_data.get("category", "UNKNOWN")
            })
            
            # Update cache
            await self.cache_manager.set_robot_status(robot_id, {
                "status": "FAILED",
                "error": error_data,
                "failed_at": datetime.utcnow().isoformat()
            })
            
            logger.error(f"Robot failed: {robot_id} - {error_data.get('message', 'Unknown error')}")
            return robot
            
        except Exception as e:
            logger.error(f"Failed to mark robot as failed: {e}")
            raise

    # Module Management
    async def register_module(self, module_data: ModuleCreate) -> Module:
        """Registrar nuevo módulo"""
        try:
            module = await self.state_manager.register_module(module_data)
            
            # Update caches
            self.module_cache[module.module_name] = module
            await self.cache_manager.invalidate_module_cache(module.module_name)
            
            logger.info(f"Module registered: {module.module_name}")
            return module
            
        except Exception as e:
            logger.error(f"Failed to register module: {e}")
            raise

    async def update_module_performance(self, module_name: str, performance_data: Dict[str, Any]):
        """Actualizar métricas de performance del módulo"""
        try:
            await self.state_manager.update_module_performance(module_name, performance_data)
            
            # Update cache
            await self.cache_manager.set_module_performance(module_name, performance_data)
            
        except Exception as e:
            logger.error(f"Failed to update module performance: {e}")

    async def check_module_health(self, module_name: str) -> ModuleHealth:
        """Verificar salud de módulo"""
        try:
            module = await self.state_manager.get_module(module_name)
            if not module:
                return ModuleHealth(
                    module_name=module_name,
                    health_status="UNKNOWN",
                    error_message="Module not found"
                )
            
            # Perform health check
            health_data = await self._perform_health_check(module)
            
            # Update module health
            await self.state_manager.update_module_health(module_name, health_data)
            
            # Update cache
            await self.cache_manager.set_module_health(module_name, health_data)
            
            return ModuleHealth(
                module_name=module_name,
                health_status=health_data["health_status"],
                response_time_ms=health_data.get("response_time_ms"),
                error_message=health_data.get("last_error_message")
            )
            
        except Exception as e:
            logger.error(f"Health check failed for module {module_name}: {e}")
            return ModuleHealth(
                module_name=module_name,
                health_status="UNKNOWN",
                error_message=str(e)
            )

    async def _perform_health_check(self, module: Module) -> Dict[str, Any]:
        """Realizar health check de módulo"""
        # This would typically make an HTTP request to the module's health endpoint
        # For MVP, we'll simulate the health check
        import random
        
        # Simulate health check
        response_time = random.randint(10, 100)
        is_healthy = random.random() > 0.1  # 90% success rate
        
        if is_healthy:
            return {
                "health_status": "HEALTHY",
                "response_time_ms": response_time,
                "consecutive_failures": 0
            }
        else:
            return {
                "health_status": "UNHEALTHY",
                "response_time_ms": response_time,
                "consecutive_failures": module.consecutive_failures + 1,
                "last_error_message": "Health check failed"
            }

    # Background Tasks
    async def _health_monitor_loop(self):
        """Loop de monitoreo de salud de módulos"""
        while self._initialized:
            try:
                modules = await self.state_manager.get_active_modules()
                
                for module in modules:
                    await self.check_module_health(module.module_name)
                
                # Wait for next health check
                await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Health monitor loop failed: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute

    async def _performance_update_loop(self):
        """Loop de actualización de performance"""
        while self._initialized:
            try:
                # Update performance metrics for all modules
                modules = await self.state_manager.get_active_modules()
                
                for module in modules:
                    metrics = await self.state_manager.get_performance_metrics(module.module_name)
                    if metrics:
                        await self.update_module_performance(module.module_name, metrics)
                
                # Wait for next performance update
                await asyncio.sleep(settings.PERFORMANCE_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Performance update loop failed: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes

    async def _cleanup_loop(self):
        """Loop de limpieza de datos antiguos"""
        while self._initialized:
            try:
                # Cleanup old data
                await self.state_manager.cleanup_old_data(days_to_keep=30)
                
                # Wait for next cleanup (daily)
                await asyncio.sleep(86400)  # 24 hours
                
            except Exception as e:
                logger.error(f"Cleanup loop failed: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour

    # Query Methods
    async def get_robot(self, robot_id: str) -> Optional[Robot]:
        """Obtener robot por ID"""
        try:
            # Try cache first
            cached_status = await self.cache_manager.get_robot_status(robot_id)
            if cached_status:
                # Get full robot data from database
                robot = await self.state_manager.get_robot(robot_id)
                if robot:
                    return robot
            
            # Fallback to database
            return await self.state_manager.get_robot(robot_id)
            
        except Exception as e:
            logger.error(f"Failed to get robot {robot_id}: {e}")
            return None

    async def get_active_robots(self, limit: int = 100) -> List[Robot]:
        """Obtener robots activos"""
        try:
            return await self.state_manager.get_active_robots(limit)
        except Exception as e:
            logger.error(f"Failed to get active robots: {e}")
            return []

    async def get_robots_by_module(self, module_name: str) -> List[Robot]:
        """Obtener robots por módulo"""
        try:
            return await self.state_manager.get_robots_by_module(module_name)
        except Exception as e:
            logger.error(f"Failed to get robots by module: {e}")
            return []

    async def get_module(self, module_name: str) -> Optional[Module]:
        """Obtener módulo por nombre"""
        try:
            # Try cache first
            if module_name in self.module_cache:
                return self.module_cache[module_name]
            
            # Get from database
            module = await self.state_manager.get_module(module_name)
            if module:
                self.module_cache[module_name] = module
            
            return module
            
        except Exception as e:
            logger.error(f"Failed to get module {module_name}: {e}")
            return None

    async def get_active_modules(self) -> List[Module]:
        """Obtener módulos activos"""
        try:
            return await self.state_manager.get_active_modules()
        except Exception as e:
            logger.error(f"Failed to get active modules: {e}")
            return []

    # System Health and Metrics
    async def get_system_health(self) -> Dict[str, Any]:
        """Obtener salud general del sistema"""
        try:
            # Check core components
            db_healthy = await self.state_manager.read_pool is not None
            cache_healthy = await self.cache_manager.health_check()
            
            # Get module health summary
            modules = await self.state_manager.get_active_modules()
            healthy_modules = [m for m in modules if m.is_healthy()]
            
            # Get active robots count
            active_robots = await self.state_manager.get_active_robots(limit=1000)
            
            return {
                "overall_status": "HEALTHY" if (db_healthy and cache_healthy) else "DEGRADED",
                "database": "HEALTHY" if db_healthy else "UNHEALTHY",
                "cache": "HEALTHY" if cache_healthy else "UNHEALTHY",
                "modules": {
                    "total": len(modules),
                    "healthy": len(healthy_modules),
                    "unhealthy": len(modules) - len(healthy_modules)
                },
                "robots": {
                    "active": len(active_robots),
                    "total_processed": sum(m.total_robots_processed for m in modules)
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "overall_status": "UNHEALTHY",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }

    async def get_performance_metrics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Obtener métricas de performance del sistema"""
        try:
            # Get system-wide metrics
            system_metrics = await self.state_manager.get_performance_metrics(
                time_range_hours=time_range_hours
            )
            
            # Get cache performance
            cache_stats = await self.cache_manager.get_cache_stats()
            cache_hit_rate = await self.cache_manager.get_hit_rate()
            
            # Get performance tracker metrics
            tracker_metrics = await self.performance_tracker.get_metrics()
            
            return {
                "system_metrics": system_metrics,
                "cache_performance": {
                    "hit_rate": cache_hit_rate,
                    "stats": cache_stats
                },
                "operation_metrics": tracker_metrics,
                "targets": PERFORMANCE_TARGETS,
                "time_range_hours": time_range_hours,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
