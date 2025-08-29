"""
Script de prueba para el flujo completo del Robot001
Prueba: Leer correos → Descargar PDFs → Enviar a RabbitMQ → Procesar con Pdf_Consumer
"""

import asyncio
import sys
import os
from datetime import datetime

# Agregar el directorio del framework al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Agregar el directorio de Mail_loop_tracking al path
mail_tracking_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Mail_loop_tracking")
sys.path.append(mail_tracking_path)

from robots.robot001.main import Robot001
from framework.shared.logger import get_logger

logger = get_logger(__name__)

async def test_robot_initialization():
    """Probar inicialización del robot"""
    print("🔧 Probando inicialización del robot...")
    
    try:
        config = {
            'email_processing': {
                'enabled': True,
                'check_interval': 60,  # 1 minuto para pruebas
                'max_emails': 10,
                'download_pdfs_only': True,
                'process_unread_only': False  # Procesar todos para pruebas
            },
            'outlook_config': {
                'folder_name': 'Iniciativa4',
                'attachment_path': './test_attachments'
            },
            'rabbitmq_config': {
                'host': 'localhost',
                'port': 5672,
                'username': 'guest',
                'password': 'guest',
                'queue_name': 'pdf_processing_queue'
            }
        }
        
        robot = Robot001(config)
        print("✅ Robot inicializado correctamente")
        
        # Obtener estado
        status = await robot.get_status()
        print(f"📊 Estado del robot: {status['robot_name']} v{status['version']}")
        print(f"📊 Componentes activos: {status['components']}")
        
        return robot
        
    except Exception as e:
        print(f"❌ Error inicializando robot: {e}")
        return None

async def test_email_reading(robot):
    """Probar lectura de correos"""
    print("\n📧 Probando lectura de correos...")
    
    try:
        result = await robot.execute_command('search_iniciativa4', {'top': 5})
        
        if result['success']:
            print(f"✅ {result['emails_count']} correos leídos de {result['folder']}")
            
            if result['emails']:
                print("📋 Primeros correos:")
                for i, email in enumerate(result['emails'][:3], 1):
                    subject = email.get('subject', 'Sin asunto')
                    sender = email.get('from', {}).get('emailAddress', {}).get('address', 'Desconocido')
                    has_attachments = email.get('hasAttachments', False)
                    print(f"   {i}. {subject}")
                    print(f"      De: {sender}")
                    print(f"      Adjuntos: {'Sí' if has_attachments else 'No'}")
        else:
            print(f"❌ Error leyendo correos: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error en prueba de lectura: {e}")

async def test_folder_summary(robot):
    """Probar resumen de carpeta"""
    print("\n📊 Probando resumen de carpeta...")
    
    try:
        result = await robot.execute_command('get_summary')
        
        if result.get('success'):
            print(f"✅ Carpeta: {result['folder_name']}")
            print(f"📊 Total mensajes: {result['total_messages']}")
            print(f"📊 No leídos: {result['unread_count']}")
        else:
            print(f"❌ Error obteniendo resumen: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error en prueba de resumen: {e}")

async def test_email_processing(robot):
    """Probar procesamiento de correos"""
    print("\n🔄 Probando procesamiento de correos...")
    
    try:
        result = await robot.execute_command('process_emails')
        
        if result['success']:
            print(f"✅ Procesados: {result['processed']} correos")
            print(f"📤 PDFs enviados: {result['pdfs_sent']} a RabbitMQ")
            print(f"❌ Errores: {result['errors']}")
            
            if result['processed'] > 0:
                print("🎉 ¡Procesamiento exitoso!")
            else:
                print("ℹ️ No hay correos nuevos para procesar")
        else:
            print(f"❌ Error en procesamiento: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error en prueba de procesamiento: {e}")

