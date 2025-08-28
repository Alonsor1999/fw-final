"""
Capa de Procesamiento Especializado - Segunda capa del sistema de procesamiento de documentos

Esta capa se encarga de:
- Procesamiento nativo de PDFs
- Procesamiento de documentos Word
- Procesamiento de emails
"""

from .pdf_processor import PDFNativeProcessor
from .word_processor import WordDocumentProcessor
from .email_processor import EmailProcessor
from .specialized_processing_coordinator import SpecializedProcessingCoordinator

__all__ = ['PDFNativeProcessor', 'WordDocumentProcessor', 'EmailProcessor', 'SpecializedProcessingCoordinator']
