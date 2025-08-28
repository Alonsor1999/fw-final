"""
Pruebas unitarias adicionales para mejorar cobertura de document_processor.py
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDocumentProcessorCoverage(unittest.TestCase):
    """Pruebas adicionales para mejorar cobertura de document_processor"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        try:
            from processors.document_processor import DocumentProcessor
            self.processor = DocumentProcessor()
            self.available = True
        except ImportError:
            self.available = False

    @patch('processors.document_processor.fitz')
    def test_extract_text_from_pdf_bytes_exception(self, mock_fitz):
        """Prueba _extract_text_from_pdf_bytes con excepción - líneas 31-33"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        # Mock para que fitz.open lance una excepción
        mock_fitz.open.side_effect = Exception("Error al abrir PDF")

        pdf_bytes = b"fake_pdf_content"
        result = self.processor._extract_text_from_pdf_bytes(pdf_bytes)

        self.assertIsNone(result)

    @patch('processors.document_processor.fitz')
    def test_extract_text_from_pdf_bytes_success(self, mock_fitz):
        """Prueba _extract_text_from_pdf_bytes con éxito"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        # Mock para simular un PDF exitoso
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Texto extraído del PDF"
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc

        pdf_bytes = b"fake_pdf_content"
        result = self.processor._extract_text_from_pdf_bytes(pdf_bytes)

        self.assertEqual(result, "Texto extraído del PDF")
        mock_doc.close.assert_called_once()

    @patch('processors.document_processor.fitz')
    def test_extract_text_from_pdf_bytes_empty_text(self, mock_fitz):
        """Prueba _extract_text_from_pdf_bytes con texto vacío"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        # Mock para simular un PDF sin texto
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "   "  # Solo espacios
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc

        pdf_bytes = b"fake_pdf_content"
        result = self.processor._extract_text_from_pdf_bytes(pdf_bytes)

        self.assertIsNone(result)

    @patch('processors.document_processor.fitz')
    def test_extract_text_from_pdf_bytes_multiple_pages(self, mock_fitz):
        """Prueba _extract_text_from_pdf_bytes con múltiples páginas"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        # Mock para simular un PDF con múltiples páginas
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Página 1"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Página 2"

        mock_doc.load_page.side_effect = [mock_page1, mock_page2]
        mock_doc.__len__.return_value = 2
        mock_fitz.open.return_value = mock_doc

        pdf_bytes = b"fake_pdf_content"
        result = self.processor._extract_text_from_pdf_bytes(pdf_bytes)

        self.assertEqual(result, "Página 1Página 2")

    @patch('processors.document_processor.DocumentProcessor._extract_text_from_pdf_bytes')
    def test_process_document_with_pdf_bytes(self, mock_extract):
        """Prueba process_document con pdf_bytes"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        mock_extract.return_value = "Texto extraído"

        pdf_bytes = b"fake_pdf_content"
        result = self.processor.process_document(pdf_bytes=pdf_bytes)

        self.assertTrue(result['success'])
        self.assertEqual(result['text'], "Texto extraído")
        self.assertIsNone(result['error'])

    @patch('builtins.open', new_callable=mock_open, read_data=b"fake_pdf_content")
    @patch('processors.document_processor.DocumentProcessor._extract_text_from_pdf_bytes')
    def test_process_document_with_file_path(self, mock_extract, mock_file):
        """Prueba process_document con file_path"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        mock_extract.return_value = "Texto extraído del archivo"

        file_path = "/path/to/test.pdf"
        result = self.processor.process_document(file_path=file_path)

        self.assertTrue(result['success'])
        self.assertEqual(result['text'], "Texto extraído del archivo")
        self.assertIsNone(result['error'])
        mock_file.assert_called_once_with(file_path, 'rb')

    def test_process_document_no_params(self):
        """Prueba process_document sin parámetros"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        result = self.processor.process_document()

        self.assertFalse(result['success'])
        self.assertIsNone(result['text'])
        self.assertIn("Debe proporcionar file_path o pdf_bytes", result['error'])

    @patch('builtins.open')
    def test_process_document_file_exception(self, mock_open_func):
        """Prueba process_document con excepción al abrir archivo"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        mock_open_func.side_effect = FileNotFoundError("Archivo no encontrado")

        result = self.processor.process_document(file_path="/path/nonexistent.pdf")

        self.assertFalse(result['success'])
        self.assertIsNone(result['text'])
        self.assertIn("Archivo no encontrado", result['error'])

    @patch('processors.document_processor.fitz')
    def test_validate_pdf_success(self, mock_fitz):
        """Prueba validate_pdf con PDF válido"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc

        pdf_bytes = b"fake_pdf_content"
        result = self.processor.validate_pdf(pdf_bytes)

        self.assertTrue(result)
        mock_doc.close.assert_called_once()

    @patch('processors.document_processor.fitz')
    def test_validate_pdf_exception(self, mock_fitz):
        """Prueba validate_pdf con PDF inválido"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        mock_fitz.open.side_effect = Exception("PDF inválido")

        pdf_bytes = b"fake_invalid_content"
        result = self.processor.validate_pdf(pdf_bytes)

        self.assertFalse(result)

    def test_init_processor(self):
        """Prueba inicialización del procesador"""
        if not self.available:
            self.skipTest("DocumentProcessor not available")

        processor = self.processor
        self.assertIsNotNone(processor.logger)

if __name__ == '__main__':
    unittest.main()
