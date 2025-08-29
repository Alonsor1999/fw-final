"""
Robot001 - Flujo Simple
Solo leer correos, descargar PDFs y enviar a cola RabbitMQ
"""

import asyncio
import os
import sys
from datetime import datetime

# Agregar el directorio del framework al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Agregar el directorio de Mail_loop_tracking al path
mail_tracking_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Mail_loop_tracking"
)
sys.path.append(mail_tracking_path)

from framework.shared.logger import get_logger

logger = get_logger(__name__)


class SimpleRobot:
    """Robot simplificado - Solo lectura, descarga y envío a RabbitMQ"""

    def __init__(self):
        self.mail_reader = None
        self.attachment_downloader = None
        self.rabbitmq_sender = None

    def initialize(self):
        """Inicializar solo los componentes necesarios"""
        try:
            logger.info("🤖 Inicializando Robot Simple...")

            # Importar módulos necesarios
            from config import validate_config
            from outlook.attachment_downloader import AttachmentDownloader
            from outlook.folder_reader import (
                get_folder_summary,
                get_messages_from_folder,
            )
            from outlook.graph_client import get_authenticated_session, validate_session
            from outlook.rabbitmq_sender import RabbitMQSender

            # Validar configuración
            validate_config()

            # Verificar autenticación con Microsoft Graph
            session = get_authenticated_session()
            if not validate_session(session):
                raise Exception("No se pudo validar la sesión de Microsoft Graph API")

            # Inicializar componentes
            self.mail_reader = {
                "get_messages": get_messages_from_folder,
                "get_summary": get_folder_summary,
                "session": session,
            }
            logger.info("✅ Lector de correos inicializado")

            self.attachment_downloader = AttachmentDownloader(
                download_dir="./robot001_attachments"
            )
            logger.info("✅ Descargador de adjuntos inicializado")

            # Configuración RabbitMQ
            rabbitmq_config = {
                "host": "localhost",
                "port": 5672,
                "username": "admin",
                "password": "admin",
                "queue_name": "pdf_processing_queue",
                "virtual_host": "/",
            }

            self.rabbitmq_sender = RabbitMQSender(rabbitmq_config)
            logger.info("✅ Sender de RabbitMQ inicializado")

            logger.info("🎉 Robot Simple inicializado correctamente")

        except Exception as e:
            logger.error(f"❌ Error inicializando robot: {e}")
            raise

    def process_emails(self):
        """Procesar correos de Iniciativa4"""
        try:
            folder_name = "Iniciativa4"

            print(f"\n📧 Obteniendo correos de '{folder_name}'...")

            # Obtener resumen de la carpeta
            summary = self.mail_reader["get_summary"](folder_name)
            print(f"📊 Carpeta: {summary['folder_name']}")
            print(f"📊 Total mensajes: {summary['total_messages']}")
            print(f"📊 No leídos: {summary['unread_count']}")

            # Obtener mensajes (solo los últimos 10 para prueba)
            messages = self.mail_reader["get_messages"](folder_name, top=10)
            print(f"📨 Procesando {len(messages)} mensajes...")

            processed_count = 0
            pdfs_sent = 0

            for message in messages:
                try:
                    message_id = message.get("id")
                    subject = message.get("subject", "Sin asunto")
                    sender = self._extract_sender_email(message)
                    has_attachments = message.get("hasAttachments", False)

                    print(f"\n📧 Procesando: {subject}")
                    print(f"   📤 De: {sender}")
                    print(f"   📎 Adjuntos: {'Sí' if has_attachments else 'No'}")

                    if not has_attachments:
                        print("   ⏭️ Sin adjuntos, saltando...")
                        continue

                    # Descargar PDFs
                    print("   📥 Descargando PDFs...")
                    pdfs_downloaded = (
                        self.attachment_downloader.download_pdf_attachments(message)
                    )

                    if not pdfs_downloaded:
                        print("   📄 No se encontraron PDFs")
                        continue

                    print(f"   ✅ Descargados {len(pdfs_downloaded)} PDFs:")
                    for pdf in pdfs_downloaded:
                        print(f"      📄 {os.path.basename(pdf)}")

                    # Enviar cada PDF a RabbitMQ
                    for pdf_path in pdfs_downloaded:
                        email_info = {
                            "subject": subject,
                            "sender": sender,
                            "received_date": message.get("receivedDateTime", ""),
                            "folder": folder_name,
                            "message_id": message_id,
                            "processing_timestamp": datetime.now().isoformat(),
                        }

                        if self.rabbitmq_sender.send_pdf_message(pdf_path, email_info):
                            pdfs_sent += 1
                            print(
                                f"   📤 Enviado a RabbitMQ: {os.path.basename(pdf_path)}"
                            )
                        else:
                            print(f"   ❌ Error enviando: {os.path.basename(pdf_path)}")

                    processed_count += 1

                except Exception as e:
                    logger.error(f"❌ Error procesando mensaje: {e}")
                    print(f"   ❌ Error: {e}")

            print(f"\n🎉 Procesamiento completado:")
            print(f"   ✅ Correos procesados: {processed_count}")
            print(f"   📤 PDFs enviados a RabbitMQ: {pdfs_sent}")

            return {
                "success": True,
                "processed": processed_count,
                "pdfs_sent": pdfs_sent,
            }

        except Exception as e:
            logger.error(f"❌ Error en procesamiento: {e}")
            print(f"❌ Error: {e}")
            return {"success": False, "error": str(e)}

    def _extract_sender_email(self, message):
        """Extraer email del remitente"""
        sender = message.get("from", {})
        if isinstance(sender, dict):
            email = sender.get("emailAddress", {}).get("address", "")
        else:
            email = str(sender)
        return email

    def close(self):
        """Cerrar conexiones"""
        if self.rabbitmq_sender:
            self.rabbitmq_sender.close()
            logger.info("✅ Conexión RabbitMQ cerrada")


def main():
    """Función principal simplificada"""
    print("=" * 60)
    print("ROBOT001 - FLUJO SIMPLE")
    print("LEER CORREOS → DESCARGAR PDFs → ENVIAR A RABBITMQ")
    print("=" * 60)
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    robot = None

    try:
        # Crear e inicializar robot
        robot = SimpleRobot()
        robot.initialize()

        # Procesar correos una sola vez
        print("\n🚀 Iniciando procesamiento de correos...")
        result = robot.process_emails()

        if result["success"]:
            print(f"\n✅ ¡Procesamiento exitoso!")
            print(f"📊 Correos procesados: {result['processed']}")
            print(f"📤 PDFs enviados a RabbitMQ: {result['pdfs_sent']}")
        else:
            print(f"\n❌ Error en procesamiento: {result['error']}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Error en main: {e}")

    finally:
        if robot:
            robot.close()

        print(f"\n✅ Proceso terminado: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)


if __name__ == "__main__":
    # Configurar logging básico
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Ejecutar
    main()
