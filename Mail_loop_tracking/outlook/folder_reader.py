"""
Módulo para leer correos de carpetas específicas de Outlook
Especialmente diseñado para la carpeta Iniciativa4
"""

from outlook.graph_client import get_authenticated_session
from config import GRAPH_API_ENDPOINT, MAIL_USER
from utils.logger_config import setup_logger
from typing import List, Dict, Optional
import json

logger = setup_logger("folder_reader")

def get_folder_id(folder_name: str) -> Optional[str]:
    """
    Obtiene el ID de una carpeta específica por nombre
    
    Args:
        folder_name: Nombre de la carpeta (ej: "Iniciativa4")
        
    Returns:
        str: ID de la carpeta o None si no se encuentra
    """
    logger.info(f"Buscando carpeta: {folder_name}")
    session = get_authenticated_session()
    
    # Primero buscar en las carpetas principales
    url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/mailFolders"
    
    try:
        response = session.get(url)
        if response.ok:
            folders = response.json().get("value", [])
            
            # Buscar la carpeta por nombre
            for folder in folders:
                if folder.get("displayName", "").lower() == folder_name.lower():
                    folder_id = folder.get("id")
                    logger.info(f"✅ Carpeta '{folder_name}' encontrada con ID: {folder_id}")
                    return folder_id
            
            # Si no se encuentra en carpetas principales, buscar en subcarpetas
            logger.info(f"Carpeta '{folder_name}' no encontrada en carpetas principales, buscando en subcarpetas...")
            
            for folder in folders:
                subfolder_id = _search_in_subfolders(session, folder.get("id"), folder_name)
                if subfolder_id:
                    return subfolder_id
            
            logger.warning(f"❌ Carpeta '{folder_name}' no encontrada")
            return None
        else:
            logger.error(f"Error HTTP al obtener carpetas: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.exception(f"Error buscando carpeta '{folder_name}': {e}")
        return None

def _search_in_subfolders(session, parent_folder_id: str, folder_name: str) -> Optional[str]:
    """
    Busca una carpeta en las subcarpetas de una carpeta padre
    
    Args:
        session: Sesión autenticada
        parent_folder_id: ID de la carpeta padre
        folder_name: Nombre de la carpeta a buscar
        
    Returns:
        str: ID de la carpeta o None si no se encuentra
    """
    url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/mailFolders/{parent_folder_id}/childFolders"
    
    try:
        response = session.get(url)
        if response.ok:
            subfolders = response.json().get("value", [])
            
            for subfolder in subfolders:
                if subfolder.get("displayName", "").lower() == folder_name.lower():
                    subfolder_id = subfolder.get("id")
                    logger.info(f"✅ Carpeta '{folder_name}' encontrada en subcarpetas con ID: {subfolder_id}")
                    return subfolder_id
                
                # Buscar recursivamente en subcarpetas anidadas
                nested_id = _search_in_subfolders(session, subfolder.get("id"), folder_name)
                if nested_id:
                    return nested_id
            
            return None
        else:
            logger.error(f"Error HTTP al obtener subcarpetas: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.exception(f"Error buscando en subcarpetas: {e}")
        return None

def get_messages_from_folder(folder_name: str, top: int = 50, 
                           order_by: str = "receivedDateTime desc") -> List[Dict]:
    """
    Obtiene mensajes de una carpeta específica
    
    Args:
        folder_name: Nombre de la carpeta (ej: "Iniciativa4")
        top: Número máximo de mensajes a obtener
        order_by: Criterio de ordenamiento
        
    Returns:
        List[Dict]: Lista de mensajes de la carpeta
    """
    logger.info(f"Obteniendo {top} mensajes de la carpeta '{folder_name}'")
    
    # Obtener ID de la carpeta
    folder_id = get_folder_id(folder_name)
    if not folder_id:
        logger.error(f"No se pudo encontrar la carpeta '{folder_name}'")
        return []
    
    # Obtener mensajes de la carpeta
    session = get_authenticated_session()
    url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/mailFolders/{folder_id}/messages?$top={top}&$orderby={order_by}"
    
    try:
        response = session.get(url)
        if response.ok:
            messages = response.json().get("value", [])
            logger.info(f"✅ {len(messages)} mensajes obtenidos de la carpeta '{folder_name}'")
            return messages
        else:
            logger.error(f"Error HTTP al obtener mensajes: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.exception(f"Error obteniendo mensajes de la carpeta '{folder_name}': {e}")
        return []

def get_messages_from_folder_with_filter(folder_name: str, 
                                        allowed_senders: Optional[List[str]] = None,
                                        blocked_senders: Optional[List[str]] = None,
                                        subject_keywords: Optional[List[str]] = None,
                                        subject_exclude_keywords: Optional[List[str]] = None,
                                        top: int = 50) -> List[Dict]:
    """
    Obtiene mensajes de una carpeta específica con filtros
    
    Args:
        folder_name: Nombre de la carpeta
        allowed_senders: Lista de remitentes permitidos
        blocked_senders: Lista de remitentes bloqueados
        subject_keywords: Palabras clave que deben estar en el subject
        subject_exclude_keywords: Palabras clave que NO deben estar en el subject
        top: Número máximo de mensajes a obtener
        
    Returns:
        List[Dict]: Lista de mensajes filtrados de la carpeta
    """
    logger.info(f"Obteniendo mensajes filtrados de la carpeta '{folder_name}'")
    
    # Obtener todos los mensajes de la carpeta
    messages = get_messages_from_folder(folder_name, top=top)
    
    if not messages:
        return []
    
    # Aplicar filtros
    filtered_messages = []
    
    for message in messages:
        if _apply_filters(message, allowed_senders, blocked_senders, subject_keywords, subject_exclude_keywords):
            filtered_messages.append(message)
    
    logger.info(f"✅ {len(filtered_messages)} mensajes aprobados por filtros de {len(messages)} totales en '{folder_name}'")
    return filtered_messages

def _apply_filters(message: Dict, 
                  allowed_senders: Optional[List[str]] = None,
                  blocked_senders: Optional[List[str]] = None,
                  subject_keywords: Optional[List[str]] = None,
                  subject_exclude_keywords: Optional[List[str]] = None) -> bool:
    """
    Aplica filtros a un mensaje
    
    Args:
        message: Mensaje a filtrar
        allowed_senders: Remitentes permitidos
        blocked_senders: Remitentes bloqueados
        subject_keywords: Palabras clave requeridas en subject
        subject_exclude_keywords: Palabras clave excluidas del subject
        
    Returns:
        bool: True si el mensaje pasa todos los filtros
    """
    # Extraer información del mensaje
    sender_email = _extract_sender_email(message)
    subject = message.get('subject', '')
    
    # Verificar remitente bloqueado
    if blocked_senders:
        for blocked in blocked_senders:
            if blocked.lower() in sender_email.lower():
                logger.debug(f"Mensaje bloqueado por remitente: {sender_email}")
                return False
    
    # Verificar remitente permitido
    if allowed_senders:
        sender_allowed = False
        for allowed in allowed_senders:
            if allowed.lower() in sender_email.lower():
                sender_allowed = True
                break
        
        if not sender_allowed:
            logger.debug(f"Mensaje rechazado - remitente no permitido: {sender_email}")
            return False
    
    # Verificar palabras excluidas en subject
    if subject_exclude_keywords:
        subject_lower = subject.lower()
        for exclude_keyword in subject_exclude_keywords:
            if exclude_keyword.lower() in subject_lower:
                logger.debug(f"Mensaje rechazado por palabra excluida en subject: '{subject}'")
                return False
    
    # Verificar palabras clave requeridas en subject
    if subject_keywords:
        subject_lower = subject.lower()
        subject_valid = False
        for keyword in subject_keywords:
            if keyword.lower() in subject_lower:
                subject_valid = True
                break
        
        if not subject_valid:
            logger.debug(f"Mensaje rechazado - no contiene palabras clave requeridas: '{subject}'")
            return False
    
    return True

def _extract_sender_email(message: Dict) -> str:
    """
    Extrae el email del remitente del mensaje
    
    Args:
        message: Mensaje de correo
        
    Returns:
        str: Email del remitente
    """
    sender = message.get('from', {})
    if isinstance(sender, dict):
        email = sender.get('emailAddress', {}).get('address', '')
    else:
        email = str(sender)
    
    return email

def get_folder_summary(folder_name: str) -> Dict:
    """
    Obtiene un resumen de la carpeta especificada
    
    Args:
        folder_name: Nombre de la carpeta
        
    Returns:
        Dict: Resumen de la carpeta
    """
    logger.info(f"Generando resumen de la carpeta '{folder_name}'")
    
    # Obtener ID de la carpeta
    folder_id = get_folder_id(folder_name)
    if not folder_id:
        return {
            'success': False,
            'error': f'Carpeta "{folder_name}" no encontrada',
            'folder_name': folder_name
        }
    
    # Obtener información de la carpeta
    session = get_authenticated_session()
    url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/mailFolders/{folder_id}"
    
    try:
        response = session.get(url)
        if response.ok:
            folder_info = response.json()
            
            # Obtener conteo de mensajes
            messages = get_messages_from_folder(folder_name, top=1000)
            
            summary = {
                'success': True,
                'folder_name': folder_name,
                'folder_id': folder_id,
                'total_messages': len(messages),
                'unread_count': folder_info.get('unreadItemCount', 0),
                'total_item_count': folder_info.get('totalItemCount', 0),
                'display_name': folder_info.get('displayName', folder_name),
                'parent_folder_id': folder_info.get('parentFolderId', None)
            }
            
            logger.info(f"✅ Resumen de '{folder_name}': {summary['total_messages']} mensajes, {summary['unread_count']} no leídos")
            return summary
        else:
            logger.error(f"Error HTTP al obtener información de carpeta: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f'Error HTTP {response.status_code}',
                'folder_name': folder_name
            }
            
    except Exception as e:
        logger.exception(f"Error generando resumen de la carpeta '{folder_name}': {e}")
        return {
            'success': False,
            'error': str(e),
            'folder_name': folder_name
        }

def list_available_folders() -> List[Dict]:
    """
    Lista todas las carpetas disponibles
    
    Returns:
        List[Dict]: Lista de carpetas disponibles
    """
    logger.info("Listando carpetas disponibles")
    session = get_authenticated_session()
    url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/mailFolders"
    
    try:
        response = session.get(url)
        if response.ok:
            folders = response.json().get("value", [])
            
            folder_list = []
            for folder in folders:
                folder_info = {
                    'id': folder.get('id'),
                    'display_name': folder.get('displayName'),
                    'total_item_count': folder.get('totalItemCount', 0),
                    'unread_item_count': folder.get('unreadItemCount', 0)
                }
                folder_list.append(folder_info)
            
            logger.info(f"✅ {len(folder_list)} carpetas encontradas")
            return folder_list
        else:
            logger.error(f"Error HTTP al listar carpetas: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.exception(f"Error listando carpetas: {e}")
        return []
