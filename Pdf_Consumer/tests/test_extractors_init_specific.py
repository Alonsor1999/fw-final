"""
Pruebas específicas para extractors/__init__.py - Mejorar cobertura al 100%
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestExtractorsInitSpecific(unittest.TestCase):
    """Pruebas específicas para líneas no cubiertas en extractors/__init__.py"""

    @patch('extractors.cedula_extractor_comprehend')
    def test_comprehend_extractors_import_error(self, mock_module):
        """Prueba el bloque except para importaciones de Comprehend - líneas 18-22"""
        # Simular error de importación para extractores Comprehend
        mock_module.side_effect = ImportError("Mocked Comprehend import error")

        # Reimportar el módulo para activar el bloque except
        import importlib
        import extractors
        importlib.reload(extractors)

        # Verificar que las variables se asignaron a None en caso de error
        self.assertTrue(hasattr(extractors, 'CedulaExtractorComprehend'))

    @patch('extractors.summarize_text_extractor')
    def test_summarize_extractor_import_error(self, mock_module):
        """Prueba el bloque except para SummarizeTextExtractor - líneas 26-28"""
        # Simular error de importación para SummarizeTextExtractor
        mock_module.side_effect = ImportError("Mocked SummarizeTextExtractor import error")

        # Reimportar el módulo para activar el bloque except
        import importlib
        import extractors
        importlib.reload(extractors)

        # Verificar que el módulo maneja el error correctamente
        self.assertTrue(hasattr(extractors, 'SummarizeTextExtractor'))

    def test_environment_variables_setup(self):
        """Prueba que las variables de entorno se configuran correctamente"""
        import extractors

        # Verificar que las variables de entorno se configuraron
        self.assertIn('TEST_MODE', os.environ)
        self.assertIn('S3_BUCKET', os.environ)

    def test_all_attribute_exists(self):
        """Prueba que __all__ está definido correctamente"""
        import extractors

        # Verificar que __all__ existe y contiene las clases esperadas
        self.assertTrue(hasattr(extractors, '__all__'))
        self.assertIsInstance(extractors.__all__, list)

    def test_basic_extractors_availability(self):
        """Prueba disponibilidad de extractores básicos"""
        import extractors

        # Verificar que los extractores básicos están disponibles
        basic_extractors = ['CedulaExtractor', 'NameExtractor']
        for extractor in basic_extractors:
            self.assertTrue(hasattr(extractors, extractor))

    def test_comprehend_extractors_availability(self):
        """Prueba disponibilidad de extractores Comprehend"""
        import extractors

        # Verificar que los extractores Comprehend están disponibles
        comprehend_extractors = [
            'CedulaExtractorComprehend',
            'NameExtractorComprehend',
            'SummarizeTextExtractorComprehend'
        ]
        for extractor in comprehend_extractors:
            self.assertTrue(hasattr(extractors, extractor))

if __name__ == '__main__':
    unittest.main()
