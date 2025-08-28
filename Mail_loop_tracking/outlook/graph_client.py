"""
Cliente autenticado para Microsoft Graph API.

Este módulo proporciona funcionalidades para:
- Autenticación con Microsoft Graph API usando MSAL
- Gestión de tokens de acceso
- Sesiones autenticadas para llamadas a la API
"""
import msal
import requests
from config import CLIENT_ID, CLIENT_SECRET, AUTHORITY_URL, GRAPH_SCOPE
from utils.logger_config import setup_logger
from utils.retry_utils import (
    retry_on_failure, 
    handle_graph_api_errors, 
    rate_limit,
    AuthenticationError,
    GraphAPIError
)

logger = setup_logger("graph_client")

@retry_on_failure(max_retries=3, delay=2.0)
@handle_graph_api_errors
def get_token() -> str:
    """
    Obtiene un token de acceso para Microsoft Graph API usando MSAL.
    
    Returns:
        str: Token de acceso válido
        
    Raises:
        AuthenticationError: Si hay error en la autenticación
        GraphAPIError: Si hay error general de la API
    """
    logger.debug("Iniciando autenticación con MSAL.")
    
    try:
        # Crear aplicación MSAL
        app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=AUTHORITY_URL,
            client_credential=CLIENT_SECRET
        )
        
        # Obtener token para cliente
        result = app.acquire_token_for_client(scopes=GRAPH_SCOPE)

        if "access_token" in result:
            logger.info("✅ Token obtenido exitosamente.")
            logger.debug(f"Token expira en: {result.get('expires_in', 'N/A')} segundos")
            return result["access_token"]
        else:
            error_msg = result.get("error_description", "Error desconocido al obtener token.")
            error_code = result.get("error", "unknown_error")
            logger.error(f"❌ Fallo al obtener token: {error_msg} (Código: {error_code})")
            raise AuthenticationError(f"Token error: {error_msg}")

    except msal.MsalException as e:
        logger.exception(f"Error de MSAL durante autenticación: {str(e)}")
        raise AuthenticationError(f"Error de MSAL: {str(e)}")
    except Exception as ex:
        logger.exception(f"Excepción durante autenticación: {str(ex)}")
        raise GraphAPIError(f"Error de autenticación: {str(ex)}")

@rate_limit(max_calls=50, time_window=60.0)  # 50 llamadas por minuto
def get_authenticated_session() -> requests.Session:
    """
    Prepara una sesión autenticada para llamadas a Microsoft Graph API.
    
    Returns:
        requests.Session: Sesión con headers de autenticación configurados
        
    Raises:
        AuthenticationError: Si no se puede obtener el token
        GraphAPIError: Si hay error general
    """
    logger.debug("Preparando sesión autenticada para llamadas a Microsoft Graph.")
    
    try:
        # Obtener token
        token = get_token()
        
        # Crear sesión con headers
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        logger.info("✅ Sesión autenticada preparada correctamente.")
        return session
        
    except AuthenticationError:
        logger.error("❌ Error de autenticación al preparar sesión")
        raise
    except Exception as ex:
        logger.exception("Error al preparar la sesión autenticada.")
        raise GraphAPIError(f"Error preparando sesión: {str(ex)}")

def validate_session(session: requests.Session) -> bool:
    """
    Valida que una sesión esté autenticada correctamente.
    
    Args:
        session: Sesión de requests a validar
        
    Returns:
        bool: True si la sesión es válida, False en caso contrario
    """
    try:
        # Verificar que la sesión tiene el header de autorización
        if "Authorization" not in session.headers:
            logger.warning("⚠️ Sesión sin header de autorización")
            return False
        
        # Verificar que el token no está vacío
        auth_header = session.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer ") or len(auth_header) < 20:
            logger.warning("⚠️ Token de autorización inválido o vacío")
            return False
        
        # Hacer una llamada de prueba más simple a la API
        # Usar un endpoint que debería estar disponible con permisos básicos
        test_url = "https://graph.microsoft.com/v1.0/users"
        response = session.get(test_url)
        
        if response.status_code == 200:
            logger.debug("✅ Sesión validada correctamente")
            return True
        elif response.status_code == 401:
            logger.warning("⚠️ Sesión no válida: token expirado o inválido")
            return False
        elif response.status_code == 403:
            logger.warning("⚠️ Sesión válida pero sin permisos suficientes")
            # Considerar válida si el token funciona pero no tiene permisos
            return True
        else:
            logger.warning(f"⚠️ Sesión con estado inesperado: {response.status_code}")
            # Para otros códigos, asumir que la sesión es válida
            return True
            
    except Exception as e:
        logger.error(f"❌ Error validando sesión: {e}")
        return False

def refresh_session_if_needed(session: requests.Session) -> requests.Session:
    """
    Refresca la sesión si es necesario.
    
    Args:
        session: Sesión actual
        
    Returns:
        requests.Session: Sesión actualizada si fue necesario
    """
    if not validate_session(session):
        logger.info("🔄 Refrescando sesión...")
        return get_authenticated_session()
    
    return session

@retry_on_failure(max_retries=2, delay=1.0)
def make_graph_request(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    """
    Realiza una petición a Microsoft Graph API con manejo de errores.
    
    Args:
        session: Sesión autenticada
        method: Método HTTP (GET, POST, etc.)
        url: URL de la petición
        **kwargs: Argumentos adicionales para requests
        
    Returns:
        requests.Response: Respuesta de la API
        
    Raises:
        GraphAPIError: Si hay error en la petición
    """
    try:
        # Refrescar sesión si es necesario
        session = refresh_session_if_needed(session)
        
        # Realizar petición
        response = session.request(method, url, **kwargs)
        
        # Manejar códigos de error específicos
        if response.status_code == 401:
            logger.error("❌ Error de autenticación en petición Graph API")
            raise AuthenticationError("Token expirado o inválido")
        elif response.status_code == 429:
            logger.warning("⚠️ Rate limit alcanzado en Graph API")
            raise GraphAPIError("Rate limit excedido")
        elif response.status_code >= 500:
            logger.error(f"❌ Error del servidor Graph API: {response.status_code}")
            raise GraphAPIError(f"Error del servidor: {response.status_code}")
        
        return response
        
    except (AuthenticationError, GraphAPIError):
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en petición Graph API: {e}")
        raise GraphAPIError(f"Error en petición: {str(e)}")
