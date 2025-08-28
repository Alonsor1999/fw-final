"""
Script de prueba específico para leer correos de la carpeta Iniciativa4
Utiliza el módulo Mail_loop_tracking para acceder a Outlook
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from outlook.folder_reader import (
    get_messages_from_folder,
    get_messages_from_folder_with_filter,
    get_folder_summary,
    list_available_folders,
    get_folder_id
)
from outlook.graph_client import get_authenticated_session, validate_session
from config import validate_config, get_config_summary
from utils.logger_config import setup_logger

logger = setup_logger("test_iniciativa4")

def test_configuration() -> bool:
    """Prueba la configuración del sistema"""
    print("🔧 Probando configuración del sistema...")
    
    try:
        validate_config()
        config_summary = get_config_summary()
        print("✅ Configuración válida")
        print(f"   Usuario: {config_summary['mail_user']}")
        print(f"   Tenant ID: {config_summary['tenant_id']}")
        return True
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def test_authentication() -> bool:
    """Prueba la autenticación con Microsoft Graph API"""
    print("🔐 Probando autenticación con Microsoft Graph API...")
    
    try:
        session = get_authenticated_session()
        if validate_session(session):
            print("✅ Autenticación exitosa")
            return True
        else:
            print("❌ Sesión no válida")
            return False
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return False

def test_folder_access(folder_name: str = "Iniciativa4") -> bool:
    """Prueba el acceso a la carpeta especificada"""
    print(f"📁 Probando acceso a la carpeta '{folder_name}'...")
    
    try:
        folder_id = get_folder_id(folder_name)
        if folder_id:
            print(f"✅ Carpeta '{folder_name}' encontrada con ID: {folder_id}")
            return True
        else:
            print(f"❌ Carpeta '{folder_name}' no encontrada")
            return False
    except Exception as e:
        print(f"❌ Error accediendo a la carpeta: {e}")
        return False

def test_list_folders():
    """Lista todas las carpetas disponibles"""
    print("📂 Listando carpetas disponibles...")
    
    try:
        folders = list_available_folders()
        if folders:
            print(f"✅ {len(folders)} carpetas encontradas:")
            for folder in folders[:10]:  # Mostrar solo las primeras 10
                print(f"   - {folder['display_name']} (ID: {folder['id'][:8]}...) - {folder['total_item_count']} mensajes")
            if len(folders) > 10:
                print(f"   ... y {len(folders) - 10} carpetas más")
        else:
            print("❌ No se encontraron carpetas")
    except Exception as e:
        print(f"❌ Error listando carpetas: {e}")

def test_get_messages(folder_name: str = "Iniciativa4", top: int = 5):
    """Prueba obtener mensajes de la carpeta"""
    print(f"📧 Obteniendo {top} mensajes de la carpeta '{folder_name}'...")
    
    try:
        messages = get_messages_from_folder(folder_name, top=top)
        if messages:
            print(f"✅ {len(messages)} mensajes obtenidos:")
            for i, message in enumerate(messages, 1):
                subject = message.get('subject', 'Sin asunto')
                sender = message.get('from', {}).get('emailAddress', {}).get('address', 'Desconocido')
                received = message.get('receivedDateTime', 'Fecha desconocida')
                is_read = message.get('isRead', True)
                
                print(f"   {i}. {subject}")
                print(f"      De: {sender}")
                print(f"      Fecha: {received}")
                print(f"      Leído: {'Sí' if is_read else 'No'}")
                print()
        else:
            print(f"❌ No se encontraron mensajes en la carpeta '{folder_name}'")
    except Exception as e:
        print(f"❌ Error obteniendo mensajes: {e}")

def test_get_messages_with_filter(folder_name: str = "Iniciativa4", top: int = 10):
    """Prueba obtener mensajes con filtros"""
    print(f"🔍 Obteniendo mensajes filtrados de '{folder_name}'...")
    
    try:
        # Filtros de ejemplo
        allowed_senders = ["@empresa.com", "@outlook.com"]
        subject_keywords = ["importante", "urgente", "revisar"]
        
        messages = get_messages_from_folder_with_filter(
            folder_name=folder_name,
            allowed_senders=allowed_senders,
            subject_keywords=subject_keywords,
            top=top
        )
        
        if messages:
            print(f"✅ {len(messages)} mensajes filtrados obtenidos:")
            for i, message in enumerate(messages, 1):
                subject = message.get('subject', 'Sin asunto')
                sender = message.get('from', {}).get('emailAddress', {}).get('address', 'Desconocido')
                print(f"   {i}. {subject} (De: {sender})")
        else:
            print(f"❌ No se encontraron mensajes que cumplan los filtros en '{folder_name}'")
    except Exception as e:
        print(f"❌ Error obteniendo mensajes filtrados: {e}")

def test_folder_summary(folder_name: str = "Iniciativa4"):
    """Prueba obtener resumen de la carpeta"""
    print(f"📊 Obteniendo resumen de la carpeta '{folder_name}'...")
    
    try:
        summary = get_folder_summary(folder_name)
        if summary.get('success'):
            print("✅ Resumen de la carpeta:")
            print(f"   Nombre: {summary['folder_name']}")
            print(f"   ID: {summary['folder_id']}")
            print(f"   Total mensajes: {summary['total_messages']}")
            print(f"   No leídos: {summary['unread_count']}")
            print(f"   Total items: {summary['total_item_count']}")
        else:
            print(f"❌ Error obteniendo resumen: {summary.get('error')}")
    except Exception as e:
        print(f"❌ Error obteniendo resumen: {e}")

def main():
    """Función principal de prueba"""
    print("=" * 70)
    print("PRUEBA DE LECTURA DE CORREOS - CARPETA INICIATIVA4")
    print("=" * 70)
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configurar carpeta a probar
    folder_name = "Iniciativa4"
    
    # Ejecutar pruebas en orden
    tests = [
        ("Configuración", test_configuration),
        ("Autenticación", test_authentication),
        ("Listar carpetas", test_list_folders),
        ("Acceso a carpeta", lambda: test_folder_access(folder_name)),
        ("Resumen de carpeta", lambda: test_folder_summary(folder_name)),
        ("Obtener mensajes", lambda: test_get_messages(folder_name, 5)),
        ("Mensajes con filtros", lambda: test_get_messages_with_filter(folder_name, 10))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"PRUEBA: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result is not None:  # Algunas funciones no retornan valor
                status = "✅ PASÓ" if result else "❌ FALLÓ"
                print(f"\n{status} - {test_name}")
            
        except Exception as e:
            print(f"\n❌ ERROR - {test_name}: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Pausa entre pruebas
    
    # Resumen final
    print(f"\n{'='*70}")
    print("RESUMEN DE PRUEBAS")
    print(f"{'='*70}")
    
    passed = sum(1 for _, result in results if result is True)
    total = len([r for _, r in results if r is not None])
    
    for test_name, result in results:
        if result is not None:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"{status} - {test_name}")
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()
