from outlook.graph_client import get_authenticated_session
from config import GRAPH_API_ENDPOINT, MAIL_USER
from utils.logger_config import setup_logger
from typing import List, Dict, Optional

logger = setup_logger("mail_reader")

def get_messages(top=5):
    """
    Función original para obtener mensajes sin filtros
    Mantiene la funcionalidad existente intacta
    """
    logger.debug(f"Solicitando últimos {top} correos de {MAIL_USER}")
    session = get_authenticated_session()
    url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/mailFolders/inbox/messages?$top={top}&$orderby=receivedDateTime desc"

    #url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/messages?$top={top}&$orderby=receivedDateTime desc"

    try:
        response = session.get(url)
        if response.ok:
            messages = response.json().get("value", [])
            logger.info(f"{len(messages)} correos obtenidos del buzón de {MAIL_USER}")
            return messages
        else:
            logger.error(f"Error HTTP al obtener mensajes: {response.status_code} - {response.text}")
    except Exception as e:
        logger.exception("Excepción durante la recuperación de correos")

    return []

class MessageFilter:
    """
    Clase para definir filtros de mensajes por remitente y palabras clave
    """
    def __init__(self, 
                 allowed_senders: Optional[List[str]] = None,
                 blocked_senders: Optional[List[str]] = None,
                 subject_keywords: Optional[List[str]] = None,
                 subject_exclude_keywords: Optional[List[str]] = None):
        """
        Inicializa el filtro de mensajes
        
        Args:
            allowed_senders: Lista de remitentes permitidos (dominios o emails completos)
            blocked_senders: Lista de remitentes bloqueados (dominios o emails completos)
            subject_keywords: Palabras clave que deben estar en el subject
            subject_exclude_keywords: Palabras clave que NO deben estar en el subject
        """
        self.allowed_senders = allowed_senders or []
        self.blocked_senders = blocked_senders or []
        self.subject_keywords = subject_keywords or []
        self.subject_exclude_keywords = subject_exclude_keywords or []
        
        logger.debug(f"Filtro inicializado - Remitentes permitidos: {len(self.allowed_senders)}, "
                    f"Remitentes bloqueados: {len(self.blocked_senders)}, "
                    f"Palabras clave subject: {len(self.subject_keywords)}, "
                    f"Palabras excluidas subject: {len(self.subject_exclude_keywords)}")

    def is_sender_allowed(self, sender_email: str) -> bool:
        """
        Verifica si el remitente está permitido según los filtros
        
        Args:
            sender_email: Email del remitente
            
        Returns:
            bool: True si el remitente está permitido
        """
        if not sender_email:
            logger.warning("Email de remitente vacío, rechazando mensaje")
            return False
            
        sender_email = sender_email.lower()
        
        # Verificar remitentes bloqueados primero
        for blocked in self.blocked_senders:
            if blocked.lower() in sender_email:
                logger.debug(f"Remitente bloqueado: {sender_email} (coincide con: {blocked})")
                return False
        
        # Si hay remitentes permitidos específicos, verificar que esté en la lista
        if self.allowed_senders:
            for allowed in self.allowed_senders:
                if allowed.lower() in sender_email:
                    logger.debug(f"Remitente permitido: {sender_email} (coincide con: {allowed})")
                    return True
            logger.debug(f"Remitente no permitido: {sender_email}")
            return False
        
        # Si no hay remitentes permitidos específicos, permitir todos excepto los bloqueados
        logger.debug(f"Remitente permitido (sin filtros específicos): {sender_email}")
        return True

    def is_subject_valid(self, subject: str) -> bool:
        """
        Verifica si el subject cumple con los filtros de palabras clave
        
        Args:
            subject: Asunto del mensaje
            
        Returns:
            bool: True si el subject es válido
        """
        if not subject:
            logger.warning("Subject vacío, rechazando mensaje")
            return False
            
        subject_lower = subject.lower()
        
        # Verificar palabras excluidas primero
        for exclude_keyword in self.subject_exclude_keywords:
            if exclude_keyword.lower() in subject_lower:
                logger.debug(f"Subject rechazado por palabra excluida: '{subject}' (contiene: '{exclude_keyword}')")
                return False
        
        # Si hay palabras clave requeridas, verificar que al menos una esté presente
        if self.subject_keywords:
            for keyword in self.subject_keywords:
                if keyword.lower() in subject_lower:
                    logger.debug(f"Subject aceptado por palabra clave: '{subject}' (contiene: '{keyword}')")
                    return True
            logger.debug(f"Subject rechazado - no contiene palabras clave requeridas: '{subject}'")
            return False
        
        # Si no hay palabras clave requeridas, aceptar todos excepto los que tienen palabras excluidas
        logger.debug(f"Subject aceptado (sin palabras clave requeridas): '{subject}'")
        return True

    def filter_message(self, message: Dict) -> bool:
        """
        Aplica todos los filtros a un mensaje
        
        Args:
            message: Diccionario con los datos del mensaje
            
        Returns:
            bool: True si el mensaje pasa todos los filtros
        """
        # Extraer información del mensaje
        sender_email = self._extract_sender_email(message)
        subject = message.get('subject', '')
        
        logger.debug(f"Filtrando mensaje - Remitente: {sender_email}, Subject: '{subject}'")
        
        # Aplicar filtros
        if not self.is_sender_allowed(sender_email):
            return False
            
        if not self.is_subject_valid(subject):
            return False
        
        logger.info(f"Mensaje aprobado por filtros - Remitente: {sender_email}, Subject: '{subject}'")
        return True

    def _extract_sender_email(self, message: Dict) -> str:
        """
        Extrae el email del remitente del mensaje
        
        Args:
            message: Diccionario con los datos del mensaje
            
        Returns:
            str: Email del remitente
        """
        # Intentar diferentes campos donde puede estar el remitente
        sender = message.get('from', {})
        if isinstance(sender, dict):
            email = sender.get('emailAddress', {}).get('address', '')
        else:
            email = str(sender)
        
        return email

