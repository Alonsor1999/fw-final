"""
Gestor de Índices - Cuarta capa del sistema

Este componente se encarga de:
- Creación y mantenimiento de índices de búsqueda
- Indexación de contenido y metadatos
- Búsqueda rápida de documentos
- Optimización de consultas
"""

import json
import sqlite3
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import hashlib


class IndexManager:
    """Gestor de índices para búsqueda rápida de documentos"""

    def __init__(self, db_path: str = "storage/documents.db"):
        self.db_path = db_path
        self.index_config = {
            'enable_full_text_index': True,
            'enable_metadata_index': True,
            'enable_semantic_index': True,
            'index_update_frequency': 'realtime',  # realtime, batch, scheduled
            'max_index_size': 100 * 1024 * 1024,  # 100MB
            'index_compression': True,
            'enable_fuzzy_search': True,
            'fuzzy_threshold': 0.8
        }
        
        # Tipos de índices soportados
        self.index_types = {
            'full_text': 'texto completo del documento',
            'metadata': 'metadatos del documento',
            'entities': 'entidades extraídas (emails, teléfonos, etc.)',
            'semantic': 'análisis semántico',
            'temporal': 'fechas y timestamps',
            'categorical': 'categorías y clasificaciones',
            'geographic': 'datos geográficos',
            'numeric': 'datos numéricos'
        }
        
        # Estadísticas de indexación
        self.stats = {
            'total_indexed_documents': 0,
            'index_size': 0,
            'index_types_created': set(),
            'last_index_update': None,
            'index_performance': {
                'avg_indexing_time': 0.0,
                'total_queries': 0,
                'avg_query_time': 0.0
            }
        }

    def create_index(self, document_id: str, document_data: Dict[str, Any], 
                    document_type: str) -> Dict[str, Any]:
        """
        Crea índices para un documento
        
        Args:
            document_id: ID del documento
            document_data: Datos del documento
            document_type: Tipo de documento
            
        Returns:
            Dict con información de la indexación
        """
        try:
            start_time = datetime.now()
            
            # Conectar a la base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crear índices según el tipo de documento
            created_indices = []
            
            # Índice de texto completo
            if self.index_config['enable_full_text_index']:
                text_content = self._extract_text_content(document_data)
                if text_content:
                    self._create_full_text_index(cursor, document_id, text_content)
                    created_indices.append('full_text')
            
            # Índice de metadatos
            if self.index_config['enable_metadata_index']:
                metadata = document_data.get('metadata', {})
                if metadata:
                    self._create_metadata_index(cursor, document_id, metadata)
                    created_indices.append('metadata')
            
            # Índice de entidades
            entities = document_data.get('extracted_entities', {})
            if entities:
                self._create_entities_index(cursor, document_id, entities)
                created_indices.append('entities')
            
            # Índice semántico
            if self.index_config['enable_semantic_index']:
                semantic_data = document_data.get('semantic_analysis', {})
                if semantic_data:
                    self._create_semantic_index(cursor, document_id, semantic_data)
                    created_indices.append('semantic')
            
            # Índice temporal
            temporal_data = self._extract_temporal_data(document_data)
            if temporal_data:
                self._create_temporal_index(cursor, document_id, temporal_data)
                created_indices.append('temporal')
            
            # Índice categórico
            categorical_data = self._extract_categorical_data(document_data)
            if categorical_data:
                self._create_categorical_index(cursor, document_id, categorical_data)
                created_indices.append('categorical')
            
            conn.commit()
            conn.close()
            
            # Actualizar estadísticas
            indexing_time = (datetime.now() - start_time).total_seconds()
            self._update_index_stats(document_id, created_indices, indexing_time)
            
            return {
                'success': True,
                'document_id': document_id,
                'created_indices': created_indices,
                'indexing_time': indexing_time,
                'total_indices': len(created_indices)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }

    def search_documents(self, query: str, search_type: str = 'full_text', 
                        filters: Dict[str, Any] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Busca documentos usando los índices
        
        Args:
            query: Consulta de búsqueda
            search_type: Tipo de búsqueda (full_text, metadata, entities, etc.)
            filters: Filtros adicionales
            limit: Límite de resultados
            
        Returns:
            Dict con resultados de la búsqueda
        """
        try:
            start_time = datetime.now()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            results = []
            
            if search_type == 'full_text':
                results = self._search_full_text(cursor, query, filters, limit)
            elif search_type == 'metadata':
                results = self._search_metadata(cursor, query, filters, limit)
            elif search_type == 'entities':
                results = self._search_entities(cursor, query, filters, limit)
            elif search_type == 'semantic':
                results = self._search_semantic(cursor, query, filters, limit)
            elif search_type == 'temporal':
                results = self._search_temporal(cursor, query, filters, limit)
            elif search_type == 'categorical':
                results = self._search_categorical(cursor, query, filters, limit)
            else:
                # Búsqueda combinada
                results = self._search_combined(cursor, query, filters, limit)
            
            conn.close()
            
            # Actualizar estadísticas de consulta
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_query_stats(query_time)
            
            return {
                'success': True,
                'query': query,
                'search_type': search_type,
                'results': results,
                'total_results': len(results),
                'query_time': query_time,
                'filters_applied': filters or {}
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }

    def update_index(self, document_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza los índices de un documento
        
        Args:
            document_id: ID del documento
            document_data: Nuevos datos del documento
            
        Returns:
            Dict con resultado de la actualización
        """
        try:
            # Eliminar índices existentes
            self.delete_index(document_id)
            
            # Crear nuevos índices
            return self.create_index(document_id, document_data, 
                                   document_data.get('document_type', 'unknown'))
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }

    def delete_index(self, document_id: str) -> Dict[str, Any]:
        """
        Elimina los índices de un documento
        
        Args:
            document_id: ID del documento
            
        Returns:
            Dict con resultado de la eliminación
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Eliminar todos los índices del documento
            cursor.execute('DELETE FROM indices WHERE document_id = ?', (document_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'document_id': document_id,
                'message': 'Índices eliminados correctamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los índices
        
        Returns:
            Dict con estadísticas completas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar documentos indexados
            cursor.execute('SELECT COUNT(DISTINCT document_id) FROM indices')
            total_indexed = cursor.fetchone()[0]
            
            # Contar por tipo de índice
            cursor.execute('''
                SELECT index_type, COUNT(*) 
                FROM indices 
                GROUP BY index_type
            ''')
            
            index_type_counts = {}
            total_indices = 0
            
            for index_type, count in cursor.fetchall():
                index_type_counts[index_type] = count
                total_indices += count
            
            # Calcular tamaño del índice
            cursor.execute('SELECT COUNT(*) FROM indices')
            index_size = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_indexed_documents': total_indexed,
                'total_indices': total_indices,
                'index_size': index_size,
                'index_types_created': list(self.stats['index_types_created']),
                'last_index_update': self.stats['last_index_update'],
                'index_performance': self.stats['index_performance'],
                'index_type_counts': index_type_counts
            }
            
        except Exception as e:
            return {'error': str(e)}

    def optimize_indexes(self) -> Dict[str, Any]:
        """
        Optimiza los índices para mejorar el rendimiento
        
        Returns:
            Dict con información de la optimización
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Analizar tablas
            cursor.execute('ANALYZE')
            
            # Optimizar índices
            cursor.execute('REINDEX')
            
            # Vacuum para liberar espacio
            cursor.execute('VACUUM')
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Índices optimizados correctamente',
                'optimization_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _create_full_text_index(self, cursor, document_id: str, text_content: str):
        """Crea índice de texto completo"""
        # Dividir texto en palabras
        words = re.findall(r'\b\w+\b', text_content.lower())
        
        # Crear índices para palabras únicas
        unique_words = set(words)
        for word in unique_words:
            if len(word) >= 3:  # Solo palabras de 3+ caracteres
                cursor.execute('''
                    INSERT INTO indices (document_id, index_type, index_value)
                    VALUES (?, ?, ?)
                ''', (document_id, 'full_text', word))

    def _create_metadata_index(self, cursor, document_id: str, metadata: Dict[str, Any]):
        """Crea índice de metadatos"""
        for key, value in metadata.items():
            if value:
                cursor.execute('''
                    INSERT INTO indices (document_id, index_type, index_value)
                    VALUES (?, ?, ?)
                ''', (document_id, 'metadata', f"{key}:{value}"))

    def _create_entities_index(self, cursor, document_id: str, entities: Dict[str, Any]):
        """Crea índice de entidades"""
        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, list):
                for entity in entity_list:
                    cursor.execute('''
                        INSERT INTO indices (document_id, index_type, index_value)
                        VALUES (?, ?, ?)
                    ''', (document_id, 'entities', f"{entity_type}:{entity}"))

    def _create_semantic_index(self, cursor, document_id: str, semantic_data: Dict[str, Any]):
        """Crea índice semántico"""
        # Índice de sentimiento
        sentiment = semantic_data.get('sentiment', {})
        if sentiment:
            cursor.execute('''
                INSERT INTO indices (document_id, index_type, index_value)
                VALUES (?, ?, ?)
            ''', (document_id, 'semantic', f"sentiment:{sentiment.get('overall', 'neutral')}"))
        
        # Índice de temas
        topics = semantic_data.get('topics', [])
        for topic in topics:
            cursor.execute('''
                INSERT INTO indices (document_id, index_type, index_value)
                VALUES (?, ?, ?)
            ''', (document_id, 'semantic', f"topic:{topic}"))
        
        # Índice de palabras clave
        keywords = semantic_data.get('keywords', [])
        for keyword in keywords:
            cursor.execute('''
                INSERT INTO indices (document_id, index_type, index_value)
                VALUES (?, ?, ?)
            ''', (document_id, 'semantic', f"keyword:{keyword}"))

    def _create_temporal_index(self, cursor, document_id: str, temporal_data: Dict[str, Any]):
        """Crea índice temporal"""
        for date_type, date_value in temporal_data.items():
            if date_value:
                cursor.execute('''
                    INSERT INTO indices (document_id, index_type, index_value)
                    VALUES (?, ?, ?)
                ''', (document_id, 'temporal', f"{date_type}:{date_value}"))

    def _create_categorical_index(self, cursor, document_id: str, categorical_data: Dict[str, Any]):
        """Crea índice categórico"""
        for category, value in categorical_data.items():
            if value:
                cursor.execute('''
                    INSERT INTO indices (document_id, index_type, index_value)
                    VALUES (?, ?, ?)
                ''', (document_id, 'categorical', f"{category}:{value}"))

    def _extract_text_content(self, document_data: Dict[str, Any]) -> str:
        """Extrae contenido de texto del documento"""
        text_content = ""
        
        # Buscar en diferentes campos de texto
        text_fields = ['text_content', 'extracted_text', 'content', 'body']
        for field in text_fields:
            if field in document_data and document_data[field]:
                text_content += str(document_data[field]) + " "
        
        return text_content.strip()

    def _extract_temporal_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae datos temporales del documento"""
        temporal_data = {}
        
        # Buscar fechas en metadatos
        metadata = document_data.get('metadata', {})
        date_fields = ['created_date', 'modified_date', 'date', 'timestamp']
        for field in date_fields:
            if field in metadata:
                temporal_data[field] = metadata[field]
        
        return temporal_data

    def _extract_categorical_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae datos categóricos del documento"""
        categorical_data = {}
        
        # Clasificación del contenido
        semantic_analysis = document_data.get('semantic_analysis', {})
        if 'content_classification' in semantic_analysis:
            categorical_data['content_type'] = semantic_analysis['content_classification']
        
        # Tipo de documento
        if 'document_type' in document_data:
            categorical_data['document_type'] = document_data['document_type']
        
        return categorical_data

    def _search_full_text(self, cursor, query: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Búsqueda en texto completo"""
        words = query.lower().split()
        results = []
        
        for word in words:
            cursor.execute('''
                SELECT DISTINCT document_id FROM indices 
                WHERE index_type = 'full_text' AND index_value LIKE ?
            ''', (f'%{word}%',))
            
            for (document_id,) in cursor.fetchall():
                results.append({
                    'document_id': document_id,
                    'match_type': 'full_text',
                    'matched_term': word
                })
        
        return results[:limit]

    def _search_metadata(self, cursor, query: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Búsqueda en metadatos"""
        cursor.execute('''
            SELECT DISTINCT document_id FROM indices 
            WHERE index_type = 'metadata' AND index_value LIKE ?
        ''', (f'%{query}%',))
        
        results = []
        for (document_id,) in cursor.fetchall():
            results.append({
                'document_id': document_id,
                'match_type': 'metadata',
                'matched_term': query
            })
        
        return results[:limit]

    def _search_entities(self, cursor, query: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Búsqueda en entidades"""
        cursor.execute('''
            SELECT DISTINCT document_id FROM indices 
            WHERE index_type = 'entities' AND index_value LIKE ?
        ''', (f'%{query}%',))
        
        results = []
        for (document_id,) in cursor.fetchall():
            results.append({
                'document_id': document_id,
                'match_type': 'entities',
                'matched_term': query
            })
        
        return results[:limit]

    def _search_semantic(self, cursor, query: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Búsqueda semántica"""
        cursor.execute('''
            SELECT DISTINCT document_id FROM indices 
            WHERE index_type = 'semantic' AND index_value LIKE ?
        ''', (f'%{query}%',))
        
        results = []
        for (document_id,) in cursor.fetchall():
            results.append({
                'document_id': document_id,
                'match_type': 'semantic',
                'matched_term': query
            })
        
        return results[:limit]

    def _search_temporal(self, cursor, query: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Búsqueda temporal"""
        cursor.execute('''
            SELECT DISTINCT document_id FROM indices 
            WHERE index_type = 'temporal' AND index_value LIKE ?
        ''', (f'%{query}%',))
        
        results = []
        for (document_id,) in cursor.fetchall():
            results.append({
                'document_id': document_id,
                'match_type': 'temporal',
                'matched_term': query
            })
        
        return results[:limit]

    def _search_categorical(self, cursor, query: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Búsqueda categórica"""
        cursor.execute('''
            SELECT DISTINCT document_id FROM indices 
            WHERE index_type = 'categorical' AND index_value LIKE ?
        ''', (f'%{query}%',))
        
        results = []
        for (document_id,) in cursor.fetchall():
            results.append({
                'document_id': document_id,
                'match_type': 'categorical',
                'matched_term': query
            })
        
        return results[:limit]

    def _search_combined(self, cursor, query: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Búsqueda combinada en todos los índices"""
        cursor.execute('''
            SELECT DISTINCT document_id, index_type FROM indices 
            WHERE index_value LIKE ?
        ''', (f'%{query}%',))
        
        results = []
        for (document_id, index_type) in cursor.fetchall():
            results.append({
                'document_id': document_id,
                'match_type': index_type,
                'matched_term': query
            })
        
        return results[:limit]

    def _update_index_stats(self, document_id: str, created_indices: List[str], indexing_time: float):
        """Actualiza estadísticas de indexación"""
        self.stats['total_indexed_documents'] += 1
        self.stats['index_types_created'].update(created_indices)
        self.stats['last_index_update'] = datetime.now().isoformat()
        
        # Actualizar tiempo promedio de indexación
        current_avg = self.stats['index_performance']['avg_indexing_time']
        total_docs = self.stats['total_indexed_documents']
        self.stats['index_performance']['avg_indexing_time'] = (
            (current_avg * (total_docs - 1) + indexing_time) / total_docs
        )

    def _update_query_stats(self, query_time: float):
        """Actualiza estadísticas de consulta"""
        self.stats['index_performance']['total_queries'] += 1
        
        current_avg = self.stats['index_performance']['avg_query_time']
        total_queries = self.stats['index_performance']['total_queries']
        self.stats['index_performance']['avg_query_time'] = (
            (current_avg * (total_queries - 1) + query_time) / total_queries
        )
