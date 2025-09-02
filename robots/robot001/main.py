"""
Robot001 - Main Entry Point
Robot especializado en procesamiento de emails de Outlook para la carpeta Iniciativa4
Flujo completo: Leer correos → Descargar PDFs → Enviar a RabbitMQ → Procesar con Pdf_Consumer
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

# Agregar el directorio del framework al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Agregar el directorio de Mail_loop_tracking al path
mail_tracking_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Mail_loop_tracking"
)
sys.path.append(mail_tracking_path)

# Agregar el directorio de Pdf_Consumer al path
pdf_consumer_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Pdf_Consumer"
)
sys.path.append(pdf_consumer_path)

from core.layers.analysis_extraction_layer.analysis_extraction_coordinator import (
    AnalysisExtractionCoordinator,
)
from core.layers.decision_layer.decision_coordinator import DecisionCoordinator
# Importar las 5 capas de procesamiento
from core.layers.ingestion_layer.ingestion_coordinator import IngestionCoordinator
from core.layers.ingestion_layer.document_classifier import DocumentClassifier
from core.layers.specialized_processing_layer.specialized_processing_coordinator import (
    SpecializedProcessingCoordinator,
)
from core.layers.storage_management_layer.storage_management_coordinator import (
    StorageManagementCoordinator,
)

from framework.core.orchestrator import Orchestrator
from framework.shared.logger import get_logger

# Importar mainExtract del Pdf_Consumer
try:
    import mainExtract
    PDF_CONSUMER_AVAILABLE = True
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("✅ Módulo mainExtract importado correctamente")
except ImportError as e:
    PDF_CONSUMER_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ No se pudo importar mainExtract: {e}")

logger = get_logger(__name__)


class Robot001:
    """Robot especializado en procesamiento de emails de Outlook para Iniciativa4"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.mail_reader = None
        self.attachment_downloader = None
        self.rabbitmq_sender = None
        self.orchestrator = None
        self.is_running = False
        self.processed_messages = (
            set()
        )  # Para evitar procesar el mismo mensaje dos veces

        # Configuración por defecto del robot
        self.robot_config = {
            "robot_id": "robot001",
            "robot_name": "Outlook Iniciativa4 Processor (Complete Flow)",
            "version": "3.0.0",
            "email_processing": {
                "enabled": True,
                "check_interval": 300,  # 5 minutos
                "max_emails": 100,
                "auto_processing": True,
                "notification_enabled": True,
                "download_pdfs_only": True,  # Solo descargar PDFs
                "process_unread_only": True,  # Solo procesar no leídos
            },
            "monitoring": {"enabled": True, "continuous": True, "log_level": "INFO"},
            "outlook_config": {
                "folder_name": "Iniciativa4",
                "download_attachments": True,
                "attachment_path": "./robot001_attachments",
            },
            "rabbitmq_config": {
                "host": "localhost",
                "port": 5672,
                "username": "admin",
                "password": "admin",
                "queue_name": "pdf_processing_queue",
                "virtual_host": "/",
            },
        }

        # Actualizar configuración
        if config:
            self.robot_config.update(config)

        self._initialize_robot()

    def _initialize_robot(self):
        """Inicializar componentes del robot"""
        try:
            logger.info(
                "Inicializando Robot001 - Procesador de Outlook Iniciativa4 (Flujo Completo)"
            )

            # Importar módulos de Mail_loop_tracking
            try:
                from config import validate_config
                from outlook.attachment_downloader import AttachmentDownloader
                from outlook.folder_reader import (
                    get_folder_summary,
                    get_messages_from_folder,
                )
                from outlook.graph_client import (
                    get_authenticated_session,
                    validate_session,
                )
                from outlook.rabbitmq_sender import RabbitMQSender

                # Validar configuración de Mail_loop_tracking
                validate_config()

                # Verificar autenticación
                session = get_authenticated_session()
                if not validate_session(session):
                    raise Exception(
                        "No se pudo validar la sesión de Microsoft Graph API"
                    )

                # Inicializar lector de correos
                self.mail_reader = {
                    "get_messages": get_messages_from_folder,
                    "get_summary": get_folder_summary,
                    "session": session,
                }
                logger.info("✅ Módulo Mail_loop_tracking inicializado correctamente")

                # Inicializar descargador de adjuntos
                attachment_path = self.robot_config["outlook_config"]["attachment_path"]
                self.attachment_downloader = AttachmentDownloader(
                    download_dir=attachment_path
                )
                logger.info("✅ Descargador de adjuntos inicializado")

                # Inicializar sender de RabbitMQ
                rabbitmq_config = self.robot_config["rabbitmq_config"]
                self.rabbitmq_sender = RabbitMQSender(rabbitmq_config)
                logger.info("✅ Sender de RabbitMQ inicializado")

            except ImportError as e:
                logger.error(f"Error importando módulos de Mail_loop_tracking: {e}")
                raise Exception("No se pudo importar el módulo Mail_loop_tracking")

            # Inicializar orquestador del framework
            self.orchestrator = Orchestrator()
            logger.info("✅ Orquestador inicializado")

            # Inicializar las 5 capas de procesamiento
            self._initialize_processing_layers()

            logger.info("✅ Robot001 inicializado correctamente")

        except Exception as e:
            logger.error(f"Error inicializando Robot001: {e}")
            raise

    def _initialize_processing_layers(self):
        """Inicializar las 5 capas de procesamiento"""
        try:
            logger.info("🔧 Inicializando capas de procesamiento...")

            # 1. Capa de Ingesta (Clasificar, validar, escanear)
            self.ingestion_coordinator = IngestionCoordinator()
            logger.info("✅ Capa 1: Ingesta inicializada")

            # 2. Capa de Procesamiento Especializado (PDFs, Word, Email)
            self.specialized_coordinator = SpecializedProcessingCoordinator()
            logger.info("✅ Capa 2: Procesamiento Especializado inicializada")

            # 3. Capa de Análisis y Extracción (Extraer datos, analizar contenido)
            self.analysis_coordinator = AnalysisExtractionCoordinator()
            logger.info("✅ Capa 3: Análisis y Extracción inicializada")

            # 4. Capa de Almacenamiento y Gestión (Storage, índices, cache)
            self.storage_coordinator = StorageManagementCoordinator()
            logger.info("✅ Capa 4: Almacenamiento y Gestión inicializada")

            # 5. Capa de Decisión (Local, AWS, híbrido, manual)
            self.decision_coordinator = DecisionCoordinator()
            logger.info("✅ Capa 5: Decisión inicializada")

            logger.info(
                "🎉 Todas las capas de procesamiento inicializadas correctamente"
            )

        except Exception as e:
            logger.error(f"❌ Error inicializando capas de procesamiento: {e}")
            raise

    async def start(self):
        """Iniciar el robot"""
        try:
            logger.info("Iniciando Robot001...")
            self.is_running = True

            # Registrar el robot en el orquestador
            # await self.orchestrator.register_robot()  # Método no disponible en MVP

            # Iniciar monitoreo si está habilitado
            if (
                self.robot_config["monitoring"]["enabled"]
                and self.robot_config["monitoring"]["continuous"]
            ):

                logger.info("Iniciando monitoreo continuo de Iniciativa4")
                # El monitoreo se maneja en el bucle principal

            logger.info("Robot001 iniciado correctamente")

        except Exception as e:
            logger.error(f"Error iniciando Robot001: {e}")
            self.is_running = False
            raise

    async def stop(self):
        """Detener el robot"""
        try:
            logger.info("Deteniendo Robot001...")
            self.is_running = False

            # Cerrar conexiones
            if self.rabbitmq_sender:
                self.rabbitmq_sender.close()
                logger.info("✅ Conexión RabbitMQ cerrada")

            # Desregistrar del orquestador
            if self.orchestrator:
                # await self.orchestrator.unregister_robot()  # Método no disponible en MVP
                pass

            logger.info("✅ Robot001 detenido correctamente")

        except Exception as e:
            logger.error(f"Error deteniendo Robot001: {e}")
            raise

    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del robot"""
        try:
            status = {
                "robot_id": self.robot_config["robot_id"],
                "robot_name": self.robot_config["robot_name"],
                "version": self.robot_config["version"],
                "is_running": self.is_running,
                "start_time": datetime.now().isoformat(),
                "components": {
                    "mail_reader": self.mail_reader is not None,
                    "attachment_downloader": self.attachment_downloader is not None,
                    "rabbitmq_sender": self.rabbitmq_sender is not None,
                    "orchestrator": self.orchestrator is not None,
                },
                "processing_stats": {
                    "processed_messages": len(self.processed_messages),
                    "processed_today": len(
                        [
                            m
                            for m in self.processed_messages
                            if m.startswith(datetime.now().strftime("%Y-%m-%d"))
                        ]
                    ),
                },
            }

            # Agregar estado de Iniciativa4 si está disponible
            if self.mail_reader:
                try:
                    folder_name = self.robot_config["outlook_config"]["folder_name"]
                    summary = self.mail_reader["get_summary"](folder_name)
                    status["iniciativa4_status"] = summary
                except Exception as e:
                    logger.error(f"Error obteniendo estado de Iniciativa4: {e}")
                    status["iniciativa4_status"] = {"error": str(e)}

            # Agregar estadísticas de adjuntos si está disponible
            if self.attachment_downloader:
                try:
                    download_stats = self.attachment_downloader.get_download_stats()
                    status["attachment_stats"] = download_stats
                except Exception as e:
                    logger.error(f"Error obteniendo estadísticas de adjuntos: {e}")
                    status["attachment_stats"] = {"error": str(e)}

            return status

        except Exception as e:
            logger.error(f"Error obteniendo estado del robot: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def execute_command(
        self, command: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Ejecutar comando específico del robot"""
        try:
            logger.info(f"Ejecutando comando: {command}")

            if command == "search_iniciativa4":
                if not self.mail_reader:
                    raise ValueError("Módulo Mail_loop_tracking no disponible")

                folder_name = self.robot_config["outlook_config"]["folder_name"]
                top = params.get("top", 50) if params else 50

                messages = self.mail_reader["get_messages"](folder_name, top=top)
                return {
                    "success": True,
                    "folder": folder_name,
                    "emails_count": len(messages),
                    "emails": messages,
                    "timestamp": datetime.now().isoformat(),
                }

            elif command == "get_summary":
                if not self.mail_reader:
                    raise ValueError("Módulo Mail_loop_tracking no disponible")

                folder_name = self.robot_config["outlook_config"]["folder_name"]
                summary = self.mail_reader["get_summary"](folder_name)
                return summary

            elif command == "process_emails":
                """Procesar correos y enviar PDFs a RabbitMQ"""
                if not all(
                    [self.mail_reader, self.attachment_downloader, self.rabbitmq_sender]
                ):
                    raise ValueError("Componentes necesarios no disponibles")

                result = await self._process_folder_emails()
                return result

            elif command == "download_attachments":
                """Descargar adjuntos de correos específicos"""
                if not self.attachment_downloader:
                    raise ValueError("Descargador de adjuntos no disponible")

                message_ids = params.get("message_ids", []) if params else []
                if not message_ids:
                    raise ValueError("Se requieren IDs de mensajes")

                result = await self._download_specific_attachments(message_ids)
                return result

            elif command == "get_status":
                return await self.get_status()

            else:
                raise ValueError(f"Comando no reconocido: {command}")

        except Exception as e:
            logger.error(f"Error ejecutando comando {command}: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "timestamp": datetime.now().isoformat(),
            }

    async def _process_folder_emails(self) -> Dict[str, Any]:
        """Procesar correos de la carpeta Iniciativa4"""
        try:
            folder_name = self.robot_config["outlook_config"]["folder_name"]
            max_emails = self.robot_config["email_processing"].get("max_emails", 100)

            logger.info(f"🔄 Procesando correos de la carpeta '{folder_name}'")

            # Obtener mensajes
            messages = self.mail_reader["get_messages"](folder_name, top=max_emails)

            if not messages:
                logger.info(f"📧 No hay mensajes para procesar en '{folder_name}'")
                return {
                    "success": True,
                    "processed": 0,
                    "pdfs_sent": 0,
                    "errors": 0,
                    "message": "No hay mensajes para procesar",
                }

            processed_count = 0
            pdfs_sent = 0
            errors = 0

            for message in messages:
                try:
                    message_id = message.get("id")
                    if not message_id:
                        continue

                    # Verificar si ya fue procesado
                    if message_id in self.processed_messages:
                        logger.debug(f"⏭️ Mensaje ya procesado: {message_id}")
                        continue

                    # Verificar si es no leído (si está habilitado)
                    if self.robot_config["email_processing"][
                        "process_unread_only"
                    ] and message.get("isRead", True):
                        logger.debug(f"⏭️ Mensaje ya leído: {message_id}")
                        continue

                    # Procesar mensaje
                    result = await self._process_single_message(message)

                    if result["success"]:
                        processed_count += 1
                        pdfs_sent += result["pdfs_sent"]
                        self.processed_messages.add(message_id)

                        # 🎯 Mostrar información de clasificación
                        if result.get("email_classification"):
                            classification = result["email_classification"]
                            route_name = classification.get("primary_route_name", "No clasificado")
                            confidence = classification.get("classification_confidence", 0)
                            logger.info(
                                f"✅ Mensaje procesado: {message.get('subject', 'Sin asunto')} "
                                f"→ Ruta: {route_name} (Confianza: {confidence:.2f})"
                            )
                        else:
                            logger.info(
                                f"✅ Mensaje procesado: {message.get('subject', 'Sin asunto')}"
                            )

                        # Log información del procesamiento
                        logger.info(f"📤 PDFs enviados a Pdf_Consumer: {result['pdfs_sent']}/{result['pdfs_downloaded']}")
                    else:
                        errors += 1
                        logger.error(f"❌ Error procesando mensaje: {result['error']}")

                except Exception as e:
                    errors += 1
                    logger.error(f"❌ Error procesando mensaje: {e}")

            logger.info(
                f"📊 Procesamiento completado: {processed_count} procesados, {pdfs_sent} PDFs enviados a Pdf_Consumer, {errors} errores"
            )

            return {
                "success": True,
                "processed": processed_count,
                "pdfs_sent": pdfs_sent,
                "errors": errors,
                "total_messages": len(messages),
                # 📤 PROCESAMIENTO SIMPLIFICADO
                "processing_summary": {
                    "method": "rabbitmq_pdf_consumer",
                    "pdfs_sent_to_consumer": pdfs_sent,
                    "message": f"PDFs enviados al Pdf_Consumer para extracción de texto y datos"
                }
            }

        except Exception as e:
            logger.error(f"❌ Error en procesamiento de correos: {e}")
            return {"success": False, "error": str(e)}

    async def _process_single_message(self, message: Dict) -> Dict[str, Any]:
        """Procesar un mensaje individual"""
        try:
            message_id = message.get("id")
            subject = message.get("subject", "Sin asunto")
            sender = self._extract_sender_email(message)
            received_date = message.get("receivedDateTime", "")
            
            # Extraer cuerpo del correo
            body = self._extract_email_body(message)

            logger.info(f"📧 Procesando: {subject} (De: {sender})")

            # 🎯 CLASIFICAR EL CORREO POR CONTENIDO
            document_classifier = DocumentClassifier()
            classification_result = document_classifier.classify_email_by_content(subject, body)
            
            logger.info(f"🎯 Clasificación del correo: {classification_result.get('primary_route_name', 'No clasificado')} "
                       f"(Confianza: {classification_result.get('classification_confidence', 0):.2f})")

            # Extraer información del correo
            email_info = {
                "subject": subject,
                "sender": sender,
                "received_date": received_date,
                "folder": self.robot_config["outlook_config"]["folder_name"],
                "message_id": message_id,
                "has_attachments": message.get("hasAttachments", False),
                "attachment_count": 0,
                "body_preview": body[:200] + "..." if len(body) > 200 else body,
                "classification": classification_result,
            }

            # 🔧 DESCARGAR TODOS LOS ADJUNTOS INMEDIATAMENTE
            logger.info(f"📥 Descargando adjuntos del mensaje: {subject}")
            all_attachments_downloaded = self.attachment_downloader.download_message_attachments(message)
            
            # Filtrar solo PDFs para el procesamiento posterior (si es necesario)
            pdfs_downloaded = [
                f for f in all_attachments_downloaded if f.lower().endswith(".pdf")
            ]

            email_info["attachment_count"] = len(all_attachments_downloaded)
            logger.info(f"📄 Adjuntos descargados: {len(all_attachments_downloaded)} archivos")
            logger.info(f"📄 PDFs para procesamiento: {len(pdfs_downloaded)} archivos")

            # 📤 Enviar TODOS los PDFs en UN SOLO mensaje a RabbitMQ
            pdfs_sent = 0
            
            if pdfs_downloaded:
                # 🔍 VERIFICAR Y FILTRAR PDFs VÁLIDOS
                valid_pdfs = []
                for pdf_path in pdfs_downloaded:
                    if self._verify_pdf_file(pdf_path):
                        valid_pdfs.append(pdf_path)
                        logger.info(f"✅ PDF válido: {pdf_path}")
                    else:
                        logger.error(f"❌ PDF inválido descartado: {pdf_path}")
                
                # 📤 Enviar TODOS los PDFs válidos en UN SOLO mensaje
                if valid_pdfs:
                    if self._send_multiple_pdfs_to_rabbitmq(valid_pdfs, email_info):
                        pdfs_sent = len(valid_pdfs)
                        logger.info(f"📤 {pdfs_sent} PDFs enviados en UN SOLO mensaje a RabbitMQ")
                    else:
                        logger.error(f"❌ Error enviando PDFs a RabbitMQ")
                else:
                    logger.warning("⚠️ No hay PDFs válidos para enviar")

            # Enviar resumen del correo
            self.rabbitmq_sender.send_email_summary(
                {
                    **email_info,
                    "pdfs_downloaded": len(pdfs_downloaded),
                    "pdfs_sent": pdfs_sent,
                    "processing_timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "success": True,
                "pdfs_sent": pdfs_sent,
                "pdfs_downloaded": len(pdfs_downloaded),
                "all_attachments_downloaded": len(all_attachments_downloaded),
                # 🎯 INFORMACIÓN DE CLASIFICACIÓN DEL CORREO
                "email_classification": classification_result,
                # 📤 PROCESAMIENTO SIMPLIFICADO - Solo envío a RabbitMQ
                "processing_method": "rabbitmq_pdf_consumer",
                "message": f"PDFs enviados a Pdf_Consumer para procesamiento: {pdfs_sent}/{len(pdfs_downloaded)}"
            }

        except Exception as e:
            logger.error(f"❌ Error procesando mensaje individual: {e}")
            return {"success": False, "error": str(e)}

    async def _download_specific_attachments(
        self, message_ids: List[str]
    ) -> Dict[str, Any]:
        """Descargar adjuntos de mensajes específicos"""
        try:
            folder_name = self.robot_config["outlook_config"]["folder_name"]
            downloaded_files = []

            for message_id in message_ids:
                try:
                    # Obtener mensaje específico
                    messages = self.mail_reader["get_messages"](folder_name, top=1000)
                    message = next(
                        (m for m in messages if m.get("id") == message_id), None
                    )

                    if not message:
                        logger.warning(f"⚠️ Mensaje no encontrado: {message_id}")
                        continue

                    # Descargar PDFs
                    pdfs = self.attachment_downloader.download_pdf_attachments(message)
                    downloaded_files.extend(pdfs)

                except Exception as e:
                    logger.error(f"❌ Error descargando adjuntos de {message_id}: {e}")

            return {
                "success": True,
                "downloaded_files": downloaded_files,
                "count": len(downloaded_files),
            }

        except Exception as e:
            logger.error(f"❌ Error descargando adjuntos específicos: {e}")
            return {"success": False, "error": str(e)}

    def _extract_sender_email(self, message: Dict) -> str:
        """Extraer email del remitente"""
        sender = message.get("from", {})
        if isinstance(sender, dict):
            email = sender.get("emailAddress", {}).get("address", "")
        else:
            email = str(sender)
        return email
    
    def _extract_email_body(self, message: Dict) -> str:
        """Extraer el cuerpo del correo electrónico"""
        try:
            # Intentar obtener el cuerpo del mensaje
            body = message.get("body", {})
            
            if isinstance(body, dict):
                # Si body es un diccionario, extraer el contenido
                content = body.get("content", "")
                content_type = body.get("contentType", "text")
                
                if content_type == "html":
                    # Si es HTML, intentar extraer solo texto
                    import re
                    # Remover tags HTML básicos
                    content = re.sub(r'<[^>]+>', '', content)
                    content = re.sub(r'&nbsp;', ' ', content)
                    content = re.sub(r'&amp;', '&', content)
                    content = re.sub(r'&lt;', '<', content)
                    content = re.sub(r'&gt;', '>', content)
                
                return content.strip()
            elif isinstance(body, str):
                return body.strip()
            else:
                return ""
                
        except Exception as e:
            logger.warning(f"Error extrayendo cuerpo del correo: {e}")
            return ""

    def _download_and_verify_pdfs(self, message: Dict) -> List[str]:
        """Descargar PDFs y verificar que se descargaron correctamente"""
        try:
            # Descargar PDFs
            pdfs_downloaded = self.attachment_downloader.download_pdf_attachments(message)
            
            # Verificar cada PDF descargado
            valid_pdfs = []
            for pdf_path in pdfs_downloaded:
                if self._verify_pdf_file(pdf_path):
                    valid_pdfs.append(pdf_path)
                    logger.info(f"✅ PDF válido descargado: {pdf_path}")
                else:
                    logger.warning(f"⚠️ PDF inválido descartado: {pdf_path}")
            
            return valid_pdfs
            
        except Exception as e:
            logger.error(f"❌ Error descargando PDFs: {e}")
            return []

    def _verify_pdf_file(self, pdf_path: str) -> bool:
        """Verificar que un archivo PDF existe y no está vacío"""
        try:
            import os
            from pathlib import Path
            
            file_path = Path(pdf_path)
            
            # Verificar que el archivo existe
            if not file_path.exists():
                logger.error(f"❌ Archivo no existe: {pdf_path}")
                return False
            
            # Verificar que no está vacío
            file_size = file_path.stat().st_size
            if file_size == 0:
                logger.error(f"❌ Archivo vacío: {pdf_path}")
                return False
            
            # Verificar que es un PDF válido (primeros bytes)
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    if header != b'%PDF':
                        logger.error(f"❌ No es un PDF válido: {pdf_path}")
                        return False
            except Exception as e:
                logger.error(f"❌ Error leyendo archivo: {pdf_path} - {e}")
                return False
            
            logger.debug(f"✅ PDF verificado: {pdf_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verificando PDF: {pdf_path} - {e}")
            return False

    def _send_multiple_pdfs_to_rabbitmq(self, pdf_paths: List[str], email_info: Dict) -> bool:
        """Enviar MÚLTIPLES PDFs en UN SOLO mensaje a RabbitMQ"""
        try:
            import uuid
            from pathlib import Path
            
            # Generar GUID único para todo el correo
            guid = str(uuid.uuid4())
            
            # 🎯 EXTRAER INFORMACIÓN DE CLASIFICACIÓN
            classification = email_info.get("classification", {})
            primary_route = classification.get("primary_route_name", "No clasificado")
            
            # 📁 CONVERTIR TODAS las rutas a absolutas
            pdf_list = []
            for pdf_path in pdf_paths:
                file_path = Path(pdf_path)
                absolute_path = str(file_path.absolute())
                pdf_list.append(absolute_path)
            
            # Crear mensaje con LISTA de PDFs - solo 3 propiedades
            message = {
                "guid": guid,
                "local_paths": pdf_list,  # 📋 LISTA de rutas de PDFs
                "primary_route_name": primary_route
            }
            
            # Enviar usando el método original pero con nuestro mensaje personalizado
            rabbitmq_success = self._send_custom_message_to_rabbitmq(message)
            
            # 🔥 LLAMAR DIRECTAMENTE A mainExtract.py después de RabbitMQ
            if rabbitmq_success:
                extract_success = self._call_mainextract_directly(message)
                if extract_success:
                    logger.info(f"✅ {len(pdf_list)} PDFs procesados por mainExtract")
                else:
                    logger.error(f"❌ Error procesando PDFs en mainExtract")
            
            return rabbitmq_success
            
        except Exception as e:
            logger.error(f"❌ Error preparando mensaje múltiple para RabbitMQ: {e}")
            return False

    def _send_pdf_to_rabbitmq(self, pdf_path: str, email_info: Dict) -> bool:
        """Enviar PDF a RabbitMQ con clasificación y rutas A, B, C"""
        try:
            import uuid
            from pathlib import Path
            
            # Generar GUID único
            guid = str(uuid.uuid4())
            
            # Obtener ruta absoluta del archivo
            file_path = Path(pdf_path)
            absolute_path = str(file_path.absolute())
            
            # 🎯 EXTRAER INFORMACIÓN DE CLASIFICACIÓN
            classification = email_info.get("classification", {})
            primary_route = classification.get("primary_route_name", "No clasificado")
            
            # Crear mensaje SIMPLIFICADO - solo 3 propiedades
            message = {
                "guid": guid,
                "local_path": absolute_path,
                "primary_route_name": primary_route
            }
            
            # Enviar usando el método original pero con nuestro mensaje personalizado
            rabbitmq_success = self._send_custom_message_to_rabbitmq(message)
            
            # 🔥 LLAMAR DIRECTAMENTE A mainExtract.py después de RabbitMQ
            if rabbitmq_success:
                extract_success = self._call_mainextract_directly(message)
                if extract_success:
                    logger.info(f"✅ PDF procesado por mainExtract: {absolute_path}")
                else:
                    logger.error(f"❌ Error procesando PDF en mainExtract: {absolute_path}")
            
            return rabbitmq_success
            
        except Exception as e:
            logger.error(f"❌ Error preparando mensaje para RabbitMQ: {e}")
            return False

    def _send_custom_message_to_rabbitmq(self, message: Dict) -> bool:
        """Enviar mensaje personalizado a RabbitMQ"""
        try:
            import json
            import pika
            
            # Convertir a JSON
            message_json = json.dumps(message, ensure_ascii=False)
            
            # Obtener configuración de RabbitMQ
            queue_name = self.robot_config["rabbitmq_config"].get("queue_name", "pdf_processing_queue")
            
            # Enviar mensaje
            self.rabbitmq_sender.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message_json.encode('utf-8'),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                    content_type='application/json'
                )
            )
            
            # 🎯 LOGS SIMPLIFICADOS
            route = message.get('primary_route_name', 'N/A')
            
            # Detectar si es un solo PDF o múltiples PDFs
            if 'local_paths' in message:
                # Múltiples PDFs
                pdf_count = len(message.get('local_paths', []))
                logger.info(f"✅ {pdf_count} PDFs enviados en UN SOLO mensaje a RabbitMQ:")
                logger.info(f"   📁 GUID: {message.get('guid', 'N/A')}")
                logger.info(f"   📄 local_paths: {pdf_count} archivos")
                for i, path in enumerate(message.get('local_paths', []), 1):
                    logger.info(f"      {i}. {path}")
                logger.info(f"   🎯 primary_route_name: {route}")
            else:
                # Un solo PDF (método anterior)
                logger.info(f"✅ PDF enviado a RabbitMQ (3 propiedades):")
                logger.info(f"   📁 GUID: {message.get('guid', 'N/A')}")
                logger.info(f"   📄 local_path: {message.get('local_path', 'N/A')}")
                logger.info(f"   🎯 primary_route_name: {route}")
            
            logger.debug(f"Mensaje JSON: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje personalizado a RabbitMQ: {e}")
            return False

    def _call_mainextract_directly(self, message: Dict) -> bool:
        """Llamar directamente al mainExtract.py con el mensaje JSON"""
        try:
            if not PDF_CONSUMER_AVAILABLE:
                logger.warning("⚠️ mainExtract no está disponible")
                return False
            
            import json
            import sys
            from io import StringIO
            
            # Preparar mensaje JSON para mainExtract
            # mainExtract espera: {"local_path": "ruta", "guid": "guid"}
            message_json = json.dumps(message, ensure_ascii=False)
            
            # 🎯 MOSTRAR INFORMACIÓN SIMPLIFICADA
            route = message.get('primary_route_name', 'N/A')
            
            # Detectar si es un solo PDF o múltiples PDFs
            if 'local_paths' in message:
                # Múltiples PDFs
                pdf_count = len(message.get('local_paths', []))
                logger.info(f"📤 Llamando mainExtract con {pdf_count} PDFs:")
                logger.info(f"   📁 GUID: {message.get('guid', 'N/A')}")
                logger.info(f"   📄 local_paths: {pdf_count} archivos")
                logger.info(f"   🎯 primary_route_name: {route}")
            else:
                # Un solo PDF (método anterior)
                logger.info(f"📤 Llamando mainExtract (3 propiedades):")
                logger.info(f"   📁 GUID: {message.get('guid', 'N/A')}")
                logger.info(f"   📄 local_path: {message.get('local_path', 'N/A')}")
                logger.info(f"   🎯 primary_route_name: {route}")
            
            logger.debug(f"Mensaje JSON: {message_json}")
            
            # Capturar stdout original
            original_stdout = sys.stdout
            captured_output = StringIO()
            
            try:
                # Redirigir stdout para capturar la salida de mainExtract
                sys.stdout = captured_output
                
                # Simular llamada con argumentos de línea de comandos
                original_argv = sys.argv.copy()
                sys.argv = ["mainExtract.py", message_json]
                
                # Llamar directamente a la función main de mainExtract
                mainExtract.main()
                
                # Restaurar argv original
                sys.argv = original_argv
                
                # Obtener la salida capturada
                output = captured_output.getvalue()
                if output:
                    logger.info(f"📄 Salida de mainExtract: {output.strip()}")
                
                logger.info(f"✅ mainExtract ejecutado exitosamente para {message.get('local_path', 'N/A')}")
                return True
                
            finally:
                # Restaurar stdout original
                sys.stdout = original_stdout
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando mainExtract: {e}")
            return False


