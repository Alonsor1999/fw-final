"""
Pruebas unitarias adicionales para mejorar cobertura de text_utils
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import re

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestTextUtilsCoverage(unittest.TestCase):
    """Pruebas adicionales para mejorar cobertura de text_utils"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        try:
            from processors.text_utils import normalize_text, summarize_text, sanitize_for_json, SimpleTokenizer
            self.normalize_text = normalize_text
            self.summarize_text = summarize_text
            self.sanitize_for_json = sanitize_for_json
            self.SimpleTokenizer = SimpleTokenizer
            self.available = True
        except ImportError:
            self.available = False

    def test_normalize_text_basic(self):
        """Prueba normalize_text con texto básico"""
        if not self.available:
            self.skipTest("text_utils not available")

        result = self.normalize_text("Texto con MAYÚSCULAS y símbolos!")
        self.assertIsInstance(result, str)

    def test_normalize_text_empty(self):
        """Prueba normalize_text con texto vacío"""
        if not self.available:
            self.skipTest("text_utils not available")

        result = self.normalize_text("")
        self.assertEqual(result, "")

    def test_normalize_text_none(self):
        """Prueba normalize_text con None"""
        if not self.available:
            self.skipTest("text_utils not available")

        result = self.normalize_text(None)
        self.assertEqual(result, "")

    def test_normalize_text_unicode_and_special_chars(self):
        """Prueba normalize_text con caracteres unicode y especiales"""
        if not self.available:
            self.skipTest("text_utils not available")

        # Test caracteres especiales
        text = "Texto\u00A0con\u200Bespacios\u200Craros®marca"
        result = self.normalize_text(text)
        self.assertNotIn("\u00A0", result)  # No-break space should be removed
        self.assertNotIn("\u200B", result)  # Zero width space should be removed
        self.assertNotIn("®", result)  # Registered mark should be removed

    def test_normalize_text_ligatures(self):
        """Prueba normalize_text con ligaduras"""
        if not self.available:
            self.skipTest("text_utils not available")

        text = "ﬁnal ﬂores"  # ligaduras fi y fl
        result = self.normalize_text(text)
        self.assertIn("final", result)
        self.assertIn("flores", result)
        self.assertNotIn("ﬁ", result)
        self.assertNotIn("ﬂ", result)

    def test_normalize_text_quotes_replacement(self):
        """Prueba normalize_text con reemplazo de comillas"""
        if not self.available:
            self.skipTest("text_utils not available")

        # Usar códigos unicode para evitar problemas de sintaxis
        text = "\u00ABtexto\u00BB \u201Ctexto\u201D \u2018apostrofe\u2019 \u2019otro\u2018"
        result = self.normalize_text(text)
        # Verificar que las comillas se reemplazaron
        self.assertNotIn("\u00AB", result)  # «
        self.assertNotIn("\u00BB", result)  # »
        self.assertNotIn("\u201C", result)  # "
        self.assertNotIn("\u201D", result)  # "

    def test_normalize_text_ocr_fixes(self):
        """Prueba normalize_text con correcciones OCR"""
        if not self.available:
            self.skipTest("text_utils not available")

        # Test OCR corrections
        text = "El Sefior Juan y la Sefiora María fueron con el Senor Pedro"
        result = self.normalize_text(text)
        self.assertIn("señor", result.lower())
        # La función reemplaza tanto Sefior como Sefiora con "señor"
        self.assertNotIn("Sefior", result)
        self.assertNotIn("Sefiora", result)
        self.assertNotIn("Senor", result)

    def test_normalize_text_line_breaks_and_hyphens(self):
        """Prueba normalize_text con saltos de línea y guiones"""
        if not self.available:
            self.skipTest("text_utils not available")

        text = "pala-\n bra\r\ncon    espacios\n\n\nseparada"
        result = self.normalize_text(text)
        self.assertIn("palabra", result)  # Should join hyphenated words
        self.assertNotIn("  ", result)  # Multiple spaces should be single
        self.assertNotIn("\n\n\n", result)  # Multiple newlines should be reduced

    def test_simple_tokenizer_to_sentences(self):
        """Prueba SimpleTokenizer.to_sentences"""
        if not self.available:
            self.skipTest("text_utils not available")

        tokenizer = self.SimpleTokenizer()

        # Test with punctuation
        text = "Primera oración. Segunda oración! Tercera oración?"
        result = tokenizer.to_sentences(text)
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 3)

        # Test with empty text
        result = tokenizer.to_sentences("")
        self.assertEqual(result, [])

        # Test with None
        result = tokenizer.to_sentences(None)
        self.assertEqual(result, [])

        # Test without punctuation (should split by periods)
        text = "Primera parte. Segunda parte"
        result = tokenizer.to_sentences(text)
        self.assertIsInstance(result, list)

        # Test with newlines
        text = "Primera línea\nSegunda línea"
        result = tokenizer.to_sentences(text)
        self.assertIsInstance(result, list)

    def test_simple_tokenizer_to_words(self):
        """Prueba SimpleTokenizer.to_words"""
        if not self.available:
            self.skipTest("text_utils not available")

        tokenizer = self.SimpleTokenizer()

        # Test with normal text
        sentence = "Estas son algunas palabras"
        result = tokenizer.to_words(sentence)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Test with empty sentence
        result = tokenizer.to_words("")
        self.assertIsInstance(result, list)

        # Test with None
        result = tokenizer.to_words(None)
        self.assertIsInstance(result, list)

    def test_summarize_text_basic(self):
        """Prueba summarize_text con texto básico"""
        if not self.available:
            self.skipTest("text_utils not available")

        text = "Esta es la primera oración. Esta es la segunda oración. Esta es la tercera oración muy larga que contiene mucho texto para procesar. Esta es la cuarta oración. Esta es la quinta oración final."
        result = self.summarize_text(text, 3)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_summarize_text_empty(self):
        """Prueba summarize_text con texto vacío"""
        if not self.available:
            self.skipTest("text_utils not available")

        result = self.summarize_text("")
        self.assertEqual(result, "")

        result = self.summarize_text(None)
        self.assertEqual(result, "")

    @patch('processors.text_utils.LsaSummarizer')
    @patch('processors.text_utils.PlaintextParser')
    def test_summarize_text_exception_handling(self, mock_parser, mock_summarizer):
        """Prueba summarize_text cuando LsaSummarizer falla"""
        if not self.available:
            self.skipTest("text_utils not available")

        # Mock para que el summarizer lance una excepción
        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.side_effect = Exception("Test exception")
        mock_summarizer.return_value = mock_summarizer_instance

        mock_parser_instance = MagicMock()
        mock_parser_instance.document = MagicMock()
        mock_parser.from_string.return_value = mock_parser_instance

        text = "Esta es una oración de prueba. Esta es otra oración. Y una tercera oración para completar."
        result = self.summarize_text(text, 2)

        # Debería manejar la excepción y retornar algo
        self.assertIsInstance(result, str)

    def test_summarize_text_fallback(self):
        """Prueba summarize_text cuando no se puede generar resumen"""
        if not self.available:
            self.skipTest("text_utils not available")

        # Texto muy corto que podría no generar resumen
        text = "Texto muy corto."
        result = self.summarize_text(text, 5)
        self.assertIsInstance(result, str)

    def test_sanitize_for_json_basic(self):
        """Prueba sanitize_for_json con texto básico"""
        if not self.available:
            self.skipTest("text_utils not available")

        text = "Texto normal con acentos áéíóú"
        result = self.sanitize_for_json(text)
        self.assertIsInstance(result, str)
        self.assertEqual(result, text)  # Should remain the same

    def test_sanitize_for_json_empty_and_none(self):
        """Prueba sanitize_for_json con texto vacío y None"""
        if not self.available:
            self.skipTest("text_utils not available")

        result = self.sanitize_for_json("")
        self.assertEqual(result, "")

        result = self.sanitize_for_json(None)
        self.assertEqual(result, "")

    def test_sanitize_for_json_null_bytes(self):
        """Prueba sanitize_for_json con bytes nulos"""
        if not self.available:
            self.skipTest("text_utils not available")

        text = "Texto con\x00byte nulo"
        result = self.sanitize_for_json(text)
        self.assertNotIn("\x00", result)
        self.assertIn("Texto con", result)

    def test_sanitize_for_json_unicode_normalization(self):
        """Prueba sanitize_for_json con normalización unicode"""
        if not self.available:
            self.skipTest("text_utils not available")

        # Texto con caracteres unicode que necesitan normalización
        text = "café"  # Puede tener diferentes representaciones unicode
        result = self.sanitize_for_json(text)
        self.assertIsInstance(result, str)
        self.assertIn("café", result)

if __name__ == '__main__':
    unittest.main()
