"""
Security Scanner - Componente para escanear documentos en busca de amenazas de seguridad
"""

import os
import re
import hashlib
import zipfile
from typing import Dict, Any, List, Optional
from pathlib import Path


class SecurityScanner:
    """Escanea documentos en busca de amenazas de seguridad"""
    
    def __init__(self):
        # Patrones de amenazas conocidas
        self.threat_patterns = {
            'suspicious_extensions': [
                '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js',
                '.jar', '.msi', '.dll', '.sys', '.drv', '.ocx', '.cpl'
            ],
            'suspicious_macros': [
                'VBA', 'macro', 'automation', 'script', 'execute',
                'shell', 'system', 'powershell', 'cmd'
            ],
            'suspicious_urls': [
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                r'ftp://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            ],
            'suspicious_ips': [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ],
            'suspicious_commands': [
                'cmd.exe', 'powershell', 'bash', 'sh', 'wget', 'curl',
                'netcat', 'nc', 'telnet', 'ftp', 'ssh'
            ]
        }
        
        # Límites de seguridad
        self.security_limits = {
            'max_nested_archives': 3,
            'max_archive_size': 50 * 1024 * 1024,  # 50MB
            'max_embedded_files': 100,
            'suspicious_content_threshold': 5
        }
    
    def scan_document(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """
        Escanea un documento en busca de amenazas de seguridad
        
        Args:
            file_path: Ruta al archivo a escanear
            document_type: Tipo de documento
            
        Returns:
            Dict con resultados del escaneo de seguridad
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    'safe': False,
                    'error': 'Archivo no encontrado',
                    'file_path': file_path
                }
            
            # Escaneo básico
            basic_scan = self._basic_security_scan(path)
            
            # Escaneo específico por tipo
            type_scan = self._type_specific_security_scan(path, document_type)
            
            # Escaneo de contenido
            content_scan = self._content_security_scan(path, document_type)
            
            # Combinar resultados
            all_threats = []
            all_threats.extend(basic_scan.get('threats', []))
            all_threats.extend(type_scan.get('threats', []))
            all_threats.extend(content_scan.get('threats', []))
            
            is_safe = len(all_threats) == 0
            
            result = {
                'safe': is_safe,
                'file_path': str(path),
                'threats_found': len(all_threats),
                'threats': all_threats,
                'basic_scan': basic_scan,
                'type_scan': type_scan,
                'content_scan': content_scan,
                'risk_level': self._calculate_risk_level(all_threats)
            }
            
            return result
            
        except Exception as e:
            return {
                'safe': False,
                'error': str(e),
                'file_path': file_path,
                'threats_found': 0,
                'threats': []
            }
    
    def _basic_security_scan(self, path: Path) -> Dict[str, Any]:
        """Realiza escaneo básico de seguridad"""
        
        threats = []
        
        try:
            # Verificar extensión sospechosa
            if path.suffix.lower() in self.threat_patterns['suspicious_extensions']:
                threats.append({
                    'type': 'suspicious_extension',
                    'severity': 'high',
                    'description': f'Extensión sospechosa: {path.suffix}',
                    'extension': path.suffix.lower()
                })
            
            # Verificar tamaño del archivo
            file_size = path.stat().st_size
            if file_size > self.security_limits['max_archive_size']:
                threats.append({
                    'type': 'large_file',
                    'severity': 'medium',
                    'description': f'Archivo muy grande: {file_size} bytes',
                    'size': file_size
                })
            
            # Verificar permisos
            if os.access(path, os.X_OK):
                threats.append({
                    'type': 'executable_permissions',
                    'severity': 'high',
                    'description': 'Archivo con permisos de ejecución',
                    'permissions': 'executable'
                })
            
            return {
                'completed': True,
                'threats': threats,
                'file_size': file_size
            }
            
        except Exception as e:
            return {
                'completed': False,
                'error': str(e),
                'threats': []
            }
    
    def _type_specific_security_scan(self, path: Path, document_type: str) -> Dict[str, Any]:
        """Realiza escaneo específico según el tipo de documento"""
        
        threats = []
        
        try:
            if document_type == 'pdf':
                threats.extend(self._scan_pdf_security(path))
            elif document_type == 'word':
                threats.extend(self._scan_word_security(path))
            elif document_type == 'email':
                threats.extend(self._scan_email_security(path))
            elif document_type == 'image':
                threats.extend(self._scan_image_security(path))
            elif document_type == 'text':
                threats.extend(self._scan_text_security(path))
            
            return {
                'completed': True,
                'threats': threats
            }
            
        except Exception as e:
            return {
                'completed': False,
                'error': str(e),
                'threats': []
            }
    
    def _scan_pdf_security(self, path: Path) -> List[Dict[str, Any]]:
        """Escanea PDF en busca de amenazas"""
        threats = []
        
        try:
            with open(path, 'rb') as f:
                content = f.read(8192)  # Leer primeros 8KB
                
                # Buscar JavaScript embebido
                if b'/JS' in content or b'/JavaScript' in content:
                    threats.append({
                        'type': 'embedded_javascript',
                        'severity': 'medium',
                        'description': 'JavaScript embebido detectado en PDF'
                    })
                
                # Buscar acciones sospechosas
                suspicious_actions = [b'/Launch', b'/SubmitForm', b'/ImportData']
                for action in suspicious_actions:
                    if action in content:
                        threats.append({
                            'type': 'suspicious_action',
                            'severity': 'high',
                            'description': f'Acción sospechosa detectada: {action.decode()}'
                        })
                
                # Buscar URLs
                urls = re.findall(rb'http[s]?://[^\s<>"]+', content)
                if urls:
                    threats.append({
                        'type': 'embedded_urls',
                        'severity': 'low',
                        'description': f'{len(urls)} URLs embebidas detectadas',
                        'url_count': len(urls)
                    })
        
        except Exception as e:
            threats.append({
                'type': 'scan_error',
                'severity': 'medium',
                'description': f'Error escaneando PDF: {str(e)}'
            })
        
        return threats
    
    def _scan_word_security(self, path: Path) -> List[Dict[str, Any]]:
        """Escanea documento Word en busca de amenazas"""
        threats = []
        
        try:
            # Para archivos .docx (ZIP)
            if path.suffix.lower() == '.docx':
                threats.extend(self._scan_zip_security(path))
            
            # Buscar macros
            with open(path, 'rb') as f:
                content = f.read(8192)
                
                # Buscar indicadores de macros
                macro_indicators = [b'VBA', b'macro', b'Automation']
                for indicator in macro_indicators:
                    if indicator in content:
                        threats.append({
                            'type': 'macro_detected',
                            'severity': 'high',
                            'description': f'Macro detectada: {indicator.decode()}'
                        })
        
        except Exception as e:
            threats.append({
                'type': 'scan_error',
                'severity': 'medium',
                'description': f'Error escaneando Word: {str(e)}'
            })
        
        return threats
    
    def _scan_email_security(self, path: Path) -> List[Dict[str, Any]]:
        """Escanea email en busca de amenazas"""
        threats = []
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Buscar URLs sospechosas
                urls = re.findall(r'http[s]?://[^\s<>"]+', content)
                if len(urls) > 10:  # Muchas URLs
                    threats.append({
                        'type': 'many_urls',
                        'severity': 'medium',
                        'description': f'Muchas URLs detectadas: {len(urls)}'
                    })
                
                # Buscar comandos sospechosos
                for cmd in self.threat_patterns['suspicious_commands']:
                    if cmd.lower() in content.lower():
                        threats.append({
                            'type': 'suspicious_command',
                            'severity': 'high',
                            'description': f'Comando sospechoso: {cmd}'
                        })
                
                # Buscar IPs
                ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', content)
                if ips:
                    threats.append({
                        'type': 'embedded_ips',
                        'severity': 'low',
                        'description': f'IPs embebidas: {len(ips)}'
                    })
        
        except Exception as e:
            threats.append({
                'type': 'scan_error',
                'severity': 'medium',
                'description': f'Error escaneando email: {str(e)}'
            })
        
        return threats
    
    def _scan_image_security(self, path: Path) -> List[Dict[str, Any]]:
        """Escanea imagen en busca de amenazas"""
        threats = []
        
        try:
            # Verificar si es un archivo compuesto (ej: imagen con datos embebidos)
            with open(path, 'rb') as f:
                content = f.read(1024)
                
                # Buscar firmas de archivos ejecutables en imagen
                if b'MZ' in content or b'PE' in content:
                    threats.append({
                        'type': 'executable_in_image',
                        'severity': 'high',
                        'description': 'Posible ejecutable embebido en imagen'
                    })
        
        except Exception as e:
            threats.append({
                'type': 'scan_error',
                'severity': 'medium',
                'description': f'Error escaneando imagen: {str(e)}'
            })
        
        return threats
    
    def _scan_text_security(self, path: Path) -> List[Dict[str, Any]]:
        """Escanea archivo de texto en busca de amenazas"""
        threats = []
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Buscar comandos sospechosos
                for cmd in self.threat_patterns['suspicious_commands']:
                    if cmd.lower() in content.lower():
                        threats.append({
                            'type': 'suspicious_command',
                            'severity': 'high',
                            'description': f'Comando sospechoso: {cmd}'
                        })
                
                # Buscar URLs
                urls = re.findall(r'http[s]?://[^\s<>"]+', content)
                if len(urls) > 5:
                    threats.append({
                        'type': 'many_urls',
                        'severity': 'low',
                        'description': f'Muchas URLs: {len(urls)}'
                    })
        
        except Exception as e:
            threats.append({
                'type': 'scan_error',
                'severity': 'medium',
                'description': f'Error escaneando texto: {str(e)}'
            })
        
        return threats
    
    def _scan_zip_security(self, path: Path) -> List[Dict[str, Any]]:
        """Escanea archivo ZIP en busca de amenazas"""
        threats = []
        
        try:
            with zipfile.ZipFile(path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # Verificar número de archivos
                if len(file_list) > self.security_limits['max_embedded_files']:
                    threats.append({
                        'type': 'too_many_files',
                        'severity': 'medium',
                        'description': f'Demasiados archivos: {len(file_list)}'
                    })
                
                # Verificar archivos sospechosos
                for file_name in file_list:
                    if any(ext in file_name.lower() for ext in self.threat_patterns['suspicious_extensions']):
                        threats.append({
                            'type': 'suspicious_embedded_file',
                            'severity': 'high',
                            'description': f'Archivo sospechoso embebido: {file_name}'
                        })
        
        except Exception as e:
            threats.append({
                'type': 'zip_scan_error',
                'severity': 'medium',
                'description': f'Error escaneando ZIP: {str(e)}'
            })
        
        return threats
    
    def _content_security_scan(self, path: Path, document_type: str) -> Dict[str, Any]:
        """Escanea contenido del documento en busca de amenazas"""
        
        threats = []
        
        try:
            # Leer contenido según el tipo
            if document_type in ['text', 'email']:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(32768)  # 32KB
            else:
                with open(path, 'rb') as f:
                    content = f.read(32768)
            
            # Buscar patrones sospechosos
            suspicious_count = 0
            
            # Buscar URLs
            if isinstance(content, bytes):
                content_str = content.decode('utf-8', errors='ignore')
            else:
                content_str = content
            
            urls = re.findall(r'http[s]?://[^\s<>"]+', content_str)
            if len(urls) > 20:
                threats.append({
                    'type': 'excessive_urls',
                    'severity': 'medium',
                    'description': f'Exceso de URLs: {len(urls)}'
                })
                suspicious_count += 1
            
            # Buscar comandos
            for cmd in self.threat_patterns['suspicious_commands']:
                if cmd.lower() in content_str.lower():
                    threats.append({
                        'type': 'suspicious_command_in_content',
                        'severity': 'high',
                        'description': f'Comando sospechoso en contenido: {cmd}'
                    })
                    suspicious_count += 1
            
            return {
                'completed': True,
                'threats': threats,
                'suspicious_patterns_found': suspicious_count
            }
            
        except Exception as e:
            return {
                'completed': False,
                'error': str(e),
                'threats': []
            }
    
    def _calculate_risk_level(self, threats: List[Dict[str, Any]]) -> str:
        """Calcula el nivel de riesgo basado en las amenazas encontradas"""
        
        if not threats:
            return 'low'
        
        high_severity = sum(1 for t in threats if t.get('severity') == 'high')
        medium_severity = sum(1 for t in threats if t.get('severity') == 'medium')
        
        if high_severity > 0:
            return 'high'
        elif medium_severity > 2:
            return 'medium'
        else:
            return 'low'
    
    def get_security_config(self) -> Dict[str, Any]:
        """Retorna la configuración de seguridad"""
        return {
            'threat_patterns': self.threat_patterns.copy(),
            'security_limits': self.security_limits.copy()
        }
