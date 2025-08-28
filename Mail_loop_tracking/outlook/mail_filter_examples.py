"""
Ejemplos de uso de las funcionalidades de filtrado de mensajes
"""
from mail_reader import (
    get_messages, 
    get_messages_by_sender, 
    get_messages_by_subject_keywords, 
    get_messages_advanced,
    MessageFilter
)
from utils.logger_config import setup_logger

logger = setup_logger("mail_filter_examples")

def ejemplo_filtro_por_remitente():
    """
    Ejemplo: Obtener mensajes solo de remitentes específicos
    """
    logger.info("=== Ejemplo: Filtro por remitente ===")
    
    # Obtener mensajes solo de dominios específicos
    dominios_permitidos = ["@empresa.com", "@cliente.com"]
    mensajes = get_messages_by_sender(dominios_permitidos, top=10)
    
    logger.info(f"Se encontraron {len(mensajes)} mensajes de los remitentes especificados")
    
    for mensaje in mensajes:
        remitente = mensaje.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
        asunto = mensaje.get('subject', 'Sin asunto')
        logger.info(f"Remitente: {remitente} | Asunto: {asunto}")

def ejemplo_filtro_por_palabras_clave():
    """
    Ejemplo: Obtener mensajes con palabras clave específicas en el subject
    """
    logger.info("=== Ejemplo: Filtro por palabras clave ===")
    
    # Palabras clave que deben estar en el subject
    palabras_clave = ["urgente", "importante", "reunión"]
    
    # Palabras que NO deben estar en el subject
    palabras_excluidas = ["spam", "publicidad", "newsletter"]
    
    mensajes = get_messages_by_subject_keywords(
        keywords=palabras_clave,
        exclude_keywords=palabras_excluidas,
        top=10
    )
    
    logger.info(f"Se encontraron {len(mensajes)} mensajes con las palabras clave especificadas")
    
    for mensaje in mensajes:
        remitente = mensaje.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
        asunto = mensaje.get('subject', 'Sin asunto')
        logger.info(f"Remitente: {remitente} | Asunto: {asunto}")

def ejemplo_filtro_avanzado():
    """
    Ejemplo: Filtro avanzado combinando múltiples criterios
    """
    logger.info("=== Ejemplo: Filtro avanzado ===")
    
    # Configuración de filtros avanzados
    remitentes_permitidos = ["@empresa.com", "jefe@", "gerente@"]
    remitentes_bloqueados = ["@spam.com", "noreply@"]
    palabras_clave_subject = ["reporte", "informe", "estado"]
    palabras_excluidas_subject = ["automático", "sistema"]
    
    mensajes = get_messages_advanced(
        allowed_senders=remitentes_permitidos,
        blocked_senders=remitentes_bloqueados,
        subject_keywords=palabras_clave_subject,
        subject_exclude_keywords=palabras_excluidas_subject,
        top=15
    )
    
    logger.info(f"Se encontraron {len(mensajes)} mensajes que cumplen todos los criterios")
    
    for mensaje in mensajes:
        remitente = mensaje.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
        asunto = mensaje.get('subject', 'Sin asunto')
        fecha = mensaje.get('receivedDateTime', 'N/A')
        logger.info(f"Fecha: {fecha} | Remitente: {remitente} | Asunto: {asunto}")

def ejemplo_filtro_personalizado():
    """
    Ejemplo: Crear un filtro personalizado usando la clase MessageFilter
    """
    logger.info("=== Ejemplo: Filtro personalizado ===")
    
    # Crear un filtro personalizado
    filtro_personalizado = MessageFilter(
        allowed_senders=["@proyecto.com", "coordinador@"],
        blocked_senders=["@no-reply.com"],
        subject_keywords=["proyecto", "tarea", "deadline"],
        subject_exclude_keywords=["completado", "finalizado"]
    )
    
    # Usar el filtro personalizado
    mensajes = get_messages(top=20, message_filter=filtro_personalizado)
    
    logger.info(f"Se encontraron {len(mensajes)} mensajes con el filtro personalizado")
    
    for mensaje in mensajes:
        remitente = mensaje.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
        asunto = mensaje.get('subject', 'Sin asunto')
        logger.info(f"Remitente: {remitente} | Asunto: {asunto}")

def ejemplo_filtro_solo_bloqueados():
    """
    Ejemplo: Filtrar solo por remitentes bloqueados (permitir todos excepto los bloqueados)
    """
    logger.info("=== Ejemplo: Filtro solo por bloqueados ===")
    
    # Solo bloquear ciertos remitentes, permitir todos los demás
    remitentes_bloqueados = ["@spam.com", "newsletter@", "noreply@"]
    
    filtro = MessageFilter(blocked_senders=remitentes_bloqueados)
    mensajes = get_messages(top=10, message_filter=filtro)
    
    logger.info(f"Se encontraron {len(mensajes)} mensajes (excluyendo remitentes bloqueados)")
    
    for mensaje in mensajes:
        remitente = mensaje.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
        asunto = mensaje.get('subject', 'Sin asunto')
        logger.info(f"Remitente: {remitente} | Asunto: {asunto}")

def ejemplo_filtro_solo_palabras_excluidas():
    """
    Ejemplo: Filtrar solo por palabras excluidas en el subject
    """
    logger.info("=== Ejemplo: Filtro solo por palabras excluidas ===")
    
    # Solo excluir ciertas palabras del subject, permitir todos los demás
    palabras_excluidas = ["spam", "publicidad", "promoción", "oferta"]
    
    filtro = MessageFilter(subject_exclude_keywords=palabras_excluidas)
    mensajes = get_messages(top=10, message_filter=filtro)
    
    logger.info(f"Se encontraron {len(mensajes)} mensajes (excluyendo subjects con palabras prohibidas)")
    
    for mensaje in mensajes:
        remitente = mensaje.get('from', {}).get('emailAddress', {}).get('address', 'N/A')
        asunto = mensaje.get('subject', 'Sin asunto')
        logger.info(f"Remitente: {remitente} | Asunto: {asunto}")

if __name__ == "__main__":
    """
    Ejecutar ejemplos de filtrado de mensajes
    """
    logger.info("Iniciando ejemplos de filtrado de mensajes")
    
    try:
        # Ejecutar ejemplos
        ejemplo_filtro_por_remitente()
        print("\n" + "="*50 + "\n")
        
        ejemplo_filtro_por_palabras_clave()
        print("\n" + "="*50 + "\n")
        
        ejemplo_filtro_avanzado()
        print("\n" + "="*50 + "\n")
        
        ejemplo_filtro_personalizado()
        print("\n" + "="*50 + "\n")
        
        ejemplo_filtro_solo_bloqueados()
        print("\n" + "="*50 + "\n")
        
        ejemplo_filtro_solo_palabras_excluidas()
        
    except Exception as e:
        logger.exception("Error durante la ejecución de ejemplos")
        print(f"Error: {e}")
    
    logger.info("Ejemplos de filtrado completados") 