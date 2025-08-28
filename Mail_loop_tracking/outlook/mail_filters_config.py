"""
Configuración de filtros predefinidos para diferentes casos de uso
"""
from outlook.mail_reader import MessageFilter
from typing import Dict, List

# Filtros predefinidos para diferentes escenarios
PREDEFINED_FILTERS = {
    # Filtro para obtener correos de clasificación de correos
    "Mail_Classification": {
        "allowed_senders": [],
        "blocked_senders": ["@no-reply.com", "@automated.com"],
        "subject_keywords": ["NOTIFICACIÓN", "ACCIÓN", "Procesamiento"],
        "subject_exclude_keywords": ["nothing"]
    }
}

def get_predefined_filter(filter_name: str) -> MessageFilter:
    """
    Obtiene un filtro predefinido por nombre
    
    Args:
        filter_name: Nombre del filtro predefinido
        
    Returns:
        MessageFilter: Instancia del filtro configurado
        
    Raises:
        ValueError: Si el filtro no existe
    """
    if filter_name not in PREDEFINED_FILTERS:
        available_filters = list(PREDEFINED_FILTERS.keys())
        raise ValueError(f"Filtro '{filter_name}' no encontrado. Filtros disponibles: {available_filters}")
    
    config = PREDEFINED_FILTERS[filter_name]
    return MessageFilter(
        allowed_senders=config.get("allowed_senders", []),
        blocked_senders=config.get("blocked_senders", []),
        subject_keywords=config.get("subject_keywords", []),
        subject_exclude_keywords=config.get("subject_exclude_keywords", [])
    )

def get_available_filters() -> List[str]:
    """
    Obtiene la lista de filtros predefinidos disponibles
    
    Returns:
        List[str]: Lista de nombres de filtros disponibles
    """
    return list(PREDEFINED_FILTERS.keys())

def create_custom_filter(allowed_senders: List[str] = None,
                        blocked_senders: List[str] = None,
                        subject_keywords: List[str] = None,
                        subject_exclude_keywords: List[str] = None) -> MessageFilter:
    """
    Crea un filtro personalizado
    
    Args:
        allowed_senders: Lista de remitentes permitidos
        blocked_senders: Lista de remitentes bloqueados
        subject_keywords: Palabras clave que deben estar en el subject
        subject_exclude_keywords: Palabras clave que NO deben estar en el subject
        
    Returns:
        MessageFilter: Instancia del filtro personalizado
    """
    return MessageFilter(
        allowed_senders=allowed_senders or [],
        blocked_senders=blocked_senders or [],
        subject_keywords=subject_keywords or [],
        subject_exclude_keywords=subject_exclude_keywords or []
    )

def combine_filters(*filters: MessageFilter) -> MessageFilter:
    """
    Combina múltiples filtros en uno solo
    
    Args:
        *filters: Filtros a combinar
        
    Returns:
        MessageFilter: Filtro combinado
    """
    if not filters:
        return MessageFilter()
    
    # Combinar todas las listas de todos los filtros
    all_allowed_senders = []
    all_blocked_senders = []
    all_subject_keywords = []
    all_subject_exclude_keywords = []
    
    for filter_obj in filters:
        all_allowed_senders.extend(filter_obj.allowed_senders)
        all_blocked_senders.extend(filter_obj.blocked_senders)
        all_subject_keywords.extend(filter_obj.subject_keywords)
        all_subject_exclude_keywords.extend(filter_obj.subject_exclude_keywords)
    
    # Eliminar duplicados
    all_allowed_senders = list(set(all_allowed_senders))
    all_blocked_senders = list(set(all_blocked_senders))
    all_subject_keywords = list(set(all_subject_keywords))
    all_subject_exclude_keywords = list(set(all_subject_exclude_keywords))
    
    return MessageFilter(
        allowed_senders=all_allowed_senders,
        blocked_senders=all_blocked_senders,
        subject_keywords=all_subject_keywords,
        subject_exclude_keywords=all_subject_exclude_keywords
    )

# Ejemplos de uso de filtros combinados
def get_urgent_business_reports() -> MessageFilter:
    """
    Combina filtros para obtener mensajes urgentes de negocio y reportes
    """
    urgent_filter = get_predefined_filter("Mail_Classification")
    reports_filter = get_predefined_filter("reports")
    return combine_filters(urgent_filter, reports_filter)

def get_project_meetings() -> MessageFilter:
    """
    Combina filtros para obtener mensajes de proyectos y reuniones
    """
    projects_filter = get_predefined_filter("projects")
    meetings_filter = get_predefined_filter("meetings")
    return combine_filters(projects_filter, meetings_filter) 