def get_messages_with_filter(top: int = 5, message_filter: Optional[MessageFilter] = None) -> List[Dict]:
    """
    Obtiene mensajes del buzón de entrada con filtros opcionales
    
    Args:
        top: Número máximo de mensajes a obtener
        message_filter: Filtro opcional para procesar mensajes
        
    Returns:
        List[Dict]: Lista de mensajes que pasan los filtros
    """
    logger.debug(f"Solicitando últimos {top} correos con filtros de {MAIL_USER}")
    session = get_authenticated_session()
    url = f"{GRAPH_API_ENDPOINT}/users/{MAIL_USER}/mailFolders/inbox/messages?$top={top}&$orderby=receivedDateTime desc"

    try:
        response = session.get(url)
        if response.ok:
            messages = response.json().get("value", [])
            logger.info(f"{len(messages)} correos obtenidos del buzón de {MAIL_USER}")
            
            # Aplicar filtros si se proporcionan
            if message_filter:
                filtered_messages = []
                for message in messages:
                    if message_filter.filter_message(message):
                        filtered_messages.append(message)
                
                logger.info(f"{len(filtered_messages)} correos aprobados por filtros de {len(messages)} totales")
                return filtered_messages
            
            return messages
        else:
            logger.error(f"Error HTTP al obtener mensajes: {response.status_code} - {response.text}")
    except Exception as e:
        logger.exception("Excepción durante la recuperación de correos")

    return []

def get_messages_by_sender(senders: List[str], top: int = 5) -> List[Dict]:
    """
    Obtiene mensajes de remitentes específicos
    
    Args:
        senders: Lista de remitentes (dominios o emails completos)
        top: Número máximo de mensajes a obtener
        
    Returns:
        List[Dict]: Lista de mensajes de los remitentes especificados
    """
    logger.info(f"Obteniendo mensajes de remitentes específicos: {senders}")
    message_filter = MessageFilter(allowed_senders=senders)
    return get_messages_with_filter(top=top, message_filter=message_filter)

def get_messages_by_subject_keywords(keywords: List[str], top: int = 5, 
                                   exclude_keywords: Optional[List[str]] = None) -> List[Dict]:
    """
    Obtiene mensajes que contengan palabras clave específicas en el subject
    
    Args:
        keywords: Lista de palabras clave que deben estar en el subject
        top: Número máximo de mensajes a obtener
        exclude_keywords: Lista de palabras clave que NO deben estar en el subject
        
    Returns:
        List[Dict]: Lista de mensajes que contienen las palabras clave
    """
    logger.info(f"Obteniendo mensajes con palabras clave en subject: {keywords}")
    message_filter = MessageFilter(
        subject_keywords=keywords,
        subject_exclude_keywords=exclude_keywords
    )
    return get_messages_with_filter(top=top, message_filter=message_filter)

def get_messages_advanced(allowed_senders: Optional[List[str]] = None,
                         blocked_senders: Optional[List[str]] = None,
                         subject_keywords: Optional[List[str]] = None,
                         subject_exclude_keywords: Optional[List[str]] = None,
                         top: int = 5) -> List[Dict]:
    """
    Obtiene mensajes con filtros avanzados combinados
    
    Args:
        allowed_senders: Lista de remitentes permitidos
        blocked_senders: Lista de remitentes bloqueados
        subject_keywords: Palabras clave que deben estar en el subject
        subject_exclude_keywords: Palabras clave que NO deben estar en el subject
        top: Número máximo de mensajes a obtener
        
    Returns:
        List[Dict]: Lista de mensajes que cumplen con todos los filtros
    """
    logger.info("Obteniendo mensajes con filtros avanzados combinados")
    message_filter = MessageFilter(
        allowed_senders=allowed_senders,
        blocked_senders=blocked_senders,
        subject_keywords=subject_keywords,
        subject_exclude_keywords=subject_exclude_keywords
    )
    return get_messages_with_filter(top=top, message_filter=message_filter)
