"""
Document Classifier - Componente para clasificar tipos de documentos
"""

import os
import mimetypes
import re
from typing import Dict, Any, Optional, List
from pathlib import Path


class DocumentClassifier:
    """Clasifica documentos según su tipo y características"""
    
    def __init__(self):
        self.supported_types = {
            'pdf': ['application/pdf'],
            'word': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                    'application/msword'],
            'email': ['message/rfc822', 'text/plain'],
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp'],
            'text': ['text/plain', 'text/html']
        }
        
        # Definir rutas de clasificación para correos
        self.email_routes = {
            'ruta_a': {
                'name': 'Estado de Cédula',
                'keywords': [
                    'estado de cédula',
                    'certificado de cédula',
                    'vigencia',
                    'indique el número de cédula y su estado',
                    'aporte el certificado',
                    'certifique el cupo numérico',
                    'certifique el estado actual de la cédula',
                    'certificar a quien corresponden los números de cedula de ciudadanía'
                ]
            },
            'ruta_b': {
                'name': 'Documentos de Identificación',
                'keywords': [
                    'copia de la tarjeta de preparación',
                    'copia web de la cédula de ciudadanía',
                    'se sirva remitir con destino a este proceso judicial, la tarjeta decadactilar',
                    'copia de la tarjeta ged',
                    'tarjeta alfabética y decadactilar',
                    'fotocédula',
                    'consulta web',
                    # 🆕 Palabras clave más flexibles para detectar mejor
                    'tarjetas decadactilares',
                    'tarjeta decadactilar',
                    'cupo numérico',
                    'cupos numéricos',
                    'dactilar',
                    'decadactilar'
                ]
            },
            'ruta_c': {
                'name': 'Procesos Postumas',
                'keywords': [
                    'postumas'
                ]
            }
        }
    
    def classify_document(self, file_path: str) -> Dict[str, Any]:
        """
        Clasifica un documento basado en su ruta de archivo
        
        Args:
            file_path: Ruta al archivo a clasificar
            
        Returns:
            Dict con información de clasificación
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            # Obtener información básica del archivo
            file_info = {
                'file_path': str(path),
                'file_name': path.name,
                'file_size': path.stat().st_size,
                'file_extension': path.suffix.lower(),
                'exists': True
            }
            
            # Determinar MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            file_info['mime_type'] = mime_type
            
            # Clasificar por extensión y MIME type
            document_type = self._determine_document_type(path.suffix.lower(), mime_type)
            file_info['document_type'] = document_type
            
            # Información adicional según el tipo
            file_info.update(self._get_type_specific_info(document_type, path))
            
            return file_info
            
        except Exception as e:
            return {
                'file_path': file_path,
                'error': str(e),
                'exists': False,
                'document_type': 'unknown'
            }
    
    def _determine_document_type(self, extension: str, mime_type: Optional[str]) -> str:
        """Determina el tipo de documento basado en extensión y MIME type"""
        
        # Mapeo de extensiones comunes
        extension_mapping = {
            '.pdf': 'pdf',
            '.doc': 'word',
            '.docx': 'word',
            '.eml': 'email',
            '.msg': 'email',
            '.txt': 'text',
            '.html': 'text',
            '.htm': 'text',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.bmp': 'image'
        }
        
        # Primero intentar por extensión
        if extension in extension_mapping:
            return extension_mapping[extension]
        
        # Luego intentar por MIME type
        if mime_type:
            for doc_type, mime_types in self.supported_types.items():
                if mime_type in mime_types:
                    return doc_type
        
        return 'unknown'
    
    def _get_type_specific_info(self, document_type: str, path: Path) -> Dict[str, Any]:
        """Obtiene información específica según el tipo de documento"""
        
        info = {}
        
        if document_type == 'pdf':
            info['pdf_pages'] = self._estimate_pdf_pages(path)
        elif document_type == 'word':
            info['word_version'] = self._detect_word_version(path)
        elif document_type == 'email':
            info['email_headers'] = self._extract_email_headers(path)
        elif document_type == 'image':
            info['image_dimensions'] = self._get_image_dimensions(path)
        
        return info
    
    def _estimate_pdf_pages(self, path: Path) -> Optional[int]:
        """Estima el número de páginas de un PDF"""
        try:
            # Implementación básica - en producción usar PyPDF2 o similar
            return None
        except:
            return None
    
    def _detect_word_version(self, path: Path) -> Optional[str]:
        """Detecta la versión de Word del documento"""
        try:
            # Implementación básica - en producción usar python-docx o similar
            if path.suffix.lower() == '.docx':
                return 'Word 2007+'
            elif path.suffix.lower() == '.doc':
                return 'Word 97-2003'
            return None
        except:
            return None
    
    def _extract_email_headers(self, path: Path) -> Optional[Dict[str, str]]:
        """Extrae headers básicos de un email"""
        try:
            # Implementación básica
            return None
        except:
            return None
    
    def _get_image_dimensions(self, path: Path) -> Optional[Dict[str, int]]:
        """Obtiene dimensiones de una imagen"""
        try:
            # Implementación básica - en producción usar Pillow
            return None
        except:
            return None
    
    def classify_email_by_content(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Clasifica un correo electrónico según el contenido del asunto y cuerpo
        
        Args:
            subject: Asunto del correo
            body: Cuerpo del correo
            
        Returns:
            Dict con información de clasificación de ruta
        """
        try:
            # Normalizar texto para búsqueda
            subject_lower = subject.lower() if subject else ""
            body_lower = body.lower() if body else ""
            combined_text = f"{subject_lower} {body_lower}"
            
            # Buscar coincidencias en cada ruta
            route_matches = {}
            
            for route_id, route_info in self.email_routes.items():
                matches = []
                for keyword in route_info['keywords']:
                    if keyword.lower() in combined_text:
                        matches.append(keyword)
                
                if matches:
                    route_matches[route_id] = {
                        'route_name': route_info['name'],
                        'matched_keywords': matches,
                        'match_count': len(matches),
                        'confidence_score': min(len(matches) / len(route_info['keywords']), 1.0)
                    }
            
            # Determinar la ruta principal (la que tiene más coincidencias)
            if route_matches:
                primary_route = max(route_matches.items(), 
                                  key=lambda x: (x[1]['match_count'], x[1]['confidence_score']))
                
                return {
                    'success': True,
                    'primary_route': primary_route[0],
                    'primary_route_name': primary_route[1]['route_name'],
                    'all_matches': route_matches,
                    'subject': subject,
                    'body_preview': body[:200] + "..." if len(body) > 200 else body,
                    'classification_confidence': primary_route[1]['confidence_score'],
                    'matched_keywords': primary_route[1]['matched_keywords']
                }
            else:
                return {
                    'success': False,
                    'primary_route': 'no_classified',
                    'primary_route_name': 'No Clasificado',
                    'all_matches': {},
                    'subject': subject,
                    'body_preview': body[:200] + "..." if len(body) > 200 else body,
                    'classification_confidence': 0.0,
                    'matched_keywords': [],
                    'message': 'No se encontraron palabras clave para clasificar'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'primary_route': 'error',
                'primary_route_name': 'Error en Clasificación',
                'subject': subject,
                'body_preview': body[:200] + "..." if len(body) > 200 else body if body else ""
            }
    
    def get_email_routes(self) -> Dict[str, Any]:
        """Retorna las rutas de clasificación de correos disponibles"""
        return self.email_routes.copy()
    
    def get_supported_types(self) -> Dict[str, list]:
        """Retorna los tipos de documentos soportados"""
        return self.supported_types.copy()
