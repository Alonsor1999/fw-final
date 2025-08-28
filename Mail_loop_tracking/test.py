"""
Script de pruebas mejorado para el sistema Mail Loop Tracking.

Este script valida:
- Configuración del sistema
- Conectividad con Microsoft Graph API
- Funcionalidades de filtrado
- Descarga de adjuntos
- Gestión de carpetas
"""
import sys
import time
from typing import Dict, List
from outlook.graph_client import get_authenticated_session, validate_session
from outlook.mail_reader import get_messages, get_messages_by_sender
from outlook.attachments import get_attachment_info
from outlook.move_mail import obtener_estado_carpetas
from outlook.mail_filters_config import get_available_filters, get_predefined_filter
from utils.logger_config import setup_logger
from config import get_config_summary, validate_config
from utils.retry_utils import GraphAPIError, AuthenticationError

logger = setup_logger("test_improved")

def test_configuration() -> bool:
    """
    Prueba la configuración del sistema.
    
    Returns:
        bool: True si la configuración es válida
    """
    logger.info("🔧 Probando configuración del sistema...")
    
    try:
        # Validar configuración
        validate_config()
        
        # Mostrar resumen de configuración
        config_summary = get_config_summary()
        logger.info("✅ Configuración válida")
        logger.debug(f"Configuración: {config_summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en configuración: {e}")
        return False

def test_authentication() -> bool:
    """
    Prueba la autenticación con Microsoft Graph API.
    
    Returns:
        bool: True si la autenticación es exitosa
    """
    logger.info("🔐 Probando autenticación con Microsoft Graph API...")
    
    try:
        # Obtener sesión autenticada
        session = get_authenticated_session()
        
        # Validar sesión
        if validate_session(session):
            logger.info("✅ Autenticación exitosa")
            return True
        else:
            logger.error("❌ Sesión no válida")
            return False
            
    except AuthenticationError as e:
        logger.error(f"❌ Error de autenticación: {e}")
        return False
    except GraphAPIError as e:
        logger.error(f"❌ Error de Graph API: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado en autenticación: {e}")
        return False

def test_mail_access() -> bool:
    """
    Prueba el acceso a mensajes de correo.
    
    Returns:
        bool: True si se puede acceder a los mensajes
    """
    logger.info("📧 Probando acceso a mensajes de correo...")
    
    try:
        # Obtener mensajes de prueba
        messages = get_messages(top=2)
        
        if messages:
            logger.info(f"✅ Acceso a mensajes exitoso: {len(messages)} mensajes obtenidos")
            
            # Mostrar información del primer mensaje
            if messages:
                first_msg = messages[0]
                subject = first_msg.get("subject", "Sin asunto")
                sender = first_msg.get("from", {}).get("emailAddress", {}).get("address", "Desconocido")
                logger.info(f"📨 Primer mensaje: '{subject}' de {sender}")
            
            return True
        else:
            logger.warning("⚠️ No se encontraron mensajes (puede ser normal)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error accediendo a mensajes: {e}")
        return False

def test_filters() -> bool:
    """
    Prueba el sistema de filtros.
    
    Returns:
        bool: True si los filtros funcionan correctamente
    """
    logger.info("🔍 Probando sistema de filtros...")
    
    try:
        # Obtener filtros disponibles
        available_filters = get_available_filters()
        logger.info(f"📋 Filtros disponibles: {available_filters}")
        
        # Probar filtro específico
        test_filter = get_predefined_filter("Mail_Classification")
        logger.info("✅ Filtro 'Mail_Classification' creado correctamente")
        
        # Probar filtrado por remitente
        test_messages = get_messages_by_sender(["@test.com"], top=1)
        logger.info(f"✅ Filtrado por remitente: {len(test_messages)} mensajes encontrados")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando filtros: {e}")
        return False

def test_attachments() -> bool:
    """
    Prueba el acceso a información de adjuntos.
    
    Returns:
        bool: True si se puede acceder a adjuntos
    """
    logger.info("📎 Probando acceso a adjuntos...")
    
    try:
        # Obtener mensajes con adjuntos
        messages = get_messages(top=5)
        
        for message in messages:
            message_id = message.get("id")
            subject = message.get("subject", "Sin asunto")
            
            # Obtener información de adjuntos
            attachment_info = get_attachment_info(message_id)
            
            if attachment_info:
                logger.info(f"📎 Mensaje '{subject}' tiene {len(attachment_info)} adjuntos")
                break
        else:
            logger.info("📭 No se encontraron mensajes con adjuntos (puede ser normal)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error accediendo a adjuntos: {e}")
        return False

def test_folders() -> bool:
    """
    Prueba el acceso a carpetas de correo.
    
    Returns:
        bool: True si se puede acceder a las carpetas
    """
    logger.info("📁 Probando acceso a carpetas...")
    
    try:
        from config import MAIL_USER
        from outlook.graph_client import get_authenticated_session
        
        session = get_authenticated_session()
        folder_info = obtener_estado_carpetas(session, MAIL_USER)
        
        if folder_info:
            logger.info(f"✅ Acceso a carpetas exitoso: {len(folder_info)} carpetas encontradas")
            
            # Mostrar algunas carpetas
            for folder_name, info in list(folder_info.items())[:3]:
                total_items = info.get("total_item_count", 0)
                logger.info(f"📁 {folder_name}: {total_items} mensajes")
            
            return True
        else:
            logger.warning("⚠️ No se pudieron obtener carpetas")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error accediendo a carpetas: {e}")
        return False

def run_all_tests() -> Dict[str, bool]:
    """
    Ejecuta todas las pruebas del sistema.
    
    Returns:
        Dict[str, bool]: Resultados de todas las pruebas
    """
    logger.info("🚀 Iniciando pruebas completas del sistema")
    
    tests = {
        "Configuración": test_configuration,
        "Autenticación": test_authentication,
        "Acceso a mensajes": test_mail_access,
        "Filtros": test_filters,
        "Adjuntos": test_attachments,
        "Carpetas": test_folders
    }
    
    results = {}
    
    for test_name, test_func in tests.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Ejecutando: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            results[test_name] = result
            
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            duration = f"{end_time - start_time:.2f}s"
            
            logger.info(f"{status} {test_name} ({duration})")
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando {test_name}: {e}")
            results[test_name] = False
    
    return results

def print_summary(results: Dict[str, bool]) -> None:
    """
    Imprime un resumen de los resultados de las pruebas.
    
    Args:
        results: Resultados de las pruebas
    """
    logger.info(f"\n{'='*60}")
    logger.info("📊 RESUMEN DE PRUEBAS")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n📈 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        logger.info("🎉 ¡Todas las pruebas pasaron! El sistema está funcionando correctamente.")
        return True
    else:
        logger.error(f"⚠️ {total - passed} pruebas fallaron. Revisa la configuración.")
        return False

def main():
    """
    Función principal del script de pruebas.
    """
    logger.info("🧪 SISTEMA DE PRUEBAS - MAIL LOOP TRACKING")
    logger.info("=" * 50)
    
    try:
        # Ejecutar todas las pruebas
        results = run_all_tests()
        
        # Mostrar resumen
        all_passed = print_summary(results)
        
        # Código de salida
        if all_passed:
            logger.info("✅ Pruebas completadas exitosamente")
            sys.exit(0)
        else:
            logger.error("❌ Algunas pruebas fallaron")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Error inesperado durante las pruebas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 