async def test_attachment_download(robot):
    """Probar descarga de adjuntos específicos"""
    print("\n📎 Probando descarga de adjuntos...")
    
    try:
        # Primero obtener algunos mensajes
        search_result = await robot.execute_command('search_iniciativa4', {'top': 3})
        
        if search_result['success'] and search_result['emails']:
            # Tomar el primer mensaje con adjuntos
            message_with_attachments = None
            for email in search_result['emails']:
                if email.get('hasAttachments', False):
                    message_with_attachments = email
                    break
            
            if message_with_attachments:
                message_id = message_with_attachments['id']
                print(f"📧 Descargando adjuntos del mensaje: {message_with_attachments.get('subject', 'Sin asunto')}")
                
                result = await robot.execute_command('download_attachments', {
                    'message_ids': [message_id]
                })
                
                if result['success']:
                    print(f"✅ {result['count']} archivos descargados")
                    for file_path in result['downloaded_files']:
                        print(f"   📄 {file_path}")
                else:
                    print(f"❌ Error descargando adjuntos: {result.get('error')}")
            else:
                print("ℹ️ No se encontraron mensajes con adjuntos")
        else:
            print("ℹ️ No hay mensajes disponibles para probar")
            
    except Exception as e:
        print(f"❌ Error en prueba de descarga: {e}")

async def test_rabbitmq_connection(robot):
    """Probar conexión con RabbitMQ"""
    print("\n🐰 Probando conexión con RabbitMQ...")
    
    try:
        if robot.rabbitmq_sender:
            # Intentar enviar un mensaje de prueba
            test_email_info = {
                'subject': 'Mensaje de prueba',
                'sender': 'test@example.com',
                'received_date': datetime.now().isoformat(),
                'folder': 'Iniciativa4',
                'message_id': 'test-123',
                'has_attachments': False,
                'attachment_count': 0
            }
            
            # Crear un archivo de prueba
            test_file_path = './test_attachments/test.pdf'
            os.makedirs('./test_attachments', exist_ok=True)
            
            with open(test_file_path, 'w') as f:
                f.write('Test PDF content')
            
            # Enviar mensaje de prueba
            success = robot.rabbitmq_sender.send_pdf_message(test_file_path, test_email_info)
            
            if success:
                print("✅ Mensaje de prueba enviado a RabbitMQ")
            else:
                print("❌ Error enviando mensaje de prueba")
        else:
            print("❌ Sender de RabbitMQ no disponible")
            
    except Exception as e:
        print(f"❌ Error en prueba de RabbitMQ: {e}")

async def main():
    """Función principal de prueba"""
    print("=" * 70)
    print("PRUEBA DEL FLUJO COMPLETO - ROBOT001")
    print("=" * 70)
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    robot = None
    
    try:
        # 1. Probar inicialización
        robot = await test_robot_initialization()
        if not robot:
            print("❌ No se pudo inicializar el robot. Abortando pruebas.")
            return
        
        # 2. Probar lectura de correos
        await test_email_reading(robot)
        
        # 3. Probar resumen de carpeta
        await test_folder_summary(robot)
        
        # 4. Probar conexión RabbitMQ
        await test_rabbitmq_connection(robot)
        
        # 5. Probar descarga de adjuntos
        await test_attachment_download(robot)
        
        # 6. Probar procesamiento completo
        await test_email_processing(robot)
        
        # 7. Mostrar estadísticas finales
        print("\n📊 Estadísticas finales:")
        final_status = await robot.get_status()
        
        if final_status.get('processing_stats'):
            stats = final_status['processing_stats']
            print(f"📊 Total procesados: {stats['processed_messages']}")
            print(f"📊 Procesados hoy: {stats['processed_today']}")
        
        if final_status.get('attachment_stats'):
            stats = final_status['attachment_stats']
            print(f"📁 Archivos descargados: {stats.get('total_files', 0)}")
            print(f"📁 Tamaño total: {stats.get('total_size_mb', 0)} MB")
        
        print("\n🎉 ¡Pruebas completadas!")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        logger.error(f"Error en pruebas: {e}")
        
    finally:
        # Limpiar
        if robot:
            await robot.stop()
            print("✅ Robot detenido")

if __name__ == "__main__":
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar pruebas
    asyncio.run(main())
