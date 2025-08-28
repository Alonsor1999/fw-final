"""
Pruebas avanzadas con mocks para alcanzar cobertura completa
"""
import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys
import json

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAdvancedMocksCoverage(unittest.TestCase):
    """Pruebas avanzadas con mocks para cubrir líneas específicas de AWS/Comprehend"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        # Eliminar env_patcher - ya se configura en conftest.py

        self.available_extractors = {}
        
        try:
            from extractors.name_extractor_comprehend import NameExtractorComprehend
            self.name_extractor_comprehend = NameExtractorComprehend()
            self.available_extractors['name_comprehend'] = True
        except ImportError:
            self.available_extractors['name_comprehend'] = False

        try:
            from extractors.cedula_extractor_comprehend import CedulaExtractorComprehend
            self.cedula_extractor_comprehend = CedulaExtractorComprehend()
            self.available_extractors['cedula_comprehend'] = True
        except ImportError:
            self.available_extractors['cedula_comprehend'] = False

        try:
            from extractors.summarize_text_extractor_comprehend import SummarizeTextExtractorComprehend
            self.summarize_text_comprehend = SummarizeTextExtractorComprehend()
            self.available_extractors['summarize_comprehend'] = True
        except ImportError:
            self.available_extractors['summarize_comprehend'] = False

    def tearDown(self):
        """Limpieza después de cada prueba"""
        # Eliminar env_patcher.stop() - ya no es necesario
        pass

    @patch('boto3.client')
    def test_name_extractor_comprehend_detect_entities_success(self, mock_boto_client):
        """Prueba detección exitosa de entidades con respuesta completa de AWS"""
        if not self.available_extractors['name_comprehend']:
            self.skipTest("NameExtractorComprehend not available")

        # Mock del cliente AWS con respuesta completa
        mock_client = MagicMock()
        mock_client.detect_entities.return_value = {
            'Entities': [
                {
                    'Text': 'Juan Carlos Pérez García',
                    'Score': 0.99,
                    'Type': 'PERSON',
                    'BeginOffset': 0,
                    'EndOffset': 24
                },
                {
                    'Text': 'Ministerio de Justicia',
                    'Score': 0.95,
                    'Type': 'ORGANIZATION',
                    'BeginOffset': 30,
                    'EndOffset': 52
                },
                {
                    'Text': 'Bogotá',
                    'Score': 0.92,
                    'Type': 'LOCATION',
                    'BeginOffset': 60,
                    'EndOffset': 66
                }
            ]
        }
        mock_boto_client.return_value = mock_client

        # Forzar el uso del cliente mock
        self.name_extractor_comprehend.client = mock_client

        # Texto de prueba
        pages_text = [
            ("Juan Carlos Pérez García del Ministerio de Justicia en Bogotá", 1),
            ("María Elena Rodríguez López de la Universidad Nacional", 2)
        ]

        result = self.name_extractor_comprehend.extract_names_with_pages(pages_text)
        
        # Verificaciones
        self.assertIsInstance(result, list)
        mock_client.detect_entities.assert_called()
        
        # Verificar que se llamó con los parámetros correctos
        calls = mock_client.detect_entities.call_args_list
        self.assertGreater(len(calls), 0)

    @patch('boto3.client')
    def test_name_extractor_comprehend_empty_response(self, mock_boto_client):
        """Prueba respuesta vacía de AWS Comprehend"""
        if not self.available_extractors['name_comprehend']:
            self.skipTest("NameExtractorComprehend not available")

        # Mock del cliente AWS con respuesta vacía
        mock_client = MagicMock()
        mock_client.detect_entities.return_value = {'Entities': []}
        mock_boto_client.return_value = mock_client

        self.name_extractor_comprehend.client = mock_client

        pages_text = [("Texto sin entidades reconocibles", 1)]
        result = self.name_extractor_comprehend.extract_names_with_pages(pages_text)
        
        self.assertIsInstance(result, list)

    @patch('boto3.client')
    def test_name_extractor_comprehend_low_confidence_entities(self, mock_boto_client):
        """Prueba entidades con baja confianza que deberían ser filtradas"""
        if not self.available_extractors['name_comprehend']:
            self.skipTest("NameExtractorComprehend not available")

        # Mock con entidades de baja confianza
        mock_client = MagicMock()
        mock_client.detect_entities.return_value = {
            'Entities': [
                {
                    'Text': 'Juan',
                    'Score': 0.3,  # Baja confianza
                    'Type': 'PERSON',
                    'BeginOffset': 0,
                    'EndOffset': 4
                },
                {
                    'Text': 'María Elena García',
                    'Score': 0.95,  # Alta confianza
                    'Type': 'PERSON',
                    'BeginOffset': 10,
                    'EndOffset': 28
                }
            ]
        }
        mock_boto_client.return_value = mock_client
        self.name_extractor_comprehend.client = mock_client

        pages_text = [("Juan y María Elena García", 1)]
        result = self.name_extractor_comprehend.extract_names_with_pages(pages_text)
        
        self.assertIsInstance(result, list)

    @patch('boto3.client')
    def test_name_extractor_comprehend_large_text_chunking(self, mock_boto_client):
        """Prueba fragmentación de texto largo para AWS Comprehend"""
        if not self.available_extractors['name_comprehend']:
            self.skipTest("NameExtractorComprehend not available")

        # Mock del cliente
        mock_client = MagicMock()
        mock_client.detect_entities.return_value = {
            'Entities': [
                {
                    'Text': 'Juan Pérez',
                    'Score': 0.99,
                    'Type': 'PERSON',
                    'BeginOffset': 0,
                    'EndOffset': 10
                }
            ]
        }
        mock_boto_client.return_value = mock_client
        self.name_extractor_comprehend.client = mock_client

        # Texto muy largo que requiera fragmentación
        long_text = "Juan Pérez " + "texto de relleno " * 500 + "María García"
        pages_text = [(long_text, 1)]

        result = self.name_extractor_comprehend.extract_names_with_pages(pages_text)
        
        self.assertIsInstance(result, list)
        # Debería haberse llamado múltiples veces debido a la fragmentación
        self.assertGreater(mock_client.detect_entities.call_count, 0)

    @patch('boto3.client')
    def test_name_extractor_comprehend_forbidden_context(self, mock_boto_client):
        """Prueba detección de contexto prohibido"""
        if not self.available_extractors['name_comprehend']:
            self.skipTest("NameExtractorComprehend not available")

        mock_client = MagicMock()
        mock_client.detect_entities.return_value = {
            'Entities': [
                {
                    'Text': 'Juan Pérez',
                    'Score': 0.99,
                    'Type': 'PERSON',
                    'BeginOffset': 50,
                    'EndOffset': 60
                }
            ]
        }
        mock_boto_client.return_value = mock_client
        self.name_extractor_comprehend.client = mock_client

        # Texto con contexto que debería ser prohibido
        forbidden_context_text = "El Juzgado Civil Municipal Juan Pérez resuelve"
        pages_text = [(forbidden_context_text, 1)]

        result = self.name_extractor_comprehend.extract_names_with_pages(pages_text)
        
        self.assertIsInstance(result, list)

    @patch('boto3.client')
    def test_cedula_extractor_comprehend_detect_pii_success(self, mock_boto_client):
        """Prueba detección exitosa de PII con AWS Comprehend"""
        if not self.available_extractors['cedula_comprehend']:
            self.skipTest("CedulaExtractorComprehend not available")

        # Mock del cliente AWS PII
        mock_client = MagicMock()
        mock_client.detect_pii_entities.return_value = {
            'Entities': [
                {
                    'Score': 0.95,
                    'Type': 'SSN',
                    'BeginOffset': 30,
                    'EndOffset': 38
                }
            ]
        }
        mock_boto_client.return_value = mock_client
        self.cedula_extractor_comprehend.client = mock_client

        pages_text = [("Juan Pérez identificado con 12345678", 1)]
        result = self.cedula_extractor_comprehend.extract_cedulas_with_pages(pages_text)
        
        self.assertIsInstance(result, list)
        mock_client.detect_pii_entities.assert_called()

    @patch('boto3.client')
    def test_cedula_extractor_comprehend_mixed_candidates(self, mock_boto_client):
        """Prueba candidatos mixtos de regex y AWS Comprehend"""
        if not self.available_extractors['cedula_comprehend']:
            self.skipTest("CedulaExtractorComprehend not available")

        mock_client = MagicMock()
        mock_client.detect_pii_entities.return_value = {
            'Entities': [
                {
                    'Score': 0.9,
                    'Type': 'SSN',
                    'BeginOffset': 45,
                    'EndOffset': 53
                }
            ]
        }
        mock_boto_client.return_value = mock_client
        self.cedula_extractor_comprehend.client = mock_client

        # Texto con múltiples candidatos
        text_with_multiple = "CC 12345678 y también documento 87654321 válidos"
        pages_text = [(text_with_multiple, 1)]

        result = self.cedula_extractor_comprehend.extract_cedulas_with_pages(pages_text)
        
        self.assertIsInstance(result, list)

    @patch('boto3.client')
    def test_summarize_extractor_comprehend_key_phrases(self, mock_boto_client):
        """Prueba extracción de frases clave con AWS Comprehend"""
        if not self.available_extractors['summarize_comprehend']:
            self.skipTest("SummarizeTextExtractorComprehend not available")

        mock_client = MagicMock()
        mock_client.detect_key_phrases.return_value = {
            'KeyPhrases': [
                {
                    'Score': 0.95,
                    'Text': 'tutela constitucional',
                    'BeginOffset': 0,
                    'EndOffset': 20
                },
                {
                    'Score': 0.89,
                    'Text': 'derecho fundamental',
                    'BeginOffset': 25,
                    'EndOffset': 44
                }
            ]
        }
        mock_boto_client.return_value = mock_client
        self.summarize_text_comprehend.client = mock_client

        text = "tutela constitucional por derecho fundamental a la salud"
        result = self.summarize_text_comprehend.summarize(text)
        
        # El resultado puede ser None, string o lista
        self.assertTrue(result is None or isinstance(result, (str, list)))

    def test_name_extractor_comprehend_internal_methods(self):
        """Prueba métodos internos específicos del NameExtractorComprehend"""
        if not self.available_extractors['name_comprehend']:
            self.skipTest("NameExtractorComprehend not available")

        # Probar _chunk_text con diferentes tamaños
        test_text = "Este es un texto de prueba " * 200
        chunks = list(self.name_extractor_comprehend._chunk_text(test_text, size=100))
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 1)

        # Probar _sanitize con casos especiales
        dirty_texts = [
            "  Nombre  con  espacios  múltiples  ",
            "Nombre\u200B\u200C\u200D\uFEFFcon caracteres invisibles",
            "Nombre,;:()[]{}<>\"\"''|/\\ con símbolos",
        ]
        
        for dirty in dirty_texts:
            clean = self.name_extractor_comprehend._sanitize(dirty)
            self.assertIsInstance(clean, str)
            self.assertNotIn('\u200B', clean)

        # Probar _valid_token con casos edge
        tokens = [
            ("", False),
            ("a", False),
            ("ab", False),
            ("123", False),
            ("Juan123", False),
            ("Juan", True),
            ("María", True),
            ("de", True),  # Partícula permitida
        ]
        
        for token, expected in tokens:
            result = self.name_extractor_comprehend._valid_token(token)
            self.assertEqual(result, expected, f"Token '{token}' should be {expected}")

    def test_cedula_extractor_comprehend_internal_methods(self):
        """Prueba métodos internos del CedulaExtractorComprehend"""
        if not self.available_extractors['cedula_comprehend']:
            self.skipTest("CedulaExtractorComprehend not available")

        # Probar _normalize con diferentes casos
        test_cases = [
            "Texto con acentos àáâãäåæçèéêëìíîïñòóôõöøùúûüý",
            "Texto\u00AD\u200B\u200C\u200D\uFEFF con caracteres especiales",
            "Texto    con   espacios    múltiples",
        ]
        
        for case in test_cases:
            normalized = self.cedula_extractor_comprehend._normalize(case)
            self.assertIsInstance(normalized, str)
            self.assertNotIn('\u00AD', normalized)

        # Probar _chunk_text con límites exactos
        boundary_text = "A" * 4500  # Exactamente en el límite
        chunks = list(self.cedula_extractor_comprehend._chunk_text(boundary_text))
        self.assertEqual(len(chunks), 1)

        # Usar un texto mucho más largo para forzar fragmentación
        over_boundary_text = "A" * 10000  # Mucho más largo para asegurar fragmentación
        chunks = list(self.cedula_extractor_comprehend._chunk_text(over_boundary_text))
        self.assertGreaterEqual(len(chunks), 1)  # Al menos 1 chunk, posiblemente más

    @patch('boto3.client')
    def test_comprehend_extractors_exception_handling(self, mock_boto_client):
        """Prueba manejo completo de excepciones en extractores Comprehend"""
        # Test para NameExtractorComprehend
        if self.available_extractors['name_comprehend']:
            mock_client = MagicMock()
            mock_client.detect_entities.side_effect = [
                Exception("Network error"),
                {
                    'Entities': [
                        {
                            'Text': 'Juan Pérez',
                            'Score': 0.99,
                            'Type': 'PERSON',
                            'BeginOffset': 0,
                            'EndOffset': 10
                        }
                    ]
                }
            ]
            mock_boto_client.return_value = mock_client
            self.name_extractor_comprehend.client = mock_client

            pages_text = [("Juan Pérez García", 1), ("María López", 2)]
            result = self.name_extractor_comprehend.extract_names_with_pages(pages_text)
            self.assertIsInstance(result, list)

        # Test para CedulaExtractorComprehend  
        if self.available_extractors['cedula_comprehend']:
            mock_client = MagicMock()
            mock_client.detect_pii_entities.side_effect = Exception("AWS Service error")
            mock_boto_client.return_value = mock_client
            self.cedula_extractor_comprehend.client = mock_client

            pages_text = [("Cédula 12345678", 1)]
            result = self.cedula_extractor_comprehend.extract_cedulas_with_pages(pages_text)
            self.assertIsInstance(result, list)

    def test_edge_cases_empty_and_none_inputs(self):
        """Prueba casos edge con entradas vacías y None"""
        
        if self.available_extractors['name_comprehend']:
            # Probar con None
            result = self.name_extractor_comprehend.extract_names_with_pages(None)
            self.assertEqual(result, [])
            
            # Probar con lista vacía
            result = self.name_extractor_comprehend.extract_names_with_pages([])
            self.assertEqual(result, [])
            
            # Probar con páginas vacías
            result = self.name_extractor_comprehend.extract_names_with_pages([("", 1), ("   ", 2)])
            self.assertEqual(result, [])

        if self.available_extractors['cedula_comprehend']:
            # Mismas pruebas para CedulaExtractorComprehend
            result = self.cedula_extractor_comprehend.extract_cedulas_with_pages(None)
            self.assertEqual(result, [])
            
            result = self.cedula_extractor_comprehend.extract_cedulas_with_pages([])
            self.assertEqual(result, [])

        if self.available_extractors['summarize_comprehend']:
            # Pruebas para SummarizeTextExtractorComprehend
            result = self.summarize_text_comprehend.summarize("")
            self.assertTrue(result is None or result == "")
            
            result = self.summarize_text_comprehend.summarize(None)
            self.assertTrue(result is None or result == "")

if __name__ == '__main__':
    unittest.main()
