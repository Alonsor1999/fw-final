"""
Coordinador de Email - Robot001
Orquesta las operaciones de procesamiento de email de Outlook
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
import sys

# Agregar el directorio del framework al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from .outlook_email_processor import OutlookEmailProcessor
from framework.shared.logger import get_logger
from framework.shared.notification_service import NotificationService

logger = get_logger(__name__)

class EmailCoordinator:
    """Coordinador para operaciones de email de Outlook"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.outlook_processor = None
        self.notification_service = None
        self.monitoring_active = False
        self.last_check_time = None
        
        # Configuración por defecto
        self.coordinator_config = {
            'monitoring_enabled': True,
            'check_interval': 300,  # 5 minutos
            'notification_enabled': True,
            'auto_processing': True,
            'max_retries': 3,
            'retry_delay': 60,  # 1 minuto
            'iniciativa4_config': {
                'priority_threshold': 'medium',
                'auto_categorize': True,
                'extract_attachments': True,
                'notify_on_high_priority': True
            }
        }
        
        # Actualizar configuración
        if config:
            self.coordinator_config.update(config)
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Inicializar servicios necesarios"""
        try:
            # Inicializar procesador de Outlook
            self.outlook_processor = OutlookEmailProcessor(
                config=self.coordinator_config.get('outlook_config', {})
            )
            
            # Inicializar servicio de notificaciones
            if self.coordinator_config.get('notification_enabled'):
                self.notification_service = NotificationService()
            
            logger.info("Servicios de email coordinador inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando servicios de email: {e}")
            raise
    
    async def start_monitoring(self):
        """Iniciar monitoreo continuo de la carpeta Iniciativa4"""
        if self.monitoring_active:
            logger.warning("Monitoreo ya está activo")
            return
        
        self.monitoring_active = True
        logger.info("Iniciando monitoreo de carpeta Iniciativa4")
        
        try:
            while self.monitoring_active:
                await self._monitor_iniciativa4_folder()
                await asyncio.sleep(self.coordinator_config['check_interval'])
                
        except Exception as e:
            logger.error(f"Error en monitoreo: {e}")
            self.monitoring_active = False
            raise
    
    async def stop_monitoring(self):
        """Detener monitoreo"""
        self.monitoring_active = False
        logger.info("Monitoreo de carpeta Iniciativa4 detenido")
    
    async def _monitor_iniciativa4_folder(self):
        """Monitorear carpeta Iniciativa4 para nuevos emails"""
        try:
            logger.debug("Verificando carpeta Iniciativa4...")
            
            # Buscar emails en Iniciativa4
            result = await self.outlook_processor.search_iniciativa4_folder()
            
            if not result.get('success'):
                logger.error(f"Error en monitoreo: {result.get('error')}")
                return
            
            emails = result.get('emails', [])
            
            # Procesar emails según configuración
            if self.coordinator_config.get('auto_processing'):
                await self._process_new_emails(emails)
            
            # Verificar emails de alta prioridad
            if self.coordinator_config.get('iniciativa4_config', {}).get('notify_on_high_priority'):
                await self._check_high_priority_emails(emails)
            
            self.last_check_time = datetime.now()
            logger.debug(f"Monitoreo completado. Emails encontrados: {len(emails)}")
            
        except Exception as e:
            logger.error(f"Error en monitoreo de Iniciativa4: {e}")
    
    async def _process_new_emails(self, emails: List[Dict[str, Any]]):
        """Procesar nuevos emails automáticamente"""
        try:
            for email in emails:
                # Verificar si es un email nuevo (últimas 24 horas)
                if self._is_new_email(email):
                    await self._handle_new_email(email)
                    
        except Exception as e:
            logger.error(f"Error procesando nuevos emails: {e}")
    
    def _is_new_email(self, email: Dict[str, Any]) -> bool:
        """Verificar si el email es nuevo (últimas 24 horas)"""
        try:
            email_date = datetime.fromisoformat(email.get('date', '').replace('Z', '+00:00'))
            return datetime.now() - email_date < timedelta(days=1)
        except:
            return False
    
    async def _handle_new_email(self, email: Dict[str, Any]):
        """Manejar un nuevo email"""
        try:
            email_id = email.get('id', 'unknown')
            subject = email.get('subject', 'Sin asunto')
            
            logger.info(f"Procesando nuevo email: {subject} (ID: {email_id})")
            
            # Extraer adjuntos si está habilitado
            if self.coordinator_config.get('iniciativa4_config', {}).get('extract_attachments'):
                await self._extract_email_attachments(email)
            
            # Categorizar automáticamente
            if self.coordinator_config.get('iniciativa4_config', {}).get('auto_categorize'):
                await self._categorize_email(email)
            
            # Notificar si es de alta prioridad
            priority = email.get('iniciativa4_metadata', {}).get('priority_level', 'normal')
            if priority == 'high' and self.notification_service:
                await self._send_priority_notification(email)
            
            logger.info(f"Email {email_id} procesado correctamente")
            
        except Exception as e:
            logger.error(f"Error manejando email {email.get('id', 'unknown')}: {e}")
    
    async def _extract_email_attachments(self, email: Dict[str, Any]):
        """Extraer adjuntos del email"""
        try:
            if email.get('has_attachments', False):
                logger.info(f"Extrayendo adjuntos del email {email.get('id')}")
                # Aquí se implementaría la lógica de extracción de adjuntos
                # Por ahora es un placeholder
                pass
        except Exception as e:
            logger.error(f"Error extrayendo adjuntos: {e}")
    
    async def _categorize_email(self, email: Dict[str, Any]):
        """Categorizar email automáticamente"""
        try:
            # La categorización ya se hace en el procesador
            # Aquí se pueden agregar acciones adicionales basadas en la categoría
            category = email.get('iniciativa4_metadata', {}).get('category', 'general')
            logger.info(f"Email {email.get('id')} categorizado como: {category}")
            
        except Exception as e:
            logger.error(f"Error categorizando email: {e}")
    
    async def _send_priority_notification(self, email: Dict[str, Any]):
        """Enviar notificación para emails de alta prioridad"""
        try:
            if not self.notification_service:
                return
            
            subject = email.get('subject', 'Sin asunto')
            sender = email.get('from', 'Remitente desconocido')
            
            notification_data = {
                'type': 'high_priority_email',
                'title': f'Email de Alta Prioridad en Iniciativa4',
                'message': f'Email de {sender}: {subject}',
                'priority': 'high',
                'email_data': {
                    'id': email.get('id'),
                    'subject': subject,
                    'from': sender,
                    'date': email.get('date')
                }
            }
            
            await self.notification_service.send_notification(notification_data)
            logger.info(f"Notificación enviada para email de alta prioridad: {email.get('id')}")
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
    
    async def _check_high_priority_emails(self, emails: List[Dict[str, Any]]):
        """Verificar emails de alta prioridad"""
        try:
            high_priority_emails = [
                e for e in emails 
                if e.get('iniciativa4_metadata', {}).get('priority_level') == 'high'
            ]
            
            if high_priority_emails and self.notification_service:
                await self._send_high_priority_summary(high_priority_emails)
                
        except Exception as e:
            logger.error(f"Error verificando emails de alta prioridad: {e}")
    
    async def _send_high_priority_summary(self, high_priority_emails: List[Dict[str, Any]]):
        """Enviar resumen de emails de alta prioridad"""
        try:
            summary_data = {
                'type': 'high_priority_summary',
                'title': f'Resumen de Emails de Alta Prioridad - Iniciativa4',
                'message': f'Se encontraron {len(high_priority_emails)} emails de alta prioridad',
                'priority': 'medium',
                'emails_count': len(high_priority_emails),
                'emails': [
                    {
                        'id': e.get('id'),
                        'subject': e.get('subject'),
                        'from': e.get('from'),
                        'date': e.get('date')
                    }
                    for e in high_priority_emails
                ]
            }
            
            await self.notification_service.send_notification(summary_data)
            
        except Exception as e:
            logger.error(f"Error enviando resumen de alta prioridad: {e}")
    
    async def get_iniciativa4_status(self) -> Dict[str, Any]:
        """Obtener estado actual de la carpeta Iniciativa4"""
        try:
            # Obtener resumen
            summary_result = await self.outlook_processor.get_iniciativa4_summary()
            
            # Agregar información del coordinador
            status = {
                'monitoring_active': self.monitoring_active,
                'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
                'coordinator_config': self.coordinator_config,
                'notification_service_active': self.notification_service is not None
            }
            
            if summary_result.get('success'):
                status.update(summary_result)
            
            return status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de Iniciativa4: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_custom_search(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar búsqueda personalizada en Iniciativa4"""
        try:
            logger.info(f"Ejecutando búsqueda personalizada: {search_params}")
            
            # Validar parámetros de búsqueda
            filters = search_params.get('filters', {})
            
            # Ejecutar búsqueda
            result = await self.outlook_processor.search_iniciativa4_folder(filters)
            
            # Agregar información adicional
            if result.get('success'):
                result['search_params'] = search_params
                result['executed_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error en búsqueda personalizada: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
