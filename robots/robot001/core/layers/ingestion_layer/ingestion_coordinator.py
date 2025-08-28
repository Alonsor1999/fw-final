"""
Ingestion Coordinator - Coordinador de la Capa de Ingesta

Maneja el flujo completo de procesamiento de documentos en la primera capa:
1. Document Classifier
2. Format Validator  
3. Security Scanner
"""

import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from .document_classifier import DocumentClassifier
from .format_validator import FormatValidator
from .security_scanner import SecurityScanner


class IngestionCoordinator:
    """Coordinador de la Capa de Ingesta"""
    
    def __init__(self):
        self.classifier = DocumentClassifier()
        self.validator = FormatValidator()
        self.scanner = SecurityScanner()
        
        # Configuración del coordinador
        self.config = {
            'enable_logging': True,
            'stop_on_validation_error': True,
            'stop_on_security_threat': False,  # Continuar pero marcar como amenaza
            'max_processing_time': 300,  # 5 minutos máximo
            'parallel_processing': False  # Procesamiento secuencial por defecto
        }
        
        # Estadísticas de procesamiento
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'validation_errors': 0,
            'security_threats': 0,
            'processing_times': []
        }
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un documento completo a través de la Capa de Ingesta
        
        Args:
            file_path: Ruta al archivo a procesar
            
        Returns:
            Dict con resultados completos del procesamiento
        """
        start_time = time.time()
        
        try:
            # Inicializar resultado
            result = {
                'success': False,
                'file_path': file_path,
                'processing_steps': [],
                'final_status': 'failed',
                'processing_time': 0,
                'errors': [],
                'warnings': []
            }
            
            # Paso 1: Clasificación del documento
            classification_result = self._step_classification(file_path)
            result['processing_steps'].append({
                'step': 'classification',
                'status': 'completed' if classification_result.get('exists') else 'failed',
                'result': classification_result
            })
            
            if not classification_result.get('exists', False):
                result['errors'].append(f"Archivo no encontrado: {file_path}")
                result['processing_time'] = time.time() - start_time
                return result
            
            # Paso 2: Validación de formato
            document_type = classification_result.get('document_type', 'unknown')
            validation_result = self._step_validation(file_path, document_type)
            result['processing_steps'].append({
                'step': 'validation',
                'status': 'completed' if validation_result.get('valid') else 'failed',
                'result': validation_result
            })
            
            if not validation_result.get('valid', False):
                result['errors'].append(f"Error de validación: {validation_result.get('error', 'Unknown error')}")
                if self.config['stop_on_validation_error']:
                    result['processing_time'] = time.time() - start_time
                    return result
            
            # Paso 3: Escaneo de seguridad
            security_result = self._step_security_scan(file_path, document_type)
            result['processing_steps'].append({
                'step': 'security_scan',
                'status': 'completed' if security_result.get('safe') else 'threats_found',
                'result': security_result
            })
            
            if not security_result.get('safe', True):
                threats_count = security_result.get('threats_found', 0)
                result['warnings'].append(f"Amenazas de seguridad detectadas: {threats_count}")
                if self.config['stop_on_security_threat']:
                    result['errors'].append("Procesamiento detenido por amenazas de seguridad")
                    result['processing_time'] = time.time() - start_time
                    return result
            
            # Determinar estado final
            result['final_status'] = self._determine_final_status(
                classification_result, validation_result, security_result
            )
            
            # Agregar resumen ejecutivo
            result['executive_summary'] = self._generate_executive_summary(
                classification_result, validation_result, security_result
            )
            
            # Marcar como exitoso si llegamos hasta aquí
            result['success'] = True
            
            # Actualizar estadísticas
            self._update_stats(result, time.time() - start_time)
            
        except Exception as e:
            result['errors'].append(f"Error en coordinación: {str(e)}")
            result['final_status'] = 'error'
        
        result['processing_time'] = time.time() - start_time
        return result
    
    def process_multiple_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Procesa múltiples documentos
        
        Args:
            file_paths: Lista de rutas de archivos a procesar
            
        Returns:
            Dict con resultados de todos los documentos
        """
        results = {
            'total_files': len(file_paths),
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'results': [],
            'summary': {}
        }
        
        for file_path in file_paths:
            try:
                result = self.process_document(file_path)
                results['results'].append(result)
                results['processed_files'] += 1
                
                if result['success']:
                    results['successful_files'] += 1
                else:
                    results['failed_files'] += 1
                    
            except Exception as e:
                error_result = {
                    'success': False,
                    'file_path': file_path,
                    'final_status': 'error',
                    'errors': [f"Error procesando archivo: {str(e)}"]
                }
                results['results'].append(error_result)
                results['failed_files'] += 1
        
        # Generar resumen
        results['summary'] = self._generate_batch_summary(results)
        
        return results
    
    def _step_classification(self, file_path: str) -> Dict[str, Any]:
        """Ejecuta el paso de clasificación"""
        try:
            return self.classifier.classify_document(file_path)
        except Exception as e:
            return {
                'exists': False,
                'error': f"Error en clasificación: {str(e)}",
                'file_path': file_path
            }
    
    def _step_validation(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Ejecuta el paso de validación"""
        try:
            return self.validator.validate_document(file_path, document_type)
        except Exception as e:
            return {
                'valid': False,
                'error': f"Error en validación: {str(e)}",
                'file_path': file_path
            }
    
    def _step_security_scan(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Ejecuta el paso de escaneo de seguridad"""
        try:
            return self.scanner.scan_document(file_path, document_type)
        except Exception as e:
            return {
                'safe': False,
                'error': f"Error en escaneo de seguridad: {str(e)}",
                'file_path': file_path,
                'threats_found': 0
            }
    
    def _determine_final_status(self, classification: Dict, validation: Dict, security: Dict) -> str:
        """Determina el estado final del procesamiento"""
        
        # Verificar si la clasificación fue exitosa
        if not classification.get('exists', False):
            return 'file_not_found'
        
        # Verificar si la validación fue exitosa
        if not validation.get('valid', False):
            return 'validation_failed'
        
        # Verificar si hay amenazas de seguridad
        if not security.get('safe', True):
            threats_count = security.get('threats_found', 0)
            if threats_count > 0:
                return 'security_threats'
        
        return 'approved'
    
    def _generate_executive_summary(self, classification: Dict, validation: Dict, security: Dict) -> Dict[str, Any]:
        """Genera un resumen ejecutivo del procesamiento"""
        
        summary = {
            'document_type': classification.get('document_type', 'unknown'),
            'file_size': classification.get('file_size', 0),
            'file_name': classification.get('file_name', 'unknown'),
            'validation_status': 'valid' if validation.get('valid') else 'invalid',
            'security_status': 'safe' if security.get('safe') else 'threats_detected',
            'threats_count': security.get('threats_found', 0),
            'risk_level': security.get('risk_level', 'unknown'),
            'recommendation': self._generate_recommendation(classification, validation, security)
        }
        
        return summary
    
    def _generate_recommendation(self, classification: Dict, validation: Dict, security: Dict) -> str:
        """Genera una recomendación basada en los resultados"""
        
        if not classification.get('exists', False):
            return "Archivo no encontrado - verificar ruta"
        
        if not validation.get('valid', False):
            return "Archivo inválido - revisar formato y estructura"
        
        if not security.get('safe', True):
            threats_count = security.get('threats_found', 0)
            risk_level = security.get('risk_level', 'unknown')
            
            if risk_level == 'high':
                return f"ALTO RIESGO - {threats_count} amenazas críticas detectadas. NO PROCESAR."
            elif risk_level == 'medium':
                return f"RIESGO MEDIO - {threats_count} amenazas detectadas. Revisar antes de procesar."
            else:
                return f"RIESGO BAJO - {threats_count} amenazas menores. Puede procesar con precaución."
        
        return "Archivo aprobado para procesamiento"
    
    def _update_stats(self, result: Dict[str, Any], processing_time: float):
        """Actualiza las estadísticas de procesamiento"""
        self.stats['total_processed'] += 1
        self.stats['processing_times'].append(processing_time)
        
        if result['success']:
            self.stats['successful'] += 1
        else:
            self.stats['failed'] += 1
        
        # Contar errores específicos
        for step in result.get('processing_steps', []):
            if step['step'] == 'validation' and step['status'] == 'failed':
                self.stats['validation_errors'] += 1
            elif step['step'] == 'security_scan' and step['status'] == 'threats_found':
                self.stats['security_threats'] += 1
    
    def _generate_batch_summary(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen del procesamiento por lotes"""
        
        total_files = batch_results['total_files']
        successful = batch_results['successful_files']
        failed = batch_results['failed_files']
        
        # Calcular estadísticas
        success_rate = (successful / total_files * 100) if total_files > 0 else 0
        failure_rate = (failed / total_files * 100) if total_files > 0 else 0
        
        # Contar estados finales
        status_counts = {}
        for result in batch_results['results']:
            status = result.get('final_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_files': total_files,
            'successful_files': successful,
            'failed_files': failed,
            'success_rate_percent': round(success_rate, 2),
            'failure_rate_percent': round(failure_rate, 2),
            'status_breakdown': status_counts,
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
            'validation_errors': 0,
            'security_threats': 0,
            'processing_times': []
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración del coordinador"""
        self.config.update(new_config)
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna la configuración actual"""
        return self.config.copy()
