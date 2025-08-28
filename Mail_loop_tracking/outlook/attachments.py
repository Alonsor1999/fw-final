"""
Módulo para descarga y gestión de adjuntos de correos.

Este módulo proporciona funcionalidades para:
- Descarga de adjuntos desde Microsoft Graph API
- Validación de archivos descargados
- Gestión de errores durante la descarga
"""
import os
import base64
import hashlib
from typing import List, Dict, Optional
from outlook.graph_client import get_authenticated_session, make_graph_request
from config import GRAPH_API_ENDPOINT, MAIL_USER, ATTACHMENTS_DIR
from utils.logger_config import setup_logger
from utils.retry_utils import retry_on_failure, MessageProcessingError

logger = setup_logger("attachments")

@retry_on_failure(max_retries=3, delay=1.0)
def download_attachments(message_id: str) -> List[str]:
    """
    Descarga todos los adjuntos de un mensaje específico.
    
    Args:
        message_id: ID del mensaje del cual descargar adjuntos
        
    Returns:
        List[str]: Lista de rutas de archivos descargados
        
    Raises:
        MessageProcessingError: Si hay error en el procesamiento del mensaje
    """
    logger.debug(f"Intentando obtener adjuntos del mensaje ID: {message_id}")
    
    try:
        session = get_authenticated_session()
        url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/messages/{message_id}/attachments"

        # Usar la función mejorada de graph_client
        response = make_graph_request(session, "GET", url)
        
        if not response.ok:
            error_msg = f"Fallo al obtener adjuntos: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            raise MessageProcessingError(error_msg)

        attachments = response.json().get("value", [])
        
        # Crear directorio si no existe
        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
        
        logger.info(f"📎 {len(attachments)} adjuntos encontrados en el mensaje {message_id}")
        
        downloaded_files = []
        
        for attachment in attachments:
            try:
                file_path = _process_attachment(attachment, message_id)
                if file_path:
                    downloaded_files.append(file_path)
            except Exception as e:
                logger.error(f"❌ Error procesando adjunto: {e}")
                continue
        
        logger.info(f"✅ {len(downloaded_files)} adjuntos descargados exitosamente")
        return downloaded_files
        
    except Exception as e:
        logger.exception(f"Excepción al descargar adjuntos del mensaje {message_id}")
        raise MessageProcessingError(f"Error descargando adjuntos: {str(e)}")

def _process_attachment(attachment: Dict, message_id: str) -> Optional[str]:
    """
    Procesa un adjunto individual.
    
    Args:
        attachment: Diccionario con información del adjunto
        message_id: ID del mensaje para logging
        
    Returns:
        str: Ruta del archivo guardado, None si hay error
    """
    try:
        # Verificar que el adjunto tenga contenido
        if "@odata.mediaContentType" not in attachment:
            logger.warning(f"⚠️ Adjunto sin tipo de contenido en mensaje {message_id}")
            return None
        
        file_name = attachment.get("name", "adjunto_sin_nombre")
        content_type = attachment.get("@odata.mediaContentType", "")
        content_bytes = attachment.get("contentBytes", "")
        
        if not content_bytes:
            logger.warning(f"⚠️ Adjunto '{file_name}' sin contenido en mensaje {message_id}")
            return None
        
        # Validar y limpiar nombre de archivo
        safe_file_name = _sanitize_filename(file_name)
        
        # Crear nombre único con hash del contenido
        content_hash = hashlib.md5(content_bytes.encode()).hexdigest()[:8]
        unique_file_name = f"{content_hash}_{safe_file_name}"
        
        file_path = os.path.join(ATTACHMENTS_DIR, unique_file_name)
        
        # Verificar si el archivo ya existe
        if os.path.exists(file_path):
            logger.info(f"📄 Archivo ya existe, saltando: {unique_file_name}")
            return file_path
        
        # Decodificar y guardar archivo
        try:
            decoded_content = base64.b64decode(content_bytes)
            
            with open(file_path, "wb") as f:
                f.write(decoded_content)
            
            # Verificar que el archivo se guardó correctamente
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logger.info(f"✅ Adjunto guardado: {unique_file_name} ({len(decoded_content)} bytes)")
                return file_path
            else:
                logger.error(f"❌ Error: archivo no se guardó correctamente: {unique_file_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error al guardar el adjunto {file_name}: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error procesando adjunto en mensaje {message_id}: {str(e)}")
        return None

def _sanitize_filename(filename: str) -> str:
    """
    Sanitiza el nombre de archivo para evitar problemas de seguridad.
    
    Args:
        filename: Nombre original del archivo
        
    Returns:
        str: Nombre sanitizado
    """
    # Caracteres peligrosos a reemplazar
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    
    sanitized = filename
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Limitar longitud
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized

def get_attachment_info(message_id: str) -> List[Dict]:
    """
    Obtiene información de los adjuntos sin descargarlos.
    
    Args:
        message_id: ID del mensaje
        
    Returns:
        List[Dict]: Lista con información de adjuntos
    """
    logger.debug(f"Obteniendo información de adjuntos del mensaje {message_id}")
    
    try:
        session = get_authenticated_session()
        url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/messages/{message_id}/attachments"
        
        response = make_graph_request(session, "GET", url)
        
        if not response.ok:
            logger.error(f"❌ Error obteniendo información de adjuntos: {response.status_code}")
            return []
        
        attachments = response.json().get("value", [])
        
        attachment_info = []
        for attachment in attachments:
            info = {
                "name": attachment.get("name", "Sin nombre"),
                "content_type": attachment.get("@odata.mediaContentType", "Desconocido"),
                "size": attachment.get("size", 0),
                "id": attachment.get("id", "")
            }
            attachment_info.append(info)
        
        logger.info(f"📋 Información de {len(attachment_info)} adjuntos obtenida")
        return attachment_info
        
    except Exception as e:
        logger.exception(f"Error obteniendo información de adjuntos: {e}")
        return []

def cleanup_old_attachments(max_age_days: int = 30) -> int:
    """
    Limpia adjuntos antiguos del directorio de adjuntos.
    
    Args:
        max_age_days: Edad máxima en días para mantener archivos
        
    Returns:
        int: Número de archivos eliminados
    """
    import time
    from datetime import datetime, timedelta
    
    logger.info(f"🧹 Limpiando adjuntos más antiguos de {max_age_days} días")
    
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    deleted_count = 0
    
    try:
        if not os.path.exists(ATTACHMENTS_DIR):
            logger.info("📁 Directorio de adjuntos no existe, nada que limpiar")
            return 0
        
        for filename in os.listdir(ATTACHMENTS_DIR):
            file_path = os.path.join(ATTACHMENTS_DIR, filename)
            
            if os.path.isfile(file_path):
                file_age = os.path.getmtime(file_path)
                
                if file_age < cutoff_time:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.debug(f"🗑️ Eliminado archivo antiguo: {filename}")
                    except Exception as e:
                        logger.error(f"❌ Error eliminando archivo {filename}: {e}")
        
        logger.info(f"✅ Limpieza completada: {deleted_count} archivos eliminados")
        return deleted_count
        
    except Exception as e:
        logger.exception(f"Error durante limpieza de adjuntos: {e}")
        return deleted_count
