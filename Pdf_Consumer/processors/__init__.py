"""
Paquete de procesadores de documentos
"""

from .document_processor import DocumentProcessor
from .local_pdf_processor import LocalPDFProcessor
from .text_utils import summarize_text, sanitize_for_json

__all__ = [
    'DocumentProcessor',
    'LocalPDFProcessor',
    'summarize_text',
    'sanitize_for_json'
]
