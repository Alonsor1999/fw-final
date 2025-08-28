"""
Pruebas unitarias adicionales para mejorar cobertura del RabbitMQConsumer
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import gzip
import base64
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRabbitMQConsumerCoverage(unittest.TestCase):
    """Pruebas adicionales para mejorar cobertura del RabbitMQConsumer"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        # Configurar TEST_MODE=true

        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            # Crear mocks para todas las dependencias
            self.config = MagicMock()
            self.config.RABBITMQ_URL = "amqp://test"
            self.config.QUEUE_NAME = "test_queue"
            self.config.PREFETCH = 1
            self.config.ON_MISSING = "ack"
            self.config.ROOT_PATH = Path("/tmp")

            self.aws_service = MagicMock()
            self.doc_processor = MagicMock()
            self.name_extractor = MagicMock()
            self.cedula_extractor = MagicMock()
            self.name_extractor_comprehend = MagicMock()
            self.summarize_text_comprehend = MagicMock()
            self.cedula_extractor_comprehend = MagicMock()
            self.summarize_text_extractor = MagicMock()

            self.consumer = RabbitMQConsumer(
                self.config,
                self.aws_service,
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

    def test_decode_pdf_from_message_host_absolute_path_exists(self):
        """Prueba _decode_pdf_from_message con host_absolute_path existente"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        # Crear archivo temporal
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test pdf content")
            tmp_path = tmp.name

        try:
            msg = {"host_absolute_path": tmp_path}
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertEqual(result, b"test pdf content")
        finally:
            os.unlink(tmp_path)

    def test_decode_pdf_from_message_host_absolute_path_not_exists(self):
        """Prueba _decode_pdf_from_message con host_absolute_path no existente"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        msg = {"host_absolute_path": "/path/that/does/not/exist.pdf"}
        result = self.consumer._decode_pdf_from_message(msg)
        self.assertIsNone(result)

    def test_decode_pdf_from_message_host_absolute_path_read_error(self):
        """Prueba _decode_pdf_from_message con error de lectura"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        # Crear directorio (no archivo) para simular error de lectura
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            msg = {"host_absolute_path": tmp_dir}
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertIsNone(result)

    def test_decode_pdf_from_message_gzip_base64_content(self):
        """Prueba _decode_pdf_from_message con contenido gzip+base64"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        # Crear contenido comprimido y codificado
        original_content = b"test pdf content"
        compressed = gzip.compress(original_content)
        encoded = base64.b64encode(compressed).decode('utf-8')

        msg = {
            "content": encoded,
            "content_encoding": "gzip+base64"
        }
        
        result = self.consumer._decode_pdf_from_message(msg)
        self.assertEqual(result, original_content)

    def test_decode_pdf_from_message_gzip_base64_error(self):
        """Prueba _decode_pdf_from_message con error en decodificación gzip+base64"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        msg = {
            "content": "invalid_base64_content",
            "content_encoding": "gzip+base64"
        }
        
        result = self.consumer._decode_pdf_from_message(msg)
        self.assertIsNone(result)

    def test_decode_pdf_from_message_absolute_path_relative(self):
        """Prueba _decode_pdf_from_message con absolute_path relativo"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        msg = {"absolute_path": "relative/path/file.pdf"}
        result = self.consumer._decode_pdf_from_message(msg)
        self.assertIsNone(result)

    def test_decode_pdf_from_message_absolute_path_absolute(self):
        """Prueba _decode_pdf_from_message con absolute_path absoluto"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        # Crear archivo temporal
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test pdf content")
            tmp_path = tmp.name

        try:
            msg = {"absolute_path": tmp_path}
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertEqual(result, b"test pdf content")
        finally:
            os.unlink(tmp_path)

    def test_decode_pdf_from_message_no_valid_source(self):
        """Prueba _decode_pdf_from_message sin fuente válida"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        msg = {"some_other_field": "value"}
        result = self.consumer._decode_pdf_from_message(msg)
        self.assertIsNone(result)

    def test_on_message_invalid_json(self):
        """Prueba on_message con JSON inválido"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()
        
        invalid_json = b"invalid json content"
        
        self.consumer.on_message(mock_channel, mock_method, mock_properties, invalid_json)
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")

    def test_on_message_no_pdf_bytes_ack(self):
        """Prueba on_message sin bytes de PDF (modo ack)"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        self.config.ON_MISSING = "ack"
        
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()
        
        valid_json = json.dumps({"file_name": "test.pdf"}).encode('utf-8')
        
        self.consumer.on_message(mock_channel, mock_method, mock_properties, valid_json)
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")

    def test_on_message_no_pdf_bytes_nack(self):
        """Prueba on_message sin bytes de PDF (modo nack)"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        self.config.ON_MISSING = "nack"
        
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()
        
        valid_json = json.dumps({"file_name": "test.pdf"}).encode('utf-8')
        
        self.consumer.on_message(mock_channel, mock_method, mock_properties, valid_json)
        mock_channel.basic_nack.assert_called_once_with(delivery_tag="test_tag", requeue=False)

    def test_on_message_successful_processing(self):
        """Prueba on_message con procesamiento exitoso completo"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        # Configurar mocks para procesamiento exitoso
        self.doc_processor.extract_text_by_pages.return_value = [("Cédula 12345678", 1)]
        self.doc_processor.process_pdf_bytes.return_value = "Texto completo"
        
        self.cedula_extractor.find_cedulas_with_pages.return_value = [
            {"number": "12345678", "pagPdf": [1]}
        ]
        self.name_extractor.extract_names_with_pages.return_value = [
            {"name": "Juan Pérez", "pagPdf": [1]}
        ]
        
        self.summarize_text_extractor.process.return_value = "Resumen"
        
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()
        
        # Crear contenido PDF válido
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"fake pdf content")
            tmp_path = tmp.name

        try:
            message = {
                "file_name": "test.pdf",
                "host_absolute_path": tmp_path
            }
            valid_json = json.dumps(message).encode('utf-8')
            
            self.consumer.on_message(mock_channel, mock_method, mock_properties, valid_json)
            mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")
        finally:
            os.unlink(tmp_path)

    def test_on_message_processing_exception(self):
        """Prueba on_message cuando ocurre excepción durante procesamiento"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        # Configurar mock para que falle
        self.aws_service.upload_to_s3.side_effect = Exception("Error de S3")
        
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = MagicMock()
        
        # Crear contenido PDF válido
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"fake pdf content")
            tmp_path = tmp.name

        try:
            message = {
                "file_name": "test.pdf",
                "host_absolute_path": tmp_path
            }
            valid_json = json.dumps(message).encode('utf-8')
            
            self.consumer.on_message(mock_channel, mock_method, mock_properties, valid_json)
            mock_channel.basic_nack.assert_called_once_with(delivery_tag="test_tag", requeue=False)
        finally:
            os.unlink(tmp_path)

    @patch('messaging.rabbitmq_consumer.pika')
    def test_run_with_exception(self, mock_pika):
        """Prueba run con excepción general"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_pika.URLParameters.side_effect = Exception("Connection error")
        
        self.consumer.run()
        # Debería manejar la excepción sin fallar

    @patch('messaging.rabbitmq_consumer.pika')
    def test_run_connection_cleanup(self, mock_pika):
        """Prueba run con limpieza de conexiones"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        
        mock_connection.channel.return_value = mock_channel
        mock_connection.is_open = True
        mock_channel.is_open = True
        
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_channel.start_consuming.side_effect = Exception("Test exception")
        
        self.consumer.run()
        
        # Verificar que se cerraron las conexiones
        mock_channel.close.assert_called_once()
        mock_connection.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
