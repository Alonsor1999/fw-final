"""
Orquestador de Resultados - Quinta capa del sistema

Este componente se encarga de:
- Orquestar y combinar resultados de múltiples fuentes
- Gestión de decisiones finales del sistema
- Consolidación de resultados de Local Resolver y AWS Services
- Generación de respuestas finales optimizadas
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path


class ResultOrchestrator:
    """Orquestador de resultados finales del sistema"""

    def __init__(self):
        # Configuración del orquestador
        self.config = {
            'enable_result_consolidation': True,
            'enable_confidence_weighting': True,
            'enable_quality_assessment': True,
            'enable_response_optimization': True,
            'max_processing_time': 60,  # segundos
            'enable_caching': True,
            'enable_metrics_collection': True
        }
        
        # Pesos de confianza para diferentes fuentes
        self.confidence_weights = {
            'local_resolver': 0.4,
            'aws_comprehend': 0.3,
            'aws_bedrock': 0.3,
            'manual_review': 0.8
        }
        
        # Criterios de calidad
        self.quality_criteria = {
            'completeness_threshold': 0.7,
            'accuracy_threshold': 0.8,
            'consistency_threshold': 0.75,
            'timeliness_threshold': 30  # segundos
        }
        
        # Estadísticas del orquestador
        self.stats = {
            'total_orchestrations': 0,
            'successful_orchestrations': 0,
            'failed_orchestrations': 0,
            'processing_times': [],
            'confidence_scores': [],
            'quality_scores': [],
            'source_combinations': []
        }

    def orchestrate_results(self, local_result: Dict[str, Any] = None,
                          aws_comprehend_result: Dict[str, Any] = None,
                          aws_bedrock_result: Dict[str, Any] = None,
                          manual_review_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Orquesta y combina resultados de múltiples fuentes
        
        Args:
            local_result: Resultado del Local Resolver
            aws_comprehend_result: Resultado de AWS Comprehend
            aws_bedrock_result: Resultado de AWS Bedrock
            manual_review_result: Resultado de revisión manual
            
        Returns:
            Dict con resultado final orquestado
        """
        start_time = time.time()
        
        try:
            # Recopilar todos los resultados disponibles
            available_results = self._collect_available_results(
                local_result, aws_comprehend_result, aws_bedrock_result, manual_review_result
            )
            
            if not available_results:
                return {
                    'success': False,
                    'error': 'No hay resultados disponibles para orquestar',
                    'orchestration_type': 'none'
                }
            
            # Consolidar resultados
            consolidated_result = self._consolidate_results(available_results)
            
            # Calcular confianza final ponderada
            final_confidence = self._calculate_weighted_confidence(available_results)
            
            # Evaluar calidad del resultado
            quality_assessment = self._assess_result_quality(consolidated_result, final_confidence)
            
            # Generar respuesta final optimizada
            final_response = self._generate_final_response(
                consolidated_result, final_confidence, quality_assessment
            )
            
            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)
            
            # Actualizar estadísticas
            self.stats['total_orchestrations'] += 1
            self.stats['successful_orchestrations'] += 1
            self.stats['confidence_scores'].append(final_confidence)
            self.stats['quality_scores'].append(quality_assessment['overall_score'])
            self.stats['source_combinations'].append(list(available_results.keys()))
            
            return {
                'success': True,
                'orchestration_type': 'multi_source',
                'final_result': final_response,
                'consolidated_data': consolidated_result,
                'final_confidence': final_confidence,
                'quality_assessment': quality_assessment,
                'processing_time': processing_time,
                'sources_used': list(available_results.keys()),
                'metadata': self._generate_orchestration_metadata(available_results)
            }
            
        except Exception as e:
            self.stats['failed_orchestrations'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'orchestration_type': 'failed'
            }

    def _collect_available_results(self, local_result: Dict[str, Any] = None,
                                 aws_comprehend_result: Dict[str, Any] = None,
                                 aws_bedrock_result: Dict[str, Any] = None,
                                 manual_review_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Recopila todos los resultados disponibles"""
        available_results = {}
        
        if local_result and local_result.get('success'):
            available_results['local_resolver'] = local_result
        
        if aws_comprehend_result and aws_comprehend_result.get('success'):
            available_results['aws_comprehend'] = aws_comprehend_result
        
        if aws_bedrock_result and aws_bedrock_result.get('success'):
            available_results['aws_bedrock'] = aws_bedrock_result
        
        if manual_review_result and manual_review_result.get('success'):
            available_results['manual_review'] = manual_review_result
        
        return available_results

    def _consolidate_results(self, available_results: Dict[str, Any]) -> Dict[str, Any]:
        """Consolida resultados de múltiples fuentes"""
        consolidated = {
            'entities': [],
            'insights': [],
            'recommendations': [],
            'decisions': [],
            'metadata': {},
            'confidence_scores': {},
            'processing_paths': []
        }
        
        # Consolidar entidades
        for source, result in available_results.items():
            if 'extracted_info' in result:
                entities = result['extracted_info'].get('key_entities', [])
                consolidated['entities'].extend(entities)
            
            if 'results' in result and 'entities' in result['results']:
                entities = result['results']['entities']
                consolidated['entities'].extend(entities)
        
        # Eliminar duplicados de entidades
        consolidated['entities'] = list(set(consolidated['entities']))
        
        # Consolidar insights
        for source, result in available_results.items():
            if 'results' in result and 'insights' in result['results']:
                insights = result['results']['insights']
                consolidated['insights'].extend(insights)
            
            if 'reasoning' in result:
                consolidated['insights'].append(result['reasoning'])
        
        # Consolidar recomendaciones
        for source, result in available_results.items():
            if 'results' in result and 'recommendations' in result['results']:
                recommendations = result['results']['recommendations']
                consolidated['recommendations'].extend(recommendations)
            
            if 'decision' in result:
                consolidated['decisions'].append(result['decision'])
        
        # Consolidar metadatos
        for source, result in available_results.items():
            if 'metadata' in result:
                consolidated['metadata'].update(result['metadata'])
            
            if 'processing_time' in result:
                consolidated['processing_paths'].append({
                    'source': source,
                    'processing_time': result['processing_time']
                })
        
        return consolidated

    def _calculate_weighted_confidence(self, available_results: Dict[str, Any]) -> float:
        """Calcula la confianza final ponderada"""
        if not self.config['enable_confidence_weighting']:
            # Promedio simple si no está habilitado el ponderado
            confidences = []
            for result in available_results.values():
                if 'confidence_score' in result:
                    confidences.append(result['confidence_score'])
            return sum(confidences) / len(confidences) if confidences else 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for source, result in available_results.items():
            weight = self.confidence_weights.get(source, 0.1)
            confidence = result.get('confidence_score', 0.5)
            
            weighted_sum += weight * confidence
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _assess_result_quality(self, consolidated_result: Dict[str, Any], 
                             final_confidence: float) -> Dict[str, Any]:
        """Evalúa la calidad del resultado consolidado"""
        if not self.config['enable_quality_assessment']:
            return {'overall_score': final_confidence}
        
        quality_scores = {}
        
        # Evaluar completitud
        completeness_score = self._assess_completeness(consolidated_result)
        quality_scores['completeness'] = completeness_score
        
        # Evaluar precisión
        accuracy_score = self._assess_accuracy(consolidated_result, final_confidence)
        quality_scores['accuracy'] = accuracy_score
        
        # Evaluar consistencia
        consistency_score = self._assess_consistency(consolidated_result)
        quality_scores['consistency'] = consistency_score
        
        # Evaluar puntualidad
        timeliness_score = self._assess_timeliness(consolidated_result)
        quality_scores['timeliness'] = timeliness_score
        
        # Calcular puntuación general
        overall_score = (
            completeness_score * 0.25 +
            accuracy_score * 0.35 +
            consistency_score * 0.25 +
            timeliness_score * 0.15
        )
        
        quality_scores['overall_score'] = overall_score
        
        # Determinar nivel de calidad
        if overall_score >= 0.9:
            quality_level = 'excellent'
        elif overall_score >= 0.8:
            quality_level = 'good'
        elif overall_score >= 0.7:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        quality_scores['quality_level'] = quality_level
        
        return quality_scores

    def _generate_final_response(self, consolidated_result: Dict[str, Any],
                               final_confidence: float,
                               quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Genera la respuesta final optimizada"""
        if not self.config['enable_response_optimization']:
            return {
                'entities': consolidated_result['entities'],
                'insights': consolidated_result['insights'],
                'recommendations': consolidated_result['recommendations'],
                'confidence': final_confidence
            }
        
        # Optimizar entidades
        optimized_entities = self._optimize_entities(consolidated_result['entities'])
        
        # Optimizar insights
        optimized_insights = self._optimize_insights(consolidated_result['insights'])
        
        # Optimizar recomendaciones
        optimized_recommendations = self._optimize_recommendations(
            consolidated_result['recommendations']
        )
        
        # Generar resumen ejecutivo
        executive_summary = self._generate_executive_summary(
            optimized_entities, optimized_insights, optimized_recommendations
        )
        
        # Determinar acción recomendada
        recommended_action = self._determine_recommended_action(
            optimized_recommendations, final_confidence, quality_assessment
        )
        
        return {
            'executive_summary': executive_summary,
            'entities': optimized_entities,
            'insights': optimized_insights,
            'recommendations': optimized_recommendations,
            'recommended_action': recommended_action,
            'confidence': final_confidence,
            'quality_level': quality_assessment.get('quality_level', 'unknown'),
            'processing_metadata': {
                'sources_used': len(consolidated_result.get('processing_paths', [])),
                'total_entities': len(optimized_entities),
                'total_insights': len(optimized_insights),
                'total_recommendations': len(optimized_recommendations)
            }
        }

    def _assess_completeness(self, consolidated_result: Dict[str, Any]) -> float:
        """Evalúa la completitud del resultado"""
        completeness_factors = []
        
        # Factor por entidades
        entity_count = len(consolidated_result.get('entities', []))
        if entity_count >= 10:
            completeness_factors.append(1.0)
        elif entity_count >= 5:
            completeness_factors.append(0.8)
        elif entity_count >= 2:
            completeness_factors.append(0.6)
        else:
            completeness_factors.append(0.3)
        
        # Factor por insights
        insight_count = len(consolidated_result.get('insights', []))
        if insight_count >= 5:
            completeness_factors.append(1.0)
        elif insight_count >= 3:
            completeness_factors.append(0.8)
        elif insight_count >= 1:
            completeness_factors.append(0.6)
        else:
            completeness_factors.append(0.2)
        
        # Factor por recomendaciones
        recommendation_count = len(consolidated_result.get('recommendations', []))
        if recommendation_count >= 3:
            completeness_factors.append(1.0)
        elif recommendation_count >= 1:
            completeness_factors.append(0.7)
        else:
            completeness_factors.append(0.3)
        
        return sum(completeness_factors) / len(completeness_factors)

    def _assess_accuracy(self, consolidated_result: Dict[str, Any], 
                        final_confidence: float) -> float:
        """Evalúa la precisión del resultado"""
        # La precisión se basa principalmente en la confianza final
        base_accuracy = final_confidence
        
        # Ajustar por consistencia de fuentes
        source_count = len(consolidated_result.get('processing_paths', []))
        if source_count >= 3:
            source_boost = 0.1
        elif source_count >= 2:
            source_boost = 0.05
        else:
            source_boost = 0.0
        
        return min(base_accuracy + source_boost, 1.0)

    def _assess_consistency(self, consolidated_result: Dict[str, Any]) -> float:
        """Evalúa la consistencia del resultado"""
        # Simular evaluación de consistencia
        consistency_score = 0.8  # Base
        
        # Ajustar por número de fuentes (más fuentes = más consistencia)
        source_count = len(consolidated_result.get('processing_paths', []))
        if source_count >= 3:
            consistency_score += 0.15
        elif source_count >= 2:
            consistency_score += 0.1
        
        return min(consistency_score, 1.0)

    def _assess_timeliness(self, consolidated_result: Dict[str, Any]) -> float:
        """Evalúa la puntualidad del resultado"""
        processing_paths = consolidated_result.get('processing_paths', [])
        
        if not processing_paths:
            return 0.5  # Valor por defecto
        
        total_time = sum(path.get('processing_time', 0) for path in processing_paths)
        
        if total_time <= self.quality_criteria['timeliness_threshold']:
            return 1.0
        elif total_time <= self.quality_criteria['timeliness_threshold'] * 2:
            return 0.8
        elif total_time <= self.quality_criteria['timeliness_threshold'] * 3:
            return 0.6
        else:
            return 0.4

    def _optimize_entities(self, entities: List[str]) -> List[str]:
        """Optimiza la lista de entidades"""
        if not entities:
            return []
        
        # Eliminar duplicados y entidades vacías
        optimized = list(set([entity.strip() for entity in entities if entity.strip()]))
        
        # Limitar a las entidades más relevantes
        return optimized[:20]

    def _optimize_insights(self, insights: List[str]) -> List[str]:
        """Optimiza la lista de insights"""
        if not insights:
            return []
        
        # Eliminar duplicados y insights vacíos
        optimized = list(set([insight.strip() for insight in insights if insight.strip()]))
        
        # Limitar a los insights más relevantes
        return optimized[:10]

    def _optimize_recommendations(self, recommendations: List[str]) -> List[str]:
        """Optimiza la lista de recomendaciones"""
        if not recommendations:
            return []
        
        # Eliminar duplicados y recomendaciones vacías
        optimized = list(set([rec.strip() for rec in recommendations if rec.strip()]))
        
        # Limitar a las recomendaciones más importantes
        return optimized[:5]

    def _generate_executive_summary(self, entities: List[str], 
                                  insights: List[str], 
                                  recommendations: List[str]) -> str:
        """Genera un resumen ejecutivo"""
        summary_parts = []
        
        # Resumen de entidades clave
        if entities:
            entity_summary = f"Identificadas {len(entities)} entidades clave"
            if len(entities) <= 5:
                entity_summary += f": {', '.join(entities)}"
            summary_parts.append(entity_summary)
        
        # Resumen de insights principales
        if insights:
            insight_summary = f"Generados {len(insights)} insights principales"
            summary_parts.append(insight_summary)
        
        # Resumen de recomendaciones
        if recommendations:
            recommendation_summary = f"Proporcionadas {len(recommendations)} recomendaciones"
            summary_parts.append(recommendation_summary)
        
        if summary_parts:
            return ". ".join(summary_parts) + "."
        else:
            return "Análisis completado con resultados básicos."

    def _determine_recommended_action(self, recommendations: List[str],
                                    final_confidence: float,
                                    quality_assessment: Dict[str, Any]) -> str:
        """Determina la acción recomendada final"""
        quality_level = quality_assessment.get('quality_level', 'unknown')
        
        if final_confidence >= 0.9 and quality_level in ['excellent', 'good']:
            return 'proceed_with_confidence'
        elif final_confidence >= 0.7 and quality_level in ['good', 'fair']:
            return 'proceed_with_caution'
        elif final_confidence >= 0.5:
            return 'require_human_review'
        else:
            return 'reprocess_or_escalate'

    def _generate_orchestration_metadata(self, available_results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera metadatos de la orquestación"""
        return {
            'timestamp': datetime.now().isoformat(),
            'sources_count': len(available_results),
            'sources_list': list(available_results.keys()),
            'orchestration_version': '1.0',
            'config_used': self.config
        }

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del orquestador"""
        avg_processing_time = (
            sum(self.stats['processing_times']) / 
            max(len(self.stats['processing_times']), 1)
        )
        
        avg_confidence = (
            sum(self.stats['confidence_scores']) / 
            max(len(self.stats['confidence_scores']), 1)
        )
        
        avg_quality = (
            sum(self.stats['quality_scores']) / 
            max(len(self.stats['quality_scores']), 1)
        )
        
        success_rate = (
            self.stats['successful_orchestrations'] / 
            max(self.stats['total_orchestrations'], 1)
        )
        
        return {
            'total_orchestrations': self.stats['total_orchestrations'],
            'successful_orchestrations': self.stats['successful_orchestrations'],
            'failed_orchestrations': self.stats['failed_orchestrations'],
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'avg_confidence_score': avg_confidence,
            'avg_quality_score': avg_quality,
            'source_combination_frequency': self._get_source_combination_frequency(),
            'config': self.config
        }

    def _get_source_combination_frequency(self) -> Dict[str, int]:
        """Obtiene la frecuencia de combinaciones de fuentes"""
        frequency = {}
        for combination in self.stats['source_combinations']:
            combination_key = '+'.join(sorted(combination))
            frequency[combination_key] = frequency.get(combination_key, 0) + 1
        return frequency
