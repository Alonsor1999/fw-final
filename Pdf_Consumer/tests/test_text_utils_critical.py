"""
Pruebas específicas para processors/text_utils.py - Cubrir líneas faltantes
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestTextUtilsCritical(unittest.TestCase):
    """Pruebas específicas para líneas no cubiertas en text_utils.py"""

    def test_sanitize_for_json_none_and_empty(self):
        """Prueba líneas 12-16: sanitize_for_json con None y cadenas vacías"""
        try:
            from processors.text_utils import sanitize_for_json

            # Probar con None (línea 13-14)
            result = sanitize_for_json(None)
            self.assertEqual(result, "")

            # Probar con cadena vacía (línea 13-14)
            result = sanitize_for_json("")
            self.assertEqual(result, "")

            # Probar con espacios en blanco
            result = sanitize_for_json("   ")
            self.assertEqual(result, "   ")  # Espacios se mantienen después de normalización

        except ImportError:
            self.skipTest("text_utils not available")

    def test_sanitize_for_json_encoding_errors(self):
        """Prueba línea 19: manejo de errores de encoding"""
        try:
            from processors.text_utils import sanitize_for_json

            # Crear texto con caracteres problemáticos que causen errores de encoding
            problematic_text = "Texto con caracteres problemáticos: \x00\x01\x02"

            result = sanitize_for_json(problematic_text)
            self.assertIsInstance(result, str)
            # Verificar que caracteres nulos fueron removidos
            self.assertNotIn("\x00", result)

        except ImportError:
            self.skipTest("text_utils not available")

    def test_summarize_text_exception_handling(self):
        """Prueba líneas 47-63: manejo de excepciones en summarize_text"""
        try:
            from processors.text_utils import summarize_text

            # Simular excepción en LSA Summarizer
            with patch('processors.text_utils.LsaSummarizer') as mock_summarizer_class:
                mock_summarizer = MagicMock()
                mock_summarizer.side_effect = Exception("Summarizer failed")
                mock_summarizer_class.return_value = mock_summarizer

                # Texto que active el fallback cuando falla el summarizer
                text = "Esta es una oración de prueba. " * 20
                result = summarize_text(text)

                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)

        except ImportError:
            self.skipTest("text_utils not available")

    def test_summarize_text_empty_summary_fallback(self):
        """Prueba línea 68: fallback cuando summary está vacío"""
        try:
            from processors.text_utils import summarize_text

            # Simular summarizer que retorna lista vacía
            with patch('processors.text_utils.LsaSummarizer') as mock_summarizer_class:
                mock_summarizer = MagicMock()
                mock_summarizer.return_value = []  # Summary vacío
                mock_summarizer_class.return_value = mock_summarizer

                text = "Texto corto para probar fallback."
                result = summarize_text(text)

                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)

        except ImportError:
            self.skipTest("text_utils not available")

    def test_normalize_text_comprehensive(self):
        """Prueba normalize_text con casos edge"""
        try:
            from processors.text_utils import normalize_text

            # Texto con todos los caracteres problemáticos
            text = "Señor Juan®\u00A0con\u200Bfi«texto»'texto'"
            result = normalize_text(text)

            self.assertIsInstance(result, str)
            # Verificar que las correcciones OCR se aplicaron
            self.assertIn("señor", result.lower())

        except ImportError:
            self.skipTest("normalize_text not available")

    def test_simple_tokenizer_methods(self):
        """Prueba métodos de SimpleTokenizer"""
        try:
            from processors.text_utils import SimpleTokenizer

            tokenizer = SimpleTokenizer()

            # Probar to_sentences con texto vacío
            result = tokenizer.to_sentences("")
            self.assertEqual(result, [])

            # Probar to_sentences con texto sin puntuación
            result = tokenizer.to_sentences("texto sin puntuacion")
            self.assertIsInstance(result, list)

            # Probar to_words con texto None
            result = tokenizer.to_words(None)
            self.assertIsInstance(result, list)

        except ImportError:
            self.skipTest("SimpleTokenizer not available")

    def test_summarize_text_edge_cases(self):
        """Prueba casos edge adicionales de summarize_text"""
        try:
            from processors.text_utils import summarize_text

            # Texto None
            result = summarize_text(None)
            self.assertEqual(result, "")

            # Texto solo con espacios
            result = summarize_text("   ")
            self.assertEqual(result, "")

            # Texto muy corto
            result = summarize_text("Corto.")
            self.assertIsInstance(result, str)

        except ImportError:
            self.skipTest("summarize_text not available")

if __name__ == '__main__':
    unittest.main()
