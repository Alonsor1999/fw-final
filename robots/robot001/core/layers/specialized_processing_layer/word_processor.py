"""
Word Document Processor - Procesador especializado para documentos Word
"""

import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pathlib import Path


class WordDocumentProcessor:
    """Procesador especializado para documentos Word (.doc, .docx)"""
    
    def __init__(self):
        self.supported_features = {
            'text_extraction': True,
            'formatting_extraction': True,
            'metadata_extraction': True,
            'image_extraction': False,  # Requiere librerías adicionales
            'structure_analysis': True,
            'style_extraction': True
        }
    
    def process_word_document(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un documento Word y extrae su contenido
        
        Args:
            file_path: Ruta al archivo Word
            
        Returns:
            Dict con información procesada del documento
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
                    'error': 'No es un archivo Word válido',
                    'file_path': str(path)
                }
            
            # Extraer información básica
            basic_info = self._extract_basic_info(path, file_type)
            
            # Extraer metadatos
            metadata = self._extract_metadata(path, file_type)
            
            # Extraer texto
            text_content = self._extract_text(path, file_type)
            
            # Extraer formato
            formatting = self._extract_formatting(path, file_type)
            
            # Analizar estructura
            structure = self._analyze_structure(path, file_type)
            
            # Extraer estilos
            styles = self._extract_styles(path, file_type)
            
            result = {
                'success': True,
                'file_path': str(path),
                'file_type': file_type,
                'basic_info': basic_info,
                'metadata': metadata,
                'text_content': text_content,
                'formatting': formatting,
                'structure': structure,
                'styles': styles,
                'processing_summary': self._generate_summary(basic_info, text_content, structure)
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _determine_file_type(self, path: Path) -> Optional[str]:
        """Determina el tipo de archivo Word"""
        extension = path.suffix.lower()
        
        if extension == '.docx':
            return 'docx'
        elif extension == '.doc':
            return 'doc'
        else:
            return None
    
    def _extract_basic_info(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae información básica del documento"""
        try:
            file_size = path.stat().st_size
            
            if file_type == 'docx':
                # Para DOCX, obtener información del ZIP
                with zipfile.ZipFile(path, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    return {
                        'file_size': file_size,
                        'file_type': 'DOCX',
                        'word_version': 'Word 2007+',
                        'embedded_files': len([f for f in file_list if not f.startswith('word/')]),
                        'has_content_types': 'Content_Types.xml' in file_list,
                        'has_rels': any(f.startswith('_rels/') for f in file_list)
                    }
            else:
                # Para DOC, información básica
                return {
                    'file_size': file_size,
                    'file_type': 'DOC',
                    'word_version': 'Word 97-2003',
                    'embedded_files': 0,
                    'has_content_types': False,
                    'has_rels': False
                }
                
        except Exception as e:
            return {
                'error': f'Error extrayendo información básica: {str(e)}',
                'file_size': 0,
                'file_type': file_type.upper(),
                'word_version': 'unknown'
            }
    
    def _extract_metadata(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae metadatos del documento"""
        try:
            metadata = {
                'title': None,
                'author': None,
                'subject': None,
                'keywords': None,
                'comments': None,
                'category': None,
                'manager': None,
                'company': None,
                'creation_date': None,
                'modification_date': None,
                'last_saved_by': None,
                'revision_number': None
            }
            
            if file_type == 'docx':
                # Extraer metadatos de DOCX
                with zipfile.ZipFile(path, 'r') as zip_file:
                    if 'docProps/core.xml' in zip_file.namelist():
                        core_xml = zip_file.read('docProps/core.xml')
                        metadata.update(self._parse_docx_metadata(core_xml))
                    
                    if 'docProps/app.xml' in zip_file.namelist():
                        app_xml = zip_file.read('docProps/app.xml')
                        metadata.update(self._parse_docx_app_metadata(app_xml))
            
            return metadata
            
        except Exception as e:
            return {
                'error': f'Error extrayendo metadatos: {str(e)}'
            }
    
    def _parse_docx_metadata(self, xml_content: bytes) -> Dict[str, Any]:
        """Parsea metadatos del archivo core.xml de DOCX"""
        metadata = {}
        
        try:
            root = ET.fromstring(xml_content)
            
            # Namespace para Office Open XML
            ns = {'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
                  'dc': 'http://purl.org/dc/elements/1.1/',
                  'dcterms': 'http://purl.org/dc/terms/'}
            
            # Extraer campos básicos
            fields = {
                'title': 'dc:title',
                'subject': 'dc:subject',
                'creator': 'dc:creator',
                'keywords': 'cp:keywords',
                'category': 'cp:category',
                'comments': 'cp:comments',
                'last_modified_by': 'cp:lastModifiedBy',
                'revision': 'cp:revision',
                'created': 'dcterms:created',
                'modified': 'dcterms:modified'
            }
            
            for key, xpath in fields.items():
                element = root.find(xpath, ns)
                if element is not None:
                    metadata[key] = element.text
            
        except Exception as e:
            metadata['parse_error'] = str(e)
        
        return metadata
    
    def _parse_docx_app_metadata(self, xml_content: bytes) -> Dict[str, Any]:
        """Parsea metadatos del archivo app.xml de DOCX"""
        metadata = {}
        
        try:
            root = ET.fromstring(xml_content)
            
            # Namespace para Office Open XML
            ns = {'': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}
            
            # Extraer campos de aplicación
            fields = {
                'application': 'Application',
                'doc_security': 'DocSecurity',
                'scale_crop': 'ScaleCrop',
                'links_up_to_date': 'LinksUpToDate',
                'characters_with_spaces': 'CharactersWithSpaces',
                'shared_doc': 'SharedDoc',
                'hyperlinks_changed': 'HyperlinksChanged',
                'app_version': 'AppVersion'
            }
            
            for key, xpath in fields.items():
                element = root.find(xpath, ns)
                if element is not None:
                    metadata[key] = element.text
            
        except Exception as e:
            metadata['parse_error'] = str(e)
        
        return metadata
    
    def _extract_text(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae texto del documento"""
        try:
            text_content = {
                'full_text': '',
                'paragraphs': [],
                'text_statistics': {},
                'encoding': 'utf-8'
            }
            
            if file_type == 'docx':
                # Extraer texto de DOCX
                with zipfile.ZipFile(path, 'r') as zip_file:
                    if 'word/document.xml' in zip_file.namelist():
                        doc_xml = zip_file.read('word/document.xml')
                        text_content.update(self._parse_docx_text(doc_xml))
            
            # Calcular estadísticas
            text_content['text_statistics'] = self._calculate_text_statistics(text_content['full_text'])
            
            return text_content
            
        except Exception as e:
            return {
                'error': f'Error extrayendo texto: {str(e)}',
                'full_text': '',
                'paragraphs': [],
                'text_statistics': {}
            }
    
    def _parse_docx_text(self, xml_content: bytes) -> Dict[str, Any]:
        """Parsea texto del archivo document.xml de DOCX"""
        text_content = {
            'full_text': '',
            'paragraphs': []
        }
        
        try:
            root = ET.fromstring(xml_content)
            
            # Namespace para WordprocessingML
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # Extraer párrafos
            paragraphs = root.findall('.//w:p', ns)
            
            for i, para in enumerate(paragraphs):
                para_text = self._extract_paragraph_text(para, ns)
                if para_text.strip():
                    text_content['paragraphs'].append({
                        'paragraph_number': i + 1,
                        'text': para_text,
                        'text_length': len(para_text)
                    })
            
            # Combinar todo el texto
            text_content['full_text'] = '\n'.join([p['text'] for p in text_content['paragraphs']])
            
        except Exception as e:
            text_content['parse_error'] = str(e)
        
        return text_content
    
    def _extract_paragraph_text(self, paragraph, ns) -> str:
        """Extrae texto de un párrafo"""
        text_parts = []
        
        # Buscar elementos de texto
        text_elements = paragraph.findall('.//w:t', ns)
        for text_elem in text_elements:
            if text_elem.text:
                text_parts.append(text_elem.text)
        
        return ' '.join(text_parts)
    
    def _extract_formatting(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae información de formato del documento"""
        try:
            formatting = {
                'has_bold': False,
                'has_italic': False,
                'has_underline': False,
                'has_strikethrough': False,
                'font_sizes': [],
                'font_families': [],
                'paragraph_styles': [],
                'text_colors': [],
                'alignment_types': []
            }
            
            if file_type == 'docx':
                # Extraer formato de DOCX
                with zipfile.ZipFile(path, 'r') as zip_file:
                    if 'word/document.xml' in zip_file.namelist():
                        doc_xml = zip_file.read('word/document.xml')
                        formatting.update(self._parse_docx_formatting(doc_xml))
            
            return formatting
            
        except Exception as e:
            return {
                'error': f'Error extrayendo formato: {str(e)}'
            }
    
    def _parse_docx_formatting(self, xml_content: bytes) -> Dict[str, Any]:
        """Parsea formato del archivo document.xml de DOCX"""
        formatting = {}
        
        try:
            root = ET.fromstring(xml_content)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # Buscar elementos de formato
            runs = root.findall('.//w:r', ns)
            
            for run in runs:
                # Verificar formato de texto
                rpr = run.find('w:rPr', ns)
                if rpr is not None:
                    if rpr.find('w:b', ns) is not None:
                        formatting['has_bold'] = True
                    if rpr.find('w:i', ns) is not None:
                        formatting['has_italic'] = True
                    if rpr.find('w:u', ns) is not None:
                        formatting['has_underline'] = True
                    if rpr.find('w:strike', ns) is not None:
                        formatting['has_strikethrough'] = True
                    
                    # Extraer tamaño de fuente
                    sz = rpr.find('w:sz', ns)
                    if sz is not None and sz.get('w:val'):
                        formatting['font_sizes'].append(sz.get('w:val'))
                    
                    # Extraer familia de fuente
                    rFonts = rpr.find('w:rFonts', ns)
                    if rFonts is not None and rFonts.get('w:ascii'):
                        formatting['font_families'].append(rFonts.get('w:ascii'))
            
            # Remover duplicados
            formatting['font_sizes'] = list(set(formatting['font_sizes']))
            formatting['font_families'] = list(set(formatting['font_families']))
            
        except Exception as e:
            formatting['parse_error'] = str(e)
        
        return formatting
    
    def _analyze_structure(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Analiza la estructura del documento"""
        try:
            structure = {
                'has_headers': False,
                'has_footers': False,
                'has_footnotes': False,
                'has_endnotes': False,
                'has_comments': False,
                'has_bookmarks': False,
                'has_hyperlinks': False,
                'structure_type': 'document'
            }
            
            if file_type == 'docx':
                # Analizar estructura de DOCX
                with zipfile.ZipFile(path, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    
                    if any(f.startswith('word/header') for f in file_list):
                        structure['has_headers'] = True
                    
                    if any(f.startswith('word/footer') for f in file_list):
                        structure['has_footers'] = True
                    
                    if 'word/footnotes.xml' in file_list:
                        structure['has_footnotes'] = True
                    
                    if 'word/endnotes.xml' in file_list:
                        structure['has_endnotes'] = True
                    
                    if 'word/comments.xml' in file_list:
                        structure['has_comments'] = True
                    
                    if 'word/bookmarks.xml' in file_list:
                        structure['has_bookmarks'] = True
                    
                    if 'word/_rels/document.xml.rels' in file_list:
                        structure['has_hyperlinks'] = True
            
            return structure
            
        except Exception as e:
            return {
                'error': f'Error analizando estructura: {str(e)}',
                'structure_type': 'unknown'
            }
    
    def _extract_styles(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Extrae estilos del documento"""
        try:
            styles = {
                'paragraph_styles': [],
                'character_styles': [],
                'table_styles': [],
                'list_styles': []
            }
            
            if file_type == 'docx':
                # Extraer estilos de DOCX
                with zipfile.ZipFile(path, 'r') as zip_file:
                    if 'word/styles.xml' in zip_file.namelist():
                        styles_xml = zip_file.read('word/styles.xml')
                        styles.update(self._parse_docx_styles(styles_xml))
            
            return styles
            
        except Exception as e:
            return {
                'error': f'Error extrayendo estilos: {str(e)}'
            }
    
    def _parse_docx_styles(self, xml_content: bytes) -> Dict[str, Any]:
        """Parsea estilos del archivo styles.xml de DOCX"""
        styles = {}
        
        try:
            root = ET.fromstring(xml_content)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # Extraer estilos de párrafo
            para_styles = root.findall('.//w:style[@w:type="paragraph"]', ns)
            styles['paragraph_styles'] = [style.get('w:styleId') for style in para_styles if style.get('w:styleId')]
            
            # Extraer estilos de carácter
            char_styles = root.findall('.//w:style[@w:type="character"]', ns)
            styles['character_styles'] = [style.get('w:styleId') for style in char_styles if style.get('w:styleId')]
            
            # Extraer estilos de tabla
            table_styles = root.findall('.//w:style[@w:type="table"]', ns)
            styles['table_styles'] = [style.get('w:styleId') for style in table_styles if style.get('w:styleId')]
            
        except Exception as e:
            styles['parse_error'] = str(e)
        
        return styles
    
    def _calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """Calcula estadísticas del texto"""
        if not text:
            return {
                'total_characters': 0,
                'total_words': 0,
                'total_paragraphs': 0,
                'average_word_length': 0
            }
        
        paragraphs = text.split('\n')
        words = text.split()
        
        total_chars = len(text)
        total_words = len(words)
        total_paragraphs = len([p for p in paragraphs if p.strip()])
        
        avg_word_length = sum(len(word) for word in words) / total_words if total_words > 0 else 0
        
        return {
            'total_characters': total_chars,
            'total_words': total_words,
            'total_paragraphs': total_paragraphs,
            'average_word_length': round(avg_word_length, 2)
        }
    
    def _generate_summary(self, basic_info: Dict, text_content: Dict, structure: Dict) -> Dict[str, Any]:
        """Genera un resumen del procesamiento"""
        return {
            'processing_successful': True,
            'file_type': basic_info.get('file_type', 'unknown'),
            'word_version': basic_info.get('word_version', 'unknown'),
            'text_extracted': len(text_content.get('full_text', '')) > 0,
            'text_length': len(text_content.get('full_text', '')),
            'paragraphs_count': len(text_content.get('paragraphs', [])),
            'structure_type': structure.get('structure_type', 'unknown'),
            'has_headers': structure.get('has_headers', False),
            'has_footers': structure.get('has_footers', False)
        }
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Retorna las características soportadas"""
        return self.supported_features.copy()
