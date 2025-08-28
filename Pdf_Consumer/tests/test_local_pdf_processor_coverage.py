"""
Pruebas unitarias adicionales para mejorar cobertura del LocalPDFProcessor
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import tempfile
import json
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestLocalPDFProcessorCoverage(unittest.TestCase):
    """Pruebas adicionales para mejorar cobertura del LocalPDFProcessor"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        # Eliminar env_patcher - ya se configura en conftest.py

        try:
            from processors.local_pdf_processor import LocalPDFProcessor
            from config import Config
            
            # Crear mocks para todas las dependencias
            self.config = MagicMock(spec=Config)
            self.config.PDF_INPUT_PATH = Path("/tmp/test_input")
            self.config.JSON_OUTPUT_PATH = Path("/tmp/test_output")
            
            self.doc_processor = MagicMock()
            self.name_extractor = MagicMock()
            self.cedula_extractor = MagicMock()
            self.name_extractor_comprehend = MagicMock()
            self.summarize_text_comprehend = MagicMock()
            self.cedula_extractor_comprehend = MagicMock()
            self.summarize_text_extractor = MagicMock()
            
            self.processor = LocalPDFProcessor(
                self.config,
                self.doc_processor,
                self.name_extractor,
                self.cedula_extractor,
                self.name_extractor_comprehend,
                self.summarize_text_comprehend,
                self.cedula_extractor_comprehend,
                self.summarize_text_extractor
            )
            self.available = True
        except ImportError:
            self.available = False

    def tearDown(self):
        """Limpieza después de cada prueba"""
        if hasattr(self, 'env_patcher'):
            self.env_patcher.stop()

    def test_find_pdf_files_directory_not_exists(self):
        """Prueba find_pdf_files cuando el directorio no existe"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Configurar path que no existe
        non_existent_path = Path("/tmp/non_existent_directory")
        self.config.PDF_INPUT_PATH = non_existent_path
        
        result = self.processor.find_pdf_files()
        self.assertEqual(result, [])

    @patch('processors.local_pdf_processor.Path.rglob')
    @patch('processors.local_pdf_processor.Path.exists')
    def test_find_pdf_files_with_exception(self, mock_exists, mock_rglob):
        """Prueba find_pdf_files cuando ocurre una excepción"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Simular que el directorio existe pero rglob falla
        mock_exists.return_value = True
        mock_rglob.side_effect = Exception("Error de permisos")
        
        result = self.processor.find_pdf_files()
        self.assertEqual(result, [])

    @patch('processors.local_pdf_processor.Path.rglob')
    @patch('processors.local_pdf_processor.Path.exists')
    def test_find_pdf_files_success(self, mock_exists, mock_rglob):
        """Prueba find_pdf_files funcionando correctamente"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Simular archivos PDF encontrados
        mock_pdf1 = MagicMock()
        mock_pdf2 = MagicMock()
        mock_rglob.return_value = [mock_pdf1, mock_pdf2]
        mock_exists.return_value = True

        result = self.processor.find_pdf_files()
        self.assertEqual(len(result), 2)

    def test_process_single_pdf_no_pages_text(self):
        """Prueba process_single_pdf cuando extract_text_by_pages retorna None"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = Path(tmp.name)
            tmp.write(b"fake pdf content")

        try:
            # Configurar mocks
            self.doc_processor.extract_text_by_pages.return_value = None
            
            result = self.processor.process_single_pdf(pdf_path)
            self.assertFalse(result)
        finally:
            # Limpiar archivo temporal
            pdf_path.unlink()

    def test_process_single_pdf_no_content(self):
        """Prueba process_single_pdf cuando process_pdf_bytes retorna None"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = Path(tmp.name)
            tmp.write(b"fake pdf content")

        try:
            # Configurar mocks
            self.doc_processor.extract_text_by_pages.return_value = [("text", 1)]
            self.doc_processor.process_pdf_bytes.return_value = None
            
            result = self.processor.process_single_pdf(pdf_path)
            self.assertFalse(result)
        finally:
            # Limpiar archivo temporal
            pdf_path.unlink()

    def test_process_single_pdf_success_with_fallback(self):
        """Prueba process_single_pdf con fallbacks funcionando"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = Path(tmp.name)
            tmp.write(b"fake pdf content")

        try:
            # Configurar mocks para simular fallbacks
            self.doc_processor.extract_text_by_pages.return_value = [("Cédula 12345678", 1)]
            self.doc_processor.process_pdf_bytes.return_value = "Texto completo"
            
            # Primer extractor no encuentra nada, segundo sí
            self.cedula_extractor.find_cedulas_with_pages.return_value = []
            self.cedula_extractor_comprehend.extract_cedulas_with_pages.return_value = [
                {"number": "12345678", "pagPdf": [1]}
            ]
            
            self.name_extractor.extract_names_with_pages.return_value = []
            self.name_extractor_comprehend.extract_names_with_pages.return_value = [
                {"name": "Juan Pérez", "pagPdf": [1]}
            ]
            
            # Configurar summarizer
            self.summarize_text_extractor.process.return_value = None
            self.summarize_text_comprehend.summarize.return_value = "Resumen del documento"
            
            # Mock para guardar JSON
            with patch.object(self.processor, '_save_json_result') as mock_save:
                result = self.processor.process_single_pdf(pdf_path)
                self.assertTrue(result)
                mock_save.assert_called_once()
        finally:
            # Limpiar archivo temporal
            pdf_path.unlink()

    def test_process_single_pdf_with_json_matter(self):
        """Prueba process_single_pdf con matter como JSON string"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = Path(tmp.name)
            tmp.write(b"fake pdf content")

        try:
            # Configurar mocks
            self.doc_processor.extract_text_by_pages.return_value = [("text", 1)]
            self.doc_processor.process_pdf_bytes.return_value = "Texto completo"
            
            self.cedula_extractor.find_cedulas_with_pages.return_value = []
            self.name_extractor.extract_names_with_pages.return_value = []
            
            # Matter como JSON válido
            json_matter = '[{"matter": "Test", "resume": "Test resume"}]'
            self.summarize_text_extractor.process.return_value = json_matter
            
            # Mock para guardar JSON
            with patch.object(self.processor, '_save_json_result') as mock_save:
                result = self.processor.process_single_pdf(pdf_path)
                self.assertTrue(result)
                mock_save.assert_called_once()
        finally:
            # Limpiar archivo temporal
            pdf_path.unlink()

    def test_process_single_pdf_with_invalid_json_matter(self):
        """Prueba process_single_pdf con matter como JSON inválido"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = Path(tmp.name)
            tmp.write(b"fake pdf content")

        try:
            # Configurar mocks
            self.doc_processor.extract_text_by_pages.return_value = [("text", 1)]
            self.doc_processor.process_pdf_bytes.return_value = "Texto completo"
            
            self.cedula_extractor.find_cedulas_with_pages.return_value = []
            self.name_extractor.extract_names_with_pages.return_value = []
            
            # Matter como JSON inválido
            invalid_json = "invalid json string"
            self.summarize_text_extractor.process.return_value = invalid_json
            
            # Mock para guardar JSON
            with patch.object(self.processor, '_save_json_result') as mock_save:
                result = self.processor.process_single_pdf(pdf_path)
                self.assertTrue(result)
                mock_save.assert_called_once()
        finally:
            # Limpiar archivo temporal
            pdf_path.unlink()

    def test_process_single_pdf_with_exception(self):
        """Prueba process_single_pdf cuando ocurre una excepción"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = Path(tmp.name)
            tmp.write(b"fake pdf content")

        try:
            # Configurar mock para que falle
            self.doc_processor.extract_text_by_pages.side_effect = Exception("Error de procesamiento")
            
            result = self.processor.process_single_pdf(pdf_path)
            self.assertFalse(result)
        finally:
            # Limpiar archivo temporal
            pdf_path.unlink()

    @patch('processors.local_pdf_processor.json.dumps')
    def test_save_json_result(self, mock_json_dumps):
        """Prueba _save_json_result"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Configurar directorio temporal para salida
        with tempfile.TemporaryDirectory() as temp_dir:
            self.config.JSON_OUTPUT_PATH = Path(temp_dir)
            
            meta = {"test": "data"}
            file_id = "test_file"
            
            mock_json_dumps.return_value = '{"test": "data"}'
            
            # Mock de write_text
            with patch('pathlib.Path.write_text') as mock_write:
                self.processor._save_json_result(meta, file_id)
                mock_write.assert_called_once()

    def test_process_all_pdfs_no_files(self):
        """Prueba process_all_pdfs cuando no hay archivos"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        with patch.object(self.processor, 'find_pdf_files', return_value=[]):
            self.processor.process_all_pdfs()
            # No debería fallar

    def test_process_all_pdfs_with_files(self):
        """Prueba process_all_pdfs con archivos para procesar"""
        if not self.available:
            self.skipTest("LocalPDFProcessor not available")

        # Crear archivos PDF temporales
        pdf_files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(suffix=f'_{i}.pdf', delete=False) as tmp:
                pdf_path = Path(tmp.name)
                tmp.write(b"fake pdf content")
                pdf_files.append(pdf_path)

        try:
            with patch.object(self.processor, 'find_pdf_files', return_value=pdf_files):
                with patch.object(self.processor, 'process_single_pdf', return_value=True):
                    self.processor.process_all_pdfs()
                    # Debería procesar todos los archivos sin fallar
        finally:
            # Limpiar archivos temporales
            for pdf_path in pdf_files:
                pdf_path.unlink()

if __name__ == '__main__':
    unittest.main()
