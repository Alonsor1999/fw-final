"""
Módulo de Correo Unificado - Gmail y Outlook
Módulo reutilizable para cualquier robot que maneje correos de Gmail y Outlook
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio padre al path para importar el framework
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from framework.modules.base_module import BaseModule

logger = logging.getLogger(__name__)

class EmailModule(BaseModule):
    """Módulo de correo unificado para Gmail y Outlook"""
    
    def __init__(self, module_id: str, robot_id: str, config: Dict[str, Any] = None):
        default_config = {
            # Configuración general
            'email_provider': 'gmail',  # 'gmail' o 'outlook'
            'email': '',
            'password': '',
            'app_password': '',  # Para Gmail con 2FA
            
            # Configuración de servidor
            'server': '',  # Se auto-configura según el provider
            'port': 993,
            'use_ssl': True,
            
            # Configuración de operaciones
            'max_emails': 50,
            'check_interval': 300,  # 5 minutos
            'mark_as_read': False,
            'download_attachments': False,
            'attachment_path': './email_attachments',
            
            # Configuración específica por provider
            'gmail_labels': ['INBOX', 'SENT', 'DRAFT', 'SPAM'],
            'outlook_folders': ['INBOX', 'SENT', 'DRAFT', 'JUNK'],
            
            # Configuración de filtros
            'default_filters': {
                'unread_only': False,
                'has_attachments': False,
                'date_from': None,
                'date_to': None,
                'sender_contains': None,
                'subject_contains': None
            }
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(module_id, robot_id, default_config)
        self.connection = None
        self.processed_emails = []
        self._setup_provider_config()
    
    def _setup_provider_config(self):
        """Configurar automáticamente según el proveedor de email"""
        provider = self.config['email_provider'].lower()
        
        # Leer variables de entorno para el proveedor específico
        self._load_env_variables(provider)
        
        if provider == 'gmail':
            self.config.update({
                'server': 'imap.gmail.com',
                'smtp_server': 'smtp.gmail.com',
                'imap_port': 993,
                'smtp_port': 587,
                'use_ssl': True,
                'use_tls': True
            })
            
            # Detectar protocolo basado en variables de entorno disponibles
            if self.config.get('GMAIL_CLIENT_ID') and self.config.get('GMAIL_CLIENT_SECRET'):
                self.config['protocol'] = 'gmail_api'
                self.config['auth_method'] = 'oauth2'
                logger.info("Configurando Gmail API con OAuth2")
            elif self.config.get('GMAIL_APP_PASSWORD'):
                self.config['protocol'] = 'imap/smtp'
                self.config['auth_method'] = 'app_password'
                logger.info("Configurando Gmail con App Password")
            else:
                self.config['protocol'] = 'imap/smtp'
                self.config['auth_method'] = 'password'
                logger.warning("Configurando Gmail con password normal (no recomendado)")
        
        elif provider == 'outlook':
            self.config.update({
                'server': 'outlook.office365.com',
                'smtp_server': 'smtp.office365.com',
                'imap_port': 993,
                'smtp_port': 587,
                'use_ssl': True,
                'use_tls': True
            })
            
            # Detectar protocolo basado en variables de entorno disponibles
            if (self.config.get('OUTLOOK_CLIENT_ID') and 
                self.config.get('OUTLOOK_CLIENT_SECRET') and 
                self.config.get('OUTLOOK_TENANT_ID')):
                self.config['protocol'] = 'graph_api'
                self.config['auth_method'] = 'oauth2'
                logger.info("Configurando Outlook con Microsoft Graph API")
            else:
                self.config['protocol'] = 'imap/smtp'
                self.config['auth_method'] = 'password'
                logger.info("Configurando Outlook con IMAP/SMTP")
        
        else:
            raise ValueError(f"Proveedor de email no soportado: {provider}")
        
        logger.info(f"Configuración automática aplicada para {provider}: {self.config['protocol']}")
    
    def _load_env_variables(self, provider: str):
        """Cargar variables de entorno específicas del proveedor"""
        import os
        
        if provider == 'gmail':
            # Variables para Gmail
            env_vars = {
                'GMAIL_EMAIL': os.getenv('GMAIL_EMAIL'),
                'GMAIL_PASSWORD': os.getenv('GMAIL_PASSWORD'),
                'GMAIL_APP_PASSWORD': os.getenv('GMAIL_APP_PASSWORD'),
                'GMAIL_CLIENT_ID': os.getenv('GMAIL_CLIENT_ID'),
                'GMAIL_CLIENT_SECRET': os.getenv('GMAIL_CLIENT_SECRET'),
                'GMAIL_REFRESH_TOKEN': os.getenv('GMAIL_REFRESH_TOKEN')
            }
            
            # Actualizar configuración con variables de entorno
            for key, value in env_vars.items():
                if value:
                    self.config[key] = value
            
            # Mapear variables de entorno a configuración estándar
            if self.config.get('GMAIL_EMAIL') and not self.config.get('email'):
                self.config['email'] = self.config['GMAIL_EMAIL']
            if self.config.get('GMAIL_APP_PASSWORD') and not self.config.get('app_password'):
                self.config['app_password'] = self.config['GMAIL_APP_PASSWORD']
            if self.config.get('GMAIL_PASSWORD') and not self.config.get('password'):
                self.config['password'] = self.config['GMAIL_PASSWORD']
        
        elif provider == 'outlook':
            # Variables para Outlook
            env_vars = {
                'OUTLOOK_EMAIL': os.getenv('OUTLOOK_EMAIL'),
                'OUTLOOK_PASSWORD': os.getenv('OUTLOOK_PASSWORD'),
                'OUTLOOK_CLIENT_ID': os.getenv('OUTLOOK_CLIENT_ID'),
                'OUTLOOK_CLIENT_SECRET': os.getenv('OUTLOOK_CLIENT_SECRET'),
                'OUTLOOK_TENANT_ID': os.getenv('OUTLOOK_TENANT_ID'),
                'OUTLOOK_REFRESH_TOKEN': os.getenv('OUTLOOK_REFRESH_TOKEN')
            }
            
            # Actualizar configuración con variables de entorno
            for key, value in env_vars.items():
                if value:
                    self.config[key] = value
            
            # Mapear variables de entorno a configuración estándar
            if self.config.get('OUTLOOK_EMAIL') and not self.config.get('email'):
                self.config['email'] = self.config['OUTLOOK_EMAIL']
            if self.config.get('OUTLOOK_PASSWORD') and not self.config.get('password'):
                self.config['password'] = self.config['OUTLOOK_PASSWORD']
        
        logger.info(f"Variables de entorno cargadas para {provider}")
    
    async def _initialize_module(self):
        """Inicialización específica del módulo de correo"""
        provider = self.config['email_provider']
        logger.info(f"Inicializando módulo de correo para {provider}")
        
        # Verificar configuración
        if not self.config.get('email'):
            raise ValueError("Email es requerido para el módulo de correo")
        
        if provider == 'gmail':
            if not self.config.get('app_password') and not self.config.get('password'):
                raise ValueError("App password o password es requerido para Gmail")
        else:  # outlook
            if not self.config.get('password'):
                raise ValueError("Password es requerido para Outlook")
        
        # Crear directorio de adjuntos si es necesario
        if self.config.get('download_attachments'):
            os.makedirs(self.config['attachment_path'], exist_ok=True)
        
        logger.info(f"Módulo de correo {provider} inicializado correctamente")
    
    async def _execute_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar operaciones de correo según los parámetros"""
        try:
            operation = params.get('operation', 'read_emails')
            
            if operation == 'read_emails':
                return await self._read_emails(params)
            elif operation == 'send_email':
                return await self._send_email(params)
            elif operation == 'search_emails':
                return await self._search_emails(params)
            elif operation == 'manage_labels':
                return await self._manage_labels(params)
            elif operation == 'delete_emails':
                return await self._delete_emails(params)
            elif operation == 'filter_emails':
                return await self._filter_emails(params)
            else:
                raise ValueError(f"Operación no soportada: {operation}")
                
        except Exception as e:
            logger.error(f"Error en operación de correo: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _read_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Leer emails de cualquier proveedor"""
        try:
            max_emails = params.get('max_emails', self.config['max_emails'])
            location = params.get('location', self._get_default_location())
            filters = params.get('filters', self.config['default_filters'])
            
            provider = self.config['email_provider']
            logger.info(f"Leyendo emails de {provider} en {location} (máximo: {max_emails})")
            
            # Simular conexión y lectura de emails
            emails = await self._simulate_read_emails(max_emails, location, filters)
            
            # Aplicar filtros adicionales
            filtered_emails = await self._apply_filters(emails, filters)
            
            # Guardar emails en base de datos
            await self._save_emails(filtered_emails, params)
            
            return {
                'success': True,
                'operation': 'read_emails',
                'provider': provider,
                'location': location,
                'emails_count': len(filtered_emails),
                'total_emails': len(emails),
                'emails': filtered_emails,
                'filters_applied': filters,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al leer emails: {e}")
            raise
    
    def _get_default_location(self) -> str:
        """Obtener ubicación por defecto según el proveedor"""
        provider = self.config['email_provider']
        if provider == 'gmail':
            return 'INBOX'
        else:  # outlook
            return 'INBOX'
    
    async def _simulate_read_emails(self, max_emails: int, location: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simular lectura de emails según el proveedor"""
        provider = self.config['email_provider']
        emails = []
        
        # Simular emails según el proveedor
        for i in range(min(max_emails, 5)):
            if provider == 'gmail':
                email = {
                    'id': f"gmail_{i+1}",
                    'subject': f"Gmail de prueba {i+1}",
                    'from': f"gmailuser{i+1}@gmail.com",
                    'to': self.config['email'],
                    'date': (datetime.now() - timedelta(hours=i)).isoformat(),
                    'body': f"Contenido del email Gmail {i+1}",
                    'is_read': i % 2 == 0,
                    'has_attachments': i % 3 == 0,
                    'label': location,
                    'priority': 'normal',
                    'gmail_thread_id': f"thread_{i+1}",
                    'gmail_message_id': f"msg_{i+1}",
                    'provider': 'gmail'
                }
            else:  # outlook
                email = {
                    'id': f"outlook_{i+1}",
                    'subject': f"Outlook de prueba {i+1}",
                    'from': f"outlookuser{i+1}@outlook.com",
                    'to': self.config['email'],
                    'date': (datetime.now() - timedelta(hours=i)).isoformat(),
                    'body': f"Contenido del email Outlook {i+1}",
                    'is_read': i % 2 == 0,
                    'has_attachments': i % 3 == 0,
                    'folder': location,
                    'priority': 'normal',
                    'provider': 'outlook'
                }
            
            emails.append(email)
        
        return emails
    
    async def _apply_filters(self, emails: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aplicar filtros a los emails"""
        filtered_emails = emails.copy()
        
        # Filtro por no leídos
        if filters.get('unread_only'):
            filtered_emails = [e for e in filtered_emails if not e.get('is_read', True)]
        
        # Filtro por adjuntos
        if filters.get('has_attachments'):
            filtered_emails = [e for e in filtered_emails if e.get('has_attachments', False)]
        
        # Filtro por remitente
        sender_contains = filters.get('sender_contains')
        if sender_contains:
            filtered_emails = [e for e in filtered_emails if sender_contains.lower() in e.get('from', '').lower()]
        
        # Filtro por asunto
        subject_contains = filters.get('subject_contains')
        if subject_contains:
            filtered_emails = [e for e in filtered_emails if subject_contains.lower() in e.get('subject', '').lower()]
        
        # Filtro por fecha
        date_from = filters.get('date_from')
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                filtered_emails = [e for e in filtered_emails if datetime.fromisoformat(e['date'].replace('Z', '+00:00')) >= date_from_dt]
            except:
                pass
        
        date_to = filters.get('date_to')
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                filtered_emails = [e for e in filtered_emails if datetime.fromisoformat(e['date'].replace('Z', '+00:00')) <= date_to_dt]
            except:
                pass
        
        return filtered_emails
    
    async def _filter_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filtrar emails existentes"""
        try:
            emails = params.get('emails', [])
            filters = params.get('filters', {})
            
            if not emails:
                raise ValueError("emails es requerido para filtrar")
            
            logger.info(f"Aplicando filtros a {len(emails)} emails")
            
            filtered_emails = await self._apply_filters(emails, filters)
            
            return {
                'success': True,
                'operation': 'filter_emails',
                'original_count': len(emails),
                'filtered_count': len(filtered_emails),
                'filters_applied': filters,
                'filtered_emails': filtered_emails,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al filtrar emails: {e}")
            raise
    
    async def _send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enviar email por cualquier proveedor"""
        try:
            to_email = params.get('to')
            subject = params.get('subject')
            body = params.get('body')
            attachments = params.get('attachments', [])
            cc = params.get('cc', [])
            bcc = params.get('bcc', [])
            
            if not all([to_email, subject, body]):
                raise ValueError("to, subject y body son requeridos para enviar email")
            
            provider = self.config['email_provider']
            logger.info(f"Enviando email {provider} a: {to_email}")
            
            # Simular envío de email
            email_data = {
                'id': f"{provider}_sent_{datetime.now().timestamp()}",
                'to': to_email,
                'cc': cc,
                'bcc': bcc,
                'subject': subject,
                'body': body,
                'attachments': attachments,
                'date': datetime.now().isoformat(),
                'status': 'sent',
                'provider': provider
            }
            
            # Agregar campos específicos del proveedor
            if provider == 'gmail':
                email_data['gmail_thread_id'] = f"sent_thread_{datetime.now().timestamp()}"
            else:  # outlook
                email_data['outlook_folder'] = 'SENT'
            
            # Guardar email enviado en base de datos
            await self._save_sent_email(email_data, params)
            
            return {
                'success': True,
                'operation': 'send_email',
                'provider': provider,
                'email_id': email_data['id'],
                'to': to_email,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al enviar email: {e}")
            raise
    
    async def _search_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Buscar emails en cualquier proveedor"""
        try:
            query = params.get('query', '')
            location = params.get('location', self._get_default_location())
            date_from = params.get('date_from')
            date_to = params.get('date_to')
            
            provider = self.config['email_provider']
            logger.info(f"Buscando emails {provider} con query: {query}")
            
            # Simular búsqueda
            search_results = await self._simulate_search_emails(query, location, date_from, date_to)
            
            return {
                'success': True,
                'operation': 'search_emails',
                'provider': provider,
                'query': query,
                'location': location,
                'results_count': len(search_results),
                'results': search_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al buscar emails: {e}")
            raise
    
    async def _simulate_search_emails(self, query: str, location: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """Simular búsqueda de emails según el proveedor"""
        provider = self.config['email_provider']
        results = []
        
        # Simular resultados de búsqueda
        for i in range(3):
            if query.lower() in f"email de búsqueda {i+1}".lower():
                if provider == 'gmail':
                    email = {
                        'id': f"gmail_search_{i+1}",
                        'subject': f"Gmail de búsqueda {i+1}",
                        'from': f"gmailsearch{i+1}@gmail.com",
                        'date': (datetime.now() - timedelta(days=i)).isoformat(),
                        'label': location,
                        'relevance_score': 0.8 - (i * 0.1),
                        'gmail_thread_id': f"search_thread_{i+1}",
                        'provider': 'gmail'
                    }
                else:  # outlook
                    email = {
                        'id': f"outlook_search_{i+1}",
                        'subject': f"Outlook de búsqueda {i+1}",
                        'from': f"outlooksearch{i+1}@outlook.com",
                        'date': (datetime.now() - timedelta(days=i)).isoformat(),
                        'folder': location,
                        'relevance_score': 0.8 - (i * 0.1),
                        'provider': 'outlook'
                    }
                results.append(email)
        
        return results
    
    async def _manage_labels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Gestionar etiquetas/carpetas según el proveedor"""
        try:
            operation = params.get('label_operation', 'list')
            email_ids = params.get('email_ids', [])
            label_name = params.get('label_name', '')
            
            provider = self.config['email_provider']
            logger.info(f"Gestionando etiquetas {provider}: {operation}")
            
            if operation == 'add_label':
                if not email_ids or not label_name:
                    raise ValueError("email_ids y label_name son requeridos para agregar etiqueta")
                
                return {
                    'success': True,
                    'operation': 'add_label',
                    'provider': provider,
                    'label_name': label_name,
                    'emails_affected': len(email_ids),
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'remove_label':
                if not email_ids or not label_name:
                    raise ValueError("email_ids y label_name son requeridos para remover etiqueta")
                
                return {
                    'success': True,
                    'operation': 'remove_label',
                    'provider': provider,
                    'label_name': label_name,
                    'emails_affected': len(email_ids),
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'list_labels':
                # Simular lista de etiquetas según el proveedor
                if provider == 'gmail':
                    labels = [
                        {'name': 'INBOX', 'type': 'system'},
                        {'name': 'SENT', 'type': 'system'},
                        {'name': 'DRAFT', 'type': 'system'},
                        {'name': 'SPAM', 'type': 'system'},
                        {'name': 'IMPORTANT', 'type': 'user'},
                        {'name': 'WORK', 'type': 'user'},
                        {'name': 'PERSONAL', 'type': 'user'}
                    ]
                else:  # outlook
                    labels = [
                        {'name': 'INBOX', 'type': 'system'},
                        {'name': 'SENT', 'type': 'system'},
                        {'name': 'DRAFT', 'type': 'system'},
                        {'name': 'JUNK', 'type': 'system'},
                        {'name': 'ARCHIVE', 'type': 'system'},
                        {'name': 'WORK', 'type': 'user'},
                        {'name': 'PERSONAL', 'type': 'user'}
                    ]
                
                return {
                    'success': True,
                    'operation': 'list_labels',
                    'provider': provider,
                    'labels': labels,
                    'timestamp': datetime.now().isoformat()
                }
            
            else:
                raise ValueError(f"Operación de etiqueta no soportada: {operation}")
                
        except Exception as e:
            logger.error(f"Error al gestionar etiquetas: {e}")
            raise
    
    async def _delete_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Eliminar emails de cualquier proveedor"""
        try:
            email_ids = params.get('email_ids', [])
            location = params.get('location', self._get_default_location())
            
            if not email_ids:
                raise ValueError("email_ids es requerido para eliminar emails")
            
            provider = self.config['email_provider']
            logger.info(f"Eliminando {len(email_ids)} emails de {provider} en {location}")
            
            # Simular eliminación
            deleted_count = len(email_ids)
            
            return {
                'success': True,
                'operation': 'delete_emails',
                'provider': provider,
                'deleted_count': deleted_count,
                'email_ids': email_ids,
                'location': location,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al eliminar emails: {e}")
            raise
    
    async def _save_emails(self, emails: List[Dict[str, Any]], params: Dict[str, Any]):
        """Guardar emails en la base de datos"""
        try:
            provider = self.config['email_provider']
            
            for email in emails:
                # Crear caso de transacción para cada email
                case_data = {
                    'case_id': f"{provider}_{email['id']}",
                    'transaction_type': f'{provider}_email_processing',
                    'status': 'completed',
                    'data': email,
                    'priority': 1,
                    'assigned_to': self.module_id,
                    'notes': f"Email {provider} procesado"
                }
                
                # Insertar en base de datos
                success = await self.db_manager.insert_case_transaction(
                    self.robot_id, case_data
                )
                
                if success:
                    self.processed_emails.append(email)
                    logger.debug(f"Email {provider} guardado: {email.get('subject', '')[:50]}...")
                else:
                    logger.warning(f"No se pudo guardar email {provider}: {email.get('subject', '')[:50]}...")
        
        except Exception as e:
            logger.error(f"Error al guardar emails: {e}")
    
    async def _save_sent_email(self, email_data: Dict[str, Any], params: Dict[str, Any]):
        """Guardar email enviado en la base de datos"""
        try:
            provider = self.config['email_provider']
            
            case_data = {
                'case_id': f"{provider}_sent_{email_data['id']}",
                'transaction_type': f'{provider}_email_sent',
                'status': 'completed',
                'data': email_data,
                'priority': 1,
                'assigned_to': self.module_id,
                'notes': f"Email {provider} enviado a {email_data.get('to', 'destinatario')}"
            }
            
            success = await self.db_manager.insert_case_transaction(
                self.robot_id, case_data
            )
            
            if success:
                logger.info(f"Email {provider} enviado guardado: {email_data.get('subject', '')[:50]}...")
            else:
                logger.warning(f"No se pudo guardar email {provider} enviado")
        
        except Exception as e:
            logger.error(f"Error al guardar email enviado: {e}")
    
    async def get_email_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del módulo de correo"""
        provider = self.config['email_provider']
        
        return {
            'total_emails_processed': len(self.processed_emails),
            'module_id': self.module_id,
            'robot_id': self.robot_id,
            'provider': provider,
            'email_config': {
                'email': self.config.get('email', ''),
                'server': self.config.get('server', ''),
                'max_emails': self.config.get('max_emails', 50)
            },
            'processed_emails': self.processed_emails[-5:]  # Últimos 5 emails como muestra
        }
    
    @staticmethod
    def get_module_info() -> Dict[str, Any]:
        """Información del módulo"""
        return {
            'name': 'Módulo de Correo Unificado',
            'description': 'Módulo para manejar correos de Gmail y Outlook de manera unificada',
            'version': '1.0.0',
            'supported_providers': ['gmail', 'outlook'],
            'operations': [
                'read_emails', 'send_email', 'search_emails', 
                'manage_labels', 'delete_emails', 'filter_emails'
            ]
        }
