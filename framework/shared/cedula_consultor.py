"""
Módulo simple para consultar cédulas y fechas de expedición
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class CedulaConsultor:
    """Consultor simple de cédulas para scraping"""
    
    def __init__(self, database_url: Optional[str] = None):
        """Inicializar consultor con URL de base de datos"""
        self.database_url = database_url or os.getenv('DATABASE_URL', 'postgresql://framework_user:framework_pass@localhost:5432/framework_db')
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.error(f"Error conectando a la base de datos: {e}")
            raise
    
    def consultar_cedula(self, cedula: str) -> Optional[Dict[str, str]]:
        """
        Consultar una cédula y retornar sus datos
        
        Args:
            cedula (str): Número de cédula a consultar
            
        Returns:
            Dict con cedula y fecha_expedicion, o None si no se encuentra
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                    SELECT cedula, fecha_expedicion
                    FROM cedulas
                    WHERE cedula = %s
                    """
                    cur.execute(query, (cedula,))
                    result = cur.fetchone()
                    
                    if result:
                        return {
                            'cedula': result['cedula'],
                            'fecha_expedicion': result['fecha_expedicion']
                        }
                    return None
                    
        except Exception as e:
            logger.error(f"Error consultando cédula {cedula}: {e}")
            raise
    
    def consultar_multiples_cedulas(self, cedulas: list) -> Dict[str, Dict[str, str]]:
        """
        Consultar múltiples cédulas de una vez
        
        Args:
            cedulas (list): Lista de números de cédula
            
        Returns:
            Dict con cédulas como clave y sus datos como valor
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Crear placeholders para la consulta IN
                    placeholders = ','.join(['%s'] * len(cedulas))
                    query = f"""
                    SELECT cedula, fecha_expedicion
                    FROM cedulas
                    WHERE cedula IN ({placeholders})
                    """
                    cur.execute(query, cedulas)
                    results = cur.fetchall()
                    
                    # Convertir resultados a diccionario
                    cedulas_dict = {}
                    for result in results:
                        cedulas_dict[result['cedula']] = {
                            'cedula': result['cedula'],
                            'fecha_expedicion': result['fecha_expedicion']
                        }
                    
                    return cedulas_dict
                    
        except Exception as e:
            logger.error(f"Error consultando múltiples cédulas: {e}")
            raise
    
    def verificar_existencia(self, cedula: str) -> bool:
        """
        Verificar si una cédula existe en la base de datos
        
        Args:
            cedula (str): Número de cédula a verificar
            
        Returns:
            bool: True si existe, False si no
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = "SELECT 1 FROM cedulas WHERE cedula = %s"
                    cur.execute(query, (cedula,))
                    return cur.fetchone() is not None
                    
        except Exception as e:
            logger.error(f"Error verificando existencia de cédula {cedula}: {e}")
            raise
    
    def obtener_todas_cedulas(self) -> Dict[str, str]:
        """
        Obtener todas las cédulas y fechas de expedición
        
        Returns:
            Dict con cédulas como clave y fechas como valor
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = "SELECT cedula, fecha_expedicion FROM cedulas ORDER BY cedula"
                    cur.execute(query)
                    results = cur.fetchall()
                    
                    cedulas_dict = {}
                    for result in results:
                        cedulas_dict[result['cedula']] = result['fecha_expedicion']
                    
                    return cedulas_dict
                    
        except Exception as e:
            logger.error(f"Error obteniendo todas las cédulas: {e}")
            raise


# Función de conveniencia para uso rápido
def consultar_cedula_rapido(cedula: str, database_url: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Función de conveniencia para consultar una cédula rápidamente
    
    Args:
        cedula (str): Número de cédula a consultar
        database_url (str, optional): URL de la base de datos
        
    Returns:
        Dict con cedula y fecha_expedicion, o None si no se encuentra
    """
    consultor = CedulaConsultor(database_url)
    return consultor.consultar_cedula(cedula)


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de cómo usar el consultor
    consultor = CedulaConsultor()
    
    # Consultar una cédula
    resultado = consultor.consultar_cedula("1.077.463.022")
    if resultado:
        print(f"Cédula: {resultado['cedula']}")
        print(f"Fecha de expedición: {resultado['fecha_expedicion']}")
    else:
        print("Cédula no encontrada")
    
    # Consultar múltiples cédulas
    cedulas = ["1.077.463.022", "11.811.703", "1077858861"]
    resultados = consultor.consultar_multiples_cedulas(cedulas)
    for cedula, datos in resultados.items():
        print(f"{cedula}: {datos['fecha_expedicion']}")
