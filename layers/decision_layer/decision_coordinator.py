"""
Coordinador de Decisión - Quinta capa del sistema

Este coordinador se encarga de:
- Orquestar el flujo entre Local Resolver, AWS Preprocessor y Result Orchestrator
- Gestionar la toma de decisiones basada en confianza
- Coordinar el enrutamiento de casos complejos a servicios AWS
- Optimizar el rendimiento del sistema de decisión
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .local_resolver import LocalResolver
from .aws_preprocessor import AWSPreprocessor
from .result_orchestrator import ResultOrchestrator


class DecisionCoordinator:
    """Coordinador de la Capa de Decisión"""

    def __init__(self, aws_region: str = 'us-east-1'):
        self.local_resolver = LocalResolver()
        self.aws_preprocessor = AWSPreprocessor(aws_region)
        self.result_orchestrator = ResultOrchestrator()
        
        # Configuración del coordinador
        self.config = {
            'enable_local_processing': True,
            'enable_aws_processing': True,
            'enable_manual_review': False,
            'confidence_threshold_high': 0.8,
            'confidence_threshold_medium': 0.6,
            'max_processing_time': 180,  # segundos
            'enable_parallel_processing': True,
            'enable_fallback_mechanism': True,
            'enable_detailed_logging': True,
            'error_recovery': True
        }
        
        # Estadísticas del coordinador
        self.stats = {
            'total_decisions': 0,
            'local_decisions': 0,
            'aws_decisions': 0,
            'manual_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'processing_times': [],
            'confidence_distribution': {
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'errors_by_component': {
                'local_resolver': 0,
                'aws_preprocessor': 0,
                'result_orchestrator': 0,
                'coordination': 0
            }
        }

    def make_decision(self, analysis_data: Dict[str, Any], 
                     confidence_score: float) -> Dict[str, Any]:
        """
        Toma una decisión basada en el análisis y la confianza
        
        Args:
            analysis_data: Datos del análisis previo
            confidence_score: Puntuación de confianza (0.0 - 1.0)
            
        Returns:
            Dict con la decisión final del sistema
        """
        start_time = time.time()
        
        try:
            # Determinar ruta de procesamiento basada en confianza
            processing_route = self._determine_processing_route(confidence_score)
            
            # Procesar según la ruta determinada
            if processing_route == 'local':
                decision_result = self._process_local_decision(analysis_data, confidence_score)
            elif processing_route == 'aws':
                decision_result = self._process_aws_decision(analysis_data, confidence_score)
            elif processing_route == 'hybrid':
                decision_result = self._process_hybrid_decision(analysis_data, confidence_score)
            else:
                decision_result = self._process_manual_decision(analysis_data, confidence_score)
            
            # Orquestar resultados finales
            final_result = self._orchestrate_final_result(decision_result)
            
            # Calcular tiempo total de procesamiento
            total_processing_time = time.time() - start_time
            self.stats['processing_times'].append(total_processing_time)
            
            # Actualizar estadísticas
            self.stats['total_decisions'] += 1
            self.stats['successful_decisions'] += 1
            self._update_confidence_distribution(confidence_score)
            
            return {
                'success': True,
                'decision_type': processing_route,
                'final_result': final_result,
                'processing_route': processing_route,
                'confidence_score': confidence_score,
                'total_processing_time': total_processing_time,
                'decision_metadata': self._generate_decision_metadata(processing_route, confidence_score)
            }
            
        except Exception as e:
            self.stats['errors_by_component']['coordination'] += 1
            self.stats['failed_decisions'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'decision_type': 'failed',
                'recommendation': 'manual_review'
            }

    def _determine_processing_route(self, confidence_score: float) -> str:
        """Determina la ruta de procesamiento basada en la confianza"""
        if confidence_score >= self.config['confidence_threshold_high']:
            return 'local'
        elif confidence_score >= self.config['confidence_threshold_medium']:
            return 'aws'
        elif self.config['enable_manual_review']:
            return 'manual'
        else:
            return 'hybrid'

    def _process_local_decision(self, analysis_data: Dict[str, Any], 
                              confidence_score: float) -> Dict[str, Any]:
        """Procesa decisión localmente"""
        try:
            local_result = self.local_resolver.resolve_high_confidence_case(
                analysis_data, confidence_score
            )
            
            if local_result['success']:
                self.stats['local_decisions'] += 1
                return {
                    'processing_type': 'local',
                    'local_result': local_result,
                    'aws_comprehend_result': None,
                    'aws_bedrock_result': None,
                    'manual_review_result': None
                }
            else:
                self.stats['errors_by_component']['local_resolver'] += 1
                # Fallback a AWS si falla el procesamiento local
                return self._process_aws_decision(analysis_data, confidence_score)
                
        except Exception as e:
            self.stats['errors_by_component']['local_resolver'] += 1
            return {
                'processing_type': 'local_failed',
                'error': str(e),
                'fallback_to_aws': True
            }

    def _process_aws_decision(self, analysis_data: Dict[str, Any], 
                            confidence_score: float) -> Dict[str, Any]:
        """Procesa decisión usando servicios AWS"""
        try:
            # Preprocesar para AWS
            preprocessed_data = self.aws_preprocessor.preprocess_for_aws(
                analysis_data, confidence_score
            )
            
            if not preprocessed_data['success']:
                self.stats['errors_by_component']['aws_preprocessor'] += 1
                return {
                    'processing_type': 'aws_failed',
                    'error': preprocessed_data['error'],
                    'fallback_to_local': True
                }
            
            # Procesar con Comprehend
            comprehend_result = self.aws_preprocessor.process_with_comprehend(preprocessed_data)
            
            # Procesar con Bedrock
            bedrock_result = self.aws_preprocessor.process_with_bedrock(preprocessed_data)
            
            self.stats['aws_decisions'] += 1
            
            return {
                'processing_type': 'aws',
                'local_result': None,
                'aws_comprehend_result': comprehend_result,
                'aws_bedrock_result': bedrock_result,
                'manual_review_result': None,
                'preprocessed_data': preprocessed_data
            }
            
        except Exception as e:
            self.stats['errors_by_component']['aws_preprocessor'] += 1
            return {
                'processing_type': 'aws_failed',
                'error': str(e),
                'fallback_to_local': True
            }

    def _process_hybrid_decision(self, analysis_data: Dict[str, Any], 
                               confidence_score: float) -> Dict[str, Any]:
        """Procesa decisión usando enfoque híbrido (local + AWS)"""
        try:
            # Intentar procesamiento local primero
            local_result = self.local_resolver.resolve_high_confidence_case(
                analysis_data, confidence_score
            )
            
            # Procesar con AWS en paralelo
            preprocessed_data = self.aws_preprocessor.preprocess_for_aws(
                analysis_data, confidence_score
            )
            
            comprehend_result = None
            bedrock_result = None
            
            if preprocessed_data['success']:
                comprehend_result = self.aws_preprocessor.process_with_comprehend(preprocessed_data)
                bedrock_result = self.aws_preprocessor.process_with_bedrock(preprocessed_data)
            
            return {
                'processing_type': 'hybrid',
                'local_result': local_result if local_result['success'] else None,
                'aws_comprehend_result': comprehend_result,
                'aws_bedrock_result': bedrock_result,
                'manual_review_result': None,
                'preprocessed_data': preprocessed_data if preprocessed_data['success'] else None
            }
            
        except Exception as e:
            self.stats['errors_by_component']['coordination'] += 1
            return {
                'processing_type': 'hybrid_failed',
                'error': str(e),
                'fallback_to_manual': True
            }

    def _process_manual_decision(self, analysis_data: Dict[str, Any], 
                               confidence_score: float) -> Dict[str, Any]:
        """Procesa decisión que requiere revisión manual"""
        try:
            # Simular revisión manual
            manual_review_result = {
                'success': True,
                'review_type': 'manual',
                'reviewer_id': 'human_reviewer_001',
                'review_timestamp': datetime.now().isoformat(),
                'confidence_score': 0.9,  # Confianza alta después de revisión manual
                'decision': 'approved_with_modifications',
                'comments': 'Documento revisado manualmente debido a baja confianza inicial',
                'recommendations': [
                    'Procesar con estándares normales',
                    'Monitorear resultados futuros',
                    'Considerar ajustes en el modelo de confianza'
                ]
            }
            
            self.stats['manual_decisions'] += 1
            
            return {
                'processing_type': 'manual',
                'local_result': None,
                'aws_comprehend_result': None,
                'aws_bedrock_result': None,
                'manual_review_result': manual_review_result
            }
            
        except Exception as e:
            return {
                'processing_type': 'manual_failed',
                'error': str(e),
                'escalation_required': True
            }

    def _orchestrate_final_result(self, decision_result: Dict[str, Any]) -> Dict[str, Any]:
        """Orquesta el resultado final usando el Result Orchestrator"""
        try:
            # Extraer resultados de diferentes fuentes
            local_result = decision_result.get('local_result')
            comprehend_result = decision_result.get('aws_comprehend_result')
            bedrock_result = decision_result.get('aws_bedrock_result')
            manual_result = decision_result.get('manual_review_result')
            
            # Orquestar resultados
            orchestrated_result = self.result_orchestrator.orchestrate_results(
                local_result=local_result,
                aws_comprehend_result=comprehend_result,
                aws_bedrock_result=bedrock_result,
                manual_review_result=manual_result
            )
            
            if not orchestrated_result['success']:
                self.stats['errors_by_component']['result_orchestrator'] += 1
            
            return orchestrated_result
            
        except Exception as e:
            self.stats['errors_by_component']['result_orchestrator'] += 1
            return {
                'success': False,
                'error': str(e),
                'orchestration_failed': True
            }

    def _update_confidence_distribution(self, confidence_score: float):
        """Actualiza la distribución de confianza"""
        if confidence_score >= self.config['confidence_threshold_high']:
            self.stats['confidence_distribution']['high'] += 1
        elif confidence_score >= self.config['confidence_threshold_medium']:
            self.stats['confidence_distribution']['medium'] += 1
        else:
            self.stats['confidence_distribution']['low'] += 1

    def _generate_decision_metadata(self, processing_route: str, 
                                  confidence_score: float) -> Dict[str, Any]:
        """Genera metadatos de la decisión"""
        return {
            'timestamp': datetime.now().isoformat(),
            'processing_route': processing_route,
            'confidence_score': confidence_score,
            'confidence_level': self._classify_confidence_level(confidence_score),
            'decision_version': '1.0',
            'config_used': {
                'confidence_threshold_high': self.config['confidence_threshold_high'],
                'confidence_threshold_medium': self.config['confidence_threshold_medium'],
                'enable_aws_processing': self.config['enable_aws_processing'],
                'enable_manual_review': self.config['enable_manual_review']
            }
        }

    def _classify_confidence_level(self, confidence_score: float) -> str:
        """Clasifica el nivel de confianza"""
        if confidence_score >= 0.9:
            return 'excellent'
        elif confidence_score >= 0.8:
            return 'high'
        elif confidence_score >= 0.6:
            return 'medium'
        elif confidence_score >= 0.4:
            return 'low'
        else:
            return 'very_low'

    def get_decision_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas del coordinador de decisión"""
        avg_processing_time = (
            sum(self.stats['processing_times']) / 
            max(len(self.stats['processing_times']), 1)
        )
        
        success_rate = (
            self.stats['successful_decisions'] / 
            max(self.stats['total_decisions'], 1)
        )
        
        # Estadísticas de componentes
        local_stats = self.local_resolver.get_resolver_stats()
        aws_stats = self.aws_preprocessor.get_preprocessor_stats()
        orchestrator_stats = self.result_orchestrator.get_orchestrator_stats()
        
        return {
            'coordinator': {
                'total_decisions': self.stats['total_decisions'],
                'successful_decisions': self.stats['successful_decisions'],
                'failed_decisions': self.stats['failed_decisions'],
                'success_rate': success_rate,
                'avg_processing_time': avg_processing_time,
                'confidence_distribution': self.stats['confidence_distribution'],
                'decision_distribution': {
                    'local': self.stats['local_decisions'],
                    'aws': self.stats['aws_decisions'],
                    'manual': self.stats['manual_decisions']
                },
                'errors_by_component': self.stats['errors_by_component']
            },
            'local_resolver': local_stats,
            'aws_preprocessor': aws_stats,
            'result_orchestrator': orchestrator_stats,
            'system_health': self._calculate_system_health()
        }

    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calcula la salud general del sistema de decisión"""
        try:
            # Calcular métricas de salud
            total_errors = sum(self.stats['errors_by_component'].values())
            total_operations = self.stats['total_decisions']
            
            error_rate = total_errors / max(total_operations, 1)
            success_rate = self.stats['successful_decisions'] / max(total_operations, 1)
            
            # Determinar estado de salud
            if success_rate >= 0.95 and error_rate <= 0.05:
                health_status = 'excellent'
            elif success_rate >= 0.90 and error_rate <= 0.10:
                health_status = 'good'
            elif success_rate >= 0.80 and error_rate <= 0.20:
                health_status = 'fair'
            else:
                health_status = 'poor'
            
            return {
                'status': health_status,
                'success_rate': success_rate,
                'error_rate': error_rate,
                'total_operations': total_operations,
                'component_errors': self.stats['errors_by_component'],
                'recommendations': self._generate_health_recommendations(health_status, error_rate)
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e)
            }

    def _generate_health_recommendations(self, health_status: str, 
                                       error_rate: float) -> List[str]:
        """Genera recomendaciones basadas en la salud del sistema"""
        recommendations = []
        
        if health_status == 'poor':
            recommendations.extend([
                'Revisar configuración de umbrales de confianza',
                'Verificar conectividad con servicios AWS',
                'Considerar aumentar recursos de procesamiento local',
                'Implementar monitoreo adicional'
            ])
        elif health_status == 'fair':
            recommendations.extend([
                'Optimizar configuración de componentes',
                'Monitorear tendencias de error',
                'Considerar ajustes menores en umbrales'
            ])
        elif health_status == 'good':
            recommendations.extend([
                'Mantener configuración actual',
                'Continuar monitoreo regular'
            ])
        else:  # excellent
            recommendations.extend([
                'Sistema funcionando óptimamente',
                'Considerar optimizaciones menores si es necesario'
            ])
        
        return recommendations

