"""
Gestor de Almacenamiento de Datos - Cuarta capa del sistema

Este componente se encarga de:
- Almacenamiento persistente de documentos procesados
- Gestión de metadatos
- Organización de datos por tipo y categoría
- Backup y recuperación de datos
"""

import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import hashlib
import pickle


class DataStorageManager:
    """Gestor de almacenamiento de datos estructurados"""

    def __init__(self, storage_path: str = "storage"):
        self.storage_path = Path(storage_path)
        self.db_path = self.storage_path / "documents.db"
        self.metadata_path = self.storage_path / "metadata"
        self.backup_path = self.storage_path / "backups"
        
        # Crear directorios si no existen
        self.storage_path.mkdir(exist_ok=True)
        self.metadata_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)
        
        # Configuración del almacenamiento
        self.config = {
            'enable_compression': True,
            'enable_encryption': False,
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'auto_backup': True,
            'backup_interval': 24,  # horas
            'retention_policy': {
                'documents': 365,  # días
                'metadata': 730,   # días
                'backups': 30      # días
            }
        }
        
        # Inicializar base de datos
        self._init_database()
        
        # Estadísticas de almacenamiento
        self.stats = {
            'total_documents': 0,
            'total_size': 0,
            'documents_by_type': {},
            'last_backup': None,
            'storage_efficiency': 0.0
        }

    def _init_database(self):
        """Inicializa la base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de documentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                document_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                hash_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                processing_status TEXT DEFAULT 'stored'
            )
        ''')
        
        # Tabla de metadatos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                metadata_type TEXT NOT NULL,
                metadata_key TEXT NOT NULL,
                metadata_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (document_id)
            )
        ''')
        
        # Tabla de índices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS indices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                index_type TEXT NOT NULL,
                index_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (document_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def store_document(self, document_data: Dict[str, Any], 
                      document_type: str, 
                      original_filename: str) -> Dict[str, Any]:
        """
        Almacena un documento procesado
        
        Args:
            document_data: Datos del documento a almacenar
            document_type: Tipo de documento (pdf, word, email)
            original_filename: Nombre original del archivo
            
        Returns:
            Dict con información del almacenamiento
        """
        try:
            # Generar ID único del documento
            document_id = self._generate_document_id(document_data, original_filename)
            
            # Crear directorio por tipo de documento
            type_dir = self.storage_path / document_type
            type_dir.mkdir(exist_ok=True)
            
            # Guardar datos del documento
            file_path = type_dir / f"{document_id}.pkl"
            
            # Comprimir datos si está habilitado
            if self.config['enable_compression']:
                import gzip
                with gzip.open(file_path, 'wb') as f:
                    pickle.dump(document_data, f)
            else:
                with open(file_path, 'wb') as f:
                    pickle.dump(document_data, f)
            
            # Calcular hash y tamaño
            file_size = file_path.stat().st_size
            hash_value = self._calculate_file_hash(file_path)
            
            # Guardar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO documents 
                (document_id, filename, document_type, file_path, file_size, hash_value, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                original_filename,
                document_type,
                str(file_path),
                file_size,
                hash_value,
                json.dumps(document_data.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
            
            # Actualizar estadísticas
            self._update_stats(document_type, file_size)
            
            return {
                'success': True,
                'document_id': document_id,
                'file_path': str(file_path),
                'file_size': file_size,
                'hash_value': hash_value,
                'storage_efficiency': self._calculate_storage_efficiency()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'document_id': None
            }

    def retrieve_document(self, document_id: str) -> Dict[str, Any]:
        """
        Recupera un documento almacenado
        
        Args:
            document_id: ID del documento a recuperar
            
        Returns:
            Dict con los datos del documento
        """
        try:
            # Buscar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_path, document_type, metadata FROM documents 
                WHERE document_id = ?
            ''', (document_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return {'success': False, 'error': 'Documento no encontrado'}
            
            file_path, document_type, metadata = result
            
            # Cargar datos del archivo
            if self.config['enable_compression']:
                import gzip
                with gzip.open(file_path, 'rb') as f:
                    document_data = pickle.load(f)
            else:
                with open(file_path, 'rb') as f:
                    document_data = pickle.load(f)
            
            return {
                'success': True,
                'document_data': document_data,
                'document_type': document_type,
                'metadata': json.loads(metadata) if metadata else {}
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_metadata(self, document_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza los metadatos de un documento
        
        Args:
            document_id: ID del documento
            metadata: Nuevos metadatos
            
        Returns:
            Dict con resultado de la actualización
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Actualizar metadatos en tabla principal
            cursor.execute('''
                UPDATE documents 
                SET metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE document_id = ?
            ''', (json.dumps(metadata), document_id))
            
            # Guardar metadatos individuales
            for key, value in metadata.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO metadata 
                    (document_id, metadata_type, metadata_key, metadata_value)
                    VALUES (?, ?, ?, ?)
                ''', (document_id, 'general', key, str(value)))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'updated_metadata': metadata}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Elimina un documento del almacenamiento
        
        Args:
            document_id: ID del documento a eliminar
            
        Returns:
            Dict con resultado de la eliminación
        """
        try:
            # Obtener información del documento
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_path, file_size FROM documents 
                WHERE document_id = ?
            ''', (document_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return {'success': False, 'error': 'Documento no encontrado'}
            
            file_path, file_size = result
            
            # Eliminar archivo físico
            if Path(file_path).exists():
                Path(file_path).unlink()
            
            # Eliminar de base de datos
            cursor.execute('DELETE FROM documents WHERE document_id = ?', (document_id,))
            cursor.execute('DELETE FROM metadata WHERE document_id = ?', (document_id,))
            cursor.execute('DELETE FROM indices WHERE document_id = ?', (document_id,))
            
            conn.commit()
            conn.close()
            
            # Actualizar estadísticas
            self.stats['total_documents'] -= 1
            self.stats['total_size'] -= file_size
            
            return {'success': True, 'deleted_document_id': document_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_backup(self) -> Dict[str, Any]:
        """
        Crea un backup del almacenamiento
        
        Returns:
            Dict con información del backup
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_path / f"backup_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            # Copiar base de datos
            shutil.copy2(self.db_path, backup_dir / "documents.db")
            
            # Copiar directorios de documentos
            for doc_type_dir in self.storage_path.iterdir():
                if doc_type_dir.is_dir() and doc_type_dir.name not in ['metadata', 'backups']:
                    shutil.copytree(doc_type_dir, backup_dir / doc_type_dir.name)
            
            # Comprimir backup
            backup_archive = self.backup_path / f"backup_{timestamp}.zip"
            shutil.make_archive(str(backup_archive).replace('.zip', ''), 'zip', backup_dir)
            
            # Eliminar directorio temporal
            shutil.rmtree(backup_dir)
            
            # Actualizar estadísticas
            self.stats['last_backup'] = timestamp
            
            return {
                'success': True,
                'backup_path': str(backup_archive),
                'backup_timestamp': timestamp
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del almacenamiento
        
        Returns:
            Dict con estadísticas completas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar documentos por tipo
            cursor.execute('''
                SELECT document_type, COUNT(*), SUM(file_size) 
                FROM documents 
                GROUP BY document_type
            ''')
            
            type_stats = {}
            total_size = 0
            
            for doc_type, count, size in cursor.fetchall():
                type_stats[doc_type] = {
                    'count': count,
                    'size': size or 0
                }
                total_size += size or 0
            
            conn.close()
            
            # Calcular eficiencia de almacenamiento
            storage_efficiency = self._calculate_storage_efficiency()
            
            return {
                'total_documents': sum(stats['count'] for stats in type_stats.values()),
                'total_size': total_size,
                'documents_by_type': type_stats,
                'storage_efficiency': storage_efficiency,
                'last_backup': self.stats['last_backup'],
                'storage_path': str(self.storage_path),
                'available_space': self._get_available_space()
            }
            
        except Exception as e:
            return {'error': str(e)}

    def _generate_document_id(self, document_data: Dict[str, Any], filename: str) -> str:
        """Genera un ID único para el documento"""
        content_hash = hashlib.sha256(
            json.dumps(document_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{content_hash}_{timestamp}"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula el hash SHA-256 de un archivo"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _update_stats(self, document_type: str, file_size: int):
        """Actualiza las estadísticas de almacenamiento"""
        self.stats['total_documents'] += 1
        self.stats['total_size'] += file_size
        
        if document_type not in self.stats['documents_by_type']:
            self.stats['documents_by_type'][document_type] = 0
        self.stats['documents_by_type'][document_type] += 1

    def _calculate_storage_efficiency(self) -> float:
        """Calcula la eficiencia del almacenamiento"""
        if self.stats['total_size'] == 0:
            return 0.0
        
        # Simulación de eficiencia basada en compresión y organización
        compression_ratio = 0.7 if self.config['enable_compression'] else 1.0
        organization_factor = 0.9  # Factor por organización de archivos
        
        return compression_ratio * organization_factor

    def _get_available_space(self) -> int:
        """Obtiene el espacio disponible en el almacenamiento"""
        try:
            return shutil.disk_usage(self.storage_path).free
        except:
            return 0
