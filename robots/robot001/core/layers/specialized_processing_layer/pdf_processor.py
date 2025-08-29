"""
PDF Native Processor - Procesador especializado para archivos PDF
"""

import re
import io
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class PDFNativeProcessor:
    """Procesador nativo para archivos PDF"""
    
    def __init__(self):
        self.supported_features = {
            'text_extraction': True,
            'metadata_extraction': True,
            'image_extraction': False,  # Requiere librerías adicionales
            'structure_analysis': True,
            'form_extraction': True
        }
    
    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un archivo PDF y extrae su contenido
        
        Args:
            file_path: Ruta al archivo PDF
            
        Returns:
            Dict con información procesada del PDF
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    'success': False,
                    'error': 'Archivo no encontrado',
                    'file_path': file_path
                }
            
            # Verificar que sea un PDF válido
            if not self._is_valid_pdf(path):
                return {
                    'success': False,
                    'error': 'No es un archivo PDF válido',
                    'file_path': str(path)
                }
            
            # Extraer información básica
            basic_info = self._extract_basic_info(path)
            
            # Extraer metadatos
            metadata = self._extract_metadata(path)
            
            # Extraer texto
            text_content = self._extract_text(path)
            
            # Analizar estructura
            structure = self._analyze_structure(path)
            
            # Extraer formularios
            forms = self._extract_forms(path)
            
            result = {
                'success': True,
                'file_path': str(path),
                'basic_info': basic_info,
                'metadata': metadata,
                'text_content': text_content,
                'structure': structure,
                'forms': forms,
                'processing_summary': self._generate_summary(basic_info, text_content, structure)
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _is_valid_pdf(self, path: Path) -> bool:
        """Verifica si el archivo es un PDF válido"""
        try:
            with open(path, 'rb') as f:
                header = f.read(4)
                return header == b'%PDF'
        except:
            return False
    
    def _extract_basic_info(self, path: Path) -> Dict[str, Any]:
        """Extrae información básica del PDF"""
        try:
            file_size = path.stat().st_size
            
            # Leer primera línea para obtener versión
            with open(path, 'rb') as f:
                first_line = f.readline().decode('ascii', errors='ignore')
                version = 'unknown'
                if first_line.startswith('%PDF-'):
                    version = first_line.split('-')[1].split()[0]
            
            # Contar páginas (implementación básica)
            page_count = self._count_pages(path)
            
            return {
                'file_size': file_size,
                'pdf_version': version,
                'page_count': page_count,
                'file_name': path.name
            }
            
        except Exception as e:
            return {
                'error': f'Error extrayendo información básica: {str(e)}',
                'file_size': 0,
                'pdf_version': 'unknown',
                'page_count': 0
            }
    
    def _extract_metadata(self, path: Path) -> Dict[str, Any]:
        """Extrae metadatos del PDF"""
        try:
            metadata = {
                'title': None,
                'author': None,
                'subject': None,
                'creator': None,
                'producer': None,
                'creation_date': None,
                'modification_date': None,
                'keywords': None
            }
            
            # Leer archivo para buscar metadatos
            with open(path, 'rb') as f:
                content = f.read(8192)  # Leer primeros 8KB
                
                # Buscar patrones de metadatos
                content_str = content.decode('utf-8', errors='ignore')
                
                # Buscar título
                title_match = re.search(r'/Title\s*\(([^)]+)\)', content_str)
                if title_match:
                    metadata['title'] = title_match.group(1)
                
                # Buscar autor
                author_match = re.search(r'/Author\s*\(([^)]+)\)', content_str)
                if author_match:
                    metadata['author'] = author_match.group(1)
                
                # Buscar sujeto
                subject_match = re.search(r'/Subject\s*\(([^)]+)\)', content_str)
                if subject_match:
                    metadata['subject'] = subject_match.group(1)
                
                # Buscar creador
                creator_match = re.search(r'/Creator\s*\(([^)]+)\)', content_str)
                if creator_match:
                    metadata['creator'] = creator_match.group(1)
                
                # Buscar productor
                producer_match = re.search(r'/Producer\s*\(([^)]+)\)', content_str)
                if producer_match:
                    metadata['producer'] = producer_match.group(1)
            
            return metadata
            
        except Exception as e:
            return {
                'error': f'Error extrayendo metadatos: {str(e)}'
            }
    
    def _extract_text(self, path: Path) -> Dict[str, Any]:
        """Extrae texto del PDF"""
        try:
            text_content = {
                'full_text': '',
                'pages_text': [],
                'text_statistics': {},
                'encoding': 'utf-8'
            }
            
            # Leer contenido del archivo
            with open(path, 'rb') as f:
                content = f.read()
                
                # Decodificar contenido
                try:
                    content_str = content.decode('utf-8', errors='ignore')
                except:
                    content_str = content.decode('latin-1', errors='ignore')
                    text_content['encoding'] = 'latin-1'
                
                # Extraer texto usando patrones básicos
                text_parts = self._extract_text_parts(content_str)
                
                text_content['full_text'] = '\n'.join(text_parts)
                text_content['pages_text'] = self._split_into_pages(text_parts)
                text_content['text_statistics'] = self._calculate_text_statistics(text_content['full_text'])
            
            return text_content
            
        except Exception as e:
            return {
                'error': f'Error extrayendo texto: {str(e)}',
                'full_text': '',
                'pages_text': [],
                'text_statistics': {}
            }
    
    def _extract_text_parts(self, content: str) -> List[str]:
        """Extrae partes de texto del contenido del PDF"""
        text_parts = []
        
        # Buscar patrones de texto en PDF
        # Patrones básicos para extraer texto
        text_patterns = [
            r'BT\s*([^E]+?)\s*ET',  # Texto entre BT y ET
            r'\(([^)]+)\)\s*Tj',     # Texto en operadores Tj
            r'\[([^\]]+)\]\s*TJ',    # Texto en operadores TJ
        ]
        
        for pattern in text_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Limpiar texto extraído
                cleaned_text = self._clean_text(match)
                if cleaned_text:
                    text_parts.append(cleaned_text)
        
        return text_parts
    
    def _clean_text(self, text: str) -> str:
        """Limpia el texto extraído"""
        # Remover caracteres de control
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remover espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Remover caracteres especiales de PDF
        text = re.sub(r'\\[0-9]{3}', '', text)  # Códigos octales
        
        return text.strip()
    
    def _split_into_pages(self, text_parts: List[str]) -> List[Dict[str, Any]]:
        """Divide el texto en páginas"""
        pages = []
        
        # Implementación básica - dividir por número de partes
        parts_per_page = max(1, len(text_parts) // 10)  # Aproximadamente 10 páginas
        
        for i in range(0, len(text_parts), parts_per_page):
            page_text = ' '.join(text_parts[i:i + parts_per_page])
            pages.append({
                'page_number': len(pages) + 1,
                'text': page_text,
                'text_length': len(page_text)
            })
        
        return pages
    
    def _calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """Calcula estadísticas del texto"""
        if not text:
            return {
                'total_characters': 0,
                'total_words': 0,
                'total_lines': 0,
                'average_word_length': 0
            }
        
        lines = text.split('\n')
        words = text.split()
        
        total_chars = len(text)
        total_words = len(words)
        total_lines = len(lines)
        
        avg_word_length = sum(len(word) for word in words) / total_words if total_words > 0 else 0
        
        return {
            'total_characters': total_chars,
            'total_words': total_words,
            'total_lines': total_lines,
            'average_word_length': round(avg_word_length, 2)
        }
    
    def _analyze_structure(self, path: Path) -> Dict[str, Any]:
        """Analiza la estructura del PDF"""
        try:
            structure = {
                'has_bookmarks': False,
                'has_links': False,
                'has_images': False,
                'has_forms': False,
                'has_annotations': False,
                'structure_type': 'unknown'
            }
            
            # Leer archivo para analizar estructura
            with open(path, 'rb') as f:
                content = f.read(16384)  # Leer 16KB
                content_str = content.decode('utf-8', errors='ignore')
                
                # Buscar indicadores de estructura
                if '/Outlines' in content_str or '/Bookmark' in content_str:
                    structure['has_bookmarks'] = True
                
                if '/Annot' in content_str or '/Link' in content_str:
                    structure['has_links'] = True
                
                if '/XObject' in content_str and '/Image' in content_str:
                    structure['has_images'] = True
                
                if '/AcroForm' in content_str:
                    structure['has_forms'] = True
                
                if '/Annots' in content_str:
                    structure['has_annotations'] = True
                
                # Determinar tipo de estructura
                if structure['has_forms']:
                    structure['structure_type'] = 'form'
                elif structure['has_bookmarks']:
                    structure['structure_type'] = 'document'
                elif structure['has_images']:
                    structure['structure_type'] = 'presentation'
                else:
                    structure['structure_type'] = 'text'
            
            return structure
            
        except Exception as e:
            return {
                'error': f'Error analizando estructura: {str(e)}',
                'structure_type': 'unknown'
            }
    
    def _extract_forms(self, path: Path) -> Dict[str, Any]:
        """Extrae información de formularios"""
        try:
            forms = {
                'has_forms': False,
                'form_fields': [],
                'form_count': 0
            }
            
            # Leer archivo para buscar formularios
            with open(path, 'rb') as f:
                content = f.read(16384)
                content_str = content.decode('utf-8', errors='ignore')
                
                if '/AcroForm' in content_str:
                    forms['has_forms'] = True
                    
                    # Buscar campos de formulario
                    field_patterns = [
                        r'/T\s*\(([^)]+)\)',  # Nombre del campo
                        r'/FT\s*/([^\s/]+)',  # Tipo de campo
                    ]
                    
                    for pattern in field_patterns:
                        matches = re.findall(pattern, content_str)
                        for match in matches:
                            forms['form_fields'].append({
                                'name': match if 'T' in pattern else 'unknown',
                                'type': match if 'FT' in pattern else 'unknown'
                            })
                    
                    forms['form_count'] = len(forms['form_fields'])
            
            return forms
            
        except Exception as e:
            return {
                'error': f'Error extrayendo formularios: {str(e)}',
                'has_forms': False,
                'form_fields': [],
                'form_count': 0
            }
    
    def _count_pages(self, path: Path) -> int:
        """Cuenta el número de páginas del PDF"""
        try:
            with open(path, 'rb') as f:
                content = f.read(32768)  # Leer 32KB
                content_str = content.decode('utf-8', errors='ignore')
                
                # Buscar patrones de páginas
                page_patterns = [
                    r'/Count\s+(\d+)',
                    r'/Page\s+\d+\s+\d+\s+R',
                ]
                
                for pattern in page_patterns:
                    matches = re.findall(pattern, content_str)
                    if matches:
                        return int(matches[0])
                
                # Estimación basada en tamaño
                file_size = path.stat().st_size
                estimated_pages = max(1, file_size // 50000)  # ~50KB por página
                return estimated_pages
                
        except:
            return 1
    
    def _generate_summary(self, basic_info: Dict, text_content: Dict, structure: Dict) -> Dict[str, Any]:
        """Genera un resumen del procesamiento"""
        return {
            'processing_successful': True,
            'pages_processed': basic_info.get('page_count', 0),
            'text_extracted': len(text_content.get('full_text', '')) > 0,
            'text_length': len(text_content.get('full_text', '')),
            'structure_type': structure.get('structure_type', 'unknown'),
            'has_forms': structure.get('has_forms', False),
            'has_images': structure.get('has_images', False)
        }
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Retorna las características soportadas"""
        return self.supported_features.copy()
