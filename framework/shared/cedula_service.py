"""
Servicio para manejar operaciones de cédulas y fechas de expedición
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import logging
from ..models.cedula import CedulaExpedicion, CedulaExpedicionCreate, CedulaExpedicionUpdate, CedulaExpedicionResponse

logger = logging.getLogger(__name__)


class CedulaService:
    """Servicio para operaciones de cédulas"""
    
    def __init__(self, database_url: str):
        """Inicializar servicio con URL de base de datos"""
        self.database_url = database_url
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            raise
    
    def create_cedula(self, cedula_data: CedulaExpedicionCreate) -> CedulaExpedicionResponse:
        """Crear nuevo registro de cédula"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                    INSERT INTO cedulas_expedicion (cedula, fecha_expedicion, fecha_texto, observaciones)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, cedula, fecha_expedicion, fecha_texto, estado, observaciones, created_at, updated_at
                    """
                    cur.execute(query, (
                        cedula_data.cedula,
                        cedula_data.fecha_expedicion,
                        cedula_data.fecha_texto,
                        cedula_data.observaciones
                    ))
                    result = cur.fetchone()
                    return CedulaExpedicionResponse(**dict(result))
        except Exception as e:
            logger.error(f"Error creando cédula: {e}")
            raise
    
    def get_cedula_by_id(self, cedula_id: int) -> Optional[CedulaExpedicionResponse]:
        """Obtener cédula por ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                    SELECT id, cedula, fecha_expedicion, fecha_texto, estado, observaciones, created_at, updated_at
                    FROM cedulas_expedicion
                    WHERE id = %s
                    """
                    cur.execute(query, (cedula_id,))
                    result = cur.fetchone()
                    if result:
                        return CedulaExpedicionResponse(**dict(result))
                    return None
        except Exception as e:
            logger.error(f"Error obteniendo cédula por ID: {e}")
            raise
    
    def get_cedula_by_number(self, cedula: str) -> Optional[CedulaExpedicionResponse]:
        """Obtener cédula por número"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                    SELECT id, cedula, fecha_expedicion, fecha_texto, estado, observaciones, created_at, updated_at
                    FROM cedulas_expedicion
                    WHERE cedula = %s
                    """
                    cur.execute(query, (cedula,))
                    result = cur.fetchone()
                    if result:
                        return CedulaExpedicionResponse(**dict(result))
                    return None
        except Exception as e:
            logger.error(f"Error obteniendo cédula por número: {e}")
            raise
    
    def get_all_cedulas(self, limit: int = 100, offset: int = 0) -> List[CedulaExpedicionResponse]:
        """Obtener todas las cédulas con paginación"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                    SELECT id, cedula, fecha_expedicion, fecha_texto, estado, observaciones, created_at, updated_at
                    FROM cedulas_expedicion
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """
                    cur.execute(query, (limit, offset))
                    results = cur.fetchall()
                    return [CedulaExpedicionResponse(**dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error obteniendo todas las cédulas: {e}")
            raise
    
    def update_cedula(self, cedula_id: int, cedula_data: CedulaExpedicionUpdate) -> Optional[CedulaExpedicionResponse]:
        """Actualizar registro de cédula"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Construir query dinámicamente basado en campos proporcionados
                    update_fields = []
                    values = []
                    
                    if cedula_data.fecha_expedicion is not None:
                        update_fields.append("fecha_expedicion = %s")
                        values.append(cedula_data.fecha_expedicion)
                    
                    if cedula_data.fecha_texto is not None:
                        update_fields.append("fecha_texto = %s")
                        values.append(cedula_data.fecha_texto)
                    
                    if cedula_data.estado is not None:
                        update_fields.append("estado = %s")
                        values.append(cedula_data.estado)
                    
                    if cedula_data.observaciones is not None:
                        update_fields.append("observaciones = %s")
                        values.append(cedula_data.observaciones)
                    
                    if not update_fields:
                        return self.get_cedula_by_id(cedula_id)
                    
                    update_fields.append("updated_at = NOW()")
                    values.append(cedula_id)
                    
                    query = f"""
                    UPDATE cedulas_expedicion
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING id, cedula, fecha_expedicion, fecha_texto, estado, observaciones, created_at, updated_at
                    """
                    
                    cur.execute(query, values)
                    result = cur.fetchone()
                    if result:
                        return CedulaExpedicionResponse(**dict(result))
                    return None
        except Exception as e:
            logger.error(f"Error actualizando cédula: {e}")
            raise
    
    def delete_cedula(self, cedula_id: int) -> bool:
        """Eliminar registro de cédula"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = "DELETE FROM cedulas_expedicion WHERE id = %s"
                    cur.execute(query, (cedula_id,))
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error eliminando cédula: {e}")
            raise
    
    def search_cedulas(self, search_term: str, limit: int = 100) -> List[CedulaExpedicionResponse]:
        """Buscar cédulas por término de búsqueda"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                    SELECT id, cedula, fecha_expedicion, fecha_texto, estado, observaciones, created_at, updated_at
                    FROM cedulas_expedicion
                    WHERE cedula ILIKE %s OR fecha_texto ILIKE %s OR observaciones ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """
                    search_pattern = f"%{search_term}%"
                    cur.execute(query, (search_pattern, search_pattern, search_pattern, limit))
                    results = cur.fetchall()
                    return [CedulaExpedicionResponse(**dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error buscando cédulas: {e}")
            raise
    
    def get_cedulas_by_estado(self, estado: str, limit: int = 100) -> List[CedulaExpedicionResponse]:
        """Obtener cédulas por estado"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                    SELECT id, cedula, fecha_expedicion, fecha_texto, estado, observaciones, created_at, updated_at
                    FROM cedulas_expedicion
                    WHERE estado = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """
                    cur.execute(query, (estado, limit))
                    results = cur.fetchall()
                    return [CedulaExpedicionResponse(**dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error obteniendo cédulas por estado: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de cédulas"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                    SELECT 
                        COUNT(*) as total_cedulas,
                        COUNT(CASE WHEN estado = 'ACTIVO' THEN 1 END) as activas,
                        COUNT(CASE WHEN estado = 'FECHA_INVALIDA' THEN 1 END) as fechas_invalidas,
                        COUNT(CASE WHEN estado = 'NO_DISPONIBLE_ANI' THEN 1 END) as no_disponibles_ani,
                        COUNT(CASE WHEN fecha_expedicion IS NOT NULL THEN 1 END) as con_fecha_valida
                    FROM cedulas_expedicion
                    """
                    cur.execute(query)
                    result = cur.fetchone()
                    return dict(result)
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            raise
