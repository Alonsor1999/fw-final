"""
Preprocesador AWS - Quinta capa del sistema

Este componente se encarga de:
- Preparar datos para servicios AWS (Comprehend, Bedrock LLM)
- Gestión de casos de confianza media/baja
- Coordinación con servicios AWS externos
- Optimización de datos para procesamiento en la nube
"""

import time
import json
import boto3
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path


class AWSPreprocessor:
    """Preprocesador para servicios AWS"""

    def __init__(self, aws_region: str = 'us-east-1'):
        self.aws_region = aws_region
        
        # Configuración del preprocesador
        self.config = {
            'enable_aws_services': True,
            'enable_comprehend': True,
            'enable_bedrock': True,
            'max_processing_time': 120,  # segundos
            'enable_data_optimization': True,
            'enable_batch_processing': True,
            'batch_size': 10,
            'enable_retry_mechanism': True,
            'max_retries': 3
        }
        
        # Configuración de servicios AWS
        self.aws_services = {
            'comprehend': {
                'enabled': True,
                'features': ['entities', 'key_phrases', 'sentiment', 'syntax'],
                'language': 'en',
                'max_chars': 5000
            },
            'bedrock': {
                'enabled': True,
                'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
                'max_tokens': 4096,
                'temperature': 0.1
            }
        }
        
        # Inicializar clientes AWS (simulado)
        self.comprehend_client = None
        self.bedrock_client = None
        
        # Estadísticas del preprocesador
        self.stats = {
            'total_processed': 0,
            'comprehend_calls': 0,
            'bedrock_calls': 0,
            'successful_processing': 0,
            'failed_processing': 0,
            'processing_times': [],
            'data_sizes': [],
            'complexity_levels': []
        }

    def preprocess_for_aws(self, analysis_data: Dict[str, Any], 
                          confidence_score: float) -> Dict[str, Any]:
        """
        Preprocesa datos para servicios AWS
        
        Args:
            analysis_data: Datos del análisis previo
            confidence_score: Puntuación de confianza
            
        Returns:
            Dict con datos preprocesados para AWS
        """
        start_time = time.time()
        
        try:
            # Evaluar complejidad del caso
            complexity_assessment = self._assess_complexity(analysis_data)
            
            # Preparar datos para Comprehend
            comprehend_data = self._prepare_for_comprehend(analysis_data)
            
            # Preparar datos para Bedrock
            bedrock_data = self._prepare_for_bedrock(analysis_data, complexity_assessment)
            
            # Optimizar datos
            optimized_data = self._optimize_data_for_aws(analysis_data)
            
            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)
            
            # Actualizar estadísticas
            self.stats['total_processed'] += 1
            self.stats['successful_processing'] += 1
            self.stats['data_sizes'].append(self._calculate_data_size(analysis_data))
            self.stats['complexity_levels'].append(complexity_assessment['level'])
            
            return {
                'success': True,
                'preprocessing_type': 'aws',
                'comprehend_data': comprehend_data,
                'bedrock_data': bedrock_data,
                'optimized_data': optimized_data,
                'complexity_assessment': complexity_assessment,
                'processing_time': processing_time,
                'aws_services_required': self._determine_aws_services(complexity_assessment),
                'estimated_aws_cost': self._estimate_aws_cost(comprehend_data, bedrock_data)
            }
            
        except Exception as e:
            self.stats['failed_processing'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'preprocessing_type': 'aws',
                'recommendation': 'fallback_to_local'
            }

    def process_with_comprehend(self, preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos con AWS Comprehend
        
        Args:
            preprocessed_data: Datos preprocesados
            
        Returns:
            Dict con resultados de Comprehend
        """
        if not self.config['enable_comprehend']:
            return {
                'success': False,
                'error': 'Comprehend deshabilitado',
                'service': 'comprehend'
            }
        
        try:
            comprehend_data = preprocessed_data.get('comprehend_data', {})
            
            # Simular llamada a Comprehend
            comprehend_results = self._simulate_comprehend_call(comprehend_data)
            
            self.stats['comprehend_calls'] += 1
            
            return {
                'success': True,
                'service': 'comprehend',
                'results': comprehend_results,
                'processing_time': time.time(),
                'confidence_boost': self._calculate_confidence_boost(comprehend_results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'service': 'comprehend'
            }

    def process_with_bedrock(self, preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa datos con AWS Bedrock
        
        Args:
            preprocessed_data: Datos preprocesados
            
        Returns:
            Dict con resultados de Bedrock
        """
        if not self.config['enable_bedrock']:
            return {
                'success': False,
                'error': 'Bedrock deshabilitado',
                'service': 'bedrock'
            }
        
        try:
            bedrock_data = preprocessed_data.get('bedrock_data', {})
            
            # Simular llamada a Bedrock
            bedrock_results = self._simulate_bedrock_call(bedrock_data)
            
            self.stats['bedrock_calls'] += 1
            
            return {
                'success': True,
                'service': 'bedrock',
                'results': bedrock_results,
                'processing_time': time.time(),
                'insights_generated': len(bedrock_results.get('insights', [])),
                'recommendations': bedrock_results.get('recommendations', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'service': 'bedrock'
            }

    def handle_complex_cases(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja casos complejos que requieren múltiples servicios AWS
        
        Args:
            analysis_data: Datos del análisis
            
        Returns:
            Dict con resultados de procesamiento complejo
        """
        try:
            # Preprocesar para AWS
            preprocessed = self.preprocess_for_aws(analysis_data, 0.5)
            
            if not preprocessed['success']:
                return preprocessed
            
            # Procesar con Comprehend
            comprehend_result = self.process_with_comprehend(preprocessed)
            
            # Procesar con Bedrock
            bedrock_result = self.process_with_bedrock(preprocessed)
            
            # Combinar resultados
            combined_results = self._combine_aws_results(comprehend_result, bedrock_result)
            
            return {
                'success': True,
                'processing_type': 'complex_aws',
                'comprehend_result': comprehend_result,
                'bedrock_result': bedrock_result,
                'combined_results': combined_results,
                'final_confidence': self._calculate_final_confidence(combined_results),
                'recommendations': combined_results.get('recommendations', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_type': 'complex_aws'
            }

    def _assess_complexity(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la complejidad del caso"""
        complexity_score = 0
        factors = []
        
        # Factor por cantidad de texto
        if 'text_content' in analysis_data:
            text_length = len(analysis_data['text_content'])
            if text_length > 10000:
                complexity_score += 0.4
                factors.append('large_text')
            elif text_length > 5000:
                complexity_score += 0.2
                factors.append('medium_text')
        
        # Factor por número de entidades
        if 'extracted_entities' in analysis_data:
            entity_count = sum(len(entities) for entities in analysis_data['extracted_entities'].values())
            if entity_count > 50:
                complexity_score += 0.3
                factors.append('many_entities')
            elif entity_count > 20:
                complexity_score += 0.15
                factors.append('moderate_entities')
        
        # Factor por tipo de documento
        if 'semantic_analysis' in analysis_data:
            semantic = analysis_data['semantic_analysis']
            if semantic.get('content_classification') in ['contract', 'legal', 'technical']:
                complexity_score += 0.3
                factors.append('complex_document_type')
        
        # Factor por sentimiento
        if 'semantic_analysis' in analysis_data:
            sentiment = semantic.get('sentiment', {}).get('overall', 'neutral')
            if sentiment in ['negative', 'mixed']:
                complexity_score += 0.2
                factors.append('complex_sentiment')
        
        # Clasificar complejidad
        if complexity_score >= 0.8:
            level = 'high'
        elif complexity_score >= 0.5:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'score': complexity_score,
            'level': level,
            'factors': factors,
            'requires_multiple_services': complexity_score > 0.6
        }

    def _prepare_for_comprehend(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara datos para AWS Comprehend"""
        comprehend_data = {
            'text': '',
            'language': 'en',
            'features': self.aws_services['comprehend']['features']
        }
        
        # Extraer texto para Comprehend
        if 'text_content' in analysis_data:
            text = analysis_data['text_content']
            # Limitar a 5000 caracteres para Comprehend
            comprehend_data['text'] = text[:5000]
        
        # Detectar idioma si es necesario
        if 'metadata' in analysis_data:
            metadata = analysis_data['metadata']
            if 'language' in metadata:
                comprehend_data['language'] = metadata['language']
        
        return comprehend_data

    def _prepare_for_bedrock(self, analysis_data: Dict[str, Any], 
                           complexity_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara datos para AWS Bedrock"""
        bedrock_data = {
            'prompt': '',
            'model_id': self.aws_services['bedrock']['model_id'],
            'max_tokens': self.aws_services['bedrock']['max_tokens'],
            'temperature': self.aws_services['bedrock']['temperature']
        }
        
        # Construir prompt para Bedrock
        prompt_parts = []
        
        # Contexto del documento
        if 'semantic_analysis' in analysis_data:
            semantic = analysis_data['semantic_analysis']
            if 'content_classification' in semantic:
                prompt_parts.append(f"Document type: {semantic['content_classification']}")
        
        # Entidades extraídas
        if 'extracted_entities' in analysis_data:
            entities = analysis_data['extracted_entities']
            entity_summary = []
            for entity_type, entity_list in entities.items():
                if entity_list:
                    entity_summary.append(f"{entity_type}: {', '.join(entity_list[:5])}")
            if entity_summary:
                prompt_parts.append(f"Key entities: {'; '.join(entity_summary)}")
        
        # Análisis semántico
        if 'semantic_analysis' in analysis_data:
            semantic = analysis_data['semantic_analysis']
            if 'sentiment' in semantic:
                sentiment = semantic['sentiment'].get('overall', 'neutral')
                prompt_parts.append(f"Sentiment: {sentiment}")
            if 'topics' in semantic:
                topics = semantic['topics'][:3]
                prompt_parts.append(f"Main topics: {', '.join(topics)}")
        
        # Instrucciones específicas basadas en complejidad
        if complexity_assessment['level'] == 'high':
            prompt_parts.append("Please provide detailed analysis and recommendations.")
        else:
            prompt_parts.append("Please provide concise analysis and key insights.")
        
        bedrock_data['prompt'] = "\n".join(prompt_parts)
        
        return bedrock_data

    def _optimize_data_for_aws(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza datos para servicios AWS"""
        optimized = {}
        
        # Optimizar texto
        if 'text_content' in analysis_data:
            text = analysis_data['text_content']
            # Limpiar y normalizar texto
            optimized['text'] = self._clean_text_for_aws(text)
        
        # Optimizar entidades
        if 'extracted_entities' in analysis_data:
            entities = analysis_data['extracted_entities']
            optimized['entities'] = self._optimize_entities(entities)
        
        # Optimizar metadatos
        if 'metadata' in analysis_data:
            metadata = analysis_data['metadata']
            optimized['metadata'] = self._optimize_metadata(metadata)
        
        return optimized

    def _determine_aws_services(self, complexity_assessment: Dict[str, Any]) -> List[str]:
        """Determina qué servicios AWS usar"""
        services = []
        
        if self.config['enable_comprehend']:
            services.append('comprehend')
        
        if self.config['enable_bedrock']:
            if complexity_assessment['level'] in ['medium', 'high']:
                services.append('bedrock')
        
        return services

    def _estimate_aws_cost(self, comprehend_data: Dict[str, Any], 
                          bedrock_data: Dict[str, Any]) -> Dict[str, float]:
        """Estima el costo de los servicios AWS"""
        costs = {
            'comprehend': 0.0,
            'bedrock': 0.0,
            'total': 0.0
        }
        
        # Estimar costo de Comprehend
        if comprehend_data.get('text'):
            text_length = len(comprehend_data['text'])
            # Precio aproximado por unidad de texto
            costs['comprehend'] = (text_length / 100) * 0.0001
        
        # Estimar costo de Bedrock
        if bedrock_data.get('prompt'):
            prompt_length = len(bedrock_data['prompt'])
            # Precio aproximado por token
            costs['bedrock'] = (prompt_length / 4) * 0.000015
        
        costs['total'] = costs['comprehend'] + costs['bedrock']
        
        return costs

    def _simulate_comprehend_call(self, comprehend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula una llamada a AWS Comprehend"""
        # Simulación de resultados de Comprehend
        return {
            'entities': [
                {'text': 'Sample Entity', 'type': 'PERSON', 'score': 0.95},
                {'text': 'Sample Organization', 'type': 'ORGANIZATION', 'score': 0.88}
            ],
            'key_phrases': [
                {'text': 'important phrase', 'score': 0.92},
                {'text': 'key concept', 'score': 0.87}
            ],
            'sentiment': {
                'overall': 'positive',
                'positive': 0.75,
                'negative': 0.15,
                'neutral': 0.10
            },
            'syntax': {
                'tokens': [],
                'parts_of_speech': []
            }
        }

    def _simulate_bedrock_call(self, bedrock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula una llamada a AWS Bedrock"""
        # Simulación de resultados de Bedrock
        return {
            'analysis': 'This document appears to be a business communication with moderate complexity.',
            'insights': [
                'Document contains multiple entities that require attention',
                'Sentiment analysis indicates positive tone',
                'Key topics suggest business-related content'
            ],
            'recommendations': [
                'Process through standard workflow',
                'Flag for human review if confidence remains low',
                'Consider additional validation for key entities'
            ],
            'confidence_boost': 0.15
        }

    def _combine_aws_results(self, comprehend_result: Dict[str, Any], 
                           bedrock_result: Dict[str, Any]) -> Dict[str, Any]:
        """Combina resultados de múltiples servicios AWS"""
        combined = {
            'entities': comprehend_result.get('results', {}).get('entities', []),
            'key_phrases': comprehend_result.get('results', {}).get('key_phrases', []),
            'sentiment': comprehend_result.get('results', {}).get('sentiment', {}),
            'analysis': bedrock_result.get('results', {}).get('analysis', ''),
            'insights': bedrock_result.get('results', {}).get('insights', []),
            'recommendations': bedrock_result.get('results', {}).get('recommendations', []),
            'confidence_boost': bedrock_result.get('results', {}).get('confidence_boost', 0.0)
        }
        
        return combined

    def _calculate_final_confidence(self, combined_results: Dict[str, Any]) -> float:
        """Calcula la confianza final después del procesamiento AWS"""
        base_confidence = 0.5  # Confianza base para casos que van a AWS
        
        # Boost de confianza de Bedrock
        confidence_boost = combined_results.get('confidence_boost', 0.0)
        
        # Boost basado en calidad de entidades
        entities = combined_results.get('entities', [])
        if entities:
            avg_entity_score = sum(entity.get('score', 0) for entity in entities) / len(entities)
            entity_boost = avg_entity_score * 0.2
        else:
            entity_boost = 0.0
        
        final_confidence = base_confidence + confidence_boost + entity_boost
        
        return min(final_confidence, 1.0)

    def _calculate_confidence_boost(self, comprehend_results: Dict[str, Any]) -> float:
        """Calcula el boost de confianza de Comprehend"""
        boost = 0.0
        
        # Boost basado en entidades
        entities = comprehend_results.get('entities', [])
        if entities:
            avg_score = sum(entity.get('score', 0) for entity in entities) / len(entities)
            boost += avg_score * 0.1
        
        # Boost basado en sentimiento
        sentiment = comprehend_results.get('sentiment', {})
        if sentiment.get('overall') == 'positive':
            boost += 0.05
        
        return min(boost, 0.2)

    def _clean_text_for_aws(self, text: str) -> str:
        """Limpia texto para servicios AWS"""
        # Eliminar caracteres especiales problemáticos
        import re
        cleaned = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
        return cleaned.strip()

    def _optimize_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Optimiza entidades para AWS"""
        optimized = {}
        for entity_type, entity_list in entities.items():
            # Limitar a las entidades más relevantes
            optimized[entity_type] = entity_list[:10]
        return optimized

    def _optimize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza metadatos para AWS"""
        # Mantener solo metadatos relevantes
        relevant_keys = ['language', 'document_type', 'created_date', 'author']
        return {k: v for k, v in metadata.items() if k in relevant_keys}

    def _calculate_data_size(self, analysis_data: Dict[str, Any]) -> int:
        """Calcula el tamaño de los datos"""
        return len(json.dumps(analysis_data, default=str))

    def get_preprocessor_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del preprocesador AWS"""
        avg_processing_time = (
            sum(self.stats['processing_times']) / 
            max(len(self.stats['processing_times']), 1)
        )
        
        avg_data_size = (
            sum(self.stats['data_sizes']) / 
            max(len(self.stats['data_sizes']), 1)
        )
        
        success_rate = (
            self.stats['successful_processing'] / 
            max(self.stats['total_processed'], 1)
        )
        
        return {
            'total_processed': self.stats['total_processed'],
            'successful_processing': self.stats['successful_processing'],
            'failed_processing': self.stats['failed_processing'],
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'avg_data_size': avg_data_size,
            'comprehend_calls': self.stats['comprehend_calls'],
            'bedrock_calls': self.stats['bedrock_calls'],
            'complexity_distribution': self._get_complexity_distribution(),
            'config': self.config
        }

    def _get_complexity_distribution(self) -> Dict[str, int]:
        """Obtiene la distribución de complejidad"""
        distribution = {'low': 0, 'medium': 0, 'high': 0}
        for level in self.stats['complexity_levels']:
            distribution[level] = distribution.get(level, 0) + 1
        return distribution
