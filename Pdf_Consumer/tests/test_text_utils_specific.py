"""
Pruebas específicas para processors/text_utils.py - Mejorar cobertura al 100%
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestTextUtilsSpecific(unittest.TestCase):
    """Pruebas específicas para líneas no cubiertas en text_utils.py"""

    def test_sanitize_for_json_with_none(self):
        """Prueba sanitize_for_json con None - líneas 12-16"""
        try:
            from processors.text_utils import sanitize_for_json

            # Probar con None
            result = sanitize_for_json(None)
            self.assertEqual(result, "")

            # Probar con cadena vacía
            result = sanitize_for_json("")
            self.assertEqual(result, "")

        except ImportError:
            self.skipTest("text_utils not available")

    def test_sanitize_for_json_encoding_errors(self):
        """Prueba sanitize_for_json con errores de encoding - línea 19"""
        try:
            from processors.text_utils import sanitize_for_json

            # Crear texto con caracteres problemáticos
            problematic_text = "Texto con caracteres especiales: \x00\x01\x02"
            result = sanitize_for_json(problematic_text)
            self.assertIsInstance(result, str)

        except ImportError:
            self.skipTest("text_utils not available")

    def test_summarize_text_long_input(self):
        """Prueba summarize_text con texto largo - líneas 47-63"""
        try:
            from processors.text_utils import summarize_text

            # Crear texto muy largo que active la lógica de resumen
            long_text = "Esta es una oración de prueba. " * 100

            result = summarize_text(long_text)
            self.assertIsInstance(result, str)
            self.assertLessEqual(len(result), len(long_text))

        except ImportError:
            self.skipTest("text_utils not available")

    def test_summarize_text_short_input(self):
        """Prueba summarize_text con texto corto - línea 68"""
        try:
            from processors.text_utils import summarize_text

            # Texto corto que no necesita resumen
            short_text = "Texto corto."

            result = summarize_text(short_text)
            self.assertIsInstance(result, str)

        except ImportError:
            self.skipTest("text_utils not available")

    def test_normalize_text_function(self):
        """Prueba la función normalize_text si existe"""
        try:
            from processors.text_utils import normalize_text

            # Texto con espacios múltiples y caracteres especiales
            text = "  Texto   con    espacios  múltiples  "
            result = normalize_text(text)
            self.assertIsInstance(result, str)

        except ImportError:
            self.skipTest("normalize_text not available")

    def test_text_utils_edge_cases(self):
        """Prueba casos edge adicionales"""
        try:
            from processors.text_utils import sanitize_for_json, summarize_text

            # Casos edge para sanitize_for_json
            edge_cases = [
                "\n\t\r",  # Solo caracteres de control
                "   ",      # Solo espacios
                "Texto\u00ADcon\u200Bcaracteres\u200Cinvisibles",  # Caracteres invisibles
            ]

            for case in edge_cases:
                result = sanitize_for_json(case)
                self.assertIsInstance(result, str)

            # Casos edge para summarize_text
            empty_result = summarize_text("")
            self.assertEqual(empty_result, "")

        except ImportError:
            self.skipTest("text_utils functions not available")

if __name__ == '__main__':
    unittest.main()
