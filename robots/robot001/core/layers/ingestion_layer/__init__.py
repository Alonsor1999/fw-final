"""
Capa de Ingesta - Primera capa del sistema de procesamiento de documentos

Esta capa se encarga de:
- Clasificación de documentos
- Validación de formatos
- Escaneo de seguridad
"""

from .document_classifier import DocumentClassifier
from .format_validator import FormatValidator
from .security_scanner import SecurityScanner
from .ingestion_coordinator import IngestionCoordinator

__all__ = ['DocumentClassifier', 'FormatValidator', 'SecurityScanner', 'IngestionCoordinator']
