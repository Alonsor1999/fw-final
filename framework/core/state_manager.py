"""
StateManager MVP - Gestor de persistencia optimizado
"""
import asyncio
import asyncpg
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from framework.config import settings
from framework.models.robot import Robot, RobotCreate, RobotUpdate
from framework.models.module import Module, ModuleCreate, ModuleUpdate, ModuleHealth
from framework.models.execution import RobotExecute, ExecutionCreate, ExecutionUpdate, ExecutionState

logger = logging.getLogger(__name__)


class CircuitBreakerMVP:
    """Circuit Breaker simplificado para protección contra DB overload"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    async def protect(self):
        """Proteger operación con circuit breaker"""
        if self.state == 'OPEN':
            if (datetime.utcnow() - self.last_failure_time).total_seconds() > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        return self

    async def __aenter__(self):
        """Async context manager entry"""
        if self.state == 'OPEN':
            if (datetime.utcnow() - self.last_failure_time).total_seconds() > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()

    def record_success(self):
        """Registrar éxito y resetear circuit breaker"""
        self.failure_count = 0
        self.state = 'CLOSED'

    def record_failure(self):
        """Registrar fallo y posiblemente abrir circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


class StateManager:
    """Gestor de persistencia optimizado con connection pooling y performance tracking"""
    
    def __init__(self):
        self.read_pool: Optional[asyncpg.Pool] = None
        self.write_pool: Optional[asyncpg.Pool] = None
        self.circuit_breaker = CircuitBreakerMVP(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
        self._initialized = False

    async def initialize(self):
        """Inicializar connection pools"""
        if self._initialized:
            return

        try:
            # Read pool para operaciones de lectura
            self.read_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=settings.DATABASE_POOL_MIN_SIZE,
                max_size=settings.DATABASE_POOL_MAX_SIZE,
                command_timeout=settings.DATABASE_POOL_TIMEOUT
            )

            # Write pool para operaciones de escritura
            self.write_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=1,
                max_size=5,
                command_timeout=settings.DATABASE_POOL_TIMEOUT
            )

            self._initialized = True
            logger.info("StateManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize StateManager: {e}")
            raise

    async def close(self):
        """Cerrar connection pools"""
        if self.read_pool:
            await self.read_pool.close()
        if self.write_pool:
            await self.write_pool.close()
        logger.info("StateManager closed")

    @asynccontextmanager
    async def get_read_connection(self):
        """Obtener conexión de lectura"""
        if not self._initialized:
            await self.initialize()
        
        async with self.circuit_breaker:
            async with self.read_pool.acquire() as conn:
                try:
                    yield conn
                except Exception as e:
                    raise

    @asynccontextmanager
    async def get_write_connection(self):
        """Obtener conexión de escritura"""
        if not self._initialized:
            await self.initialize()
        
        async with self.circuit_breaker:
            async with self.write_pool.acquire() as conn:
                try:
                    yield conn
                except Exception as e:
                    raise

    # Robot Operations
    async def create_robot(self, robot_data: RobotCreate) -> Robot:
        """Crear robot simple con registro en base de datos"""
        start_time = datetime.utcnow()
        
        robot_id = f"robot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{asyncio.current_task().get_name()}"
        
        async with self.get_write_connection() as conn:
            # INSERT simple para registro de robot
            query = """
                INSERT INTO robots (
                    robot_id, robot_name, description, robot_type, status, config_data, tags
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """
            
            row = await conn.fetchrow(
                query,
                robot_id,
                robot_data.robot_name,
                robot_data.description,
                robot_data.robot_type,
                "active",
                json.dumps(robot_data.config_data),
                robot_data.tags
            )

        # Crear esquema y tablas automáticamente para el robot
        try:
            from framework.core.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            await db_manager.initialize()
            
            schema_created = await db_manager.create_robot_schema(robot_id)
            if schema_created:
                logger.info(f"Schema y tablas creadas automáticamente para robot: {robot_id}")
            else:
                logger.warning(f"No se pudieron crear las tablas para robot: {robot_id}")
                
            await db_manager.close()
            
        except Exception as e:
            logger.error(f"Error al crear esquema para robot {robot_id}: {e}")
            # No fallar la creación del robot si falla la creación del esquema

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"Robot created in {processing_time:.2f}ms: {robot_id}")
        
        # Convertir config_data de JSON string a dict si es necesario
        robot_dict = dict(row)
        if isinstance(robot_dict.get('config_data'), str):
            try:
                robot_dict['config_data'] = json.loads(robot_dict['config_data'])
            except json.JSONDecodeError:
                logger.warning(f"Error parsing config_data JSON for robot {robot_id}, using empty dict")
                robot_dict['config_data'] = {}
        
        return Robot(**robot_dict)

    async def get_robot(self, robot_id: str) -> Optional[Robot]:
        """Obtener robot por ID"""
        async with self.get_read_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM robots WHERE robot_id = $1",
                robot_id
            )
            if not row:
                return None
            
            # Convertir config_data de JSON string a dict si es necesario
            robot_dict = dict(row)
            if isinstance(robot_dict.get('config_data'), str):
                try:
                    robot_dict['config_data'] = json.loads(robot_dict['config_data'])
                except json.JSONDecodeError:
                    logger.warning(f"Error parsing config_data JSON for robot {robot_id}, using empty dict")
                    robot_dict['config_data'] = {}
            
            return Robot(**robot_dict)

    async def update_robot(self, robot_id: str, update_data: RobotUpdate) -> Optional[Robot]:
        """Actualizar robot con estructura simple"""
        async with self.get_write_connection() as conn:
            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1
            
            if update_data.robot_name:
                set_clauses.append(f"robot_name = ${param_count}")
                values.append(update_data.robot_name)
                param_count += 1
            
            if update_data.description is not None:
                set_clauses.append(f"description = ${param_count}")
                values.append(update_data.description)
                param_count += 1
            
            if update_data.robot_type:
                set_clauses.append(f"robot_type = ${param_count}")
                values.append(update_data.robot_type)
                param_count += 1
            
            if update_data.status:
                set_clauses.append(f"status = ${param_count}")
                values.append(update_data.status)
                param_count += 1
            
            if update_data.config_data is not None:
                set_clauses.append(f"config_data = ${param_count}")
                values.append(json.dumps(update_data.config_data))
                param_count += 1
            
            if update_data.tags is not None:
                set_clauses.append(f"tags = ${param_count}")
                values.append(update_data.tags)
                param_count += 1
            
            if not set_clauses:
                return await self.get_robot(robot_id)
            
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1
            
            values.append(robot_id)
            
            query = f"""
                UPDATE robots 
                SET {', '.join(set_clauses)}
                WHERE robot_id = ${param_count}
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *values)
            if not row:
                return None
            
            # Convertir config_data de JSON string a dict si es necesario
            robot_dict = dict(row)
            if isinstance(robot_dict.get('config_data'), str):
                try:
                    robot_dict['config_data'] = json.loads(robot_dict['config_data'])
                except json.JSONDecodeError:
                    logger.warning(f"Error parsing config_data JSON for robot {robot_id}, using empty dict")
                    robot_dict['config_data'] = {}
            
            return Robot(**robot_dict)

    async def get_active_robots(self, limit: int = 100) -> List[Robot]:
        """Obtener robots activos"""
        async with self.get_read_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM robots 
                WHERE status = 'active'
                ORDER BY created_at ASC
                LIMIT $1
                """,
                limit
            )
            robots = []
            for row in rows:
                # Convertir config_data de JSON string a dict si es necesario
                robot_dict = dict(row)
                if isinstance(robot_dict.get('config_data'), str):
                    try:
                        robot_dict['config_data'] = json.loads(robot_dict['config_data'])
                    except json.JSONDecodeError:
                        logger.warning(f"Error parsing config_data JSON for robot {robot_dict.get('robot_id', 'unknown')}, using empty dict")
                        robot_dict['config_data'] = {}
                robots.append(Robot(**robot_dict))
            return robots

    async def get_robots_by_type(self, robot_type: str, status: Optional[str] = None) -> List[Robot]:
        """Obtener robots por tipo"""
        async with self.get_read_connection() as conn:
            if status:
                rows = await conn.fetch(
                    "SELECT * FROM robots WHERE robot_type = $1 AND status = $2 ORDER BY created_at DESC",
                    robot_type, status
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM robots WHERE robot_type = $1 ORDER BY created_at DESC",
                    robot_type
                )
            robots = []
            for row in rows:
                # Convertir config_data de JSON string a dict si es necesario
                robot_dict = dict(row)
                if isinstance(robot_dict.get('config_data'), str):
                    try:
                        robot_dict['config_data'] = json.loads(robot_dict['config_data'])
                    except json.JSONDecodeError:
                        logger.warning(f"Error parsing config_data JSON for robot {robot_dict.get('robot_id', 'unknown')}, using empty dict")
                        robot_dict['config_data'] = {}
                robots.append(Robot(**robot_dict))
            return robots

    # Module Operations
    async def register_module(self, module_data: ModuleCreate) -> Module:
        """Registrar módulo nuevo"""
        module_id = f"{module_data.module_name}_{module_data.module_version}_{settings.ENVIRONMENT}"
        
        async with self.get_write_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO module_registry (
                    module_id, module_name, module_version, supported_robot_types,
                    health_endpoint, registration_data, security_level
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                module_id,
                module_data.module_name,
                module_data.module_version,
                module_data.supported_robot_types,
                module_data.health_endpoint,
                json.dumps(module_data.registration_data),
                module_data.security_level.value
            )
            return Module(**dict(row))

    async def get_module(self, module_name: str) -> Optional[Module]:
        """Obtener módulo por nombre"""
        async with self.get_read_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM module_registry WHERE module_name = $1",
                module_name
            )
            if row:
                row_dict = dict(row)
                # Parse JSON fields
                if isinstance(row_dict.get('registration_data'), str):
                    row_dict['registration_data'] = json.loads(row_dict['registration_data'])
                if isinstance(row_dict.get('compliance_flags'), str):
                    row_dict['compliance_flags'] = json.loads(row_dict['compliance_flags'])
                if isinstance(row_dict.get('enterprise_features'), str):
                    row_dict['enterprise_features'] = json.loads(row_dict['enterprise_features'])
                return Module(**row_dict)
            return None

    async def get_active_modules(self) -> List[Module]:
        """Obtener módulos activos para routing"""
        async with self.get_read_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM module_registry 
                WHERE is_active = true AND health_status = 'HEALTHY'
                ORDER BY performance_score DESC, capacity_utilization ASC
                """
            )
            modules = []
            for row in rows:
                row_dict = dict(row)
                # Parse JSON fields
                if isinstance(row_dict.get('registration_data'), str):
                    row_dict['registration_data'] = json.loads(row_dict['registration_data'])
                if isinstance(row_dict.get('compliance_flags'), str):
                    row_dict['compliance_flags'] = json.loads(row_dict['compliance_flags'])
                if isinstance(row_dict.get('enterprise_features'), str):
                    row_dict['enterprise_features'] = json.loads(row_dict['enterprise_features'])
                modules.append(Module(**row_dict))
            return modules

    async def update_module_performance(self, module_name: str, performance_data: Dict[str, Any]):
        """Actualizar métricas de performance del módulo"""
        async with self.get_write_connection() as conn:
            await conn.execute(
                """
                UPDATE module_registry 
                SET performance_score = $2,
                    performance_tier = $3,
                    avg_processing_time_ms = $4,
                    capacity_utilization = $5,
                    last_performance_check = NOW(),
                    updated_at = NOW()
                WHERE module_name = $1
                """,
                module_name,
                performance_data.get('performance_score', 1.0),
                performance_data.get('performance_tier', 'MEDIUM'),
                performance_data.get('avg_processing_time_ms', 0),
                performance_data.get('capacity_utilization', 0.0)
            )

    async def update_module_health(self, module_name: str, health_data: Dict[str, Any]):
        """Actualizar estado de salud del módulo"""
        async with self.get_write_connection() as conn:
            await conn.execute(
                """
                UPDATE module_registry 
                SET health_status = $2,
                    last_health_check = NOW(),
                    consecutive_failures = $3,
                    last_error_message = $4,
                    updated_at = NOW()
                WHERE module_name = $1
                """,
                module_name,
                health_data.get('health_status', 'UNKNOWN'),
                health_data.get('consecutive_failures', 0),
                health_data.get('last_error_message')
            )

    # Execution Operations
    async def create_execution(self, execution_data: ExecutionCreate) -> RobotExecute:
        """Crear ejecución de robot"""
        execute_id = f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{asyncio.current_task().get_name()}"
        
        async with self.get_write_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO robot_execute (
                    execute_id, robot_id, module_name, execution_state,
                    total_steps, timeout_seconds, max_retries,
                    contains_sensitive_data, compliance_context
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                """,
                execute_id,
                execution_data.robot_id,
                execution_data.module_name,
                ExecutionState.PENDING.value,
                execution_data.total_steps,
                execution_data.timeout_seconds,
                execution_data.max_retries,
                execution_data.contains_sensitive_data,
                json.dumps(execution_data.compliance_context)
            )
            
            # Convertir campos JSON de string a dict si es necesario
            execution_dict = dict(row)
            json_fields = ['step_details', 'resource_peak_usage', 'execution_metadata', 'compliance_context']
            
            for field in json_fields:
                if isinstance(execution_dict.get(field), str):
                    try:
                        execution_dict[field] = json.loads(execution_dict[field])
                    except json.JSONDecodeError:
                        logger.warning(f"Error parsing {field} JSON for execution {execute_id}, using empty dict")
                        execution_dict[field] = {}
            
            return RobotExecute(**execution_dict)

    async def update_execution(self, execute_id: str, update_data: ExecutionUpdate) -> Optional[RobotExecute]:
        """Actualizar ejecución de robot"""
        async with self.get_write_connection() as conn:
            # Build dynamic update query similar to robot update
            set_clauses = []
            values = []
            param_count = 1
            
            if update_data.execution_state:
                set_clauses.append(f"execution_state = ${param_count}")
                values.append(update_data.execution_state.value)
                param_count += 1
            
            if update_data.current_step:
                set_clauses.append(f"current_step = ${param_count}")
                values.append(update_data.current_step)
                param_count += 1
            
            if update_data.progress_percentage is not None:
                set_clauses.append(f"progress_percentage = ${param_count}")
                values.append(update_data.progress_percentage)
                param_count += 1
            
            if update_data.completed_steps is not None:
                set_clauses.append(f"completed_steps = ${param_count}")
                values.append(update_data.completed_steps)
                param_count += 1
            
            if update_data.cpu_usage_percent is not None:
                set_clauses.append(f"cpu_usage_percent = ${param_count}")
                values.append(update_data.cpu_usage_percent)
                param_count += 1
            
            if update_data.memory_usage_mb is not None:
                set_clauses.append(f"memory_usage_mb = ${param_count}")
                values.append(update_data.memory_usage_mb)
                param_count += 1
            
            if update_data.efficiency_score is not None:
                set_clauses.append(f"efficiency_score = ${param_count}")
                values.append(update_data.efficiency_score)
                param_count += 1
            
            if update_data.error_message:
                set_clauses.append(f"error_message = ${param_count}")
                values.append(update_data.error_message)
                param_count += 1
            
            # Add completion timestamp
            if update_data.execution_state in [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED]:
                set_clauses.append(f"completed_at = ${param_count}")
                values.append(datetime.utcnow())
                param_count += 1
            
            if not set_clauses:
                return await self.get_execution(execute_id)
            
            values.append(execute_id)
            
            query = f"""
                UPDATE robot_execute 
                SET {', '.join(set_clauses)}
                WHERE execute_id = ${param_count}
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *values)
            return RobotExecute(**dict(row)) if row else None

    async def get_execution(self, execute_id: str) -> Optional[RobotExecute]:
        """Obtener ejecución por ID"""
        async with self.get_read_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM robot_execute WHERE execute_id = $1",
                execute_id
            )
            if not row:
                return None
            
            # Convertir campos JSON de string a dict si es necesario
            execution_dict = dict(row)
            json_fields = ['step_details', 'resource_peak_usage', 'execution_metadata', 'compliance_context']
            
            for field in json_fields:
                if isinstance(execution_dict.get(field), str):
                    try:
                        execution_dict[field] = json.loads(execution_dict[field])
                    except json.JSONDecodeError:
                        logger.warning(f"Error parsing {field} JSON for execution {execute_id}, using empty dict")
                        execution_dict[field] = {}
            
            return RobotExecute(**execution_dict)

    async def get_active_executions(self) -> List[RobotExecute]:
        """Obtener ejecuciones activas"""
        async with self.get_read_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM robot_execute 
                WHERE execution_state IN ('PENDING', 'RUNNING', 'RETRYING', 'PAUSED')
                ORDER BY started_at ASC
                """
            )
            return [RobotExecute(**dict(row)) for row in rows]

    # Performance Analytics
    async def get_robot_stats(self, robot_type: Optional[str] = None, 
                            time_range_hours: int = 24) -> Dict[str, Any]:
        """Obtener estadísticas de robots"""
        async with self.get_read_connection() as conn:
            since_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            if robot_type:
                # Robot type-specific metrics
                robot_stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total_robots,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                        COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count
                    FROM robots 
                    WHERE robot_type = $1 AND created_at >= $2
                    """,
                    robot_type, since_time
                )
            else:
                # System-wide metrics
                robot_stats = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total_robots,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                        COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count
                    FROM robots 
                    WHERE created_at >= $1
                    """,
                    since_time
                )
            
            return dict(robot_stats) if robot_stats else {}

    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Limpiar datos antiguos para mantener performance"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        async with self.get_write_connection() as conn:
            # Cleanup old executions
            await conn.execute(
                "DELETE FROM robot_execute WHERE completed_at < $1",
                cutoff_date
            )
            
            # Cleanup old inactive robots
            await conn.execute(
                "DELETE FROM robots WHERE created_at < $1 AND status = 'inactive'",
                cutoff_date
            )
            
            logger.info(f"Cleaned up data older than {days_to_keep} days")
