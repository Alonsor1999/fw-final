import asyncio
import asyncpg
import logging
from typing import Dict, List, Optional, Any
from framework.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager para operaciones de base de datos PostgreSQL"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.connection: Optional[asyncpg.Connection] = None
    
    async def initialize(self):
        """Inicializar conexión a PostgreSQL"""
        try:
            # Detectar si estamos ejecutando desde fuera del contenedor
            import socket
            try:
                # Intentar conectar a 'postgres' (hostname interno)
                socket.gethostbyname('postgres')
                host = settings.POSTGRES_HOST
            except socket.gaierror:
                # Si no funciona, usar localhost (fuera del contenedor)
                host = 'localhost'
                logger.info(f"Using localhost for database connection (outside container)")
            
            self.pool = await asyncpg.create_pool(
                host=host,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                min_size=1,
                max_size=10
            )
            logger.info(f"DatabaseManager initialized successfully with host: {host}")
        except Exception as e:
            logger.error(f"Failed to initialize DatabaseManager: {e}")
            raise
    
    async def close(self):
        """Cerrar conexiones"""
        if self.pool:
            await self.pool.close()
            logger.info("DatabaseManager closed")
    
    async def create_robot_schema(self, robot_id: str) -> bool:
        """Crear esquema para un robot específico"""
        try:
            async with self.pool.acquire() as conn:
                # Crear el esquema
                schema_name = f"robot{robot_id}"
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                
                # Crear tabla CASES_TRANSACTIONS
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.cases_transactions (
                        id SERIAL PRIMARY KEY,
                        case_id VARCHAR(50) NOT NULL,
                        transaction_type VARCHAR(100) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data JSONB,
                        priority INTEGER DEFAULT 1,
                        assigned_to VARCHAR(100),
                        notes TEXT
                    )
                """)
                
                # Crear tabla AUDITS_EVENTS
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.audits_events (
                        id SERIAL PRIMARY KEY,
                        event_type VARCHAR(100) NOT NULL,
                        event_source VARCHAR(100) NOT NULL,
                        event_data JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id VARCHAR(100),
                        session_id VARCHAR(100),
                        ip_address INET,
                        user_agent TEXT
                    )
                """)
                
                # Crear tabla CASES_HISTORICAL
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.cases_historical (
                        id SERIAL PRIMARY KEY,
                        case_id VARCHAR(50) NOT NULL,
                        action_type VARCHAR(100) NOT NULL,
                        action_description TEXT,
                        performed_by VARCHAR(100),
                        performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        previous_state JSONB,
                        new_state JSONB,
                        changes_summary TEXT
                    )
                """)
                
                # Crear tabla Abogados
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.abogados (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(200) NOT NULL,
                        apellido VARCHAR(200) NOT NULL,
                        email VARCHAR(255) UNIQUE,
                        telefono VARCHAR(20),
                        especialidad VARCHAR(100),
                        colegio_abogados VARCHAR(100),
                        numero_colegiado VARCHAR(50),
                        estado VARCHAR(50) DEFAULT 'activo',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crear tabla Ciudadanos
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.ciudadanos (
                        id SERIAL PRIMARY KEY,
                        dni VARCHAR(20) UNIQUE NOT NULL,
                        nombre VARCHAR(200) NOT NULL,
                        apellido VARCHAR(200) NOT NULL,
                        email VARCHAR(255),
                        telefono VARCHAR(20),
                        direccion TEXT,
                        fecha_nacimiento DATE,
                        estado VARCHAR(50) DEFAULT 'activo',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crear índices para mejor rendimiento
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_cases_case_id ON {schema_name}.cases_transactions(case_id)")
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_audits_timestamp ON {schema_name}.audits_events(timestamp)")
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_historical_case_id ON {schema_name}.cases_historical(case_id)")
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_abogados_email ON {schema_name}.abogados(email)")
                await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{schema_name}_ciudadanos_dni ON {schema_name}.ciudadanos(dni)")
                
                logger.info(f"Schema {schema_name} and tables created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create schema {robot_id}: {e}")
            return False
    
    async def drop_robot_schema(self, robot_id: str) -> bool:
        """Eliminar esquema de un robot"""
        try:
            async with self.pool.acquire() as conn:
                schema_name = f"robot{robot_id}"
                await conn.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
                logger.info(f"Schema {schema_name} dropped successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to drop schema {robot_id}: {e}")
            return False
    
    async def get_robot_schemas(self) -> List[str]:
        """Obtener lista de esquemas de robots"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name LIKE 'robot%'
                    ORDER BY schema_name
                """
                rows = await conn.fetch(query)
                return [row['schema_name'] for row in rows]
        except Exception as e:
            logger.error(f"Failed to get robot schemas: {e}")
            return []
    
    async def get_schema_info(self, robot_id: str) -> Dict[str, Any]:
        """Obtener información detallada del esquema de un robot"""
        try:
            async with self.pool.acquire() as conn:
                schema_name = f"robot{robot_id}"
                
                # Verificar si el esquema existe
                schema_exists = await conn.fetchval(f"""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.schemata 
                        WHERE schema_name = $1
                    )
                """, schema_name)
                
                if not schema_exists:
                    return {"exists": False, "message": f"Schema {schema_name} does not exist"}
                
                # Obtener tablas del esquema
                tables_query = """
                    SELECT table_name, table_type
                    FROM information_schema.tables 
                    WHERE table_schema = $1
                    ORDER BY table_name
                """
                tables = await conn.fetch(tables_query, schema_name)
                
                # Obtener conteo de registros por tabla
                table_counts = {}
                for table in tables:
                    table_name = table['table_name']
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {schema_name}.{table_name}")
                    table_counts[table_name] = count
                
                return {
                    "exists": True,
                    "schema_name": schema_name,
                    "tables": [table['table_name'] for table in tables],
                    "table_counts": table_counts,
                    "total_tables": len(tables)
                }
                
        except Exception as e:
            logger.error(f"Failed to get schema info for {robot_id}: {e}")
            return {"exists": False, "error": str(e)}
    
    async def insert_case_transaction(self, robot_id: str, case_data: Dict[str, Any]) -> bool:
        """Insertar transacción de caso"""
        try:
            async with self.pool.acquire() as conn:
                schema_name = f"robot{robot_id}"
                query = f"""
                    INSERT INTO {schema_name}.cases_transactions 
                    (case_id, transaction_type, status, data, priority, assigned_to, notes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                await conn.execute(
                    query,
                    case_data.get('case_id'),
                    case_data.get('transaction_type'),
                    case_data.get('status', 'pending'),
                    case_data.get('data'),
                    case_data.get('priority', 1),
                    case_data.get('assigned_to'),
                    case_data.get('notes')
                )
                return True
        except Exception as e:
            logger.error(f"Failed to insert case transaction: {e}")
            return False
    
    async def insert_audit_event(self, robot_id: str, event_data: Dict[str, Any]) -> bool:
        """Insertar evento de auditoría"""
        try:
            async with self.pool.acquire() as conn:
                schema_name = f"robot{robot_id}"
                query = f"""
                    INSERT INTO {schema_name}.audits_events 
                    (event_type, event_source, event_data, user_id, session_id, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                await conn.execute(
                    query,
                    event_data.get('event_type'),
                    event_data.get('event_source'),
                    event_data.get('event_data'),
                    event_data.get('user_id'),
                    event_data.get('session_id'),
                    event_data.get('ip_address'),
                    event_data.get('user_agent')
                )
                return True
        except Exception as e:
            logger.error(f"Failed to insert audit event: {e}")
            return False
    
    async def archive_case(self, robot_id: str, case_id: str, action_data: Dict[str, Any]) -> bool:
        """Archivar caso en histórico"""
        try:
            async with self.pool.acquire() as conn:
                schema_name = f"robot{robot_id}"
                
                # Obtener estado actual del caso
                current_case = await conn.fetchrow(f"""
                    SELECT * FROM {schema_name}.cases_transactions 
                    WHERE case_id = $1
                """, case_id)
                
                if current_case:
                    # Insertar en histórico
                    await conn.execute(f"""
                        INSERT INTO {schema_name}.cases_historical 
                        (case_id, action_type, action_description, performed_by, previous_state, new_state, changes_summary)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    case_id,
                    action_data.get('action_type'),
                    action_data.get('action_description'),
                    action_data.get('performed_by'),
                    dict(current_case),
                    action_data.get('new_state'),
                    action_data.get('changes_summary')
                    )
                    
                    # Actualizar estado en tabla principal
                    await conn.execute(f"""
                        UPDATE {schema_name}.cases_transactions 
                        SET status = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE case_id = $2
                    """, action_data.get('new_status', 'archived'), case_id)
                    
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to archive case: {e}")
            return False
