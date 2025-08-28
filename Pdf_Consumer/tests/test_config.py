"""
Pruebas unitarias para la configuración - VERSIÓN ACTUALIZADA
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestConfig(unittest.TestCase):
    """Pruebas para la clase Config"""

    @patch.dict(os.environ, {'TEST_MODE': 'true'}, clear=True)
    def test_config_default_values(self):
        """Prueba los valores por defecto de Config en modo test"""
        try:
            from config.config import Config
            config = Config()

            self.assertTrue(config.TEST_MODE)
            self.assertEqual(config.AWS_REGION, "us-east-1")
            self.assertEqual(config.QUEUE_NAME, "pdf_ingest_q")
            self.assertIsInstance(config.PREFETCH, int)

        except ImportError:
            self.skipTest("Config module not available")

    @patch.dict(os.environ, {
        'TEST_MODE': 'true',
        'AWS_REGION': 'us-east-1',
        'S3_BUCKET': 'test-bucket',
        'RABBITMQ_URL': 'amqp://test:test@localhost:5672/',
        'QUEUE_NAME': 'test-queue',
        'PREFETCH': '10'
    })
    def test_config_initialization_with_env_vars(self):
        """Prueba la inicialización de Config con variables de entorno"""
        try:
            from config.config import Config
            config = Config()

            self.assertEqual(config.AWS_REGION, 'us-east-1')
            self.assertEqual(config.S3_BUCKET, 'test-bucket')
            self.assertEqual(config.RABBITMQ_URL, 'amqp://test:test@localhost:5672/')
            self.assertEqual(config.QUEUE_NAME, 'test-queue')
            self.assertEqual(config.PREFETCH, 10)

        except ImportError:
            self.skipTest("Config module not available")

    @patch.dict(os.environ, {'TEST_MODE': 'false'}, clear=True)
    def test_config_missing_required_vars(self):
        """Prueba el comportamiento cuando faltan variables requeridas sin TEST_MODE"""
        try:
            from config.config import Config
            # Esta prueba debe fallar sin S3_BUCKET cuando TEST_MODE=false
            with self.assertRaises(RuntimeError):
                config = Config()
        except ImportError:
            self.skipTest("Config module not available")

    @patch.dict(os.environ, {
        'TEST_MODE': 'true',
        'PREFETCH': '15'
    })
    def test_config_prefetch_conversion(self):
        """Prueba que PREFETCH se convierte correctamente a entero"""
        try:
            from config.config import Config
            config = Config()
            self.assertIsInstance(config.PREFETCH, int)
            self.assertEqual(config.PREFETCH, 15)
        except ImportError:
            self.skipTest("Config module not available")

class TestConstants(unittest.TestCase):
    """Pruebas para las constantes"""

    def test_constants_import(self):
        """Prueba que las constantes se pueden importar"""
        try:
            from config.constants import CONNECTORS, BLACKLIST_PHRASES
            self.assertIsInstance(CONNECTORS, (list, set, tuple))
            self.assertIsInstance(BLACKLIST_PHRASES, (list, set, tuple))
        except ImportError:
            self.skipTest("Constants module not available")

    def test_constants_values(self):
        """Prueba que las constantes tienen valores válidos"""
        try:
            from config.constants import CONNECTORS, BLACKLIST_PHRASES
            self.assertGreater(len(CONNECTORS), 0)
            self.assertGreater(len(BLACKLIST_PHRASES), 0)
        except ImportError:
            self.skipTest("Constants module not available")

if __name__ == '__main__':
    unittest.main()
