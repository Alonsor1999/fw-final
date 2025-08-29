"""
Document Classifier - Componente para clasificar tipos de documentos
"""

import os
import mimetypes
from typing import Dict, Any, Optional
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
    
    def get_supported_types(self) -> Dict[str, list]:
        """Retorna los tipos de documentos soportados"""
        return self.supported_types.copy()
