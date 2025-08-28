"""
Content Analyzer - Analizador de contenido semántico

Componente de la tercera capa que se encarga de analizar el contenido semántico
de los documentos procesados por las capas anteriores.
"""

import re
from typing import Dict, Any, List, Optional, Union
from collections import Counter, defaultdict
from datetime import datetime


class ContentAnalyzer:
    """Analizador de contenido semántico de documentos"""
    
    def __init__(self):
        self.analysis_config = {
            'enable_sentiment_analysis': True,
            'enable_topic_extraction': True,
            'enable_keyword_analysis': True,
            'enable_readability_analysis': True,
            'enable_content_classification': True,
            'min_keyword_length': 3,
            'max_keywords': 20
        }
        
        # Categorías de contenido predefinidas
        self.content_categories = {
            'business': ['contract', 'invoice', 'report', 'proposal', 'meeting', 'financial', 'budget', 'revenue', 'profit', 'loss'],
            'technical': ['specification', 'documentation', 'code', 'api', 'database', 'system', 'architecture', 'design', 'implementation'],
            'legal': ['agreement', 'contract', 'terms', 'conditions', 'liability', 'legal', 'law', 'regulation', 'compliance', 'policy'],
            'academic': ['research', 'study', 'analysis', 'methodology', 'conclusion', 'hypothesis', 'data', 'results', 'findings'],
            'personal': ['email', 'message', 'communication', 'personal', 'family', 'friend', 'social', 'private'],
            'news': ['news', 'article', 'report', 'update', 'announcement', 'press', 'media', 'publication']
        }
        
        # Palabras de sentimiento
        self.sentiment_words = {
            'positive': ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect', 'outstanding', 'superb', 'brilliant', 'excellent', 'positive', 'success', 'win', 'achieve', 'improve', 'benefit', 'advantage', 'opportunity'],
            'negative': ['bad', 'terrible', 'awful', 'horrible', 'disaster', 'failure', 'problem', 'issue', 'error', 'wrong', 'negative', 'lose', 'fail', 'damage', 'harm', 'risk', 'danger', 'threat', 'concern', 'worry'],
            'neutral': ['normal', 'standard', 'regular', 'usual', 'typical', 'average', 'common', 'general', 'basic', 'simple', 'clear', 'obvious', 'evident']
        }
    
    def analyze_content(self, content: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """
        Analiza el contenido semántico del documento
        
        Args:
            content: Contenido procesado de las capas anteriores
            document_type: Tipo de documento (pdf, word, email)
            
        Returns:
            Dict con análisis semántico del contenido
        """
        try:
            result = {
                'success': False,
                'semantic_analysis': {},
                'content_classification': {},
                'sentiment_analysis': {},
                'topic_analysis': {},
                'readability_analysis': {},
                'analysis_summary': {}
            }
            
            # Extraer texto del contenido
            text_content = self._extract_text_content(content, document_type)
            
            if not text_content:
                result['error'] = 'No se pudo extraer texto del contenido'
                return result
            
            # Realizar análisis semántico
            if self.analysis_config['enable_sentiment_analysis']:
                result['sentiment_analysis'] = self._analyze_sentiment(text_content)
            
            if self.analysis_config['enable_topic_extraction']:
                result['topic_analysis'] = self._extract_topics(text_content)
            
            if self.analysis_config['enable_keyword_analysis']:
                result['semantic_analysis']['keywords'] = self._extract_keywords(text_content)
            
            if self.analysis_config['enable_readability_analysis']:
                result['readability_analysis'] = self._analyze_readability(text_content)
            
            if self.analysis_config['enable_content_classification']:
                result['content_classification'] = self._classify_content(text_content)
            
            # Generar resumen del análisis
            result['analysis_summary'] = self._generate_analysis_summary(result)
            
            result['success'] = True
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en análisis de contenido: {str(e)}'
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
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analiza el sentimiento del texto"""
        sentiment_analysis = {
            'overall_sentiment': 'neutral',
            'sentiment_scores': {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            },
            'sentiment_words': {
                'positive': [],
                'negative': [],
                'neutral': []
            },
            'confidence': 0.0
        }
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Contar palabras de sentimiento
        for sentiment_type, words_list in self.sentiment_words.items():
            found_words = []
            for word in words_list:
                if word in text_lower:
                    count = text_lower.count(word)
                    sentiment_analysis['sentiment_scores'][sentiment_type] += count
                    if word not in found_words:
                        found_words.append(word)
            sentiment_analysis['sentiment_words'][sentiment_type] = found_words
        
        # Determinar sentimiento general
        positive_score = sentiment_analysis['sentiment_scores']['positive']
        negative_score = sentiment_analysis['sentiment_scores']['negative']
        neutral_score = sentiment_analysis['sentiment_scores']['neutral']
        
        total_sentiment_words = positive_score + negative_score + neutral_score
        
        if total_sentiment_words > 0:
            if positive_score > negative_score:
                sentiment_analysis['overall_sentiment'] = 'positive'
                sentiment_analysis['confidence'] = positive_score / total_sentiment_words
            elif negative_score > positive_score:
                sentiment_analysis['overall_sentiment'] = 'negative'
                sentiment_analysis['confidence'] = negative_score / total_sentiment_words
            else:
                sentiment_analysis['overall_sentiment'] = 'neutral'
                sentiment_analysis['confidence'] = neutral_score / total_sentiment_words
        else:
            sentiment_analysis['overall_sentiment'] = 'neutral'
            sentiment_analysis['confidence'] = 0.0
        
        return sentiment_analysis
    
    def _extract_topics(self, text: str) -> Dict[str, Any]:
        """Extrae temas principales del texto"""
        topic_analysis = {
            'main_topics': [],
            'topic_keywords': {},
            'topic_scores': {},
            'topic_distribution': {}
        }
        
        # Análisis básico de temas basado en palabras clave
        text_lower = text.lower()
        words = text_lower.split()
        
        # Filtrar palabras comunes
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        filtered_words = [word for word in words if len(word) >= 3 and word not in stop_words]
        
        # Contar frecuencia de palabras
        word_freq = Counter(filtered_words)
        
        # Identificar temas basados en categorías
        for category, keywords in self.content_categories.items():
            category_score = 0
            found_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    category_score += word_freq.get(keyword, 0)
                    found_keywords.append(keyword)
            
            if category_score > 0:
                topic_analysis['main_topics'].append(category)
                topic_analysis['topic_keywords'][category] = found_keywords
                topic_analysis['topic_scores'][category] = category_score
        
        # Ordenar temas por puntuación
        topic_analysis['main_topics'].sort(key=lambda x: topic_analysis['topic_scores'].get(x, 0), reverse=True)
        
        # Calcular distribución de temas
        total_score = sum(topic_analysis['topic_scores'].values())
        if total_score > 0:
            for category in topic_analysis['main_topics']:
                score = topic_analysis['topic_scores'][category]
                topic_analysis['topic_distribution'][category] = score / total_score
        
        return topic_analysis
    
    def _extract_keywords(self, text: str) -> Dict[str, Any]:
        """Extrae palabras clave del texto"""
        keyword_analysis = {
            'keywords': [],
            'keyword_scores': {},
            'keyword_frequency': {},
            'keyword_categories': {}
        }
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Filtrar palabras
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        filtered_words = [word for word in words if len(word) >= self.analysis_config['min_keyword_length'] and word not in stop_words]
        
        # Contar frecuencia
        word_freq = Counter(filtered_words)
        
        # Obtener palabras clave más frecuentes
        keywords = word_freq.most_common(self.analysis_config['max_keywords'])
        
        for keyword, frequency in keywords:
            keyword_analysis['keywords'].append(keyword)
            keyword_analysis['keyword_frequency'][keyword] = frequency
            
            # Calcular puntuación basada en frecuencia y longitud
            score = frequency * len(keyword)
            keyword_analysis['keyword_scores'][keyword] = score
            
            # Categorizar palabras clave
            category = self._categorize_keyword(keyword)
            keyword_analysis['keyword_categories'][keyword] = category
        
        return keyword_analysis
    
    def _categorize_keyword(self, keyword: str) -> str:
        """Categoriza una palabra clave"""
        for category, keywords in self.content_categories.items():
            if keyword in keywords:
                return category
        
        # Categorización básica basada en patrones
        if re.match(r'\d+', keyword):
            return 'numeric'
        elif keyword.endswith(('ing', 'ed', 'er', 'est')):
            return 'action'
        elif keyword.endswith(('tion', 'sion', 'ment', 'ness')):
            return 'concept'
        else:
            return 'general'
    
    def _analyze_readability(self, text: str) -> Dict[str, Any]:
        """Analiza la legibilidad del texto"""
        readability_analysis = {
            'readability_score': 0.0,
            'readability_level': 'unknown',
            'metrics': {
                'sentence_count': 0,
                'word_count': 0,
                'syllable_count': 0,
                'average_sentence_length': 0.0,
                'average_word_length': 0.0,
                'complex_word_ratio': 0.0
            }
        }
        
        # Contar oraciones
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        readability_analysis['metrics']['sentence_count'] = len(sentences)
        
        # Contar palabras
        words = text.split()
        readability_analysis['metrics']['word_count'] = len(words)
        
        # Contar sílabas (aproximación)
        syllable_count = 0
        complex_words = 0
        
        for word in words:
            word_syllables = self._count_syllables(word)
            syllable_count += word_syllables
            if word_syllables > 2:
                complex_words += 1
        
        readability_analysis['metrics']['syllable_count'] = syllable_count
        
        # Calcular métricas promedio
        if readability_analysis['metrics']['sentence_count'] > 0:
            readability_analysis['metrics']['average_sentence_length'] = (
                readability_analysis['metrics']['word_count'] / readability_analysis['metrics']['sentence_count']
            )
        
        if readability_analysis['metrics']['word_count'] > 0:
            readability_analysis['metrics']['average_word_length'] = (
                readability_analysis['metrics']['syllable_count'] / readability_analysis['metrics']['word_count']
            )
            readability_analysis['metrics']['complex_word_ratio'] = (
                complex_words / readability_analysis['metrics']['word_count']
            )
        
        # Calcular puntuación de legibilidad (Flesch Reading Ease)
        if (readability_analysis['metrics']['sentence_count'] > 0 and 
            readability_analysis['metrics']['word_count'] > 0):
            
            avg_sentence_length = readability_analysis['metrics']['average_sentence_length']
            avg_syllables_per_word = readability_analysis['metrics']['average_word_length']
            
            flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
            readability_analysis['readability_score'] = max(0, min(100, flesch_score))
            
            # Determinar nivel de legibilidad
            if flesch_score >= 90:
                readability_analysis['readability_level'] = 'very_easy'
            elif flesch_score >= 80:
                readability_analysis['readability_level'] = 'easy'
            elif flesch_score >= 70:
                readability_analysis['readability_level'] = 'fairly_easy'
            elif flesch_score >= 60:
                readability_analysis['readability_level'] = 'standard'
            elif flesch_score >= 50:
                readability_analysis['readability_level'] = 'fairly_difficult'
            elif flesch_score >= 30:
                readability_analysis['readability_level'] = 'difficult'
            else:
                readability_analysis['readability_level'] = 'very_difficult'
        
        return readability_analysis
    
    def _count_syllables(self, word: str) -> int:
        """Cuenta las sílabas en una palabra (aproximación)"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        on_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel
        
        if word.endswith('e'):
            count -= 1
        if count == 0:
            count = 1
        
        return count
    
    def _classify_content(self, text: str) -> Dict[str, Any]:
        """Clasifica el contenido del documento"""
        content_classification = {
            'primary_category': 'unknown',
            'secondary_categories': [],
            'category_scores': {},
            'confidence': 0.0,
            'classification_features': {}
        }
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Calcular puntuaciones para cada categoría
        for category, keywords in self.content_categories.items():
            score = 0
            found_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    keyword_count = text_lower.count(keyword)
                    score += keyword_count
                    if keyword not in found_keywords:
                        found_keywords.append(keyword)
            
            if score > 0:
                content_classification['category_scores'][category] = score
                content_classification['classification_features'][category] = found_keywords
        
        # Determinar categoría principal
        if content_classification['category_scores']:
            max_score = max(content_classification['category_scores'].values())
            total_score = sum(content_classification['category_scores'].values())
            
            for category, score in content_classification['category_scores'].items():
                if score == max_score:
                    content_classification['primary_category'] = category
                    content_classification['confidence'] = score / total_score if total_score > 0 else 0.0
                    break
            
            # Obtener categorías secundarias
            sorted_categories = sorted(content_classification['category_scores'].items(), 
                                     key=lambda x: x[1], reverse=True)
            
            for category, score in sorted_categories[1:3]:  # Top 3 después de la principal
                if score > 0:
                    content_classification['secondary_categories'].append(category)
        
        return content_classification
    
    def _generate_analysis_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen del análisis"""
        summary = {
            'analysis_timestamp': datetime.now().isoformat(),
            'sentiment_summary': {},
            'topic_summary': {},
            'readability_summary': {},
            'classification_summary': {},
            'overall_insights': []
        }
        
        # Resumen de sentimiento
        sentiment = analysis_result.get('sentiment_analysis', {})
        if sentiment:
            summary['sentiment_summary'] = {
                'overall_sentiment': sentiment.get('overall_sentiment', 'unknown'),
                'confidence': sentiment.get('confidence', 0.0),
                'sentiment_words_found': sum(len(words) for words in sentiment.get('sentiment_words', {}).values())
            }
        
        # Resumen de temas
        topics = analysis_result.get('topic_analysis', {})
        if topics:
            summary['topic_summary'] = {
                'main_topics': topics.get('main_topics', [])[:3],  # Top 3 temas
                'topic_count': len(topics.get('main_topics', [])),
                'primary_topic': topics.get('main_topics', ['unknown'])[0] if topics.get('main_topics') else 'unknown'
            }
        
        # Resumen de legibilidad
        readability = analysis_result.get('readability_analysis', {})
        if readability:
            summary['readability_summary'] = {
                'readability_level': readability.get('readability_level', 'unknown'),
                'readability_score': readability.get('readability_score', 0.0),
                'word_count': readability.get('metrics', {}).get('word_count', 0),
                'sentence_count': readability.get('metrics', {}).get('sentence_count', 0)
            }
        
        # Resumen de clasificación
        classification = analysis_result.get('content_classification', {})
        if classification:
            summary['classification_summary'] = {
                'primary_category': classification.get('primary_category', 'unknown'),
                'secondary_categories': classification.get('secondary_categories', []),
                'confidence': classification.get('confidence', 0.0)
            }
        
        # Generar insights generales
        insights = []
        
        if sentiment.get('overall_sentiment') != 'neutral':
            insights.append(f"El documento tiene un sentimiento {sentiment.get('overall_sentiment')}")
        
        if topics.get('main_topics'):
            insights.append(f"Temas principales: {', '.join(topics.get('main_topics', [])[:2])}")
        
        if readability.get('readability_level') in ['difficult', 'very_difficult']:
            insights.append("El documento tiene un nivel de legibilidad complejo")
        
        if classification.get('primary_category') != 'unknown':
            insights.append(f"Categoría principal: {classification.get('primary_category')}")
        
        summary['overall_insights'] = insights
        
        return summary
    
    def update_analysis_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración del análisis"""
        self.analysis_config.update(new_config)
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Retorna la configuración actual del análisis"""
        return self.analysis_config.copy()
    
    def add_content_category(self, category_name: str, keywords: List[str]):
        """Agrega una nueva categoría de contenido"""
        self.content_categories[category_name] = keywords
    
    def add_sentiment_words(self, sentiment_type: str, words: List[str]):
        """Agrega palabras de sentimiento"""
        if sentiment_type in self.sentiment_words:
            self.sentiment_words[sentiment_type].extend(words)
        else:
            self.sentiment_words[sentiment_type] = words
