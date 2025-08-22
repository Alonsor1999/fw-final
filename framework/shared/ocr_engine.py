"""
OCREngine MVP - Sistema de OCR con document deduplication y resource tracking
"""
import logging
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """Información del documento para OCR"""
    document_id: str
    file_path: str
    file_size: int
    mime_type: str
    language: str = "en"
    confidence_threshold: float = 0.7
    processing_priority: str = "normal"


@dataclass
class OCRResult:
    """Resultado del procesamiento OCR"""
    document_id: str
    extracted_text: str
    confidence_score: float
    processing_time_ms: int
    language_detected: str
    word_count: int
    character_count: int
    processing_errors: List[str]
    metadata: Dict[str, Any]


class DocumentDeduplicatorMVP:
    """Sistema de deduplicación de documentos"""
    
    def __init__(self):
        self.document_hashes: Dict[str, Dict[str, Any]] = {}
        self.similarity_cache: Dict[str, List[str]] = {}

    def calculate_document_hash(self, file_path: str, file_size: int) -> str:
        """Calcular hash del documento"""
        # For MVP, we'll use a simple hash based on file size and path
        # In production, this would use actual file content
        content = f"{file_path}:{file_size}:{datetime.utcnow().strftime('%Y%m%d')}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_duplicate(self, document_hash: str, similarity_threshold: float = 0.9) -> Optional[str]:
        """Verificar si documento es duplicado"""
        if document_hash in self.document_hashes:
            return self.document_hashes[document_hash]["document_id"]
        
        # Check for similar documents
        for existing_hash, info in self.document_hashes.items():
            similarity = self._calculate_similarity(document_hash, existing_hash)
            if similarity >= similarity_threshold:
                return info["document_id"]
        
        return None

    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """Calcular similitud entre hashes"""
        # Simple similarity calculation for MVP
        # In production, this would use more sophisticated algorithms
        if hash1 == hash2:
            return 1.0
        
        # Count matching characters
        matches = sum(1 for a, b in zip(hash1, hash2) if a == b)
        return matches / max(len(hash1), len(hash2))

    def register_document(self, document_id: str, document_hash: str, metadata: Dict[str, Any]):
        """Registrar documento procesado"""
        self.document_hashes[document_hash] = {
            "document_id": document_id,
            "registered_at": datetime.utcnow(),
            "metadata": metadata
        }

    def get_duplicate_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de deduplicación"""
        return {
            "total_documents": len(self.document_hashes),
            "unique_documents": len(set(info["document_id"] for info in self.document_hashes.values())),
            "duplicate_rate": 1 - (len(set(info["document_id"] for info in self.document_hashes.values())) / len(self.document_hashes)) if self.document_hashes else 0
        }


class ResourceTrackerMVP:
    """Sistema de tracking de recursos para OCR"""
    
    def __init__(self):
        self.resource_usage: Dict[str, Dict[str, Any]] = {}
        self.processing_history: List[Dict[str, Any]] = []

    def start_processing(self, document_id: str) -> Dict[str, Any]:
        """Iniciar tracking de recursos"""
        start_time = datetime.utcnow()
        
        # Simulate resource usage
        resource_info = {
            "document_id": document_id,
            "start_time": start_time,
            "cpu_usage": 0.0,
            "memory_usage_mb": 0,
            "disk_usage_mb": 0,
            "estimated_duration": 30  # seconds
        }
        
        self.resource_usage[document_id] = resource_info
        return resource_info

    def update_resources(self, document_id: str, cpu_percent: float, memory_mb: int, disk_mb: int):
        """Actualizar uso de recursos"""
        if document_id in self.resource_usage:
            self.resource_usage[document_id].update({
                "cpu_usage": cpu_percent,
                "memory_usage_mb": memory_mb,
                "disk_usage_mb": disk_mb,
                "last_updated": datetime.utcnow()
            })

    def finish_processing(self, document_id: str, processing_time_ms: int, success: bool = True):
        """Finalizar tracking de recursos"""
        if document_id in self.resource_usage:
            resource_info = self.resource_usage[document_id]
            resource_info.update({
                "end_time": datetime.utcnow(),
                "processing_time_ms": processing_time_ms,
                "success": success
            })
            
            # Move to history
            self.processing_history.append(resource_info)
            del self.resource_usage[document_id]

    def get_resource_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de recursos"""
        if not self.processing_history:
            return {}
        
        processing_times = [record["processing_time_ms"] for record in self.processing_history]
        cpu_usage = [record.get("cpu_usage", 0) for record in self.processing_history]
        memory_usage = [record.get("memory_usage_mb", 0) for record in self.processing_history]
        
        return {
            "total_processed": len(self.processing_history),
            "avg_processing_time_ms": sum(processing_times) / len(processing_times),
            "avg_cpu_usage": sum(cpu_usage) / len(cpu_usage),
            "avg_memory_usage_mb": sum(memory_usage) / len(memory_usage),
            "currently_processing": len(self.resource_usage)
        }


