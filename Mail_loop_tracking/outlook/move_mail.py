"""
Módulo para gestión de carpetas y movimiento de correos en Microsoft Graph API.

Este módulo proporciona funcionalidades para:
- Crear carpetas personalizadas en el buzón de correo
- Mover mensajes entre carpetas
- Gestionar el estado de procesamiento de correos
"""
import requests
from typing import Optional
from utils.logger_config import setup_logger

logger = setup_logger("move_mail")

def get_or_create_folder(session, user: str, folder_name: str = "Procesados") -> Optional[str]:
    """
    Obtiene el ID de una carpeta existente o la crea si no existe.
    
    Args:
        session: Sesión autenticada de Microsoft Graph API
        user: ID del usuario de correo (email o ID)
        folder_name: Nombre de la carpeta a buscar o crear
        
    Returns:
        str: ID de la carpeta encontrada o creada, None si hay error
        
    Raises:
        Exception: Si hay error en la comunicación con la API
    """
    logger.info(f"Buscando carpeta '{folder_name}' para usuario {user}")
    
    url = f"https://graph.microsoft.com/v1.0/users/{user}/mailFolders"
    
    try:
        response = session.get(url)
        
        if response.ok:
            folders = response.json().get("value", [])
            
            # Buscar carpeta existente
            for folder in folders:
                if folder["displayName"].lower() == folder_name.lower():
                    folder_id = folder["id"]
                    logger.info(f"✅ Carpeta '{folder_name}' encontrada con ID: {folder_id}")
                    return folder_id
            
            # Crear carpeta si no existe
            logger.info(f"📂 Carpeta '{folder_name}' no existe, creando...")
            create_url = f"https://graph.microsoft.com/v1.0/users/{user}/mailFolders"
            create_data = {"displayName": folder_name}
            
            create_response = session.post(create_url, json=create_data)
            
            if create_response.ok:
                new_folder_id = create_response.json()["id"]
                logger.info(f"✅ Carpeta '{folder_name}' creada exitosamente con ID: {new_folder_id}")
                return new_folder_id
            else:
                error_msg = f"Error creando carpeta '{folder_name}': {create_response.text}"
                logger.error(f"❌ {error_msg}")
                return None
        else:
            error_msg = f"Error obteniendo carpetas: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return None
            
    except Exception as e:
        logger.exception(f"Excepción durante gestión de carpeta '{folder_name}': {e}")
        return None

def mover_correo(session, user: str, message_id: str, folder_id: str) -> bool:
    """
    Mueve un correo a una carpeta específica.
    
    Args:
        session: Sesión autenticada de Microsoft Graph API
        user: ID del usuario de correo (email o ID)
        message_id: ID del mensaje a mover
        folder_id: ID de la carpeta destino
        
    Returns:
        bool: True si el movimiento fue exitoso, False en caso contrario
        
    Raises:
        Exception: Si hay error en la comunicación con la API
    """
    logger.info(f"Moviendo correo {message_id} a carpeta {folder_id}")
    
    url = f"https://graph.microsoft.com/v1.0/users/{user}/messages/{message_id}/move"
    move_data = {"destinationId": folder_id}
    
    try:
        response = session.post(url, json=move_data)
        
        if response.ok:
            logger.info(f"✅ Correo {message_id} movido exitosamente a carpeta '{folder_id}'")
            return True
        else:
            error_msg = f"Error al mover correo {message_id}: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return False
            
    except Exception as e:
        logger.exception(f"Excepción durante movimiento de correo {message_id}: {e}")
        return False

def marcar_como_procesado(session, user: str, message_id: str, folder_name: str = "Procesados") -> bool:
    """
    Marca un correo como procesado moviéndolo a la carpeta de procesados.
    
    Args:
        session: Sesión autenticada de Microsoft Graph API
        user: ID del usuario de correo (email o ID)
        message_id: ID del mensaje a marcar como procesado
        folder_name: Nombre de la carpeta de procesados
        
    Returns:
        bool: True si el proceso fue exitoso, False en caso contrario
    """
    logger.info(f"Marcando correo {message_id} como procesado")
    
    # Obtener o crear carpeta de procesados
    folder_id = get_or_create_folder(session, user, folder_name)
    
    if not folder_id:
        logger.error(f"❌ No se pudo obtener/crear carpeta '{folder_name}'")
        return False
    
    # Mover el correo
    return mover_correo(session, user, message_id, folder_id)

def obtener_estado_carpetas(session, user: str) -> dict:
    """
    Obtiene información sobre todas las carpetas del buzón de correo.
    
    Args:
        session: Sesión autenticada de Microsoft Graph API
        user: ID del usuario de correo (email o ID)
        
    Returns:
        dict: Información de las carpetas con formato {nombre: id}
    """
    logger.info(f"Obteniendo estado de carpetas para usuario {user}")
    
    url = f"https://graph.microsoft.com/v1.0/users/{user}/mailFolders"
    
    try:
        response = session.get(url)
        
        if response.ok:
            folders = response.json().get("value", [])
            folder_info = {}
            
            for folder in folders:
                folder_info[folder["displayName"]] = {
                    "id": folder["id"],
                    "total_item_count": folder.get("totalItemCount", 0),
                    "unread_item_count": folder.get("unreadItemCount", 0)
                }
            
            logger.info(f"✅ Se encontraron {len(folder_info)} carpetas")
            logger.debug(f"Información de carpetas: {folder_info}")
            
            return folder_info
        else:
            error_msg = f"Error obteniendo carpetas: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return {}
            
    except Exception as e:
        logger.exception(f"Excepción durante obtención de carpetas: {e}")
        return {}
