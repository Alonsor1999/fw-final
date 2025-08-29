"""
Email Processor - Procesador especializado para archivos de email
"""

import re
import email
import base64
from email import policy
from email.parser import BytesParser
from typing import Dict, Any, List, Optional
from pathlib import Path


class EmailProcessor:
    """Procesador especializado para archivos de email (.eml, .msg)"""
    
    def __init__(self):
        self.supported_features = {
            'header_extraction': True,
            'body_extraction': True,
            'attachment_extraction': True,
            'metadata_extraction': True,
            'structure_analysis': True,
            'link_extraction': True
        }
    
    def process_email(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un archivo de email y extrae su contenido
        
        Args:
            file_path: Ruta al archivo de email
            
        Returns:
            Dict con información procesada del email
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    'success': False,
                    'error': 'Archivo no encontrado',
                    'file_path': file_path
                }
            
            # Verificar tipo de archivo
            file_type = self._determine_file_type(path)
            if not file_type:
                return {
                    'success': False,
                    'error': 'No es un archivo de email válido',
                    'file_path': str(path)
                }
            
            # Extraer información básica
            basic_info = self._extract_basic_info(path, file_type)
            
            # Extraer headers
            headers = self._extract_headers(path, file_type)
            
            # Extraer cuerpo del email
            body_content = self._extract_body(path, file_type)
            
            # Extraer adjuntos
            attachments = self._extract_attachments(path, file_type)
            
            # Analizar estructura
            structure = self._analyze_structure(path, file_type)
            
            # Extraer enlaces
            links = self._extract_links(body_content)
            
            result = {
                'success': True,
                'file_path': str(path),
                'file_type': file_type,
                'basic_info': basic_info,
                'headers': headers,
                'body_content': body_content,
                'attachments': attachments,
                'structure': structure,
                'links': links,
                'processing_summary': self._generate_summary(basic_info, headers, body_content, attachments)
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _determine_file_type(self, path: Path) -> Optional[str]:
        """Determina el tipo de archivo de email"""
        extension = path.suffix.lower()
        
        if extension == '.eml':
            return 'eml'
        elif extension == '.msg':
            return 'msg'
        else:
            return None
    
    def _extract_basic_info(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae información básica del email"""
        try:
            file_size = path.stat().st_size
            
            return {
                'file_size': file_size,
                'file_type': file_type.upper(),
                'file_name': path.name,
                'encoding': 'utf-8'
            }
            
        except Exception as e:
            return {
                'error': f'Error extrayendo información básica: {str(e)}',
                'file_size': 0,
                'file_type': file_type.upper()
            }
    
    def _extract_headers(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae headers del email"""
        try:
            headers = {
                'from': None,
                'to': None,
                'cc': None,
                'bcc': None,
                'subject': None,
                'date': None,
                'message_id': None,
                'reply_to': None,
                'return_path': None,
                'content_type': None,
                'mime_version': None,
                'x_headers': {},
                'all_headers': {}
            }
            
            if file_type == 'eml':
                # Procesar archivo EML
                with open(path, 'rb') as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                    
                    # Extraer headers principales
                    headers['from'] = msg.get('from')
                    headers['to'] = msg.get('to')
                    headers['cc'] = msg.get('cc')
                    headers['bcc'] = msg.get('bcc')
                    headers['subject'] = msg.get('subject')
                    headers['date'] = msg.get('date')
                    headers['message_id'] = msg.get('message-id')
                    headers['reply_to'] = msg.get('reply-to')
                    headers['return_path'] = msg.get('return-path')
                    headers['content_type'] = msg.get('content-type')
                    headers['mime_version'] = msg.get('mime-version')
                    
                    # Extraer headers X- (personalizados)
                    for header_name, header_value in msg.items():
                        headers['all_headers'][header_name] = header_value
                        if header_name.lower().startswith('x-'):
                            headers['x_headers'][header_name] = header_value
            
            return headers
            
        except Exception as e:
            return {
                'error': f'Error extrayendo headers: {str(e)}'
            }
    
    def _extract_body(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae el cuerpo del email"""
        try:
            body_content = {
                'text_body': '',
                'html_body': '',
                'body_parts': [],
                'content_type': 'text/plain',
                'encoding': 'utf-8'
            }
            
            if file_type == 'eml':
                # Procesar archivo EML
                with open(path, 'rb') as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                    
                    # Extraer diferentes partes del cuerpo
                    body_content.update(self._extract_email_body_parts(msg))
            
            return body_content
            
        except Exception as e:
            return {
                'error': f'Error extrayendo cuerpo: {str(e)}',
                'text_body': '',
                'html_body': '',
                'body_parts': []
            }
    
    def _extract_email_body_parts(self, msg) -> Dict[str, Any]:
        """Extrae las diferentes partes del cuerpo del email"""
        body_content = {
            'text_body': '',
            'html_body': '',
            'body_parts': [],
            'content_type': 'text/plain'
        }
        
        try:
            # Procesar mensaje multipart
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get('content-disposition', '')
                    
                    # Ignorar adjuntos
                    if 'attachment' in content_disposition:
                        continue
                    
                    # Extraer contenido según tipo
                    if content_type == 'text/plain':
                        text_content = part.get_content()
                        if text_content:
                            body_content['text_body'] += text_content
                            body_content['body_parts'].append({
                                'type': 'text/plain',
                                'content': text_content,
                                'encoding': part.get_content_charset() or 'utf-8'
                            })
                    
                    elif content_type == 'text/html':
                        html_content = part.get_content()
                        if html_content:
                            body_content['html_body'] += html_content
                            body_content['body_parts'].append({
                                'type': 'text/html',
                                'content': html_content,
                                'encoding': part.get_content_charset() or 'utf-8'
                            })
            else:
                # Mensaje simple
                content_type = msg.get_content_type()
                content = msg.get_content()
                
                if content_type == 'text/plain':
                    body_content['text_body'] = content
                    body_content['body_parts'].append({
                        'type': 'text/plain',
                        'content': content,
                        'encoding': msg.get_content_charset() or 'utf-8'
                    })
                elif content_type == 'text/html':
                    body_content['html_body'] = content
                    body_content['body_parts'].append({
                        'type': 'text/html',
                        'content': content,
                        'encoding': msg.get_content_charset() or 'utf-8'
                    })
            
            # Determinar tipo de contenido principal
            if body_content['html_body']:
                body_content['content_type'] = 'text/html'
            elif body_content['text_body']:
                body_content['content_type'] = 'text/plain'
            
        except Exception as e:
            body_content['error'] = str(e)
        
        return body_content
    
    def _extract_attachments(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae información de adjuntos"""
        try:
            attachments = {
                'count': 0,
                'files': [],
                'total_size': 0,
                'types': []
            }
            
            if file_type == 'eml':
                # Procesar archivo EML
                with open(path, 'rb') as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                    
                    # Buscar adjuntos
                    for part in msg.walk():
                        content_disposition = part.get('content-disposition', '')
                        
                        if 'attachment' in content_disposition:
                            filename = part.get_filename()
                            content_type = part.get_content_type()
                            content_size = len(part.get_payload(decode=True)) if part.get_payload() else 0
                            
                            attachment_info = {
                                'filename': filename or f'attachment_{len(attachments["files"]) + 1}',
                                'content_type': content_type,
                                'size': content_size,
                                'encoding': part.get_content_charset() or 'unknown'
                            }
                            
                            attachments['files'].append(attachment_info)
                            attachments['total_size'] += content_size
                            
                            if content_type not in attachments['types']:
                                attachments['types'].append(content_type)
                    
                    attachments['count'] = len(attachments['files'])
            
            return attachments
            
        except Exception as e:
            return {
                'error': f'Error extrayendo adjuntos: {str(e)}',
                'count': 0,
                'files': [],
                'total_size': 0,
                'types': []
            }
    
    def _analyze_structure(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Analiza la estructura del email"""
        try:
            structure = {
                'is_multipart': False,
                'has_attachments': False,
                'has_html': False,
                'has_text': False,
                'has_inline_images': False,
                'structure_type': 'simple'
            }
            
            if file_type == 'eml':
                # Procesar archivo EML
                with open(path, 'rb') as f:
                    msg = BytesParser(policy=policy.default).parse(f)
                    
                    structure['is_multipart'] = msg.is_multipart()
                    
                    # Analizar partes del mensaje
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = part.get('content-disposition', '')
                        
                        if 'attachment' in content_disposition:
                            structure['has_attachments'] = True
                        elif content_type == 'text/html':
                            structure['has_html'] = True
                        elif content_type == 'text/plain':
                            structure['has_text'] = True
                        elif content_type.startswith('image/') and 'inline' in content_disposition:
                            structure['has_inline_images'] = True
                    
                    # Determinar tipo de estructura
                    if structure['has_attachments']:
                        structure['structure_type'] = 'with_attachments'
                    elif structure['has_html'] and structure['has_text']:
                        structure['structure_type'] = 'multipart_alternative'
                    elif structure['has_html']:
                        structure['structure_type'] = 'html_only'
                    elif structure['has_text']:
                        structure['structure_type'] = 'text_only'
            
            return structure
            
        except Exception as e:
            return {
                'error': f'Error analizando estructura: {str(e)}',
                'structure_type': 'unknown'
            }
    
    def _extract_links(self, body_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae enlaces del cuerpo del email"""
        try:
            links = {
                'urls': [],
                'email_addresses': [],
                'total_links': 0
            }
            
            # Extraer URLs del texto
            text_content = body_content.get('text_body', '') + ' ' + body_content.get('html_body', '')
            
            if text_content:
                # Buscar URLs
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, text_content)
                links['urls'] = list(set(urls))  # Remover duplicados
                
                # Buscar direcciones de email
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text_content)
                links['email_addresses'] = list(set(emails))  # Remover duplicados
                
                links['total_links'] = len(links['urls']) + len(links['email_addresses'])
            
            return links
            
        except Exception as e:
            return {
                'error': f'Error extrayendo enlaces: {str(e)}',
                'urls': [],
                'email_addresses': [],
                'total_links': 0
            }
    
    def _generate_summary(self, basic_info: Dict, headers: Dict, body_content: Dict, attachments: Dict) -> Dict[str, Any]:
        """Genera un resumen del procesamiento"""
        return {
            'processing_successful': True,
            'file_type': basic_info.get('file_type', 'unknown'),
            'file_size': basic_info.get('file_size', 0),
            'has_subject': bool(headers.get('subject')),
            'has_from': bool(headers.get('from')),
            'has_to': bool(headers.get('to')),
            'text_body_length': len(body_content.get('text_body', '')),
            'html_body_length': len(body_content.get('html_body', '')),
            'attachments_count': attachments.get('count', 0),
            'attachments_size': attachments.get('total_size', 0),
            'body_parts_count': len(body_content.get('body_parts', []))
        }
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Retorna las características soportadas"""
        return self.supported_features.copy()
