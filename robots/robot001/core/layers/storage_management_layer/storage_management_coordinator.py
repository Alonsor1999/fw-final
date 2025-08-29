"""
Coordinador de Almacenamiento y Gestión de Datos - Cuarta capa del sistema

Este coordinador se encarga de:
- Orquestar el flujo entre Data Storage Manager, Index Manager y Cache Manager
- Gestionar el almacenamiento completo de documentos procesados
- Optimizar el rendimiento del sistema de almacenamiento
- Coordinar operaciones de backup y recuperación
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .data_storage_manager import DataStorageManager
from .index_manager import IndexManager
from .cache_manager import CacheManager


class StorageManagementCoordinator:
    """Coordinador de la Capa de Almacenamiento y Gestión de Datos"""

    def __init__(self, storage_path: str = "storage"):
        self.storage_manager = DataStorageManager(storage_path)
        self.index_manager = IndexManager(f"{storage_path}/documents.db")
        self.cache_manager = CacheManager()
        
        # Configuración del coordinador
        self.config = {
            'enable_caching': True,
            'enable_indexing': True,
            'enable_compression': True,
            'enable_backup': True,
            'auto_optimization': True,
            'optimization_interval': 3600,  # segundos
            'max_processing_time': 300,     # segundos
            'enable_detailed_logging': True,
            'error_recovery': True,
            'batch_operations': True,
            'batch_size': 100
        }
        
        # Estadísticas del coordinador
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'storage_operations': 0,
            'index_operations': 0,
            'cache_operations': 0,
            'processing_times': [],
            'errors_by_component': {
                'storage': 0,
                'index': 0,
                'cache': 0,
                'coordination': 0
            },
            'last_optimization': None,
            'last_backup': None
        }

    def store_document_complete(self, document_data: Dict[str, Any], 
                               document_type: str, 
                               original_filename: str) -> Dict[str, Any]:
        """
        Almacena un documento completo con indexación y caché
        
        Args:
            document_data: Datos del documento procesado
            document_type: Tipo de documento (pdf, word, email)
            original_filename: Nombre original del archivo
            
        Returns:
            Dict con resultados completos del almacenamiento
        """
        start_time = time.time()
        
        try:
            # Paso 1: Almacenar en Data Storage Manager
            storage_result = self.storage_manager.store_document(
                document_data, document_type, original_filename
            )
            
            if not storage_result['success']:
                self.stats['errors_by_component']['storage'] += 1
                return {
                    'success': False,
                    'error': f"Error en almacenamiento: {storage_result['error']}",
                    'step': 'storage'
                }
            
            document_id = storage_result['document_id']
            self.stats['storage_operations'] += 1
            
            # Paso 2: Crear índices
            if self.config['enable_indexing']:
                index_result = self.index_manager.create_index(
                    document_id, document_data, document_type
                )
                
                if not index_result['success']:
                    self.stats['errors_by_component']['index'] += 1
                    # Continuar aunque falle la indexación
                    index_result = {
                        'success': False,
                        'error': index_result['error'],
                        'created_indices': []
                    }
                else:
                    self.stats['index_operations'] += 1
            
            # Paso 3: Almacenar en caché
            if self.config['enable_caching']:
                cache_key = f"doc_{document_id}"
                cache_success = self.cache_manager.set(
                    cache_key, document_data, ttl=3600  # 1 hora
                )
                
                if cache_success:
                    self.stats['cache_operations'] += 1
                
                cache_result = {
                    'success': cache_success,
                    'cache_key': cache_key
                }
            else:
                cache_result = {'success': False, 'reason': 'caching_disabled'}
            
            # Calcular tiempo total
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)
            
            # Actualizar estadísticas
            self.stats['total_operations'] += 1
            self.stats['successful_operations'] += 1
            
            return {
                'success': True,
                'document_id': document_id,
                'storage_result': storage_result,
                'index_result': index_result if self.config['enable_indexing'] else None,
                'cache_result': cache_result,
                'processing_time': processing_time,
                'total_size': storage_result.get('file_size', 0)
            }
            
        except Exception as e:
            self.stats['errors_by_component']['coordination'] += 1
            self.stats['failed_operations'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'step': 'coordination'
            }

    def retrieve_document_complete(self, document_id: str) -> Dict[str, Any]:
        """
        Recupera un documento completo con optimizaciones de caché
        
        Args:
            document_id: ID del documento a recuperar
            
        Returns:
            Dict con el documento y metadatos
        """
        start_time = time.time()
        
        try:
            # Paso 1: Intentar recuperar desde caché
            if self.config['enable_caching']:
                cache_key = f"doc_{document_id}"
                cached_data = self.cache_manager.get(cache_key)
                
                if cached_data is not None:
                    self.stats['cache_operations'] += 1
                    processing_time = time.time() - start_time
                    
                    return {
                        'success': True,
                        'document_data': cached_data,
                        'source': 'cache',
                        'processing_time': processing_time
                    }
            
            # Paso 2: Recuperar desde almacenamiento
            storage_result = self.storage_manager.retrieve_document(document_id)
            
            if not storage_result['success']:
                self.stats['errors_by_component']['storage'] += 1
                return {
                    'success': False,
                    'error': storage_result['error'],
                    'source': 'storage'
                }
            
            document_data = storage_result['document_data']
            self.stats['storage_operations'] += 1
            
            # Paso 3: Actualizar caché
            if self.config['enable_caching']:
                cache_key = f"doc_{document_id}"
                self.cache_manager.set(cache_key, document_data, ttl=3600)
                self.stats['cache_operations'] += 1
            
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)
            
            return {
                'success': True,
                'document_data': document_data,
                'source': 'storage',
                'processing_time': processing_time,
                'metadata': storage_result.get('metadata', {})
            }
            
        except Exception as e:
            self.stats['errors_by_component']['coordination'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'source': 'coordination'
            }

    def search_documents(self, query: str, search_type: str = 'full_text',
                        filters: Dict[str, Any] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Busca documentos usando índices y caché
        
        Args:
            query: Consulta de búsqueda
            search_type: Tipo de búsqueda
            filters: Filtros adicionales
            limit: Límite de resultados
            
        Returns:
            Dict con resultados de la búsqueda
        """
        start_time = time.time()
        
        try:
            # Paso 1: Buscar en índices
            if self.config['enable_indexing']:
                search_result = self.index_manager.search_documents(
                    query, search_type, filters, limit
                )
                
                if not search_result['success']:
                    self.stats['errors_by_component']['index'] += 1
                    return {
                        'success': False,
                        'error': search_result['error'],
                        'source': 'index'
                    }
                
                self.stats['index_operations'] += 1
                
                # Paso 2: Recuperar documentos completos
                documents = []
                for result in search_result['results']:
                    doc_id = result['document_id']
                    doc_result = self.retrieve_document_complete(doc_id)
                    
                    if doc_result['success']:
                        documents.append({
                            'document_id': doc_id,
                            'document_data': doc_result['document_data'],
                            'match_info': result
                        })
                
                processing_time = time.time() - start_time
                
                return {
                    'success': True,
                    'query': query,
                    'search_type': search_type,
                    'documents': documents,
                    'total_results': len(documents),
                    'processing_time': processing_time,
                    'index_stats': search_result
                }
            else:
                return {
                    'success': False,
                    'error': 'Indexación deshabilitada',
                    'source': 'coordination'
                }
                
        except Exception as e:
            self.stats['errors_by_component']['coordination'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'source': 'coordination'
            }

    def update_document(self, document_id: str, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un documento existente
        
        Args:
            document_id: ID del documento
            new_data: Nuevos datos del documento
            
        Returns:
            Dict con resultado de la actualización
        """
        start_time = time.time()
        
        try:
            # Paso 1: Actualizar en almacenamiento
            storage_result = self.storage_manager.store_document(
                new_data, new_data.get('document_type', 'unknown'), 
                new_data.get('original_filename', 'unknown')
            )
            
            if not storage_result['success']:
                self.stats['errors_by_component']['storage'] += 1
                return {
                    'success': False,
                    'error': storage_result['error'],
                    'step': 'storage'
                }
            
            # Paso 2: Actualizar índices
            if self.config['enable_indexing']:
                index_result = self.index_manager.update_index(document_id, new_data)
                
                if not index_result['success']:
                    self.stats['errors_by_component']['index'] += 1
                    # Continuar aunque falle la actualización de índices
            
            # Paso 3: Actualizar caché
            if self.config['enable_caching']:
                cache_key = f"doc_{document_id}"
                self.cache_manager.delete(cache_key)
                self.cache_manager.set(cache_key, new_data, ttl=3600)
            
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)
            
            return {
                'success': True,
                'document_id': document_id,
                'processing_time': processing_time,
                'storage_result': storage_result,
                'index_result': index_result if self.config['enable_indexing'] else None
            }
            
        except Exception as e:
            self.stats['errors_by_component']['coordination'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'step': 'coordination'
            }

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Elimina un documento completamente
        
        Args:
            document_id: ID del documento a eliminar
            
        Returns:
            Dict con resultado de la eliminación
        """
        start_time = time.time()
        
        try:
            # Paso 1: Eliminar de almacenamiento
            storage_result = self.storage_manager.delete_document(document_id)
            
            if not storage_result['success']:
                self.stats['errors_by_component']['storage'] += 1
                return {
                    'success': False,
                    'error': storage_result['error'],
                    'step': 'storage'
                }
            
            # Paso 2: Eliminar índices
            if self.config['enable_indexing']:
                index_result = self.index_manager.delete_index(document_id)
                
                if not index_result['success']:
                    self.stats['errors_by_component']['index'] += 1
            
            # Paso 3: Eliminar de caché
            if self.config['enable_caching']:
                cache_key = f"doc_{document_id}"
                self.cache_manager.delete(cache_key)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'document_id': document_id,
                'processing_time': processing_time,
                'storage_result': storage_result,
                'index_result': index_result if self.config['enable_indexing'] else None
            }
            
        except Exception as e:
            self.stats['errors_by_component']['coordination'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'step': 'coordination'
            }

    def create_backup(self) -> Dict[str, Any]:
        """
        Crea un backup completo del sistema
        
        Returns:
            Dict con información del backup
        """
        if not self.config['enable_backup']:
            return {
                'success': False,
                'error': 'Backup deshabilitado en configuración'
            }
        
        try:
            # Paso 1: Crear backup de almacenamiento
            storage_backup = self.storage_manager.create_backup()
            
            if not storage_backup['success']:
                return {
                    'success': False,
                    'error': f"Error en backup de almacenamiento: {storage_backup['error']}"
                }
            
            # Paso 2: Guardar caché si está habilitado
            cache_backup = None
            if self.config['enable_caching']:
                cache_backup = self.cache_manager.save_cache()
            
            # Paso 3: Optimizar índices
            index_optimization = None
            if self.config['enable_indexing']:
                index_optimization = self.index_manager.optimize_indexes()
            
            self.stats['last_backup'] = datetime.now().isoformat()
            
            return {
                'success': True,
                'storage_backup': storage_backup,
                'cache_backup': cache_backup,
                'index_optimization': index_optimization,
                'backup_timestamp': self.stats['last_backup']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def optimize_system(self) -> Dict[str, Any]:
        """
        Optimiza todo el sistema de almacenamiento
        
        Returns:
            Dict con información de la optimización
        """
        if not self.config['auto_optimization']:
            return {
                'success': False,
                'error': 'Optimización automática deshabilitada'
            }
        
        try:
            optimization_results = {}
            
            # Optimizar caché
            if self.config['enable_caching']:
                cache_optimization = self.cache_manager.optimize_cache()
                optimization_results['cache'] = cache_optimization
            
            # Optimizar índices
            if self.config['enable_indexing']:
                index_optimization = self.index_manager.optimize_indexes()
                optimization_results['index'] = index_optimization
            
            # Obtener estadísticas de almacenamiento
            storage_stats = self.storage_manager.get_storage_stats()
            optimization_results['storage'] = storage_stats
            
            self.stats['last_optimization'] = datetime.now().isoformat()
            
            return {
                'success': True,
                'optimization_results': optimization_results,
                'optimization_timestamp': self.stats['last_optimization']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del sistema
        
        Returns:
            Dict con estadísticas de todos los componentes
        """
        try:
            # Estadísticas del coordinador
            coordinator_stats = {
                'total_operations': self.stats['total_operations'],
                'successful_operations': self.stats['successful_operations'],
                'failed_operations': self.stats['failed_operations'],
                'success_rate': (
                    self.stats['successful_operations'] / max(self.stats['total_operations'], 1)
                ),
                'avg_processing_time': (
                    sum(self.stats['processing_times']) / max(len(self.stats['processing_times']), 1)
                ),
                'errors_by_component': self.stats['errors_by_component'],
                'last_optimization': self.stats['last_optimization'],
                'last_backup': self.stats['last_backup']
            }
            
            # Estadísticas de componentes
            storage_stats = self.storage_manager.get_storage_stats()
            index_stats = self.index_manager.get_index_stats()
            cache_stats = self.cache_manager.get_stats()
            
            return {
                'coordinator': coordinator_stats,
                'storage': storage_stats,
                'index': index_stats,
                'cache': cache_stats,
                'system_health': self._calculate_system_health()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'coordinator_stats': coordinator_stats if 'coordinator_stats' in locals() else None
            }

    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calcula la salud general del sistema"""
        try:
            # Obtener estadísticas básicas
            total_ops = self.stats['total_operations']
            success_ops = self.stats['successful_operations']
            error_counts = self.stats['errors_by_component']
            
            # Calcular métricas de salud
            success_rate = success_ops / max(total_ops, 1)
            error_rate = sum(error_counts.values()) / max(total_ops, 1)
            
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
                'total_operations': total_ops,
                'component_errors': error_counts
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e)
            }
