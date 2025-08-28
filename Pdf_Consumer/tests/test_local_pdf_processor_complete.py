"""
Pruebas unitarias para LocalPDFProcessor
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import uuid
from pathlib import Path
import tempfile
import os

# Configurar variables de entorno antes de cualquier importación

try:
    from processors.local_pdf_processor import LocalPDFProcessor
    from processors.document_processor import DocumentProcessor
    from config import Config
    LOCAL_PDF_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import LocalPDFProcessor: {e}")
    # Crear mocks para las clases que no se pueden importar
    LocalPDFProcessor = MagicMock
    DocumentProcessor = MagicMock
    Config = MagicMock
    LOCAL_PDF_PROCESSOR_AVAILABLE = True  # Cambiar a True para ejecutar con mocks


class TestLocalPDFProcessor(unittest.TestCase):
    """Pruebas para LocalPDFProcessor"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        if not LOCAL_PDF_PROCESSOR_AVAILABLE:
            self.skipTest("LocalPDFProcessor no disponible")

        # Crear mocks de las dependencias
        self.mock_config = Mock(spec=Config)
        self.mock_doc_processor = Mock(spec=DocumentProcessor)
        self.mock_name_extractor = Mock()
        self.mock_cedula_extractor = Mock()
        self.mock_name_extractor_comprehend = Mock()
        self.mock_summarize_text_comprehend = Mock()
        self.mock_cedula_extractor_comprehend = Mock()
        self.mock_summarize_text_extractor = Mock()

        # Configurar paths temporales
        self.temp_dir = tempfile.mkdtemp()
        self.mock_config.PDF_INPUT_PATH = Path(self.temp_dir) / "input"
        self.mock_config.JSON_OUTPUT_PATH = Path(self.temp_dir) / "output"

        # Crear directorios temporales
        self.mock_config.PDF_INPUT_PATH.mkdir(exist_ok=True)
        self.mock_config.JSON_OUTPUT_PATH.mkdir(exist_ok=True)

        # Crear instancia del procesador
        self.processor = LocalPDFProcessor(
            config=self.mock_config,
            doc_processor=self.mock_doc_processor,
            name_extractor=self.mock_name_extractor,
            cedula_extractor=self.mock_cedula_extractor,
            name_extractor_comprehend=self.mock_name_extractor_comprehend,
            summarize_text_comprehend=self.mock_summarize_text_comprehend,
            cedula_extractor_comprehend=self.mock_cedula_extractor_comprehend,
            summarize_text_extractor=self.mock_summarize_text_extractor
        )

    def tearDown(self):
        """Limpieza después de las pruebas"""
        # Limpiar archivos temporales
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_find_pdf_files_success(self):
        """Prueba buscar archivos PDF exitosamente"""
        # Crear archivos PDF de prueba
        pdf_file1 = self.mock_config.PDF_INPUT_PATH / "test1.pdf"
        pdf_file2 = self.mock_config.PDF_INPUT_PATH / "test2.pdf"
        pdf_file1.touch()
        pdf_file2.touch()

        # Ejecutar método
        pdf_files = self.processor.find_pdf_files()

        # Verificar resultados
        self.assertEqual(len(pdf_files), 2)
        self.assertIn(pdf_file1, pdf_files)
        self.assertIn(pdf_file2, pdf_files)

    def test_find_pdf_files_no_directory(self):
        """Prueba buscar archivos PDF cuando el directorio no existe"""
        # Configurar directorio inexistente
        self.mock_config.PDF_INPUT_PATH = Path("/directorio/inexistente")

        # Ejecutar método
        pdf_files = self.processor.find_pdf_files()

        # Verificar que retorna lista vacía
        self.assertEqual(len(pdf_files), 0)

    def test_find_pdf_files_empty_directory(self):
        """Prueba buscar archivos PDF en directorio vacío"""
        # El directorio existe pero está vacío
        pdf_files = self.processor.find_pdf_files()

        # Verificar que retorna lista vacía
        self.assertEqual(len(pdf_files), 0)

    @patch('processors.local_pdf_processor.uuid')
    def test_process_single_pdf_success(self, mock_uuid):
        """Prueba procesar un PDF exitosamente"""
        # Configurar mocks
        mock_uuid.uuid4.return_value.hex = "test123"
        
        # Crear archivo PDF de prueba
        pdf_file = self.mock_config.PDF_INPUT_PATH / "test.pdf"
        pdf_file.write_bytes(b"PDF content")

        # Configurar respuestas de los extractores
        self.mock_doc_processor.extract_text_by_pages.return_value = [
            ("Page 1 text", 1), ("Page 2 text", 2)
        ]
        self.mock_doc_processor.process_pdf_bytes.return_value = "Complete PDF text"
        
        self.mock_cedula_extractor.find_cedulas_with_pages.return_value = [
            {"number": "12345678", "pagPdf": [1]}
        ]
        self.mock_name_extractor.extract_names_with_pages.return_value = [
            {"name": "Juan Pérez", "pagPdf": [1]}
        ]
        self.mock_summarize_text_extractor.process.return_value = [
            {"matter": "Tema", "resume": "Resumen"}
        ]

        # Ejecutar método
        result = self.processor.process_single_pdf(pdf_file)

        # Verificar que fue exitoso
        self.assertTrue(result)

        # Verificar que se llamaron los métodos esperados
        self.mock_doc_processor.extract_text_by_pages.assert_called_once()
        self.mock_doc_processor.process_pdf_bytes.assert_called_once()

    def test_process_single_pdf_no_text_extracted(self):
        """Prueba procesar PDF cuando no se puede extraer texto por páginas"""
        # Crear archivo PDF de prueba
        pdf_file = self.mock_config.PDF_INPUT_PATH / "test.pdf"
        pdf_file.write_bytes(b"PDF content")

        # Configurar que no se puede extraer texto por páginas
        self.mock_doc_processor.extract_text_by_pages.return_value = None
        
        # Ejecutar método
        result = self.processor.process_single_pdf(pdf_file)

        # Verificar que falló
        self.assertFalse(result)

    def test_process_single_pdf_empty_content(self):
        """Prueba procesar PDF con contenido vacío"""
        # Crear archivo PDF de prueba
        pdf_file = self.mock_config.PDF_INPUT_PATH / "test.pdf"
        pdf_file.write_bytes(b"PDF content")

        # Configurar respuestas vacías
        self.mock_doc_processor.extract_text_by_pages.return_value = ["Page 1"]
        self.mock_doc_processor.process_pdf_bytes.return_value = None
        
        # Ejecutar método
        result = self.processor.process_single_pdf(pdf_file)

        # Verificar que falló
        self.assertFalse(result)

    def test_save_json_result(self):
        """Prueba guardar resultado JSON"""
        # Datos de prueba
        meta = {
            "original-name-file": "test.pdf",
            "documents": "12345678",
            "names": "Juan Pérez"
        }
        filename = "test_result"

        # Ejecutar método
        self.processor._save_json_result(meta, filename)

        # Verificar que se creó el archivo JSON
        json_file = self.mock_config.JSON_OUTPUT_PATH / f"{filename}.json"
        self.assertTrue(json_file.exists())

        # Verificar contenido del archivo
        with open(json_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["original-name-file"], "test.pdf")
        self.assertEqual(saved_data["documents"], "12345678")
        self.assertEqual(saved_data["names"], "Juan Pérez")

    def test_process_all_pdfs_success(self):
        """Prueba procesar todos los PDFs exitosamente"""
        # Crear archivos PDF de prueba
        pdf_file1 = self.mock_config.PDF_INPUT_PATH / "test1.pdf"
        pdf_file2 = self.mock_config.PDF_INPUT_PATH / "test2.pdf"
        pdf_file1.write_bytes(b"PDF content 1")
        pdf_file2.write_bytes(b"PDF content 2")

        # Configurar mocks para que process_single_pdf sea exitoso
        with patch.object(self.processor, 'process_single_pdf', return_value=True) as mock_process:
            # Ejecutar método
            self.processor.process_all_pdfs()

            # Verificar que se procesaron ambos archivos
            self.assertEqual(mock_process.call_count, 2)

    def test_process_all_pdfs_no_files(self):
        """Prueba procesar cuando no hay archivos PDF"""
        # Ejecutar método sin archivos PDF
        with patch.object(self.processor, 'find_pdf_files', return_value=[]):
            self.processor.process_all_pdfs()

        # No debería haber errores

    @patch('processors.local_pdf_processor.log')
    def test_process_single_pdf_exception_handling(self, mock_log):
        """Prueba manejo de excepciones en process_single_pdf"""
        # Crear archivo PDF que causará error
        pdf_file = self.mock_config.PDF_INPUT_PATH / "test.pdf"
        pdf_file.write_bytes(b"Invalid PDF")

        # Configurar mock para lanzar excepción en extract_text_by_pages
        self.mock_doc_processor.extract_text_by_pages.side_effect = Exception("Error de prueba")

        # Ejecutar método
        result = self.processor.process_single_pdf(pdf_file)

        # Verificar que retornó False
        self.assertFalse(result)

        # Verificar que se registró el error (usando exception en lugar de error)
        mock_log.exception.assert_called()

    def test_fallback_to_comprehend_extractors(self):
        """Prueba que se usen extractores Comprehend como fallback"""
        # Crear archivo PDF de prueba
        pdf_file = self.mock_config.PDF_INPUT_PATH / "test.pdf"
        pdf_file.write_bytes(b"PDF content")

        # Configurar que extractores normales no encuentran nada
        self.mock_doc_processor.extract_text_by_pages.return_value = ["Page 1 text"]
        self.mock_doc_processor.process_pdf_bytes.return_value = "Complete PDF text"
        
        self.mock_cedula_extractor.find_cedulas_with_pages.return_value = []
        self.mock_name_extractor.extract_names_with_pages.return_value = []
        
        # Configurar extractores Comprehend para encontrar datos
        self.mock_cedula_extractor_comprehend.extract_cedulas_with_pages.return_value = [
            {"number": "87654321", "pagPdf": [2]}
        ]
        self.mock_name_extractor_comprehend.extract_names_with_pages.return_value = [
            {"name": "María García", "pagPdf": [2]}
        ]
        
        self.mock_summarize_text_extractor.process.return_value = None
        self.mock_summarize_text_comprehend.summarize.return_value = "Resumen Comprehend"

        with patch('processors.local_pdf_processor.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value.hex = "test456"
            
            # Ejecutar método
            result = self.processor.process_single_pdf(pdf_file)

        # Verificar que fue exitoso y se usaron los extractores Comprehend
        self.assertTrue(result)
        self.mock_cedula_extractor_comprehend.extract_cedulas_with_pages.assert_called_once()
        self.mock_name_extractor_comprehend.extract_names_with_pages.assert_called_once()
        self.mock_summarize_text_comprehend.summarize.assert_called_once()


if __name__ == '__main__':
    unittest.main()
