"""
Pruebas adicionales para SummarizeTextExtractorComprehend - Completar 100% cobertura
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import os
import sys
import time
from botocore.exceptions import ClientError

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSummarizeTextExtractorComprehendMissingLines(unittest.TestCase):
    """Pruebas específicas para líneas no cubiertas en SummarizeTextExtractorComprehend"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        try:
            from extractors.summarize_text_extractor_comprehend import SummarizeTextExtractorComprehend
            self.extractor = SummarizeTextExtractorComprehend()
            self.available = True
        except ImportError:
            self.available = False

    def test_call_with_retries_throttling_exception(self):
        """Prueba _call_with_retries con ThrottlingException y reintentos"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_fn = Mock()
        # Primera llamada falla con ThrottlingException, segunda funciona
        mock_fn.side_effect = [
            ClientError({'Error': {'Code': 'ThrottlingException'}}, 'test'),
            "success"
        ]

        with patch('time.sleep') as mock_sleep:
            result = self.extractor._call_with_retries(mock_fn, test_param="value")

            self.assertEqual(result, "success")
            self.assertEqual(mock_fn.call_count, 2)
            mock_sleep.assert_called_once_with(0.5)

    def test_call_with_retries_too_many_requests_exception(self):
        """Prueba _call_with_retries con TooManyRequestsException"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_fn = Mock()
        mock_fn.side_effect = [
            ClientError({'Error': {'Code': 'TooManyRequestsException'}}, 'test'),
            ClientError({'Error': {'Code': 'TooManyRequestsException'}}, 'test'),
            "success"
        ]

        with patch('time.sleep') as mock_sleep:
            result = self.extractor._call_with_retries(mock_fn)

            self.assertEqual(result, "success")
            self.assertEqual(mock_fn.call_count, 3)
            self.assertEqual(mock_sleep.call_count, 2)

    def test_call_with_retries_service_unavailable_exception(self):
        """Prueba _call_with_retries con ServiceUnavailableException"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_fn = Mock()
        mock_fn.side_effect = [
            ClientError({'Error': {'Code': 'ServiceUnavailableException'}}, 'test'),
            "success"
        ]

        with patch('time.sleep') as mock_sleep:
            result = self.extractor._call_with_retries(mock_fn)

            self.assertEqual(result, "success")
            mock_sleep.assert_called_once()

    def test_call_with_retries_non_retryable_exception(self):
        """Prueba _call_with_retries con excepción no reintentable"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_fn = Mock()
        mock_fn.side_effect = ClientError({'Error': {'Code': 'AccessDeniedException'}}, 'test')

        with self.assertRaises(ClientError):
            self.extractor._call_with_retries(mock_fn)

    def test_call_with_retries_max_retries_exceeded(self):
        """Prueba _call_with_retries cuando se exceden los reintentos"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_fn = Mock()
        mock_fn.side_effect = ClientError({'Error': {'Code': 'ThrottlingException'}}, 'test')

        with patch('time.sleep') as mock_sleep:
            with self.assertRaises(ClientError):
                self.extractor._call_with_retries(mock_fn)

            # Debería haber intentado 3 veces (con 3 delays) más el intento final
            self.assertEqual(mock_fn.call_count, 4)
            self.assertEqual(mock_sleep.call_count, 3)

    def test_detect_language_with_multiple_languages(self):
        """Prueba _detect_language con múltiples idiomas detectados"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_response = {
            'Languages': [
                {'LanguageCode': 'en', 'Score': 0.6},
                {'LanguageCode': 'es', 'Score': 0.9},
                {'LanguageCode': 'fr', 'Score': 0.3}
            ]
        }

        with patch.object(self.extractor.comprehend, 'detect_dominant_language', return_value=mock_response):
            result = self.extractor._detect_language("Test text")
            self.assertEqual(result, "es")  # Debería devolver el de mayor score

    def test_detect_language_empty_languages_list(self):
        """Prueba _detect_language con lista vacía de idiomas"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_response = {'Languages': []}

        with patch.object(self.extractor.comprehend, 'detect_dominant_language', return_value=mock_response):
            result = self.extractor._detect_language("Test text")
            self.assertEqual(result, "es")  # Debería usar el idioma por defecto

    def test_detect_language_no_languages_key(self):
        """Prueba _detect_language sin clave Languages en respuesta"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_response = {}

        with patch.object(self.extractor.comprehend, 'detect_dominant_language', return_value=mock_response):
            result = self.extractor._detect_language("Test text")
            self.assertEqual(result, "es")  # Debería usar el idioma por defecto

    def test_split_by_bytes_sentence_exactly_max_bytes(self):
        """Prueba _split_by_bytes con oración que tiene exactamente MAX_BYTES"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        # Crear una oración que tenga exactamente MAX_BYTES bytes
        sentence = "A" * (self.extractor.MAX_BYTES - 1) + "."

        result = self.extractor._split_by_bytes(sentence)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].encode("utf-8")), self.extractor.MAX_BYTES)

    def test_split_by_bytes_multiple_oversized_sentences(self):
        """Prueba _split_by_bytes con múltiples oraciones que exceden MAX_BYTES"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        # Crear múltiples oraciones grandes
        long_sentence = "Esta es una oración muy larga. " * 200
        text = long_sentence + long_sentence + long_sentence

        result = self.extractor._split_by_bytes(text)
        self.assertGreater(len(result), 1)

        # Verificar que ningún chunk exceda MAX_BYTES
        for chunk in result:
            self.assertLessEqual(len(chunk.encode("utf-8")), self.extractor.MAX_BYTES)

    def test_split_by_bytes_multibyte_character_boundary(self):
        """Prueba _split_by_bytes cortando exactamente en límite de carácter multibyte"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        # Crear texto con caracteres multibyte cerca del límite
        base_text = "ñ" * (self.extractor.MAX_BYTES // 2)  # ñ = 2 bytes en UTF-8

        result = self.extractor._split_by_bytes(base_text)
        self.assertGreater(len(result), 0)

        # Verificar que los chunks resultantes son válidos UTF-8
        for chunk in result:
            self.assertIsInstance(chunk, str)
            chunk.encode("utf-8")  # No debería fallar

    def test_normalize_whitespace_with_all_invisible_chars(self):
        """Prueba _normalize_whitespace con todos los caracteres invisibles"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        text = "Texto\u00ADcon\u200Bcaracteres\u200C\u200D\uFEFFinvisibles"
        result = self.extractor._normalize_whitespace(text)

        # Verificar que se eliminaron todos los caracteres invisibles
        self.assertNotIn("\u00AD", result)
        self.assertNotIn("\u200B", result)
        self.assertNotIn("\u200C", result)
        self.assertNotIn("\u200D", result)
        self.assertNotIn("\uFEFF", result)
        self.assertEqual(result, "Textoconcaracteresinvisibles")

    def test_normalize_whitespace_complex_whitespace(self):
        """Prueba _normalize_whitespace con patrones complejos de espacios"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        text = "   Texto   con    espacios   \t\t  múltiples   "
        result = self.extractor._normalize_whitespace(text)

        self.assertEqual(result, "Texto con espacios múltiples")

    @patch('extractors.summarize_text_extractor_comprehend.boto3.client')
    def test_init_with_env_region(self, mock_boto_client):
        """Prueba inicialización usando región de variable de entorno"""
        with patch.dict(os.environ, {'AWS_REGION': 'eu-west-1'}):
            extractor = self.extractor.__class__(region=None)
            self.assertEqual(extractor.region, "eu-west-1")
            mock_boto_client.assert_called_with("comprehend", region_name="eu-west-1")

    @patch('extractors.summarize_text_extractor_comprehend.boto3.client')
    def test_init_with_default_region(self, mock_boto_client):
        """Prueba inicialización con región por defecto"""
        with patch.dict(os.environ, {}, clear=True):
            extractor = self.extractor.__class__(region=None)
            self.assertEqual(extractor.region, "us-east-1")
            mock_boto_client.assert_called_with("comprehend", region_name="us-east-1")

    def test_init_with_custom_parameters(self):
        """Prueba inicialización con parámetros personalizados"""
        extractor = self.extractor.__class__(
            region="ap-south-1",
            max_frases=10,
            debug=False
        )

        self.assertEqual(extractor.region, "ap-south-1")
        self.assertEqual(extractor.max_frases, 10)
        self.assertEqual(extractor.debug, False)

    def test_split_by_bytes_empty_after_strip(self):
        """Prueba _split_by_bytes con texto que queda vacío después de strip"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        text = "   \t   \n   "  # Solo espacios en blanco
        result = self.extractor._split_by_bytes(text)
        self.assertEqual(result, [])

    def test_detect_language_text_truncation(self):
        """Prueba _detect_language con texto que se trunca a 4500 caracteres"""
        if not self.available:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        # Texto más largo que 4500 caracteres
        long_text = "Test text. " * 500  # Aproximadamente 5500 caracteres

        mock_response = {'Languages': [{'LanguageCode': 'en', 'Score': 0.9}]}

        with patch.object(self.extractor.comprehend, 'detect_dominant_language', return_value=mock_response) as mock_detect:
            result = self.extractor._detect_language(long_text)

            # Verificar que se llamó con texto truncado
            call_args = mock_detect.call_args[1]
            self.assertLessEqual(len(call_args['Text']), 4500)
            self.assertEqual(result, "en")

if __name__ == '__main__':
    unittest.main()
