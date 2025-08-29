"""
Analysis Extraction Coordinator - Coordinador de la Capa de Análisis y Extracción

Maneja el flujo completo de análisis y extracción de datos en la tercera capa:
1. Data Extractor
2. Content Analyzer  
3. Information Synthesizer
"""

import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .data_extractor import DataExtractor
from .content_analyzer import ContentAnalyzer
from .information_synthesizer import InformationSynthesizer


class AnalysisExtractionCoordinator:
    """Coordinador de la Capa de Análisis y Extracción de Datos"""
    
    def __init__(self):
        self.data_extractor = DataExtractor()
        self.content_analyzer = ContentAnalyzer()
        self.information_synthesizer = InformationSynthesizer()
        
        # Configuración del coordinador
        self.config = {
            'enable_parallel_processing': False,  # Procesamiento secuencial por defecto
            'enable_caching': True,  # Habilitar caché de resultados
            'max_processing_time': 300,  # 5 minutos máximo
            'enable_quality_validation': True,  # Validación de calidad
            'enable_insight_generation': True,  # Generación de insights
            'enable_recommendation_engine': True,  # Motor de recomendaciones
            'enable_detailed_logging': True,  # Logging detallado
            'error_recovery': True  # Recuperación de errores
        }
        
        # Estadísticas de procesamiento
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'extraction_success': 0,
            'analysis_success': 0,
            'synthesis_success': 0,
            'processing_times': [],
            'errors_by_component': {
                'extraction': 0,
                'analysis': 0,
                'synthesis': 0,
                'coordination': 0
            }
        }
        
        # Caché de resultados
        self.result_cache = {}
    
    def process_document(self, processed_content: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """
        Procesa un documento a través de toda la cadena de análisis y extracción
        
        Args:
            processed_content: Contenido procesado de las capas anteriores
            document_type: Tipo de documento (pdf, word, email)
            
        Returns:
            Dict con resultados completos del análisis y extracción
        """
        start_time = time.time()
        
        try:
            # Inicializar resultado
            result = {
                'success': False,
                'document_type': document_type,
                'processing_time': 0,
                'component_results': {},
                'final_synthesis': {},
                'errors': [],
                'warnings': [],
                'processing_summary': {}
            }
            
            # Verificar contenido de entrada
            if not processed_content or not isinstance(processed_content, dict):
                result['errors'].append('Contenido de entrada inválido')
                result['processing_time'] = time.time() - start_time
                return result
            
            # Paso 1: Extracción de datos
            extraction_result = self._execute_data_extraction(processed_content, document_type)
            result['component_results']['extraction'] = extraction_result
            
            if not extraction_result.get('success', False):
                result['errors'].append(f"Error en extracción: {extraction_result.get('error', 'Unknown error')}")
                self._update_component_stats('extraction', False)
            else:
                self._update_component_stats('extraction', True)
            
            # Paso 2: Análisis de contenido
            analysis_result = self._execute_content_analysis(processed_content, document_type)
            result['component_results']['analysis'] = analysis_result
            
            if not analysis_result.get('success', False):
                result['errors'].append(f"Error en análisis: {analysis_result.get('error', 'Unknown error')}")
                self._update_component_stats('analysis', False)
            else:
                self._update_component_stats('analysis', True)
            
            # Paso 3: Síntesis de información
            if extraction_result.get('success', False) and analysis_result.get('success', False):
                synthesis_result = self._execute_information_synthesis(
                    extraction_result, analysis_result, document_type
                )
                result['component_results']['synthesis'] = synthesis_result
                result['final_synthesis'] = synthesis_result
                
                if not synthesis_result.get('success', False):
                    result['errors'].append(f"Error en síntesis: {synthesis_result.get('error', 'Unknown error')}")
                    self._update_component_stats('synthesis', False)
                else:
                    self._update_component_stats('synthesis', True)
                    result['success'] = True
            else:
                result['errors'].append("No se pudo realizar la síntesis debido a errores en componentes anteriores")
                self._update_component_stats('synthesis', False)
            
            # Generar resumen de procesamiento
            result['processing_summary'] = self._generate_processing_summary(result)
            
            # Actualizar estadísticas generales
            self._update_stats(result, time.time() - start_time)
            
        except Exception as e:
            result['errors'].append(f"Error en coordinación: {str(e)}")
            self._update_component_stats('coordination', False)
        
        result['processing_time'] = time.time() - start_time
        return result
    
    def process_multiple_documents(self, documents_data: List[Dict[str, Any]], 
                                 document_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Procesa múltiples documentos a través de la cadena de análisis y extracción
        
        Args:
            documents_data: Lista de contenidos procesados de documentos
            document_types: Lista de tipos de documentos (opcional)
            
        Returns:
            Dict con resultados de todos los documentos
        """
        results = {
            'total_documents': len(documents_data),
            'processed_documents': 0,
            'successful_documents': 0,
            'failed_documents': 0,
            'results': [],
            'summary': {},
            'type_breakdown': {
                'pdf': {'total': 0, 'successful': 0, 'failed': 0},
                'word': {'total': 0, 'successful': 0, 'failed': 0},
                'email': {'total': 0, 'successful': 0, 'failed': 0},
                'unknown': {'total': 0, 'successful': 0, 'failed': 0}
            }
        }
        
        for i, document_data in enumerate(documents_data):
            try:
                document_type = document_types[i] if document_types and i < len(document_types) else 'unknown'
                result = self.process_document(document_data, document_type)
                results['results'].append(result)
                results['processed_documents'] += 1
                
                # Actualizar contadores generales
                if result['success']:
                    results['successful_documents'] += 1
                else:
                    results['failed_documents'] += 1
                
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
                    'document_type': 'unknown',
                    'errors': [f"Error procesando documento: {str(e)}"]
                }
                results['results'].append(error_result)
                results['failed_documents'] += 1
                results['type_breakdown']['unknown']['total'] += 1
                results['type_breakdown']['unknown']['failed'] += 1
        
        # Generar resumen
        results['summary'] = self._generate_batch_summary(results)
        
        return results
    
    def _execute_data_extraction(self, processed_content: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Ejecuta la extracción de datos"""
        try:
            return self.data_extractor.extract_data(processed_content, document_type)
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en extracción de datos: {str(e)}'
            }
    
    def _execute_content_analysis(self, processed_content: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Ejecuta el análisis de contenido"""
        try:
            return self.content_analyzer.analyze_content(processed_content, document_type)
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en análisis de contenido: {str(e)}'
            }
    
    def _execute_information_synthesis(self, extraction_result: Dict[str, Any], 
                                     analysis_result: Dict[str, Any], 
                                     document_type: str) -> Dict[str, Any]:
        """Ejecuta la síntesis de información"""
        try:
            return self.information_synthesizer.synthesize_information(
                extraction_result, analysis_result, document_type
            )
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en síntesis de información: {str(e)}'
            }
    
    def _generate_processing_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen del procesamiento"""
        summary = {
            'processing_success': result['success'],
            'components_executed': 3,
            'components_successful': 0,
            'components_failed': 0,
            'total_errors': len(result['errors']),
            'total_warnings': len(result['warnings']),
            'processing_time': result['processing_time']
        }
        
        # Contar componentes exitosos
        component_results = result.get('component_results', {})
        for component, component_result in component_results.items():
            if component_result.get('success', False):
                summary['components_successful'] += 1
            else:
                summary['components_failed'] += 1
        
        return summary
    
    def _update_stats(self, result: Dict[str, Any], processing_time: float):
        """Actualiza las estadísticas de procesamiento"""
        self.stats['total_processed'] += 1
        self.stats['processing_times'].append(processing_time)
        
        if result['success']:
            self.stats['successful'] += 1
        else:
            self.stats['failed'] += 1
    
    def _update_component_stats(self, component: str, success: bool):
        """Actualiza las estadísticas por componente"""
        if success:
            if component == 'extraction':
                self.stats['extraction_success'] += 1
            elif component == 'analysis':
                self.stats['analysis_success'] += 1
            elif component == 'synthesis':
                self.stats['synthesis_success'] += 1
        else:
            self.stats['errors_by_component'][component] += 1
    
    def _generate_batch_summary(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen del procesamiento por lotes"""
        total_docs = batch_results['total_documents']
        successful = batch_results['successful_documents']
        failed = batch_results['failed_documents']
        
        # Calcular estadísticas
        success_rate = (successful / total_docs * 100) if total_docs > 0 else 0
        failure_rate = (failed / total_docs * 100) if total_docs > 0 else 0
        
        return {
            'total_documents': total_docs,
            'successful_documents': successful,
            'failed_documents': failed,
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
    
    def get_component_capabilities(self) -> Dict[str, Any]:
        """
        Retorna las capacidades de todos los componentes
        
        Returns:
            Dict con capacidades de cada componente
        """
        return {
            'data_extractor': {
                'extraction_patterns': self.data_extractor.get_extraction_patterns(),
                'entity_types': self.data_extractor.entity_types
            },
            'content_analyzer': {
                'analysis_config': self.content_analyzer.get_analysis_config(),
                'content_categories': self.content_analyzer.content_categories,
                'sentiment_words': list(self.content_analyzer.sentiment_words.keys())
            },
            'information_synthesizer': {
                'synthesis_config': self.information_synthesizer.get_synthesis_config(),
                'information_patterns': self.information_synthesizer.information_patterns,
                'insight_types': self.information_synthesizer.insight_types
            }
        }
    
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
            'extraction_success': 0,
            'analysis_success': 0,
            'synthesis_success': 0,
            'processing_times': [],
            'errors_by_component': {
                'extraction': 0,
                'analysis': 0,
                'synthesis': 0,
                'coordination': 0
            }
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración del coordinador"""
        self.config.update(new_config)
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna la configuración actual"""
        return self.config.copy()
    
    def clear_cache(self):
        """Limpia el caché de resultados"""
        self.result_cache.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Retorna información del caché"""
        return {
            'cache_size': len(self.result_cache),
            'cache_enabled': self.config.get('enable_caching', True)
        }
    
    def validate_processing_chain(self) -> Dict[str, Any]:
        """
        Valida que todos los componentes estén funcionando correctamente
        
        Returns:
            Dict con estado de validación de cada componente
        """
        validation_result = {
            'overall_status': 'unknown',
            'components_status': {},
            'validation_details': {}
        }
        
        # Validar Data Extractor
        try:
            test_patterns = self.data_extractor.get_extraction_patterns()
            validation_result['components_status']['data_extractor'] = 'healthy'
            validation_result['validation_details']['data_extractor'] = f"Patterns available: {len(test_patterns)}"
        except Exception as e:
            validation_result['components_status']['data_extractor'] = 'error'
            validation_result['validation_details']['data_extractor'] = f"Error: {str(e)}"
        
        # Validar Content Analyzer
        try:
            test_config = self.content_analyzer.get_analysis_config()
            validation_result['components_status']['content_analyzer'] = 'healthy'
            validation_result['validation_details']['content_analyzer'] = f"Config available: {len(test_config)} settings"
        except Exception as e:
            validation_result['components_status']['content_analyzer'] = 'error'
            validation_result['validation_details']['content_analyzer'] = f"Error: {str(e)}"
        
        # Validar Information Synthesizer
        try:
            test_config = self.information_synthesizer.get_synthesis_config()
            validation_result['components_status']['information_synthesizer'] = 'healthy'
            validation_result['validation_details']['information_synthesizer'] = f"Config available: {len(test_config)} settings"
        except Exception as e:
            validation_result['components_status']['information_synthesizer'] = 'error'
            validation_result['validation_details']['information_synthesizer'] = f"Error: {str(e)}"
        
        # Determinar estado general
        healthy_components = sum(1 for status in validation_result['components_status'].values() if status == 'healthy')
        total_components = len(validation_result['components_status'])
        
        if healthy_components == total_components:
            validation_result['overall_status'] = 'healthy'
        elif healthy_components > 0:
            validation_result['overall_status'] = 'partial'
        else:
            validation_result['overall_status'] = 'error'
        
        return validation_result