class OCREngineMVP:
    """Sistema de OCR con deduplicación y resource tracking"""
    
    def __init__(self, max_concurrent_processing: int = 5):
        self.max_concurrent_processing = max_concurrent_processing
        self.deduplicator = DocumentDeduplicatorMVP()
        self.resource_tracker = ResourceTrackerMVP()
        self.processing_queue: List[DocumentInfo] = []
        self.processing_results: Dict[str, OCRResult] = {}
        self.processing_stats = {
            "total_processed": 0,
            "successful_processing": 0,
            "failed_processing": 0,
            "duplicates_found": 0,
            "avg_processing_time_ms": 0.0
        }

    async def process_document(self, document_info: DocumentInfo) -> OCRResult:
        """Procesar documento con OCR"""
        start_time = datetime.utcnow()
        
        try:
            # Check for duplicates
            document_hash = self.deduplicator.calculate_document_hash(
                document_info.file_path, document_info.file_size
            )
            
            duplicate_id = self.deduplicator.is_duplicate(document_hash)
            if duplicate_id:
                self.processing_stats["duplicates_found"] += 1
                logger.info(f"Duplicate document found: {document_info.document_id} -> {duplicate_id}")
                
                # Return cached result if available
                if duplicate_id in self.processing_results:
                    cached_result = self.processing_results[duplicate_id]
                    return OCRResult(
                        document_id=document_info.document_id,
                        extracted_text=cached_result.extracted_text,
                        confidence_score=cached_result.confidence_score,
                        processing_time_ms=1,  # Very fast for duplicates
                        language_detected=cached_result.language_detected,
                        word_count=cached_result.word_count,
                        character_count=cached_result.character_count,
                        processing_errors=["Duplicate document"],
                        metadata={"duplicate_of": duplicate_id}
                    )
            
            # Start resource tracking
            self.resource_tracker.start_processing(document_info.document_id)
            
            # Simulate OCR processing
            await self._simulate_ocr_processing(document_info)
            
            # Generate OCR result
            result = await self._generate_ocr_result(document_info, start_time)
            
            # Register document for deduplication
            self.deduplicator.register_document(
                document_info.document_id, 
                document_hash,
                {"file_size": document_info.file_size, "mime_type": document_info.mime_type}
            )
            
            # Store result
            self.processing_results[document_info.document_id] = result
            
            # Update stats
            self.processing_stats["total_processed"] += 1
            self.processing_stats["successful_processing"] += 1
            
            # Finish resource tracking
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.resource_tracker.finish_processing(document_info.document_id, int(processing_time), True)
            
            logger.info(f"Document processed successfully: {document_info.document_id}")
            return result
            
        except Exception as e:
            # Update stats
            self.processing_stats["total_processed"] += 1
            self.processing_stats["failed_processing"] += 1
            
            # Finish resource tracking with error
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.resource_tracker.finish_processing(document_info.document_id, int(processing_time), False)
            
            logger.error(f"Failed to process document {document_info.document_id}: {e}")
            raise

    async def _simulate_ocr_processing(self, document_info: DocumentInfo):
        """Simular procesamiento OCR"""
        # Simulate processing time based on file size
        base_time = 2.0  # seconds
        size_factor = document_info.file_size / (1024 * 1024)  # MB
        processing_time = base_time + (size_factor * 0.5)
        
        # Update resource usage during processing
        for i in range(int(processing_time * 10)):  # Update every 100ms
            cpu_usage = 50 + (i % 20)  # Simulate CPU variation
            memory_usage = 100 + (i % 50)  # Simulate memory variation
            disk_usage = document_info.file_size / (1024 * 1024)  # MB
            
            self.resource_tracker.update_resources(
                document_info.document_id, cpu_usage, memory_usage, disk_usage
            )
            
            await asyncio.sleep(0.1)

    async def _generate_ocr_result(self, document_info: DocumentInfo, start_time: datetime) -> OCRResult:
        """Generar resultado OCR"""
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Simulate extracted text
        extracted_text = f"Sample extracted text from {document_info.file_path}. "
        extracted_text += "This is a simulated OCR result for demonstration purposes. "
        extracted_text += "In a real implementation, this would contain the actual text extracted from the document."
        
        # Calculate confidence score
        confidence_score = 0.85 + (processing_time / 10000)  # Higher confidence for longer processing
        confidence_score = min(confidence_score, 0.98)  # Cap at 98%
        
        # Count words and characters
        word_count = len(extracted_text.split())
        character_count = len(extracted_text)
        
        return OCRResult(
            document_id=document_info.document_id,
            extracted_text=extracted_text,
            confidence_score=confidence_score,
            processing_time_ms=int(processing_time),
            language_detected=document_info.language,
            word_count=word_count,
            character_count=character_count,
            processing_errors=[],
            metadata={
                "file_size": document_info.file_size,
                "mime_type": document_info.mime_type,
                "confidence_threshold": document_info.confidence_threshold,
                "processing_priority": document_info.processing_priority
            }
        )

    async def get_document_result(self, document_id: str) -> Optional[OCRResult]:
        """Obtener resultado de documento específico"""
        return self.processing_results.get(document_id)

    async def get_processing_status(self, document_id: str) -> Dict[str, Any]:
        """Obtener estado de procesamiento"""
        # Check if currently processing
        if document_id in self.resource_tracker.resource_usage:
            resource_info = self.resource_tracker.resource_usage[document_id]
            return {
                "document_id": document_id,
                "status": "processing",
                "start_time": resource_info["start_time"].isoformat(),
                "cpu_usage": resource_info.get("cpu_usage", 0),
                "memory_usage_mb": resource_info.get("memory_usage_mb", 0),
                "estimated_completion": (
                    resource_info["start_time"] + 
                    timedelta(seconds=resource_info.get("estimated_duration", 30))
                ).isoformat()
            }
        
        # Check if completed
        if document_id in self.processing_results:
            result = self.processing_results[document_id]
            return {
                "document_id": document_id,
                "status": "completed",
                "confidence_score": result.confidence_score,
                "processing_time_ms": result.processing_time_ms,
                "word_count": result.word_count,
                "language_detected": result.language_detected
            }
        
        # Check if in queue
        for doc in self.processing_queue:
            if doc.document_id == document_id:
                return {
                    "document_id": document_id,
                    "status": "queued",
                    "queue_position": self.processing_queue.index(doc) + 1
                }
        
        return {"document_id": document_id, "status": "not_found"}

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento"""
        resource_stats = self.resource_tracker.get_resource_stats()
        duplicate_stats = self.deduplicator.get_duplicate_stats()
        
        return {
            "processing_stats": self.processing_stats,
            "resource_stats": resource_stats,
            "duplicate_stats": duplicate_stats,
            "queue_size": len(self.processing_queue),
            "currently_processing": len(self.resource_tracker.resource_usage),
            "total_results_cached": len(self.processing_results)
        }

    async def search_results(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Buscar en resultados OCR"""
        results = []
        
        for document_id, result in self.processing_results.items():
            if query.lower() in result.extracted_text.lower():
                results.append({
                    "document_id": document_id,
                    "extracted_text": result.extracted_text[:200] + "..." if len(result.extracted_text) > 200 else result.extracted_text,
                    "confidence_score": result.confidence_score,
                    "word_count": result.word_count,
                    "language_detected": result.language_detected,
                    "processing_time_ms": result.processing_time_ms
                })
                
                if len(results) >= limit:
                    break
        
        return results

    async def get_confidence_analysis(self) -> Dict[str, Any]:
        """Obtener análisis de confianza"""
        if not self.processing_results:
            return {}
        
        confidence_scores = [result.confidence_score for result in self.processing_results.values()]
        
        return {
            "total_documents": len(confidence_scores),
            "avg_confidence": sum(confidence_scores) / len(confidence_scores),
            "min_confidence": min(confidence_scores),
            "max_confidence": max(confidence_scores),
            "high_confidence": len([score for score in confidence_scores if score >= 0.9]),
            "medium_confidence": len([score for score in confidence_scores if 0.7 <= score < 0.9]),
            "low_confidence": len([score for score in confidence_scores if score < 0.7])
        }

    async def clear_old_results(self, older_than_hours: int = 24):
        """Limpiar resultados antiguos"""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        # This would typically check creation timestamps
        # For MVP, we'll just clear some results
        if len(self.processing_results) > 100:
            # Keep only the most recent 100 results
            recent_results = dict(list(self.processing_results.items())[-100:])
            cleared_count = len(self.processing_results) - len(recent_results)
            self.processing_results = recent_results
            
            logger.info(f"Cleared {cleared_count} old OCR results")

    async def export_results(self, format: str = "json") -> Dict[str, Any]:
        """Exportar resultados en formato específico"""
        if format.lower() == "json":
            return {
                "processing_stats": self.processing_stats,
                "resource_stats": self.resource_tracker.get_resource_stats(),
                "duplicate_stats": self.deduplicator.get_duplicate_stats(),
                "results_count": len(self.processing_results),
                "export_timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def reset_stats(self):
        """Resetear estadísticas"""
        self.processing_stats = {
            "total_processed": 0,
            "successful_processing": 0,
            "failed_processing": 0,
            "duplicates_found": 0,
            "avg_processing_time_ms": 0.0
        }
        logger.info("OCR engine stats reset")
