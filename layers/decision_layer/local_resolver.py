"""
Resolutor Local - Quinta capa del sistema

Este componente se encarga de:
- Resolución local de casos de alta confianza
- Procesamiento rápido sin necesidad de servicios externos
- Aplicación de reglas y lógica de negocio local
- Optimización de rendimiento para casos simples
"""

import time
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path


class LocalResolver:
    """Resolutor local para casos de alta confianza"""

    def __init__(self):
        # Configuración del resolutor local
        self.config = {
            'enable_local_processing': True,
            'confidence_threshold': 0.8,
            'max_processing_time': 30,  # segundos
            'enable_caching': True,
            'enable_rule_engine': True,
            'enable_pattern_matching': True,
            'enable_business_logic': True
        }
        
        # Reglas de negocio locales
        self.business_rules = {
            'document_classification': {
                'invoice': ['factura', 'invoice', 'bill', 'recibo'],
                'contract': ['contrato', 'contract', 'agreement', 'acuerdo'],
                'report': ['reporte', 'report', 'informe'],
                'email': ['email', 'correo', 'mail', 'mensaje'],
                'letter': ['carta', 'letter', 'correspondencia']
            },
            'priority_levels': {
                'urgent': ['urgente', 'urgent', 'inmediato', 'crítico'],
                'high': ['alto', 'high', 'importante'],
                'normal': ['normal', 'regular', 'standard'],
                'low': ['bajo', 'low', 'baja prioridad']
            },
            'action_types': {
                'approve': ['aprobar', 'approve', 'aceptar', 'accept'],
                'reject': ['rechazar', 'reject', 'denegar', 'deny'],
                'review': ['revisar', 'review', 'examinar', 'examine'],
                'forward': ['reenviar', 'forward', 'transferir', 'transfer']
            }
        }
        
        # Patrones de reconocimiento
        self.patterns = {
            'dates': r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b|\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b',
            'amounts': r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP)',
            'percentages': r'\d+(?:\.\d+)?%',
            'phone_numbers': r'(\+?[\d\s\-\(\)]{7,})',
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'urls': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        }
        
        # Estadísticas del resolutor
        self.stats = {
            'total_resolved': 0,
            'successful_resolutions': 0,
            'failed_resolutions': 0,
            'processing_times': [],
            'confidence_scores': [],
            'rule_applications': 0,
            'pattern_matches': 0
        }

    def resolve_high_confidence_case(self, analysis_data: Dict[str, Any], 
                                   confidence_score: float) -> Dict[str, Any]:
        """
        Resuelve un caso de alta confianza localmente
        
        Args:
            analysis_data: Datos del análisis previo
            confidence_score: Puntuación de confianza (0.0 - 1.0)
            
        Returns:
            Dict con la resolución local
        """
        start_time = time.time()
        
        try:
            # Verificar umbral de confianza
            if confidence_score < self.config['confidence_threshold']:
                return {
                    'success': False,
                    'error': f'Confianza insuficiente: {confidence_score} < {self.config["confidence_threshold"]}',
                    'recommendation': 'use_aws_services'
                }
            
            # Extraer información clave
            extracted_info = self._extract_key_information(analysis_data)
            
            # Aplicar reglas de negocio
            business_logic_result = self._apply_business_logic(extracted_info)
            
            # Realizar análisis de patrones
            pattern_analysis = self._analyze_patterns(analysis_data)
            
            # Generar decisión local
            local_decision = self._generate_local_decision(
                extracted_info, business_logic_result, pattern_analysis, confidence_score
            )
            
            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)
            
            # Actualizar estadísticas
            self.stats['total_resolved'] += 1
            self.stats['successful_resolutions'] += 1
            self.stats['confidence_scores'].append(confidence_score)
            
            return {
                'success': True,
                'resolution_type': 'local',
                'decision': local_decision,
                'confidence_score': confidence_score,
                'processing_time': processing_time,
                'extracted_info': extracted_info,
                'business_logic_result': business_logic_result,
                'pattern_analysis': pattern_analysis,
                'reasoning': self._generate_reasoning(extracted_info, business_logic_result)
            }
            
        except Exception as e:
            self.stats['failed_resolutions'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'resolution_type': 'local',
                'recommendation': 'use_aws_services'
            }

    def _extract_key_information(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae información clave del análisis"""
        extracted_info = {
            'document_type': None,
            'priority_level': 'normal',
            'action_required': None,
            'key_entities': [],
            'dates': [],
            'amounts': [],
            'contacts': []
        }
        
        # Extraer tipo de documento
        if 'semantic_analysis' in analysis_data:
            semantic = analysis_data['semantic_analysis']
            if 'content_classification' in semantic:
                extracted_info['document_type'] = semantic['content_classification']
        
        # Extraer entidades clave
        if 'extracted_entities' in analysis_data:
            entities = analysis_data['extracted_entities']
            for entity_type, entity_list in entities.items():
                if isinstance(entity_list, list):
                    extracted_info['key_entities'].extend(entity_list)
        
        # Extraer fechas
        if 'text_content' in analysis_data:
            text = analysis_data['text_content']
            dates = re.findall(self.patterns['dates'], text)
            extracted_info['dates'] = dates
        
        # Extraer montos
        if 'text_content' in analysis_data:
            text = analysis_data['text_content']
            amounts = re.findall(self.patterns['amounts'], text)
            extracted_info['amounts'] = amounts
        
        # Extraer contactos
        if 'text_content' in analysis_data:
            text = analysis_data['text_content']
            emails = re.findall(self.patterns['emails'], text)
            phones = re.findall(self.patterns['phone_numbers'], text)
            extracted_info['contacts'] = emails + phones
        
        return extracted_info

    def _apply_business_logic(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica reglas de negocio locales"""
        self.stats['rule_applications'] += 1
        
        business_result = {
            'document_category': None,
            'priority_assessment': 'normal',
            'recommended_action': None,
            'risk_level': 'low',
            'compliance_status': 'compliant'
        }
        
        # Clasificar documento
        if extracted_info['document_type']:
            doc_type = extracted_info['document_type'].lower()
            for category, keywords in self.business_rules['document_classification'].items():
                if any(keyword in doc_type for keyword in keywords):
                    business_result['document_category'] = category
                    break
        
        # Determinar prioridad
        text_content = ' '.join(extracted_info['key_entities']).lower()
        for priority, keywords in self.business_rules['priority_levels'].items():
            if any(keyword in text_content for keyword in keywords):
                business_result['priority_assessment'] = priority
                break
        
        # Determinar acción recomendada
        for action, keywords in self.business_rules['action_types'].items():
            if any(keyword in text_content for keyword in keywords):
                business_result['recommended_action'] = action
                break
        
        # Evaluar nivel de riesgo
        risk_indicators = ['urgent', 'critical', 'error', 'problem', 'issue']
        if any(indicator in text_content for indicator in risk_indicators):
            business_result['risk_level'] = 'high'
        
        return business_result

    def _analyze_patterns(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza patrones en los datos"""
        self.stats['pattern_matches'] += 1
        
        pattern_result = {
            'date_patterns': [],
            'financial_patterns': [],
            'contact_patterns': [],
            'url_patterns': [],
            'structured_data': {}
        }
        
        if 'text_content' in analysis_data:
            text = analysis_data['text_content']
            
            # Buscar fechas
            pattern_result['date_patterns'] = re.findall(self.patterns['dates'], text)
            
            # Buscar datos financieros
            pattern_result['financial_patterns'] = re.findall(self.patterns['amounts'], text)
            pattern_result['financial_patterns'].extend(re.findall(self.patterns['percentages'], text))
            
            # Buscar contactos
            pattern_result['contact_patterns'] = re.findall(self.patterns['emails'], text)
            pattern_result['contact_patterns'].extend(re.findall(self.patterns['phone_numbers'], text))
            
            # Buscar URLs
            pattern_result['url_patterns'] = re.findall(self.patterns['urls'], text)
        
        return pattern_result

    def _generate_local_decision(self, extracted_info: Dict[str, Any], 
                               business_logic: Dict[str, Any], 
                               pattern_analysis: Dict[str, Any],
                               confidence_score: float) -> Dict[str, Any]:
        """Genera una decisión local basada en el análisis"""
        
        decision = {
            'action': 'process_locally',
            'priority': business_logic['priority_assessment'],
            'category': business_logic['document_category'],
            'risk_level': business_logic['risk_level'],
            'processing_path': 'standard',
            'estimated_time': self._estimate_processing_time(extracted_info),
            'resources_required': self._estimate_resources(extracted_info),
            'confidence_level': self._classify_confidence(confidence_score)
        }
        
        # Determinar acción específica
        if business_logic['recommended_action']:
            decision['action'] = business_logic['recommended_action']
        
        # Ajustar ruta de procesamiento basada en complejidad
        complexity = self._assess_complexity(extracted_info, pattern_analysis)
        if complexity == 'high':
            decision['processing_path'] = 'detailed'
        elif complexity == 'low':
            decision['processing_path'] = 'fast_track'
        
        # Determinar si necesita revisión humana
        if (business_logic['risk_level'] == 'high' or 
            confidence_score < 0.9 or 
            complexity == 'high'):
            decision['human_review_required'] = True
        else:
            decision['human_review_required'] = False
        
        return decision

    def _generate_reasoning(self, extracted_info: Dict[str, Any], 
                          business_logic: Dict[str, Any]) -> str:
        """Genera el razonamiento detrás de la decisión"""
        reasoning_parts = []
        
        # Razonamiento del tipo de documento
        if business_logic['document_category']:
            reasoning_parts.append(
                f"Documento clasificado como {business_logic['document_category']}"
            )
        
        # Razonamiento de prioridad
        if business_logic['priority_assessment'] != 'normal':
            reasoning_parts.append(
                f"Prioridad {business_logic['priority_assessment']} detectada"
            )
        
        # Razonamiento de acción
        if business_logic['recommended_action']:
            reasoning_parts.append(
                f"Acción recomendada: {business_logic['recommended_action']}"
            )
        
        # Razonamiento de riesgo
        if business_logic['risk_level'] == 'high':
            reasoning_parts.append("Nivel de riesgo alto detectado")
        
        # Razonamiento de entidades
        if extracted_info['key_entities']:
            reasoning_parts.append(
                f"Entidades clave identificadas: {len(extracted_info['key_entities'])}"
            )
        
        return "; ".join(reasoning_parts) if reasoning_parts else "Análisis estándar aplicado"

    def _estimate_processing_time(self, extracted_info: Dict[str, Any]) -> int:
        """Estima el tiempo de procesamiento en segundos"""
        base_time = 5  # tiempo base en segundos
        
        # Ajustar por número de entidades
        entity_factor = len(extracted_info['key_entities']) * 0.5
        
        # Ajustar por complejidad del documento
        complexity_factor = 1.0
        if extracted_info['document_type'] in ['contract', 'report']:
            complexity_factor = 2.0
        
        # Ajustar por cantidad de datos
        data_factor = (len(extracted_info['dates']) + 
                      len(extracted_info['amounts']) + 
                      len(extracted_info['contacts'])) * 0.3
        
        estimated_time = base_time + entity_factor + data_factor
        estimated_time *= complexity_factor
        
        return min(int(estimated_time), self.config['max_processing_time'])

    def _estimate_resources(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Estima los recursos necesarios"""
        return {
            'cpu_usage': 'low',
            'memory_usage': 'low',
            'storage_required': 'minimal',
            'network_usage': 'none'
        }

    def _classify_confidence(self, confidence_score: float) -> str:
        """Clasifica el nivel de confianza"""
        if confidence_score >= 0.95:
            return 'excellent'
        elif confidence_score >= 0.85:
            return 'good'
        elif confidence_score >= 0.75:
            return 'fair'
        else:
            return 'poor'

    def _assess_complexity(self, extracted_info: Dict[str, Any], 
                          pattern_analysis: Dict[str, Any]) -> str:
        """Evalúa la complejidad del caso"""
        complexity_score = 0
        
        # Factor por número de entidades
        complexity_score += len(extracted_info['key_entities']) * 0.1
        
        # Factor por tipo de documento
        if extracted_info['document_type'] in ['contract', 'report']:
            complexity_score += 0.5
        
        # Factor por cantidad de patrones
        complexity_score += len(pattern_analysis['date_patterns']) * 0.05
        complexity_score += len(pattern_analysis['financial_patterns']) * 0.1
        complexity_score += len(pattern_analysis['contact_patterns']) * 0.05
        
        if complexity_score >= 1.0:
            return 'high'
        elif complexity_score >= 0.5:
            return 'medium'
        else:
            return 'low'

    def get_resolver_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del resolutor local"""
        avg_processing_time = (
            sum(self.stats['processing_times']) / 
            max(len(self.stats['processing_times']), 1)
        )
        
        avg_confidence = (
            sum(self.stats['confidence_scores']) / 
            max(len(self.stats['confidence_scores']), 1)
        )
        
        success_rate = (
            self.stats['successful_resolutions'] / 
            max(self.stats['total_resolved'], 1)
        )
        
        return {
            'total_resolved': self.stats['total_resolved'],
            'successful_resolutions': self.stats['successful_resolutions'],
            'failed_resolutions': self.stats['failed_resolutions'],
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'avg_confidence_score': avg_confidence,
            'rule_applications': self.stats['rule_applications'],
            'pattern_matches': self.stats['pattern_matches'],
            'config': self.config
        }

