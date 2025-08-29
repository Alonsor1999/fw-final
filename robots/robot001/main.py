"""
Robot001 - Main Entry Point
Robot especializado en procesamiento de emails de Outlook para la carpeta Iniciativa4
Flujo completo: Leer correos → Descargar PDFs → Enviar a RabbitMQ → Procesar con Pdf_Consumer
"""

import asyncio
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

from core.layers.analysis_extraction_layer.analysis_extraction_coordinator import (
    AnalysisExtractionCoordinator,
)
from core.layers.decision_layer.decision_coordinator import DecisionCoordinator

# Importar las 5 capas de procesamiento
from core.layers.ingestion_layer.ingestion_coordinator import IngestionCoordinator
from core.layers.specialized_processing_layer.specialized_processing_coordinator import (
    SpecializedProcessingCoordinator,
)
from core.layers.storage_management_layer.storage_management_coordinator import (
    StorageManagementCoordinator,
)

from framework.core.orchestrator import Orchestrator
from framework.shared.logger import get_logger

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
            total_layer_results = []
            total_final_decisions = []

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

                        # 🎯 Recopilar resultados de las 5 capas
                        if "layer_processing_results" in result:
                            total_layer_results.extend(
                                result["layer_processing_results"]
                            )
                        if "final_decisions" in result:
                            total_final_decisions.extend(result["final_decisions"])

                        logger.info(
                            f"✅ Mensaje procesado: {message.get('subject', 'Sin asunto')}"
                        )

                        # Log información de las capas si están disponibles
                        if result.get("final_decisions"):
                            successful_layers = len(
                                [
                                    r
                                    for r in result["final_decisions"]
                                    if r.get("success")
                                ]
                            )
                            logger.info(
                                f"🎯 Capas procesadas exitosamente: {successful_layers}/{len(result.get('layer_processing_results', []))}"
                            )
                    else:
                        errors += 1
                        logger.error(f"❌ Error procesando mensaje: {result['error']}")

                except Exception as e:
                    errors += 1
                    logger.error(f"❌ Error procesando mensaje: {e}")

            logger.info(
                f"📊 Procesamiento completado: {processed_count} procesados, {pdfs_sent} PDFs enviados, {errors} errores"
            )

            # Estadísticas de las 5 capas
            successful_layer_processing = len(
                [r for r in total_layer_results if r.get("success", False)]
            )
            total_layer_processing = len(total_layer_results)

            if total_layer_processing > 0:
                logger.info(
                    f"🎯 Capas de procesamiento: {successful_layer_processing}/{total_layer_processing} exitosas"
                )
                logger.info(
                    f"🎉 Decisiones finales generadas: {len(total_final_decisions)}"
                )

            return {
                "success": True,
                "processed": processed_count,
                "pdfs_sent": pdfs_sent,
                "errors": errors,
                "total_messages": len(messages),
                # 🎉 RESULTADOS DE LAS 5 CAPAS
                "layer_processing_summary": {
                    "total_pdfs_processed_through_layers": total_layer_processing,
                    "successful_layer_processing": successful_layer_processing,
                    "failed_layer_processing": total_layer_processing
                    - successful_layer_processing,
                    "total_final_decisions": len(total_final_decisions),
                },
                "all_layer_results": total_layer_results,
                "all_final_decisions": total_final_decisions,
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

            logger.info(f"📧 Procesando: {subject} (De: {sender})")

            # Extraer información del correo
            email_info = {
                "subject": subject,
                "sender": sender,
                "received_date": received_date,
                "folder": self.robot_config["outlook_config"]["folder_name"],
                "message_id": message_id,
                "has_attachments": message.get("hasAttachments", False),
                "attachment_count": 0,
            }

            # Descargar PDFs si está habilitado
            pdfs_downloaded = []
            if self.robot_config["email_processing"]["download_pdfs_only"]:
                pdfs_downloaded = self.attachment_downloader.download_pdf_attachments(
                    message
                )
            else:
                # Descargar todos los adjuntos
                all_attachments = (
                    self.attachment_downloader.download_message_attachments(message)
                )
                pdfs_downloaded = [
                    f for f in all_attachments if f.lower().endswith(".pdf")
                ]

            email_info["attachment_count"] = len(pdfs_downloaded)

            # Enviar PDFs a RabbitMQ y procesar a través de las 5 capas
            pdfs_sent = 0
            layer_processing_results = []

            for pdf_path in pdfs_downloaded:
                # 📤 PASO 1: Enviar a RabbitMQ (flujo original)
                if self.rabbitmq_sender.send_pdf_message(pdf_path, email_info):
                    pdfs_sent += 1
                    logger.info(f"📤 PDF enviado a RabbitMQ: {pdf_path}")

                    # 🔄 PASO 2: Procesar a través de las 5 capas (NUEVA FUNCIONALIDAD)
                    layer_result = await self._process_pdf_through_layers(
                        pdf_path, email_info
                    )
                    layer_processing_results.append(layer_result)

                    if layer_result.get("success", False):
                        logger.info(
                            f"🎯 PDF procesado exitosamente a través de las 5 capas: {pdf_path}"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Error procesando PDF a través de las capas: {layer_result.get('error', 'Desconocido')}"
                        )
                else:
                    logger.error(f"❌ Error enviando PDF a RabbitMQ: {pdf_path}")

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
                # 🎉 RESULTADO DE LAS 5 CAPAS - DECISIÓN FINAL DE LA ÚLTIMA CAPA
                "layer_processing_results": layer_processing_results,
                "final_decisions": [
                    result.get("final_decision_result", {})
                    for result in layer_processing_results
                    if result.get("success", False)
                ],
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

    async def _process_pdf_through_layers(
        self, pdf_path: str, email_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa un PDF a través de las 5 capas secuencialmente

        Args:
            pdf_path: Ruta del archivo PDF
            email_info: Información del correo electrónico

        Returns:
            Dict con el resultado de la última capa (Decision Layer)
        """
        try:
            logger.info(f"🔄 Procesando PDF a través de las 5 capas: {pdf_path}")
            start_time = time.time()

            # 🔸 CAPA 1: Ingesta (Clasificar, validar, escanear)
            logger.info("📥 Capa 1: Procesando Ingesta...")
            ingestion_result = self.ingestion_coordinator.process_document(pdf_path)
            if not ingestion_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Error en Capa de Ingesta: {ingestion_result.get('error', 'Desconocido')}",
                    "failed_layer": "ingestion",
                    "pdf_path": pdf_path,
                }

            # 🔸 CAPA 2: Procesamiento Especializado (PDFs específicamente)
            logger.info("🔧 Capa 2: Procesando Especializado...")
            specialized_result = self.specialized_coordinator.process_document(pdf_path)
            if not specialized_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Error en Capa de Procesamiento Especializado: {specialized_result.get('error', 'Desconocido')}",
                    "failed_layer": "specialized_processing",
                    "pdf_path": pdf_path,
                }

            # 🔸 CAPA 3: Análisis y Extracción (Extraer datos, analizar contenido)
            logger.info("🔍 Capa 3: Procesando Análisis y Extracción...")
            analysis_result = self.analysis_coordinator.process_document(pdf_path)
            if not analysis_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Error en Capa de Análisis y Extracción: {analysis_result.get('error', 'Desconocido')}",
                    "failed_layer": "analysis_extraction",
                    "pdf_path": pdf_path,
                }

            # 🔸 CAPA 4: Almacenamiento y Gestión (Storage, índices, cache)
            logger.info("💾 Capa 4: Procesando Almacenamiento...")
            storage_result = self.storage_coordinator.process_document(pdf_path)
            if not storage_result.get("success", False):
                return {
                    "success": False,
                    "error": f"Error en Capa de Almacenamiento: {storage_result.get('error', 'Desconocido')}",
                    "failed_layer": "storage_management",
                    "pdf_path": pdf_path,
                }

            # 🔸 CAPA 5: Decisión (Local, AWS, híbrido, manual) - LA ÚLTIMA CAPA
            logger.info("🎯 Capa 5: Procesando Decisión...")
            decision_result = self.decision_coordinator.process_decision(
                analysis_result.get("extracted_data", {})
            )

            # Calcular tiempo total de procesamiento
            total_time = time.time() - start_time

            # ✅ RESULTADO FINAL - Devolver el resultado de la Decision Layer
            final_result = {
                "success": decision_result.get("success", False),
                "pdf_path": pdf_path,
                "email_info": email_info,
                "processing_summary": {
                    "total_processing_time": total_time,
                    "layers_processed": 5,
                    "final_decision": decision_result,
                },
                # 🎉 RESULTADO DE LA ÚLTIMA CAPA (Decision Layer)
                "final_decision_result": decision_result,
            }

            if decision_result.get("success", False):
                logger.info(
                    f"✅ PDF procesado exitosamente a través de las 5 capas: {pdf_path}"
                )
                logger.info(
                    f"🎯 Decisión final: {decision_result.get('decision_type', 'N/A')} con confianza {decision_result.get('confidence_score', 'N/A')}"
                )
            else:
                logger.error(
                    f"❌ Error en Capa de Decisión: {decision_result.get('error', 'Desconocido')}"
                )
                final_result["success"] = False
                final_result["error"] = (
                    f"Error en Capa de Decisión: {decision_result.get('error', 'Desconocido')}"
                )
                final_result["failed_layer"] = "decision"

            return final_result

        except Exception as e:
            logger.error(f"❌ Error crítico procesando PDF a través de las capas: {e}")
            return {
                "success": False,
                "error": f"Error crítico: {str(e)}",
                "failed_layer": "critical_error",
                "pdf_path": pdf_path,
            }


async def main():
    """Función principal del robot"""
    print("=" * 60)
    print("ROBOT001 - PROCESADOR DE OUTLOOK PARA INICIATIVA4")
    print(
        "FLUJO COMPLETO: CORREOS → PDFs → RABBITMQ → 5 CAPAS DE PROCESAMIENTO → DECISIÓN FINAL"
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

        # Mantener el robot ejecutándose con procesamiento automático
        print("\n🤖 Robot ejecutándose con procesamiento automático...")
        print("📧 Monitoreando carpeta Iniciativa4 cada 10 segundos")
        print("📄 Descargando PDFs y enviando a RabbitMQ")
        print("🔄 Procesando PDFs a través de las 5 capas:")
        print("   📥 Capa 1: Ingesta (Clasificar, validar, escanear)")
        print("   🔧 Capa 2: Procesamiento Especializado (PDFs)")
        print("   🔍 Capa 3: Análisis y Extracción (Datos)")
        print("   💾 Capa 4: Almacenamiento y Gestión")
        print("   🎯 Capa 5: Decisión Final (Local/AWS/Híbrido)")
        print("\nPresiona Ctrl+C para detener")

        try:
            check_interval = config["email_processing"]["check_interval"]
            cycle_count = 0

            while robot.is_running:
                cycle_count += 1
                print(
                    f"\n[{datetime.now().strftime('%H:%M:%S')}] Ciclo #{cycle_count} - Procesando correos..."
                )

                try:
                    # Procesar correos automáticamente
                    result = await robot.execute_command("process_emails")

                    if result["success"]:
                        print(f"✅ Procesados: {result['processed']} correos")
                        print(f"📤 PDFs enviados: {result['pdfs_sent']} a RabbitMQ")

                        # 🎯 MOSTRAR RESULTADOS DE LAS 5 CAPAS
                        if result.get("layer_processing_summary"):
                            summary = result["layer_processing_summary"]
                            print(
                                f"🔄 PDFs procesados por las 5 capas: {summary['total_pdfs_processed_through_layers']}"
                            )
                            print(
                                f"✅ Capas exitosas: {summary['successful_layer_processing']}"
                            )
                            print(
                                f"🎉 Decisiones finales generadas: {summary['total_final_decisions']}"
                            )

                            # Mostrar algunas decisiones finales si están disponibles
                            if result.get("all_final_decisions"):
                                print("🎯 Últimas decisiones finales:")
                                for i, decision in enumerate(
                                    result["all_final_decisions"][-3:]
                                ):  # Mostrar últimas 3
                                    decision_type = decision.get("decision_type", "N/A")
                                    confidence = decision.get("confidence_score", "N/A")
                                    print(
                                        f"   📊 Decisión {i+1}: {decision_type} (confianza: {confidence})"
                                    )

                        if result["errors"] > 0:
                            print(f"❌ Errores: {result['errors']}")
                    else:
                        print(
                            f"❌ Error en procesamiento: {result.get('error', 'Desconocido')}"
                        )

                    # Mostrar estadísticas
                    stats = await robot.get_status()
                    if stats.get("processing_stats"):
                        proc_stats = stats["processing_stats"]
                        print(
                            f"📊 Total procesados: {proc_stats['processed_messages']}"
                        )
                        print(f"📊 Procesados hoy: {proc_stats['processed_today']}")

                except Exception as e:
                    logger.error(f"Error en ciclo de procesamiento: {e}")
                    print(f"❌ Error en ciclo: {e}")

                # Esperar hasta el siguiente ciclo
                print(
                    f"⏳ Esperando {check_interval} segundos hasta el siguiente ciclo..."
                )
                await asyncio.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n🛑 Deteniendo robot...")

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
