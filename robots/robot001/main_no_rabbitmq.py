"""
Robot001 - Main Entry Point (Sin RabbitMQ)
Robot especializado en procesamiento de emails de Outlook para la carpeta Iniciativa4
Flujo: Leer correos → Descargar PDFs → Simular envío a RabbitMQ
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Agregar el directorio del framework al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Agregar el directorio de Mail_loop_tracking al path
mail_tracking_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Mail_loop_tracking")
sys.path.append(mail_tracking_path)

from framework.shared.logger import get_logger
from framework.core.orchestrator import Orchestrator

logger = get_logger(__name__)

class MockRabbitMQSender:
    """Simulador de RabbitMQ para pruebas"""
    
    def __init__(self, config):
        self.config = config
        logger.info("🐰 Mock RabbitMQ Sender inicializado (modo simulación)")
    
    def send_pdf_message(self, pdf_path: str, email_info: Dict[str, Any]) -> bool:
        """Simular envío de mensaje PDF"""
        logger.info(f"📤 [SIMULACIÓN] PDF enviado a RabbitMQ: {pdf_path}")
        logger.info(f"📧 Email: {email_info.get('subject', 'Sin asunto')}")
        logger.info(f"👤 Remitente: {email_info.get('sender', 'Desconocido')}")
        return True
    
    def send_email_summary(self, email_summary: Dict[str, Any]) -> bool:
        """Simular envío de resumen"""
        logger.info(f"📋 [SIMULACIÓN] Resumen enviado a RabbitMQ")
        return True
    
    def close(self):
        """Cerrar conexión simulada"""
        logger.info("✅ Mock RabbitMQ cerrado")

class Robot001:
    """Robot especializado en procesamiento de emails de Outlook para Iniciativa4"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.mail_reader = None
        self.attachment_downloader = None
        self.rabbitmq_sender = None
        self.orchestrator = None
        self.is_running = False
        self.processed_messages = set()  # Para evitar procesar el mismo mensaje dos veces
        
        # Configuración por defecto del robot
        self.robot_config = {
            'robot_id': 'robot001',
            'robot_name': 'Outlook Iniciativa4 Processor (Sin RabbitMQ)',
            'version': '3.0.0',
            'email_processing': {
                'enabled': True,
                'check_interval': 300,  # 5 minutos
                'max_emails': 100,
                'auto_processing': True,
                'notification_enabled': True,
                'download_pdfs_only': True,  # Solo descargar PDFs
                'process_unread_only': True  # Solo procesar no leídos
            },
            'monitoring': {
                'enabled': True,
                'continuous': True,
                'log_level': 'INFO'
            },
            'outlook_config': {
                'folder_name': 'Iniciativa4',
                'download_attachments': True,
                'attachment_path': './robot001_attachments'
            },
            'rabbitmq_config': {
                'host': 'localhost',
                'port': 5672,
                'username': 'guest',
                'password': 'guest',
                'queue_name': 'pdf_processing_queue',
                'virtual_host': '/'
            }
        }
        
        # Actualizar configuración
        if config:
            self.robot_config.update(config)
        
        self._initialize_robot()
    
    def _initialize_robot(self):
        """Inicializar componentes del robot"""
        try:
            logger.info("Inicializando Robot001 - Procesador de Outlook Iniciativa4 (Sin RabbitMQ)")
            
            # Importar módulos de Mail_loop_tracking
            try:
                from outlook.folder_reader import get_messages_from_folder, get_folder_summary
                from outlook.graph_client import get_authenticated_session, validate_session
                from outlook.attachment_downloader import AttachmentDownloader
                from config import validate_config
                
                # Validar configuración de Mail_loop_tracking
                validate_config()
                
                # Verificar autenticación
                session = get_authenticated_session()
                if not validate_session(session):
                    raise Exception("No se pudo validar la sesión de Microsoft Graph API")
                
                # Inicializar lector de correos
                self.mail_reader = {
                    'get_messages': get_messages_from_folder,
                    'get_summary': get_folder_summary,
                    'session': session
                }
                logger.info("✅ Módulo Mail_loop_tracking inicializado correctamente")
                
                # Inicializar descargador de adjuntos
                attachment_path = self.robot_config['outlook_config']['attachment_path']
                self.attachment_downloader = AttachmentDownloader(download_dir=attachment_path)
                logger.info("✅ Descargador de adjuntos inicializado")
                
                # Inicializar sender de RabbitMQ (mock)
                rabbitmq_config = self.robot_config['rabbitmq_config']
                self.rabbitmq_sender = MockRabbitMQSender(rabbitmq_config)
                logger.info("✅ Mock Sender de RabbitMQ inicializado")
                
            except ImportError as e:
                logger.error(f"Error importando módulos de Mail_loop_tracking: {e}")
                raise Exception("No se pudo importar el módulo Mail_loop_tracking")
            
            # Inicializar orquestador del framework
            self.orchestrator = Orchestrator(
                robot_id=self.robot_config['robot_id'],
                config=self.robot_config
            )
            logger.info("✅ Orquestador inicializado")
            
            logger.info("✅ Robot001 inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando Robot001: {e}")
            raise
    
    async def start(self):
        """Iniciar el robot"""
        try:
            logger.info("Iniciando Robot001...")
            self.is_running = True
            
            # Registrar el robot en el orquestador
            await self.orchestrator.register_robot()
            
            # Iniciar monitoreo si está habilitado
            if (self.robot_config['monitoring']['enabled'] and 
                self.robot_config['monitoring']['continuous']):
                
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
                logger.info("✅ Mock RabbitMQ cerrado")
            
            # Desregistrar del orquestador
            if self.orchestrator:
                await self.orchestrator.unregister_robot()
            
            logger.info("✅ Robot001 detenido correctamente")
            
        except Exception as e:
            logger.error(f"Error deteniendo Robot001: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del robot"""
        try:
            status = {
                'robot_id': self.robot_config['robot_id'],
                'robot_name': self.robot_config['robot_name'],
                'version': self.robot_config['version'],
                'is_running': self.is_running,
                'start_time': datetime.now().isoformat(),
                'components': {
                    'mail_reader': self.mail_reader is not None,
                    'attachment_downloader': self.attachment_downloader is not None,
                    'rabbitmq_sender': self.rabbitmq_sender is not None,
                    'orchestrator': self.orchestrator is not None
                },
                'processing_stats': {
                    'processed_messages': len(self.processed_messages),
                    'processed_today': len([m for m in self.processed_messages if m.startswith(datetime.now().strftime('%Y-%m-%d'))])
                }
            }
            
            # Agregar estado de Iniciativa4 si está disponible
            if self.mail_reader:
                try:
                    folder_name = self.robot_config['outlook_config']['folder_name']
                    summary = self.mail_reader['get_summary'](folder_name)
                    status['iniciativa4_status'] = summary
                except Exception as e:
                    logger.error(f"Error obteniendo estado de Iniciativa4: {e}")
                    status['iniciativa4_status'] = {'error': str(e)}
            
            # Agregar estadísticas de adjuntos si está disponible
            if self.attachment_downloader:
                try:
                    download_stats = self.attachment_downloader.get_download_stats()
                    status['attachment_stats'] = download_stats
                except Exception as e:
                    logger.error(f"Error obteniendo estadísticas de adjuntos: {e}")
                    status['attachment_stats'] = {'error': str(e)}
            
            return status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del robot: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecutar comando específico del robot"""
        try:
            logger.info(f"Ejecutando comando: {command}")
            
            if command == 'search_iniciativa4':
                if not self.mail_reader:
                    raise ValueError("Módulo Mail_loop_tracking no disponible")
                
                folder_name = self.robot_config['outlook_config']['folder_name']
                top = params.get('top', 50) if params else 50
                
                messages = self.mail_reader['get_messages'](folder_name, top=top)
                return {
                    'success': True,
                    'folder': folder_name,
                    'emails_count': len(messages),
                    'emails': messages,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif command == 'get_summary':
                if not self.mail_reader:
                    raise ValueError("Módulo Mail_loop_tracking no disponible")
                
                folder_name = self.robot_config['outlook_config']['folder_name']
                summary = self.mail_reader['get_summary'](folder_name)
                return summary
            
            elif command == 'process_emails':
                """Procesar correos y enviar PDFs a RabbitMQ"""
                if not all([self.mail_reader, self.attachment_downloader, self.rabbitmq_sender]):
                    raise ValueError("Componentes necesarios no disponibles")
                
                result = await self._process_folder_emails()
                return result
            
            elif command == 'download_attachments':
                """Descargar adjuntos de correos específicos"""
                if not self.attachment_downloader:
                    raise ValueError("Descargador de adjuntos no disponible")
                
                message_ids = params.get('message_ids', []) if params else []
                if not message_ids:
                    raise ValueError("Se requieren IDs de mensajes")
                
                result = await self._download_specific_attachments(message_ids)
                return result
            
            elif command == 'get_status':
                return await self.get_status()
            
            else:
                raise ValueError(f"Comando no reconocido: {command}")
                
        except Exception as e:
            logger.error(f"Error ejecutando comando {command}: {e}")
            return {
                'success': False,
                'error': str(e),
                'command': command,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _process_folder_emails(self) -> Dict[str, Any]:
        """Procesar correos de la carpeta Iniciativa4"""
        try:
            folder_name = self.robot_config['outlook_config']['folder_name']
            max_emails = self.robot_config['email_processing']['max_emails']
            
            logger.info(f"🔄 Procesando correos de la carpeta '{folder_name}'")
            
            # Obtener mensajes
            messages = self.mail_reader['get_messages'](folder_name, top=max_emails)
            
            if not messages:
                logger.info(f"📧 No hay mensajes para procesar en '{folder_name}'")
                return {
                    'success': True,
                    'processed': 0,
                    'pdfs_sent': 0,
                    'errors': 0,
                    'message': 'No hay mensajes para procesar'
                }
            
            processed_count = 0
            pdfs_sent = 0
            errors = 0
            
            for message in messages:
                try:
                    message_id = message.get('id')
                    if not message_id:
                        continue
                    
                    # Verificar si ya fue procesado
                    if message_id in self.processed_messages:
                        logger.debug(f"⏭️ Mensaje ya procesado: {message_id}")
                        continue
                    
                    # Verificar si es no leído (si está habilitado)
                    if (self.robot_config['email_processing']['process_unread_only'] and 
                        message.get('isRead', True)):
                        logger.debug(f"⏭️ Mensaje ya leído: {message_id}")
                        continue
                    
                    # Procesar mensaje
                    result = await self._process_single_message(message)
                    
                    if result['success']:
                        processed_count += 1
                        pdfs_sent += result['pdfs_sent']
                        self.processed_messages.add(message_id)
                        logger.info(f"✅ Mensaje procesado: {message.get('subject', 'Sin asunto')}")
                    else:
                        errors += 1
                        logger.error(f"❌ Error procesando mensaje: {result['error']}")
                
                except Exception as e:
                    errors += 1
                    logger.error(f"❌ Error procesando mensaje: {e}")
            
            logger.info(f"📊 Procesamiento completado: {processed_count} procesados, {pdfs_sent} PDFs enviados, {errors} errores")
            
            return {
                'success': True,
                'processed': processed_count,
                'pdfs_sent': pdfs_sent,
                'errors': errors,
                'total_messages': len(messages)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento de correos: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _process_single_message(self, message: Dict) -> Dict[str, Any]:
        """Procesar un mensaje individual"""
        try:
            message_id = message.get('id')
            subject = message.get('subject', 'Sin asunto')
            sender = self._extract_sender_email(message)
            received_date = message.get('receivedDateTime', '')
            
            logger.info(f"📧 Procesando: {subject} (De: {sender})")
            
            # Extraer información del correo
            email_info = {
                'subject': subject,
                'sender': sender,
                'received_date': received_date,
                'folder': self.robot_config['outlook_config']['folder_name'],
                'message_id': message_id,
                'has_attachments': message.get('hasAttachments', False),
                'attachment_count': 0
            }
            
            # Descargar PDFs si está habilitado
            pdfs_downloaded = []
            if self.robot_config['email_processing']['download_pdfs_only']:
                pdfs_downloaded = self.attachment_downloader.download_pdf_attachments(message)
            else:
                # Descargar todos los adjuntos
                all_attachments = self.attachment_downloader.download_message_attachments(message)
                pdfs_downloaded = [f for f in all_attachments if f.lower().endswith('.pdf')]
            
            email_info['attachment_count'] = len(pdfs_downloaded)
            
            # Enviar PDFs a RabbitMQ (simulado)
            pdfs_sent = 0
            for pdf_path in pdfs_downloaded:
                if self.rabbitmq_sender.send_pdf_message(pdf_path, email_info):
                    pdfs_sent += 1
                    logger.info(f"📤 PDF enviado a RabbitMQ: {pdf_path}")
                else:
                    logger.error(f"❌ Error enviando PDF a RabbitMQ: {pdf_path}")
            
            # Enviar resumen del correo
            self.rabbitmq_sender.send_email_summary({
                **email_info,
                'pdfs_downloaded': len(pdfs_downloaded),
                'pdfs_sent': pdfs_sent,
                'processing_timestamp': datetime.now().isoformat()
            })
            
            return {
                'success': True,
                'pdfs_sent': pdfs_sent,
                'pdfs_downloaded': len(pdfs_downloaded)
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje individual: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _download_specific_attachments(self, message_ids: List[str]) -> Dict[str, Any]:
        """Descargar adjuntos de mensajes específicos"""
        try:
            folder_name = self.robot_config['outlook_config']['folder_name']
            downloaded_files = []
            
            for message_id in message_ids:
                try:
                    # Obtener mensaje específico
                    messages = self.mail_reader['get_messages'](folder_name, top=1000)
                    message = next((m for m in messages if m.get('id') == message_id), None)
                    
                    if not message:
                        logger.warning(f"⚠️ Mensaje no encontrado: {message_id}")
                        continue
                    
                    # Descargar PDFs
                    pdfs = self.attachment_downloader.download_pdf_attachments(message)
                    downloaded_files.extend(pdfs)
                    
                except Exception as e:
                    logger.error(f"❌ Error descargando adjuntos de {message_id}: {e}")
            
            return {
                'success': True,
                'downloaded_files': downloaded_files,
                'count': len(downloaded_files)
            }
            
        except Exception as e:
            logger.error(f"❌ Error descargando adjuntos específicos: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_sender_email(self, message: Dict) -> str:
        """Extraer email del remitente"""
        sender = message.get('from', {})
        if isinstance(sender, dict):
            email = sender.get('emailAddress', {}).get('address', '')
        else:
            email = str(sender)
        return email

async def main():
    """Función principal del robot"""
    print("=" * 60)
    print("ROBOT001 - PROCESADOR DE OUTLOOK PARA INICIATIVA4")
    print("FLUJO: CORREOS → PDFs → SIMULACIÓN RABBITMQ")
    print("=" * 60)
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    robot = None
    
    try:
        # Configuración del robot
        config = {
            'email_processing': {
                'enabled': True,
                'check_interval': 300,  # 5 minutos
                'notification_enabled': True,
                'auto_processing': True,
                'download_pdfs_only': True,  # Solo descargar PDFs
                'process_unread_only': True  # Solo procesar no leídos
            },
            'monitoring': {
                'enabled': True,
                'continuous': True
            },
            'outlook_config': {
                'folder_name': 'Iniciativa4',  # Especificar la carpeta
                'attachment_path': './robot001_attachments'
            },
            'rabbitmq_config': {
                'host': 'localhost',
                'port': 5672,
                'username': 'guest',
                'password': 'guest',
                'queue_name': 'pdf_processing_queue'
            }
        }
        
        # Crear e inicializar el robot
        robot = Robot001(config)
        
        # Mostrar estado inicial
        status = await robot.get_status()
        print(f"Estado del robot: {status['robot_name']} v{status['version']}")
        print(f"Componentes activos: {status['components']}")
        
        # Mostrar información de la carpeta
        if status.get('iniciativa4_status', {}).get('success'):
            folder_info = status['iniciativa4_status']
            print(f"Carpeta configurada: {folder_info['folder_name']}")
            print(f"Total mensajes: {folder_info['total_messages']}")
            print(f"No leídos: {folder_info['unread_count']}")
        
        # Mostrar estadísticas de adjuntos
        if status.get('attachment_stats'):
            stats = status['attachment_stats']
            print(f"Adjuntos descargados: {stats.get('total_files', 0)} archivos")
            print(f"Tamaño total: {stats.get('total_size_mb', 0)} MB")
        
        # Iniciar el robot
        await robot.start()
        
        # Mantener el robot ejecutándose con procesamiento automático
        print("\n🤖 Robot ejecutándose con procesamiento automático...")
        print("📧 Monitoreando carpeta Iniciativa4 cada 5 minutos")
        print("📄 Descargando PDFs y simulando envío a RabbitMQ")
        print("🔄 Modo simulación: No se requiere RabbitMQ real")
        print("\nPresiona Ctrl+C para detener")
        
        try:
            check_interval = config['email_processing']['check_interval']
            cycle_count = 0
            
            while robot.is_running:
                cycle_count += 1
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Ciclo #{cycle_count} - Procesando correos...")
                
                try:
                    # Procesar correos automáticamente
                    result = await robot.execute_command('process_emails')
                    
                    if result['success']:
                        print(f"✅ Procesados: {result['processed']} correos")
                        print(f"📤 PDFs enviados: {result['pdfs_sent']} a RabbitMQ (simulado)")
                        if result['errors'] > 0:
                            print(f"❌ Errores: {result['errors']}")
                    else:
                        print(f"❌ Error en procesamiento: {result.get('error', 'Desconocido')}")
                    
                    # Mostrar estadísticas
                    stats = await robot.get_status()
                    if stats.get('processing_stats'):
                        proc_stats = stats['processing_stats']
                        print(f"📊 Total procesados: {proc_stats['processed_messages']}")
                        print(f"📊 Procesados hoy: {proc_stats['processed_today']}")
                    
                except Exception as e:
                    logger.error(f"Error en ciclo de procesamiento: {e}")
                    print(f"❌ Error en ciclo: {e}")
                
                # Esperar hasta el siguiente ciclo
                print(f"⏳ Esperando {check_interval} segundos hasta el siguiente ciclo...")
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
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar el robot
    asyncio.run(main())
