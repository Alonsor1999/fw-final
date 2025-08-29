"""
Data Extractor - Extractor de datos estructurados

Componente de la tercera capa que se encarga de extraer datos estructurados
de los documentos procesados por las capas anteriores.
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime


class DataExtractor:
    """Extractor de datos estructurados de documentos"""
    
    def __init__(self):
        self.extraction_patterns = {
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phones': r'(\+?[\d\s\-\(\)]{7,})',
            'dates': r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b|\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b',
            'urls': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'ip_addresses': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'credit_cards': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'social_security': r'\b\d{3}-\d{2}-\d{4}\b',
            'currencies': r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP)',
            'percentages': r'\d+(?:\.\d+)?%',
            'measurements': r'\d+(?:\.\d+)?\s*(?:cm|mm|m|km|in|ft|yd|kg|g|lb|oz)',
            'postal_codes': r'\b\d{5}(?:-\d{4})?\b',
            'names': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            'companies': r'\b[A-Z][a-zA-Z\s&]+(?:Inc|Corp|LLC|Ltd|Company|Co|Corporation)\b'
        }
        
        self.entity_types = {
            'personal_info': ['names', 'emails', 'phones', 'social_security'],
            'financial': ['currencies', 'credit_cards'],
            'technical': ['urls', 'ip_addresses', 'dates'],
            'measurements': ['measurements', 'percentages'],
            'locations': ['postal_codes'],
            'organizations': ['companies']
        }
    
    def extract_data(self, content: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """
        Extrae datos estructurados del contenido procesado
        
        Args:
            content: Contenido procesado de las capas anteriores
            document_type: Tipo de documento (pdf, word, email)
            
        Returns:
            Dict con datos extraídos estructurados
        """
        try:
            result = {
                'success': False,
                'extracted_data': {},
                'entities_found': {},
                'data_quality': {},
                'extraction_summary': {}
            }
            
            # Extraer texto del contenido
            text_content = self._extract_text_content(content, document_type)
            
            if not text_content:
                result['error'] = 'No se pudo extraer texto del contenido'
                return result
            
            # Extraer entidades
            entities = self._extract_entities(text_content)
            result['entities_found'] = entities
            
            # Extraer datos estructurados específicos
            structured_data = self._extract_structured_data(text_content, document_type)
            result['extracted_data'] = structured_data
            
            # Calcular calidad de datos
            data_quality = self._calculate_data_quality(entities, structured_data)
            result['data_quality'] = data_quality
            
            # Generar resumen
            result['extraction_summary'] = self._generate_extraction_summary(entities, structured_data)
            
            result['success'] = True
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en extracción de datos: {str(e)}'
            }
    
    def _extract_text_content(self, content: Dict[str, Any], document_type: str) -> str:
        """Extrae el texto del contenido procesado"""
        text_parts = []
        
        if document_type == 'pdf':
            text_content = content.get('text_content', {})
            text_parts.append(text_content.get('full_text', ''))
            
        elif document_type == 'word':
            text_content = content.get('text_content', {})
            text_parts.append(text_content.get('full_text', ''))
            
        elif document_type == 'email':
            body_content = content.get('body_content', {})
            text_parts.append(body_content.get('text_body', ''))
            text_parts.append(body_content.get('html_body', ''))
            
            # Extraer texto de headers
            headers = content.get('headers', {})
            for key, value in headers.items():
                if value and isinstance(value, str):
                    text_parts.append(f"{key}: {value}")
        
        return ' '.join(text_parts)
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrae entidades del texto usando patrones predefinidos"""
        entities = {}
        
        for entity_type, pattern in self.extraction_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Limpiar y deduplicar matches
                cleaned_matches = []
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]  # Para grupos de captura
                    cleaned_match = match.strip()
                    if cleaned_match and cleaned_match not in cleaned_matches:
                        cleaned_matches.append(cleaned_match)
                
                entities[entity_type] = {
                    'count': len(cleaned_matches),
                    'values': cleaned_matches
                }
        
        return entities
    
    def _extract_structured_data(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extrae datos estructurados específicos según el tipo de documento"""
        structured_data = {
            'document_info': {},
            'contact_info': {},
            'financial_data': {},
            'technical_data': {},
            'metadata': {}
        }
        
        # Extraer información de contacto
        structured_data['contact_info'] = self._extract_contact_info(text)
        
        # Extraer datos financieros
        structured_data['financial_data'] = self._extract_financial_data(text)
        
        # Extraer datos técnicos
        structured_data['technical_data'] = self._extract_technical_data(text)
        
        # Extraer metadatos específicos del documento
        structured_data['metadata'] = self._extract_document_metadata(text, document_type)
        
        return structured_data
    
    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extrae información de contacto"""
        contact_info = {
            'emails': [],
            'phones': [],
            'names': [],
            'addresses': []
        }
        
        # Extraer emails
        email_pattern = self.extraction_patterns['emails']
        emails = re.findall(email_pattern, text)
        contact_info['emails'] = list(set(emails))
        
        # Extraer teléfonos
        phone_pattern = self.extraction_patterns['phones']
        phones = re.findall(phone_pattern, text)
        contact_info['phones'] = list(set(phones))
        
        # Extraer nombres
        name_pattern = self.extraction_patterns['names']
        names = re.findall(name_pattern, text)
        contact_info['names'] = list(set(names))
        
        # Extraer direcciones (patrón básico)
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)'
        addresses = re.findall(address_pattern, text, re.IGNORECASE)
        contact_info['addresses'] = list(set(addresses))
        
        return contact_info
    
    def _extract_financial_data(self, text: str) -> Dict[str, Any]:
        """Extrae datos financieros"""
        financial_data = {
            'currencies': [],
            'credit_cards': [],
            'percentages': [],
            'amounts': []
        }
        
        # Extraer monedas
        currency_pattern = self.extraction_patterns['currencies']
        currencies = re.findall(currency_pattern, text)
        financial_data['currencies'] = list(set(currencies))
        
        # Extraer tarjetas de crédito
        cc_pattern = self.extraction_patterns['credit_cards']
        credit_cards = re.findall(cc_pattern, text)
        financial_data['credit_cards'] = list(set(credit_cards))
        
        # Extraer porcentajes
        percent_pattern = self.extraction_patterns['percentages']
        percentages = re.findall(percent_pattern, text)
        financial_data['percentages'] = list(set(percentages))
        
        # Extraer cantidades numéricas
        amount_pattern = r'\b\d+(?:,\d{3})*(?:\.\d{2})?\b'
        amounts = re.findall(amount_pattern, text)
        financial_data['amounts'] = list(set(amounts))
        
        return financial_data
    
    def _extract_technical_data(self, text: str) -> Dict[str, Any]:
        """Extrae datos técnicos"""
        technical_data = {
            'urls': [],
            'ip_addresses': [],
            'dates': [],
            'measurements': []
        }
        
        # Extraer URLs
        url_pattern = self.extraction_patterns['urls']
        urls = re.findall(url_pattern, text)
        technical_data['urls'] = list(set(urls))
        
        # Extraer direcciones IP
        ip_pattern = self.extraction_patterns['ip_addresses']
        ips = re.findall(ip_pattern, text)
        technical_data['ip_addresses'] = list(set(ips))
        
        # Extraer fechas
        date_pattern = self.extraction_patterns['dates']
        dates = re.findall(date_pattern, text)
        technical_data['dates'] = list(set(dates))
        
        # Extraer medidas
        measurement_pattern = self.extraction_patterns['measurements']
        measurements = re.findall(measurement_pattern, text)
        technical_data['measurements'] = list(set(measurements))
        
        return technical_data
    
    def _extract_document_metadata(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extrae metadatos específicos del documento"""
        metadata = {
            'document_type': document_type,
            'extraction_timestamp': datetime.now().isoformat(),
            'text_length': len(text),
            'word_count': len(text.split()),
            'line_count': len(text.split('\n')),
            'language_indicators': self._detect_language_indicators(text)
        }
        
        # Detectar idioma basado en palabras comunes
        metadata['detected_language'] = self._detect_language(text)
        
        return metadata
    
    def _detect_language_indicators(self, text: str) -> Dict[str, int]:
        """Detecta indicadores de idioma"""
        indicators = {
            'spanish': 0,
            'english': 0,
            'french': 0,
            'german': 0
        }
        
        # Palabras comunes en español
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como', 'pero', 'sus', 'me', 'hasta', 'hay', 'donde', 'han', 'quien', 'están', 'estado', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros']
        
        # Palabras comunes en inglés
        english_words = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us']
        
        text_lower = text.lower()
        words = text_lower.split()
        
        for word in words:
            if word in spanish_words:
                indicators['spanish'] += 1
            elif word in english_words:
                indicators['english'] += 1
        
        return indicators
    
    def _detect_language(self, text: str) -> str:
        """Detecta el idioma principal del texto"""
        indicators = self._detect_language_indicators(text)
        
        max_count = max(indicators.values())
        if max_count == 0:
            return 'unknown'
        
        for language, count in indicators.items():
            if count == max_count:
                return language
        
        return 'unknown'
    
    def _calculate_data_quality(self, entities: Dict[str, Any], structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula la calidad de los datos extraídos"""
        quality_metrics = {
            'completeness': 0.0,
            'accuracy': 0.0,
            'consistency': 0.0,
            'uniqueness': 0.0,
            'overall_score': 0.0
        }
        
        # Calcular completitud
        total_entities = sum(entity.get('count', 0) for entity in entities.values())
        quality_metrics['completeness'] = min(1.0, total_entities / 100)  # Normalizado
        
        # Calcular precisión (simulado)
        quality_metrics['accuracy'] = 0.85  # Valor simulado
        
        # Calcular consistencia
        contact_info = structured_data.get('contact_info', {})
        financial_data = structured_data.get('financial_data', {})
        
        consistency_score = 0.0
        if contact_info.get('emails') and contact_info.get('phones'):
            consistency_score += 0.3
        if financial_data.get('currencies') and financial_data.get('amounts'):
            consistency_score += 0.3
        if entities.get('dates'):
            consistency_score += 0.4
        
        quality_metrics['consistency'] = consistency_score
        
        # Calcular unicidad
        total_values = 0
        unique_values = 0
        
        for entity in entities.values():
            values = entity.get('values', [])
            total_values += len(values)
            unique_values += len(set(values))
        
        if total_values > 0:
            quality_metrics['uniqueness'] = unique_values / total_values
        else:
            quality_metrics['uniqueness'] = 1.0
        
        # Calcular puntuación general
        quality_metrics['overall_score'] = (
            quality_metrics['completeness'] * 0.3 +
            quality_metrics['accuracy'] * 0.3 +
            quality_metrics['consistency'] * 0.2 +
            quality_metrics['uniqueness'] * 0.2
        )
        
        return quality_metrics
    
    def _generate_extraction_summary(self, entities: Dict[str, Any], structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen de la extracción"""
        total_entities = sum(entity.get('count', 0) for entity in entities.values())
        
        summary = {
            'total_entities_extracted': total_entities,
            'entity_types_found': len(entities),
            'contact_info_extracted': bool(structured_data.get('contact_info', {}).get('emails') or 
                                         structured_data.get('contact_info', {}).get('phones')),
            'financial_data_extracted': bool(structured_data.get('financial_data', {}).get('currencies') or 
                                           structured_data.get('financial_data', {}).get('amounts')),
            'technical_data_extracted': bool(structured_data.get('technical_data', {}).get('urls') or 
                                           structured_data.get('technical_data', {}).get('dates')),
            'data_quality_score': structured_data.get('data_quality', {}).get('overall_score', 0.0),
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def get_extraction_patterns(self) -> Dict[str, str]:
        """Retorna los patrones de extracción disponibles"""
        return self.extraction_patterns.copy()
    
    def add_custom_pattern(self, pattern_name: str, pattern: str):
        """Agrega un patrón personalizado de extracción"""
        self.extraction_patterns[pattern_name] = pattern
    
    def remove_pattern(self, pattern_name: str):
        """Elimina un patrón de extracción"""
        if pattern_name in self.extraction_patterns:
            del self.extraction_patterns[pattern_name]
