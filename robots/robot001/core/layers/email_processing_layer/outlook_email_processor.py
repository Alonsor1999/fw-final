"""
Procesador de Email de Outlook - Robot001
Maneja operaciones específicas de Outlook incluyendo búsqueda en carpeta Iniciativa4
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
import sys

# Agregar el directorio del framework al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from framework.modules.bot_modules.email_module import EmailModule
from framework.shared.logger import get_logger

logger = get_logger(__name__)

class OutlookEmailProcessor:
    """Procesador específico para emails de Outlook"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.email_module = None
        self.outlook_config = {
            'email_provider': 'outlook',
            'max_emails': 100,
            'check_interval': 300,
            'mark_as_read': False,
            'download_attachments': True,
            'attachment_path': './outlook_attachments',
            'outlook_folders': ['INBOX', 'SENT', 'DRAFT', 'JUNK', 'Iniciativa4'],
            'default_filters': {
                'unread_only': False,
                'has_attachments': False,
                'date_from': None,
                'date_to': None,
                'sender_contains': None,
                'subject_contains': None
            }
        }
        
        # Actualizar configuración con parámetros personalizados
        if config:
            self.outlook_config.update(config)
        
        self._initialize_email_module()
    
    def _initialize_email_module(self):
        """Inicializar el módulo de email de Outlook"""
        try:
            self.email_module = EmailModule(
                module_id="outlook_processor_001",
                robot_id="robot001",
                config=self.outlook_config
            )
            logger.info("Módulo de email de Outlook inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar módulo de email: {e}")
            raise
    
    async def search_iniciativa4_folder(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Buscar emails específicamente en la carpeta Iniciativa4
        
        Args:
            filters: Filtros adicionales para la búsqueda
            
        Returns:
            Dict con los resultados de la búsqueda
        """
        try:
            logger.info("Iniciando búsqueda en carpeta Iniciativa4")
            
            # Configurar parámetros específicos para Iniciativa4
            search_params = {
                'operation': 'read_emails',
                'location': 'Iniciativa4',
                'max_emails': self.outlook_config['max_emails'],
                'filters': filters or self.outlook_config['default_filters']
            }
            
            # Ejecutar búsqueda
            result = await self.email_module.execute(search_params)
            
            if result.get('success'):
                emails = result.get('emails', [])
                logger.info(f"Encontrados {len(emails)} emails en carpeta Iniciativa4")
                
                # Procesar emails encontrados
                processed_emails = await self._process_iniciativa4_emails(emails)
                
                return {
                    'success': True,
                    'folder': 'Iniciativa4',
                    'emails_count': len(emails),
                    'processed_count': len(processed_emails),
                    'emails': processed_emails,
                    'timestamp': datetime.now().isoformat(),
                    'search_filters': search_params['filters']
                }
            else:
                logger.error(f"Error en búsqueda: {result.get('error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error al buscar en carpeta Iniciativa4: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _process_iniciativa4_emails(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesar emails específicos de la carpeta Iniciativa4
        
        Args:
            emails: Lista de emails encontrados
            
        Returns:
            Lista de emails procesados con información adicional
        """
        processed_emails = []
        
        for email in emails:
            try:
                # Agregar información específica de Iniciativa4
                processed_email = email.copy()
                processed_email['iniciativa4_metadata'] = {
                    'processed_at': datetime.now().isoformat(),
                    'priority_level': self._determine_priority(email),
                    'action_required': self._check_action_required(email),
                    'category': self._categorize_email(email),
                    'extracted_data': await self._extract_key_data(email)
                }
                
                processed_emails.append(processed_email)
                
            except Exception as e:
                logger.error(f"Error procesando email {email.get('id', 'unknown')}: {e}")
                # Agregar email con error para tracking
                email['processing_error'] = str(e)
                processed_emails.append(email)
        
        return processed_emails
    
    def _determine_priority(self, email: Dict[str, Any]) -> str:
        """Determinar prioridad del email basado en contenido"""
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        
        # Palabras clave de alta prioridad
        high_priority_keywords = ['urgente', 'crítico', 'importante', 'deadline', 'fecha límite']
        medium_priority_keywords = ['revisar', 'pendiente', 'siguiente paso']
        
        for keyword in high_priority_keywords:
            if keyword in subject or keyword in body:
                return 'high'
        
        for keyword in medium_priority_keywords:
            if keyword in subject or keyword in body:
                return 'medium'
        
        return 'normal'
    
    def _check_action_required(self, email: Dict[str, Any]) -> bool:
        """Verificar si el email requiere acción"""
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        
        action_keywords = [
            'responder', 'revisar', 'aprobar', 'rechazar', 'completar',
            'respond', 'review', 'approve', 'reject', 'complete'
        ]
        
        return any(keyword in subject or keyword in body for keyword in action_keywords)
    
    def _categorize_email(self, email: Dict[str, Any]) -> str:
        """Categorizar el email según su contenido"""
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        
        categories = {
            'reporte': ['reporte', 'report', 'informe', 'summary'],
            'solicitud': ['solicitud', 'request', 'solicitar', 'pedido'],
            'notificación': ['notificación', 'notification', 'aviso', 'alert'],
            'seguimiento': ['seguimiento', 'follow-up', 'followup', 'status'],
            'documento': ['documento', 'document', 'adjunto', 'attachment']
        }
        
        for category, keywords in categories.items():
            if any(keyword in subject or keyword in body for keyword in keywords):
                return category
        
        return 'general'
    
    async def _extract_key_data(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer datos clave del email"""
        extracted_data = {
            'sender_domain': self._extract_domain(email.get('from', '')),
            'has_attachments': email.get('has_attachments', False),
            'word_count': len(email.get('body', '').split()),
            'date_received': email.get('date'),
            'is_recent': self._is_recent_email(email.get('date'))
        }
        
        # Extraer fechas mencionadas en el contenido
        extracted_data['mentioned_dates'] = self._extract_dates(email.get('body', ''))
        
        # Extraer números de teléfono
        extracted_data['phone_numbers'] = self._extract_phone_numbers(email.get('body', ''))
        
        return extracted_data
    
    def _extract_domain(self, email_address: str) -> str:
        """Extraer dominio del email"""
        try:
            return email_address.split('@')[1] if '@' in email_address else ''
        except:
            return ''
    
    def _is_recent_email(self, date_str: str) -> bool:
        """Verificar si el email es reciente (últimas 24 horas)"""
        try:
            email_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return datetime.now() - email_date < timedelta(days=1)
        except:
            return False
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extraer fechas mencionadas en el texto"""
        # Implementación básica - se puede mejorar con regex más sofisticado
        import re
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extraer números de teléfono del texto"""
        import re
        phone_patterns = [
            r'\+?[\d\s\-\(\)]{10,}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\d{3}-\d{3}-\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        return list(set(phones))
    
    async def get_iniciativa4_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la carpeta Iniciativa4"""
        try:
            # Buscar todos los emails en Iniciativa4
            result = await self.search_iniciativa4_folder()
            
            if not result.get('success'):
                return result
            
            emails = result.get('emails', [])
            
            # Generar estadísticas
            summary = {
                'total_emails': len(emails),
                'unread_count': len([e for e in emails if not e.get('is_read', True)]),
                'with_attachments': len([e for e in emails if e.get('has_attachments', False)]),
                'priority_breakdown': {
                    'high': len([e for e in emails if e.get('iniciativa4_metadata', {}).get('priority_level') == 'high']),
                    'medium': len([e for e in emails if e.get('iniciativa4_metadata', {}).get('priority_level') == 'medium']),
                    'normal': len([e for e in emails if e.get('iniciativa4_metadata', {}).get('priority_level') == 'normal'])
                },
                'category_breakdown': {},
                'recent_emails': len([e for e in emails if e.get('iniciativa4_metadata', {}).get('extracted_data', {}).get('is_recent', False)]),
                'action_required': len([e for e in emails if e.get('iniciativa4_metadata', {}).get('action_required', False)])
            }
            
            # Contar categorías
            for email in emails:
                category = email.get('iniciativa4_metadata', {}).get('category', 'general')
                summary['category_breakdown'][category] = summary['category_breakdown'].get(category, 0) + 1
            
            return {
                'success': True,
                'folder': 'Iniciativa4',
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando resumen de Iniciativa4: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
