"""
Information Synthesizer - Sintetizador de información

Componente de la tercera capa que se encarga de sintetizar y consolidar
toda la información extraída y analizada de los documentos.
"""

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from collections import defaultdict


class InformationSynthesizer:
    """Sintetizador de información de documentos"""
    
    def __init__(self):
        self.synthesis_config = {
            'enable_cross_reference': True,
            'enable_pattern_recognition': True,
            'enable_insight_generation': True,
            'enable_summary_creation': True,
            'enable_recommendation_engine': True,
            'max_insights': 10,
            'max_recommendations': 5
        }
        
        # Patrones de información predefinidos
        self.information_patterns = {
            'contact_patterns': ['email', 'phone', 'address', 'name'],
            'financial_patterns': ['currency', 'amount', 'price', 'cost', 'budget'],
            'temporal_patterns': ['date', 'time', 'deadline', 'schedule'],
            'technical_patterns': ['url', 'ip', 'code', 'system', 'api'],
            'business_patterns': ['contract', 'agreement', 'proposal', 'meeting']
        }
        
        # Tipos de insights
        self.insight_types = {
            'data_quality': 'Calidad de datos extraídos',
            'content_analysis': 'Análisis de contenido',
            'pattern_detection': 'Detección de patrones',
            'anomaly_detection': 'Detección de anomalías',
            'trend_analysis': 'Análisis de tendencias',
            'recommendation': 'Recomendaciones'
        }
    
    def synthesize_information(self, extraction_result: Dict[str, Any], 
                             analysis_result: Dict[str, Any], 
                             document_type: str) -> Dict[str, Any]:
        """
        Sintetiza toda la información extraída y analizada
        
        Args:
            extraction_result: Resultado de la extracción de datos
            analysis_result: Resultado del análisis de contenido
            document_type: Tipo de documento
            
        Returns:
            Dict con información sintetizada
        """
        try:
            result = {
                'success': False,
                'synthesized_data': {},
                'cross_references': {},
                'patterns_detected': {},
                'insights_generated': {},
                'recommendations': {},
                'consolidated_summary': {},
                'synthesis_metadata': {}
            }
            
            # Verificar que ambos resultados sean exitosos
            if not extraction_result.get('success', False) or not analysis_result.get('success', False):
                result['error'] = 'Los resultados de extracción o análisis no son válidos'
                return result
            
            # Sintetizar datos extraídos
            result['synthesized_data'] = self._synthesize_extracted_data(extraction_result, document_type)
            
            # Crear referencias cruzadas
            if self.synthesis_config['enable_cross_reference']:
                result['cross_references'] = self._create_cross_references(extraction_result, analysis_result)
            
            # Detectar patrones
            if self.synthesis_config['enable_pattern_recognition']:
                result['patterns_detected'] = self._detect_patterns(extraction_result, analysis_result)
            
            # Generar insights
            if self.synthesis_config['enable_insight_generation']:
                result['insights_generated'] = self._generate_insights(extraction_result, analysis_result)
            
            # Crear resumen consolidado
            if self.synthesis_config['enable_summary_creation']:
                result['consolidated_summary'] = self._create_consolidated_summary(
                    extraction_result, analysis_result, result
                )
            
            # Generar recomendaciones
            if self.synthesis_config['enable_recommendation_engine']:
                result['recommendations'] = self._generate_recommendations(
                    extraction_result, analysis_result, result
                )
            
            # Agregar metadatos de síntesis
            result['synthesis_metadata'] = self._create_synthesis_metadata(result)
            
            result['success'] = True
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en síntesis de información: {str(e)}'
            }
    
    def _synthesize_extracted_data(self, extraction_result: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Sintetiza los datos extraídos"""
        synthesized_data = {
            'document_profile': {},
            'entity_summary': {},
            'data_quality_assessment': {},
            'content_overview': {},
            'extraction_highlights': {}
        }
        
        # Perfil del documento
        extracted_data = extraction_result.get('extracted_data', {})
        entities = extraction_result.get('entities_found', {})
        
        synthesized_data['document_profile'] = {
            'document_type': document_type,
            'total_entities': sum(entity.get('count', 0) for entity in entities.values()),
            'entity_types': list(entities.keys()),
            'has_contact_info': bool(extracted_data.get('contact_info', {}).get('emails') or 
                                   extracted_data.get('contact_info', {}).get('phones')),
            'has_financial_data': bool(extracted_data.get('financial_data', {}).get('currencies') or 
                                     extracted_data.get('financial_data', {}).get('amounts')),
            'has_technical_data': bool(extracted_data.get('technical_data', {}).get('urls') or 
                                     extracted_data.get('technical_data', {}).get('dates'))
        }
        
        # Resumen de entidades
        entity_summary = {}
        for entity_type, entity_data in entities.items():
            entity_summary[entity_type] = {
                'count': entity_data.get('count', 0),
                'sample_values': entity_data.get('values', [])[:3]  # Primeros 3 valores
            }
        synthesized_data['entity_summary'] = entity_summary
        
        # Evaluación de calidad de datos
        data_quality = extraction_result.get('data_quality', {})
        synthesized_data['data_quality_assessment'] = {
            'overall_score': data_quality.get('overall_score', 0.0),
            'completeness': data_quality.get('completeness', 0.0),
            'accuracy': data_quality.get('accuracy', 0.0),
            'consistency': data_quality.get('consistency', 0.0),
            'uniqueness': data_quality.get('uniqueness', 0.0)
        }
        
        # Resumen de contenido
        metadata = extracted_data.get('metadata', {})
        synthesized_data['content_overview'] = {
            'text_length': metadata.get('text_length', 0),
            'word_count': metadata.get('word_count', 0),
            'detected_language': metadata.get('detected_language', 'unknown'),
            'extraction_timestamp': metadata.get('extraction_timestamp', '')
        }
        
        # Puntos destacados de la extracción
        highlights = []
        if entities.get('emails'):
            highlights.append(f"Se encontraron {entities['emails']['count']} direcciones de email")
        if entities.get('phones'):
            highlights.append(f"Se encontraron {entities['phones']['count']} números de teléfono")
        if entities.get('dates'):
            highlights.append(f"Se encontraron {entities['dates']['count']} fechas")
        if entities.get('urls'):
            highlights.append(f"Se encontraron {entities['urls']['count']} URLs")
        
        synthesized_data['extraction_highlights'] = highlights
        
        return synthesized_data
    
    def _create_cross_references(self, extraction_result: Dict[str, Any], 
                                analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Crea referencias cruzadas entre extracción y análisis"""
        cross_references = {
            'sentiment_entities': {},
            'topic_entities': {},
            'quality_insights': {},
            'content_patterns': {}
        }
        
        # Relacionar entidades con sentimiento
        entities = extraction_result.get('entities_found', {})
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        
        sentiment_entities = {}
        for entity_type, entity_data in entities.items():
            entity_values = entity_data.get('values', [])
            sentiment_entities[entity_type] = {
                'count': entity_data.get('count', 0),
                'sentiment_context': sentiment_analysis.get('overall_sentiment', 'neutral'),
                'sentiment_confidence': sentiment_analysis.get('confidence', 0.0)
            }
        cross_references['sentiment_entities'] = sentiment_entities
        
        # Relacionar entidades con temas
        topic_analysis = analysis_result.get('topic_analysis', {})
        topic_entities = {}
        for entity_type, entity_data in entities.items():
            main_topics = topic_analysis.get('main_topics', [])
            topic_entities[entity_type] = {
                'count': entity_data.get('count', 0),
                'related_topics': main_topics[:2] if main_topics else []
            }
        cross_references['topic_entities'] = topic_entities
        
        # Insights de calidad
        data_quality = extraction_result.get('data_quality', {})
        readability = analysis_result.get('readability_analysis', {})
        
        cross_references['quality_insights'] = {
            'data_quality_score': data_quality.get('overall_score', 0.0),
            'readability_level': readability.get('readability_level', 'unknown'),
            'readability_score': readability.get('readability_score', 0.0),
            'quality_assessment': self._assess_overall_quality(data_quality, readability)
        }
        
        # Patrones de contenido
        content_patterns = {}
        for pattern_type, pattern_keywords in self.information_patterns.items():
            pattern_matches = []
            for keyword in pattern_keywords:
                if keyword in entities:
                    pattern_matches.append(keyword)
            content_patterns[pattern_type] = pattern_matches
        
        cross_references['content_patterns'] = content_patterns
        
        return cross_references
    
    def _detect_patterns(self, extraction_result: Dict[str, Any], 
                        analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta patrones en la información"""
        patterns_detected = {
            'information_patterns': {},
            'content_patterns': {},
            'quality_patterns': {},
            'anomaly_patterns': {}
        }
        
        entities = extraction_result.get('entities_found', {})
        
        # Patrones de información
        for pattern_type, pattern_keywords in self.information_patterns.items():
            pattern_data = {}
            for keyword in pattern_keywords:
                if keyword in entities:
                    pattern_data[keyword] = {
                        'count': entities[keyword].get('count', 0),
                        'values': entities[keyword].get('values', [])[:5]  # Primeros 5 valores
                    }
            if pattern_data:
                patterns_detected['information_patterns'][pattern_type] = pattern_data
        
        # Patrones de contenido
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        topic_analysis = analysis_result.get('topic_analysis', {})
        readability_analysis = analysis_result.get('readability_analysis', {})
        
        patterns_detected['content_patterns'] = {
            'sentiment_pattern': {
                'overall_sentiment': sentiment_analysis.get('overall_sentiment', 'neutral'),
                'sentiment_words_found': sum(len(words) for words in sentiment_analysis.get('sentiment_words', {}).values())
            },
            'topic_pattern': {
                'main_topics': topic_analysis.get('main_topics', []),
                'topic_distribution': topic_analysis.get('topic_distribution', {})
            },
            'readability_pattern': {
                'readability_level': readability_analysis.get('readability_level', 'unknown'),
                'complexity_indicators': {
                    'avg_sentence_length': readability_analysis.get('metrics', {}).get('average_sentence_length', 0.0),
                    'complex_word_ratio': readability_analysis.get('metrics', {}).get('complex_word_ratio', 0.0)
                }
            }
        }
        
        # Patrones de calidad
        data_quality = extraction_result.get('data_quality', {})
        patterns_detected['quality_patterns'] = {
            'quality_distribution': {
                'completeness': data_quality.get('completeness', 0.0),
                'accuracy': data_quality.get('accuracy', 0.0),
                'consistency': data_quality.get('consistency', 0.0),
                'uniqueness': data_quality.get('uniqueness', 0.0)
            },
            'quality_level': self._determine_quality_level(data_quality.get('overall_score', 0.0))
        }
        
        # Patrones de anomalías
        patterns_detected['anomaly_patterns'] = self._detect_anomalies(extraction_result, analysis_result)
        
        return patterns_detected
    
    def _detect_anomalies(self, extraction_result: Dict[str, Any], 
                         analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta anomalías en los datos"""
        anomalies = {
            'data_anomalies': [],
            'content_anomalies': [],
            'quality_anomalies': []
        }
        
        # Anomalías en datos
        entities = extraction_result.get('entities_found', {})
        if entities.get('credit_cards') and entities['credit_cards']['count'] > 0:
            anomalies['data_anomalies'].append("Se detectaron números de tarjeta de crédito")
        
        if entities.get('social_security') and entities['social_security']['count'] > 0:
            anomalies['data_anomalies'].append("Se detectaron números de seguridad social")
        
        # Anomalías en contenido
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        if sentiment_analysis.get('overall_sentiment') == 'negative':
            anomalies['content_anomalies'].append("Contenido con sentimiento negativo detectado")
        
        readability_analysis = analysis_result.get('readability_analysis', {})
        if readability_analysis.get('readability_level') in ['very_difficult', 'difficult']:
            anomalies['content_anomalies'].append("Documento con alta complejidad de lectura")
        
        # Anomalías de calidad
        data_quality = extraction_result.get('data_quality', {})
        if data_quality.get('overall_score', 0.0) < 0.5:
            anomalies['quality_anomalies'].append("Baja calidad general de datos extraídos")
        
        if data_quality.get('completeness', 0.0) < 0.3:
            anomalies['quality_anomalies'].append("Extracción incompleta de datos")
        
        return anomalies
    
    def _generate_insights(self, extraction_result: Dict[str, Any], 
                          analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Genera insights basados en la información extraída y analizada"""
        insights = {
            'data_insights': [],
            'content_insights': [],
            'quality_insights': [],
            'business_insights': [],
            'technical_insights': []
        }
        
        entities = extraction_result.get('entities_found', {})
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        topic_analysis = analysis_result.get('topic_analysis', {})
        readability_analysis = analysis_result.get('readability_analysis', {})
        data_quality = extraction_result.get('data_quality', {})
        
        # Insights de datos
        total_entities = sum(entity.get('count', 0) for entity in entities.values())
        if total_entities > 20:
            insights['data_insights'].append(f"Documento rico en información con {total_entities} entidades extraídas")
        elif total_entities < 5:
            insights['data_insights'].append("Documento con información limitada")
        
        if entities.get('emails') and entities['emails']['count'] > 0:
            insights['data_insights'].append(f"Se encontraron {entities['emails']['count']} direcciones de contacto")
        
        # Insights de contenido
        if sentiment_analysis.get('overall_sentiment') != 'neutral':
            insights['content_insights'].append(f"El documento presenta un sentimiento {sentiment_analysis.get('overall_sentiment')}")
        
        main_topics = topic_analysis.get('main_topics', [])
        if main_topics:
            insights['content_insights'].append(f"Temas principales identificados: {', '.join(main_topics[:3])}")
        
        # Insights de calidad
        quality_score = data_quality.get('overall_score', 0.0)
        if quality_score > 0.8:
            insights['quality_insights'].append("Alta calidad de datos extraídos")
        elif quality_score < 0.5:
            insights['quality_insights'].append("Se requiere revisión de la calidad de datos")
        
        # Insights de negocio
        if entities.get('currencies') or entities.get('amounts'):
            insights['business_insights'].append("Documento contiene información financiera")
        
        if entities.get('companies'):
            insights['business_insights'].append("Se identificaron referencias a empresas")
        
        # Insights técnicos
        if entities.get('urls'):
            insights['technical_insights'].append(f"Se encontraron {entities['urls']['count']} referencias web")
        
        if entities.get('ip_addresses'):
            insights['technical_insights'].append("Se detectaron direcciones IP")
        
        if readability_analysis.get('readability_level') in ['easy', 'very_easy']:
            insights['technical_insights'].append("Documento con alta legibilidad")
        
        return insights
    
    def _create_consolidated_summary(self, extraction_result: Dict[str, Any], 
                                   analysis_result: Dict[str, Any], 
                                   synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un resumen consolidado de toda la información"""
        consolidated_summary = {
            'document_overview': {},
            'key_findings': [],
            'data_summary': {},
            'analysis_summary': {},
            'synthesis_highlights': [],
            'overall_assessment': {}
        }
        
        # Resumen del documento
        extracted_data = extraction_result.get('extracted_data', {})
        metadata = extracted_data.get('metadata', {})
        
        consolidated_summary['document_overview'] = {
            'document_type': metadata.get('document_type', 'unknown'),
            'text_length': metadata.get('text_length', 0),
            'word_count': metadata.get('word_count', 0),
            'detected_language': metadata.get('detected_language', 'unknown'),
            'processing_timestamp': datetime.now().isoformat()
        }
        
        # Hallazgos clave
        entities = extraction_result.get('entities_found', {})
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        topic_analysis = analysis_result.get('topic_analysis', {})
        
        key_findings = []
        
        # Hallazgos de entidades
        total_entities = sum(entity.get('count', 0) for entity in entities.values())
        key_findings.append(f"Se extrajeron {total_entities} entidades de {len(entities)} tipos diferentes")
        
        # Hallazgos de sentimiento
        if sentiment_analysis.get('overall_sentiment') != 'neutral':
            key_findings.append(f"Sentimiento predominante: {sentiment_analysis.get('overall_sentiment')}")
        
        # Hallazgos de temas
        main_topics = topic_analysis.get('main_topics', [])
        if main_topics:
            key_findings.append(f"Tema principal: {main_topics[0]}")
        
        consolidated_summary['key_findings'] = key_findings
        
        # Resumen de datos
        consolidated_summary['data_summary'] = {
            'entities_extracted': len(entities),
            'total_entities': total_entities,
            'data_quality_score': extraction_result.get('data_quality', {}).get('overall_score', 0.0),
            'extraction_success': extraction_result.get('success', False)
        }
        
        # Resumen de análisis
        consolidated_summary['analysis_summary'] = {
            'sentiment_detected': sentiment_analysis.get('overall_sentiment', 'neutral'),
            'topics_identified': len(main_topics),
            'readability_level': analysis_result.get('readability_analysis', {}).get('readability_level', 'unknown'),
            'analysis_success': analysis_result.get('success', False)
        }
        
        # Puntos destacados de la síntesis
        synthesis_highlights = []
        if synthesis_result.get('patterns_detected', {}).get('information_patterns'):
            synthesis_highlights.append("Se detectaron patrones de información específicos")
        
        if synthesis_result.get('insights_generated', {}).get('data_insights'):
            synthesis_highlights.append("Se generaron insights valiosos sobre los datos")
        
        consolidated_summary['synthesis_highlights'] = synthesis_highlights
        
        # Evaluación general
        data_quality = extraction_result.get('data_quality', {}).get('overall_score', 0.0)
        sentiment_confidence = sentiment_analysis.get('confidence', 0.0)
        
        overall_score = (data_quality + sentiment_confidence) / 2
        
        consolidated_summary['overall_assessment'] = {
            'processing_success': True,
            'data_quality_score': data_quality,
            'analysis_confidence': sentiment_confidence,
            'overall_score': overall_score,
            'assessment_level': self._determine_assessment_level(overall_score)
        }
        
        return consolidated_summary
    
    def _generate_recommendations(self, extraction_result: Dict[str, Any], 
                                analysis_result: Dict[str, Any], 
                                synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = {
            'data_recommendations': [],
            'content_recommendations': [],
            'quality_recommendations': [],
            'action_recommendations': []
        }
        
        # Recomendaciones de datos
        entities = extraction_result.get('entities_found', {})
        if not entities.get('emails') and not entities.get('phones'):
            recommendations['data_recommendations'].append("Considerar extraer información de contacto adicional")
        
        if entities.get('credit_cards') or entities.get('social_security'):
            recommendations['data_recommendations'].append("Revisar seguridad de datos sensibles extraídos")
        
        # Recomendaciones de contenido
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        if sentiment_analysis.get('overall_sentiment') == 'negative':
            recommendations['content_recommendations'].append("Revisar contenido con sentimiento negativo")
        
        readability_analysis = analysis_result.get('readability_analysis', {})
        if readability_analysis.get('readability_level') in ['difficult', 'very_difficult']:
            recommendations['content_recommendations'].append("Considerar simplificar el lenguaje del documento")
        
        # Recomendaciones de calidad
        data_quality = extraction_result.get('data_quality', {})
        if data_quality.get('overall_score', 0.0) < 0.7:
            recommendations['quality_recommendations'].append("Mejorar la calidad de extracción de datos")
        
        if data_quality.get('completeness', 0.0) < 0.5:
            recommendations['quality_recommendations'].append("Completar la extracción de datos faltantes")
        
        # Recomendaciones de acción
        topic_analysis = analysis_result.get('topic_analysis', {})
        main_topics = topic_analysis.get('main_topics', [])
        
        if 'business' in main_topics:
            recommendations['action_recommendations'].append("Documento relevante para análisis de negocio")
        
        if 'technical' in main_topics:
            recommendations['action_recommendations'].append("Requiere revisión técnica especializada")
        
        if 'legal' in main_topics:
            recommendations['action_recommendations'].append("Considerar revisión legal del contenido")
        
        return recommendations
    
    def _create_synthesis_metadata(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Crea metadatos de la síntesis"""
        return {
            'synthesis_timestamp': datetime.now().isoformat(),
            'synthesis_version': '1.0',
            'components_processed': ['extraction', 'analysis', 'synthesis'],
            'config_used': self.synthesis_config.copy(),
            'processing_summary': {
                'cross_references_created': bool(synthesis_result.get('cross_references')),
                'patterns_detected': bool(synthesis_result.get('patterns_detected')),
                'insights_generated': bool(synthesis_result.get('insights_generated')),
                'recommendations_created': bool(synthesis_result.get('recommendations'))
            }
        }
    
    def _assess_overall_quality(self, data_quality: Dict[str, Any], 
                               readability: Dict[str, Any]) -> str:
        """Evalúa la calidad general"""
        quality_score = data_quality.get('overall_score', 0.0)
        readability_score = readability.get('readability_score', 0.0)
        
        avg_score = (quality_score + readability_score / 100) / 2
        
        if avg_score >= 0.8:
            return 'excellent'
        elif avg_score >= 0.6:
            return 'good'
        elif avg_score >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
    def _determine_quality_level(self, quality_score: float) -> str:
        """Determina el nivel de calidad"""
        if quality_score >= 0.9:
            return 'excellent'
        elif quality_score >= 0.7:
            return 'good'
        elif quality_score >= 0.5:
            return 'fair'
        else:
            return 'poor'
    
    def _determine_assessment_level(self, overall_score: float) -> str:
        """Determina el nivel de evaluación general"""
        if overall_score >= 0.8:
            return 'excellent'
        elif overall_score >= 0.6:
            return 'good'
        elif overall_score >= 0.4:
            return 'fair'
        else:
            return 'needs_improvement'
    
    def update_synthesis_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración de síntesis"""
        self.synthesis_config.update(new_config)
    
    def get_synthesis_config(self) -> Dict[str, Any]:
        """Retorna la configuración actual de síntesis"""
        return self.synthesis_config.copy()
    
    def add_information_pattern(self, pattern_name: str, keywords: List[str]):
        """Agrega un nuevo patrón de información"""
        self.information_patterns[pattern_name] = keywords
    
    def add_insight_type(self, insight_name: str, description: str):
        """Agrega un nuevo tipo de insight"""
        self.insight_types[insight_name] = description
