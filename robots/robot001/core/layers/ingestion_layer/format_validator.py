"""
Format Validator - Componente para validar formatos de documentos
"""

import os
import hashlib
from typing import Dict, Any, List, Tuple
from pathlib import Path


class FormatValidator:
    """Valida el formato y estructura de documentos"""
    
    def __init__(self):
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            'pdf': ['.pdf'],
            'word': ['.doc', '.docx'],
            'email': ['.eml', '.msg'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'text': ['.txt', '.html', '.htm']
        }
        
        # Patrones de validación por tipo
        self.validation_patterns = {
            'pdf': self._validate_pdf,
            'word': self._validate_word,
            'email': self._validate_email,
            'image': self._validate_image,
            'text': self._validate_text
        }
    
    def validate_document(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """
        Valida un documento según su tipo
        
        Args:
            file_path: Ruta al archivo a validar
            document_type: Tipo de documento (pdf, word, email, etc.)
            
        Returns:
            Dict con resultados de validación
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    'valid': False,
                    'error': 'Archivo no encontrado',
                    'file_path': file_path
                }
            
            # Validaciones básicas
            basic_validation = self._basic_validation(path)
            if not basic_validation['valid']:
                return basic_validation
            
            # Validación específica por tipo
            type_validation = self._type_specific_validation(path, document_type)
            
            # Combinar resultados
            result = {
                'valid': basic_validation['valid'] and type_validation['valid'],
                'file_path': str(path),
                'file_size': path.stat().st_size,
                'file_hash': self._calculate_file_hash(path),
                'basic_validation': basic_validation,
                'type_validation': type_validation
            }
            
            return result
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _basic_validation(self, path: Path) -> Dict[str, Any]:
        """Realiza validaciones básicas del archivo"""
        
        try:
            # Verificar tamaño
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'Archivo demasiado grande: {file_size} bytes'
                }
            
            if file_size == 0:
                return {
                    'valid': False,
                    'error': 'Archivo vacío'
                }
            
            # Verificar permisos de lectura
            if not os.access(path, os.R_OK):
                return {
                    'valid': False,
                    'error': 'Sin permisos de lectura'
                }
            
            # Verificar que sea un archivo regular
            if not path.is_file():
                return {
                    'valid': False,
                    'error': 'No es un archivo regular'
                }
            
            return {
                'valid': True,
                'file_size': file_size,
                'readable': True,
                'is_file': True
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error en validación básica: {str(e)}'
            }
    
    def _type_specific_validation(self, path: Path, document_type: str) -> Dict[str, Any]:
        """Realiza validación específica según el tipo de documento"""
        
        if document_type not in self.validation_patterns:
            return {
                'valid': False,
                'error': f'Tipo de documento no soportado: {document_type}'
            }
        
        try:
            return self.validation_patterns[document_type](path)
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error en validación específica: {str(e)}'
            }
    
    def _validate_pdf(self, path: Path) -> Dict[str, Any]:
        """Valida archivo PDF"""
        try:
            # Verificar extensión
            if path.suffix.lower() != '.pdf':
                return {
                    'valid': False,
                    'error': 'Extensión incorrecta para PDF'
                }
            
            # Verificar magic bytes (PDF)
            with open(path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return {
                        'valid': False,
                        'error': 'No es un archivo PDF válido'
                    }
            
            return {
                'valid': True,
                'pdf_version': self._detect_pdf_version(path),
                'has_text': self._pdf_has_text(path)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validando PDF: {str(e)}'
            }
    
    def _validate_word(self, path: Path) -> Dict[str, Any]:
        """Valida archivo Word"""
        try:
            extension = path.suffix.lower()
            if extension not in ['.doc', '.docx']:
                return {
                    'valid': False,
                    'error': 'Extensión incorrecta para Word'
                }
            
            # Verificar magic bytes
            with open(path, 'rb') as f:
                if extension == '.doc':
                    # DOC file magic bytes
                    header = f.read(8)
                    if not header.startswith(b'\xD0\xCF\x11\xE0'):
                        return {
                            'valid': False,
                            'error': 'No es un archivo DOC válido'
                        }
                elif extension == '.docx':
                    # DOCX es un ZIP con estructura específica
                    header = f.read(4)
                    if header != b'PK\x03\x04':
                        return {
                            'valid': False,
                            'error': 'No es un archivo DOCX válido'
                        }
            
            return {
                'valid': True,
                'word_version': 'Word 2007+' if extension == '.docx' else 'Word 97-2003'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validando Word: {str(e)}'
            }
    
    def _validate_email(self, path: Path) -> Dict[str, Any]:
        """Valida archivo de email"""
        try:
            extension = path.suffix.lower()
            if extension not in ['.eml', '.msg']:
                return {
                    'valid': False,
                    'error': 'Extensión incorrecta para email'
                }
            
            # Verificar estructura básica de email
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                if not first_line or ':' not in first_line:
                    return {
                        'valid': False,
                        'error': 'No es un archivo de email válido'
                    }
            
            return {
                'valid': True,
                'email_format': extension
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validando email: {str(e)}'
            }
    
    def _validate_image(self, path: Path) -> Dict[str, Any]:
        """Valida archivo de imagen"""
        try:
            extension = path.suffix.lower()
            if extension not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return {
                    'valid': False,
                    'error': 'Extensión incorrecta para imagen'
                }
            
            # Verificar magic bytes de imágenes
            with open(path, 'rb') as f:
                header = f.read(8)
                
                if extension in ['.jpg', '.jpeg']:
                    if not header.startswith(b'\xFF\xD8'):
                        return {
                            'valid': False,
                            'error': 'No es un archivo JPEG válido'
                        }
                elif extension == '.png':
                    if not header.startswith(b'\x89PNG'):
                        return {
                            'valid': False,
                            'error': 'No es un archivo PNG válido'
                        }
                elif extension == '.gif':
                    if not header.startswith(b'GIF8'):
                        return {
                            'valid': False,
                            'error': 'No es un archivo GIF válido'
                        }
                elif extension == '.bmp':
                    if not header.startswith(b'BM'):
                        return {
                            'valid': False,
                            'error': 'No es un archivo BMP válido'
                        }
            
            return {
                'valid': True,
                'image_format': extension
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validando imagen: {str(e)}'
            }
    
    def _validate_text(self, path: Path) -> Dict[str, Any]:
        """Valida archivo de texto"""
        try:
            extension = path.suffix.lower()
            if extension not in ['.txt', '.html', '.htm']:
                return {
                    'valid': False,
                    'error': 'Extensión incorrecta para texto'
                }
            
            # Verificar que sea legible como texto
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # Leer primeros 1KB
                if not content.strip():
                    return {
                        'valid': False,
                        'error': 'Archivo de texto vacío'
                    }
            
            return {
                'valid': True,
                'text_format': extension,
                'encoding': 'utf-8'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validando texto: {str(e)}'
            }
    
    def _calculate_file_hash(self, path: Path) -> str:
        """Calcula hash SHA-256 del archivo"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ''
    
    def _detect_pdf_version(self, path: Path) -> str:
        """Detecta versión de PDF"""
        try:
            with open(path, 'rb') as f:
                first_line = f.readline().decode('ascii', errors='ignore')
                if first_line.startswith('%PDF-'):
                    version = first_line.split('-')[1].split()[0]
                    return version
            return 'unknown'
        except:
            return 'unknown'
    
    def _pdf_has_text(self, path: Path) -> bool:
        """Verifica si PDF tiene texto extraíble"""
        try:
            # Implementación básica - en producción usar PyPDF2 o similar
            return True
        except:
            return False
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Retorna las reglas de validación"""
        return {
            'max_file_size': self.max_file_size,
            'allowed_extensions': self.allowed_extensions.copy()
        }