async def main():
    """Función principal del robot"""
    print("=" * 60)
    print("ROBOT001 - PROCESADOR DE OUTLOOK PARA INICIATIVA4")
    print(
        "FLUJO SIMPLIFICADO: CORREOS → PDFs → RABBITMQ → PDF_CONSUMER → EXTRACCIÓN DE DATOS"
    )
    print("=" * 60)
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    robot = None

    try:
        # Configuración del robot
        config = {
            "email_processing": {
                "enabled": True,
                "check_interval": 10,  # 5 minutos
                "notification_enabled": True,
                "auto_processing": True,
                "download_pdfs_only": True,  # Solo descargar PDFs
                "process_unread_only": True,  # Solo procesar no leídos
            },
            "monitoring": {"enabled": True, "continuous": True},
            "outlook_config": {
                "folder_name": "Iniciativa4",  # Especificar la carpeta
                "attachment_path": "./robot001_attachments",
            },
            "rabbitmq_config": {
                "host": "localhost",
                "port": 5672,
                "username": "admin",
                "password": "admin",
                "queue_name": "pdf_processing_queue",
            },
        }

        # Crear e inicializar el robot
        robot = Robot001(config)

        # Mostrar estado inicial
        status = await robot.get_status()
        print(f"Estado del robot: {status['robot_name']} v{status['version']}")
        print(f"Componentes activos: {status['components']}")

        # Mostrar información de la carpeta
        if status.get("iniciativa4_status", {}).get("success"):
            folder_info = status["iniciativa4_status"]
            print(f"Carpeta configurada: {folder_info['folder_name']}")
            print(f"Total mensajes: {folder_info['total_messages']}")
            print(f"No leídos: {folder_info['unread_count']}")

        # Mostrar estadísticas de adjuntos
        if status.get("attachment_stats"):
            stats = status["attachment_stats"]
            print(f"Adjuntos descargados: {stats.get('total_files', 0)} archivos")
            print(f"Tamaño total: {stats.get('total_size_mb', 0)} MB")

        # Iniciar el robot
        await robot.start()

        # Procesar correos una sola vez
        print("\n🤖 Robot procesando correos una sola vez...")
        print("📧 Leyendo correos de la carpeta Iniciativa4")
        print("📄 Descargando PDFs y enviando a RabbitMQ")
        print("🔄 Procesando PDFs a través de las 5 capas:")
        print("   📥 Capa 1: Ingesta (Clasificar, validar, escanear)")
        print("   🔧 Capa 2: Procesamiento Especializado (PDFs)")
        print("   🔍 Capa 3: Análisis y Extracción (Datos)")
        print("   💾 Capa 4: Almacenamiento y Gestión")
        print("   🎯 Capa 5: Decisión Final (Local/AWS/Híbrido)")
        print("\nProcesando...")

        try:
            # Procesar correos una sola vez
            result = await robot.execute_command("process_emails")

            if result["success"]:
                print(f"✅ Procesados: {result['processed']} correos")
                print(f"📤 Adjuntos enviados: {result['pdfs_sent']} a RabbitMQ")

                # 🎯 MOSTRAR RESULTADOS DE CLASIFICACIÓN DE CORREOS
                if result.get("email_classification_summary"):
                    class_summary = result["email_classification_summary"]
                    print(f"\n🎯 CLASIFICACIÓN DE CORREOS:")
                    print(f"   📋 Ruta A (Estado de Cédula): {class_summary['ruta_a_count']}")
                    print(f"   📋 Ruta B (Documentos de Identificación): {class_summary['ruta_b_count']}")
                    print(f"   📋 Ruta C (Procesos Postumas): {class_summary['ruta_c_count']}")
                    print(f"   ❓ No clasificados: {class_summary['unclassified_count']}")
                    print(f"   ❌ Errores de clasificación: {class_summary['classification_errors']}")

                # 🎯 MOSTRAR RESULTADOS DE LAS 5 CAPAS
                if result.get("layer_processing_summary"):
                    summary = result["layer_processing_summary"]
                    print(f"\n🔄 PROCESAMIENTO DE CAPAS:")
                    print(
                        f"   📄 PDFs procesados por las 5 capas: {summary['total_pdfs_processed_through_layers']}"
                    )
                    print(
                        f"   ✅ Capas exitosas: {summary['successful_layer_processing']}"
                    )
                    print(
                        f"   🎉 Decisiones finales generadas: {summary['total_final_decisions']}"
                    )

                    # Mostrar algunas decisiones finales si están disponibles
                    if result.get("all_final_decisions"):
                        print("\n🎯 ÚLTIMAS DECISIONES FINALES:")
                        for i, decision in enumerate(
                            result["all_final_decisions"][-3:]
                        ):  # Mostrar últimas 3
                            decision_type = decision.get("decision_type", "N/A")
                            confidence = decision.get("confidence_score", "N/A")
                            print(
                                f"   📊 Decisión {i+1}: {decision_type} (confianza: {confidence})"
                            )

                if result["errors"] > 0:
                    print(f"\n❌ Errores: {result['errors']}")
                    
                print(f"\n✅ PROCESAMIENTO COMPLETADO")
                print(f"📊 Total mensajes en carpeta: {result['total_messages']}")
                print(f"📊 Mensajes procesados: {result['processed']}")
                
            else:
                print(
                    f"❌ Error en procesamiento: {result.get('error', 'Desconocido')}"
                )

        except Exception as e:
            logger.error(f"Error en procesamiento: {e}")
            print(f"❌ Error en procesamiento: {e}")

    except Exception as e:
        print(f"\n❌ Error en el robot: {e}")
        logger.error(f"Error en main del robot: {e}")

    finally:
        # Detener el robot
        if robot:
            await robot.stop()

        print("✅ Robot detenido.")
        print("=" * 60)


if __name__ == "__main__":
    # Configurar logging
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Ejecutar el robot
    asyncio.run(main())
