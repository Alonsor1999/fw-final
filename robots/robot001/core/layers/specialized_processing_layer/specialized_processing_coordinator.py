"""
Specialized Processing Coordinator - Coordinador de la Capa de Procesamiento Especializado

Maneja el flujo completo de procesamiento especializado de documentos en la segunda capa:
1. PDF Native Processor
2. Word Document Processor  
3. Email Processor
"""

import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .pdf_processor import PDFNativeProcessor
from .word_processor import WordDocumentProcessor
from .email_processor import EmailProcessor


class SpecializedProcessingCoordinator:
    """Coordinador de la Capa de Procesamiento Especializado"""
    
    def __init__(self):
        self.pdf_processor = PDFNativeProcessor()
        self.word_processor = WordDocumentProcessor()
        self.email_processor = EmailProcessor()
        
        # Configuración del coordinador
        self.config = {
            'enable_logging': True,
            'parallel_processing': False,  # Procesamiento secuencial por defecto
            'max_processing_time': 600,  # 10 minutos máximo
            'extract_images': False,  # Extracción de imágenes deshabilitada por defecto
            'extract_attachments': True,  # Extracción de adjuntos habilitada
            'preserve_formatting': True,  # Preservar formato
            'generate_summary': True,  # Generar resumen automático
            'error_recovery': True  # Recuperación de errores
        }
        
        # Estadísticas de procesamiento
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'pdf_processed': 0,
            'word_processed': 0,
            'email_processed': 0,
            'processing_times': [],
            'errors_by_type': {
                'pdf': 0,
                'word': 0,
                'email': 0,
                'unknown': 0
            }
        }
    
    def process_document(self, file_path: str, document_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Procesa un documento con el procesador especializado correspondiente
        
        Args:
            file_path: Ruta al archivo a procesar
            document_type: Tipo de documento (opcional, se auto-detecta si no se proporciona)
            
        Returns:
            Dict con resultados completos del procesamiento especializado
        """
        start_time = time.time()
        
        try:
            # Inicializar resultado
            result = {
                'success': False,
                'file_path': file_path,
                'document_type': document_type,
                'processor_used': None,
                'processing_time': 0,
                'errors': [],
                'warnings': [],
                'extracted_content': {},
                'processing_summary': {}
            }
            
            # Auto-detectar tipo de documento si no se proporciona
            if not document_type:
                document_type = self._detect_document_type(file_path)
                result['document_type'] = document_type
            
            # Seleccionar procesador apropiado
            processor, processor_name = self._select_processor(document_type)
            result['processor_used'] = processor_name
            
            if not processor:
                result['errors'].append(f"No se encontró procesador para el tipo: {document_type}")
                result['processing_time'] = time.time() - start_time
                return result
            
            # Procesar documento
            processing_result = self._process_with_processor(processor, file_path, document_type)
            
            if processing_result.get('success', False):
                result['success'] = True
                result['extracted_content'] = processing_result
                result['processing_summary'] = self._generate_processing_summary(processing_result, document_type)
                
                # Actualizar estadísticas específicas
                self._update_type_stats(document_type, True)
            else:
                result['errors'].append(f"Error en procesamiento: {processing_result.get('error', 'Unknown error')}")
                self._update_type_stats(document_type, False)
            
            # Actualizar estadísticas generales
            self._update_stats(result, time.time() - start_time)
            
        except Exception as e:
            result['errors'].append(f"Error en coordinación: {str(e)}")
            self._update_type_stats('unknown', False)
        
        result['processing_time'] = time.time() - start_time
        return result
    
    def process_multiple_documents(self, file_paths: List[str], document_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Procesa múltiples documentos con sus procesadores especializados correspondientes
        
        Args:
            file_paths: Lista de rutas de archivos a procesar
            document_types: Lista de tipos de documentos (opcional)
            
        Returns:
            Dict con resultados de todos los documentos
        """
        results = {
            'total_files': len(file_paths),
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'results': [],
            'summary': {},
            'type_breakdown': {
                'pdf': {'total': 0, 'successful': 0, 'failed': 0},
                'word': {'total': 0, 'successful': 0, 'failed': 0},
                'email': {'total': 0, 'successful': 0, 'failed': 0},
                'unknown': {'total': 0, 'successful': 0, 'failed': 0}
            }
        }
        
        for i, file_path in enumerate(file_paths):
            try:
                document_type = document_types[i] if document_types and i < len(document_types) else None
                result = self.process_document(file_path, document_type)
                results['results'].append(result)
                results['processed_files'] += 1
                
                # Actualizar contadores generales
                if result['success']:
                    results['successful_files'] += 1
                else:
                    results['failed_files'] += 1
                
                # Actualizar desglose por tipo
                doc_type = result.get('document_type', 'unknown')
                if doc_type in results['type_breakdown']:
                    results['type_breakdown'][doc_type]['total'] += 1
                    if result['success']:
                        results['type_breakdown'][doc_type]['successful'] += 1
                    else:
                        results['type_breakdown'][doc_type]['failed'] += 1
                else:
                    results['type_breakdown']['unknown']['total'] += 1
                    if result['success']:
                        results['type_breakdown']['unknown']['successful'] += 1
                    else:
                        results['type_breakdown']['unknown']['failed'] += 1
                        
            except Exception as e:
                error_result = {
                    'success': False,
                    'file_path': file_path,
                    'document_type': 'unknown',
                    'processor_used': None,
                    'errors': [f"Error procesando archivo: {str(e)}"]
                }
                results['results'].append(error_result)
                results['failed_files'] += 1
                results['type_breakdown']['unknown']['total'] += 1
                results['type_breakdown']['unknown']['failed'] += 1
        
        # Generar resumen
        results['summary'] = self._generate_batch_summary(results)
        
        return results
    
    def get_processor_capabilities(self) -> Dict[str, Any]:
        """
        Retorna las capacidades de todos los procesadores
        
        Returns:
            Dict con capacidades de cada procesador
        """
        return {
            'pdf_processor': self.pdf_processor.get_supported_features(),
            'word_processor': self.word_processor.get_supported_features(),
            'email_processor': self.email_processor.get_supported_features()
        }
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Retorna los formatos soportados por cada procesador
        
        Returns:
            Dict con formatos soportados
        """
        return {
            'pdf_processor': ['.pdf'],
            'word_processor': ['.doc', '.docx'],
            'email_processor': ['.eml', '.msg']
        }
    
    def _detect_document_type(self, file_path: str) -> str:
        """Detecta el tipo de documento basado en la extensión del archivo"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension in ['.pdf']:
            return 'pdf'
        elif extension in ['.doc', '.docx']:
            return 'word'
        elif extension in ['.eml', '.msg']:
            return 'email'
        else:
            return 'unknown'
    
    def _select_processor(self, document_type: str) -> tuple[Optional[Union[PDFNativeProcessor, WordDocumentProcessor, EmailProcessor]], str]:
        """Selecciona el procesador apropiado para el tipo de documento"""
        if document_type == 'pdf':
            return self.pdf_processor, 'PDFNativeProcessor'
        elif document_type == 'word':
            return self.word_processor, 'WordDocumentProcessor'
        elif document_type == 'email':
            return self.email_processor, 'EmailProcessor'
        else:
            return None, 'Unknown'
    
    def _process_with_processor(self, processor, file_path: str, document_type: str) -> Dict[str, Any]:
        """Ejecuta el procesamiento con el procesador específico"""
        try:
            if document_type == 'pdf':
                return processor.process_pdf(file_path)
            elif document_type == 'word':
                return processor.process_word_document(file_path)
            elif document_type == 'email':
                return processor.process_email(file_path)
            else:
                return {
                    'success': False,
                    'error': f'Tipo de documento no soportado: {document_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en procesamiento: {str(e)}'
            }
    
    def _generate_processing_summary(self, processing_result: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Genera un resumen del procesamiento"""
        summary = {
            'document_type': document_type,
            'processing_successful': processing_result.get('success', False),
            'content_extracted': False,
            'metadata_extracted': False,
            'structure_analyzed': False,
            'extraction_details': {}
        }
        
        if processing_result.get('success', False):
            # Extraer información específica según el tipo de documento
            if document_type == 'pdf':
                basic_info = processing_result.get('basic_info', {})
                text_content = processing_result.get('text_content', {})
                structure = processing_result.get('structure', {})
                
                summary.update({
                    'content_extracted': len(text_content.get('full_text', '')) > 0,
                    'metadata_extracted': bool(processing_result.get('metadata', {})),
                    'structure_analyzed': bool(structure),
                    'pages_count': basic_info.get('page_count', 0),
                    'file_size': basic_info.get('file_size', 0),
                    'extraction_details': {
                        'text_length': len(text_content.get('full_text', '')),
                        'has_forms': structure.get('has_forms', False),
                        'has_images': structure.get('has_images', False),
                        'structure_type': structure.get('structure_type', 'unknown')
                    }
                })
            
            elif document_type == 'word':
                basic_info = processing_result.get('basic_info', {})
                text_content = processing_result.get('text_content', {})
                structure = processing_result.get('structure', {})
                
                summary.update({
                    'content_extracted': len(text_content.get('full_text', '')) > 0,
                    'metadata_extracted': bool(processing_result.get('metadata', {})),
                    'structure_analyzed': bool(structure),
                    'paragraphs_count': len(text_content.get('paragraphs', [])),
                    'file_size': basic_info.get('file_size', 0),
                    'extraction_details': {
                        'text_length': len(text_content.get('full_text', '')),
                        'has_headers': structure.get('has_headers', False),
                        'has_footers': structure.get('has_footers', False),
                        'word_version': basic_info.get('word_version', 'unknown')
                    }
                })
            
            elif document_type == 'email':
                basic_info = processing_result.get('basic_info', {})
                body_content = processing_result.get('body_content', {})
                attachments = processing_result.get('attachments', {})
                
                summary.update({
                    'content_extracted': len(body_content.get('text_body', '')) > 0 or len(body_content.get('html_body', '')) > 0,
                    'metadata_extracted': bool(processing_result.get('headers', {})),
                    'structure_analyzed': bool(processing_result.get('structure', {})),
                    'attachments_count': attachments.get('count', 0),
                    'file_size': basic_info.get('file_size', 0),
                    'extraction_details': {
                        'text_body_length': len(body_content.get('text_body', '')),
                        'html_body_length': len(body_content.get('html_body', '')),
                        'has_attachments': attachments.get('count', 0) > 0,
                        'attachments_size': attachments.get('total_size', 0)
                    }
                })
        
        return summary
    
    def _update_stats(self, result: Dict[str, Any], processing_time: float):
        """Actualiza las estadísticas de procesamiento"""
        self.stats['total_processed'] += 1
        self.stats['processing_times'].append(processing_time)
        
        if result['success']:
            self.stats['successful'] += 1
        else:
            self.stats['failed'] += 1
    
    def _update_type_stats(self, document_type: str, success: bool):
        """Actualiza las estadísticas por tipo de documento"""
        if success:
            if document_type == 'pdf':
                self.stats['pdf_processed'] += 1
            elif document_type == 'word':
                self.stats['word_processed'] += 1
            elif document_type == 'email':
                self.stats['email_processed'] += 1
        else:
            self.stats['errors_by_type'][document_type] += 1
    
    def _generate_batch_summary(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen del procesamiento por lotes"""
        total_files = batch_results['total_files']
        successful = batch_results['successful_files']
        failed = batch_results['failed_files']
        
        # Calcular estadísticas
        success_rate = (successful / total_files * 100) if total_files > 0 else 0
        failure_rate = (failed / total_files * 100) if total_files > 0 else 0
        
        return {
            'total_files': total_files,
            'successful_files': successful,
            'failed_files': failed,
            'success_rate_percent': round(success_rate, 2),
            'failure_rate_percent': round(failure_rate, 2),
            'type_breakdown': batch_results['type_breakdown'],
            'average_processing_time': self._calculate_average_processing_time()
        }
    
    def _calculate_average_processing_time(self) -> float:
        """Calcula el tiempo promedio de procesamiento"""
        if not self.stats['processing_times']:
            return 0.0
        
        return sum(self.stats['processing_times']) / len(self.stats['processing_times'])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna las estadísticas de procesamiento"""
        stats_copy = self.stats.copy()
        
        # Calcular métricas adicionales
        if stats_copy['total_processed'] > 0:
            stats_copy['success_rate'] = (stats_copy['successful'] / stats_copy['total_processed']) * 100
            stats_copy['failure_rate'] = (stats_copy['failed'] / stats_copy['total_processed']) * 100
        else:
            stats_copy['success_rate'] = 0
            stats_copy['failure_rate'] = 0
        
        if stats_copy['processing_times']:
            stats_copy['avg_processing_time'] = sum(stats_copy['processing_times']) / len(stats_copy['processing_times'])
            stats_copy['min_processing_time'] = min(stats_copy['processing_times'])
            stats_copy['max_processing_time'] = max(stats_copy['processing_times'])
        else:
            stats_copy['avg_processing_time'] = 0
            stats_copy['min_processing_time'] = 0
            stats_copy['max_processing_time'] = 0
        
        return stats_copy
    
    def reset_statistics(self):
        """Reinicia las estadísticas"""
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'pdf_processed': 0,
            'word_processed': 0,
            'email_processed': 0,
            'processing_times': [],
            'errors_by_type': {
                'pdf': 0,
                'word': 0,
                'email': 0,
                'unknown': 0
            }
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración del coordinador"""
        self.config.update(new_config)
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna la configuración actual"""
        return self.config.copy()
    
    def validate_document_type(self, file_path: str, expected_type: str) -> bool:
        """
        Valida si un archivo corresponde al tipo esperado
        
        Args:
            file_path: Ruta al archivo
            expected_type: Tipo esperado (pdf, word, email)
            
        Returns:
            True si el tipo coincide, False en caso contrario
        """
        detected_type = self._detect_document_type(file_path)
        return detected_type == expected_type
    
    def get_processing_recommendations(self, file_path: str) -> Dict[str, Any]:
        """
        Genera recomendaciones de procesamiento para un archivo
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Dict con recomendaciones
        """
        document_type = self._detect_document_type(file_path)
        processor, processor_name = self._select_processor(document_type)
        
        recommendations = {
            'document_type': document_type,
            'processor_recommended': processor_name,
            'supported_features': processor.get_supported_features() if processor else {},
            'processing_notes': []
        }
        
        if document_type == 'pdf':
            recommendations['processing_notes'].extend([
                "Extracción de texto y metadatos disponible",
                "Análisis de estructura y formularios soportado",
                "Extracción de imágenes requiere librerías adicionales"
            ])
        elif document_type == 'word':
            recommendations['processing_notes'].extend([
                "Extracción de texto y formato disponible",
                "Análisis de estructura y estilos soportado",
                "Metadatos del documento accesibles"
            ])
        elif document_type == 'email':
            recommendations['processing_notes'].extend([
                "Extracción de headers y cuerpo disponible",
                "Análisis de adjuntos soportado",
                "Extracción de enlaces y metadatos disponible"
            ])
        else:
            recommendations['processing_notes'].append("Tipo de documento no soportado")
        
        return recommendations
