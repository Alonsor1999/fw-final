"""
Pruebas exhaustivas para RabbitMQConsumer - 100% cobertura
"""
import unittest
from unittest.mock import patch, MagicMock, Mock, call
import json
import gzip
import base64
import uuid
import os
import sys
from pathlib import Path
import tempfile

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRabbitMQConsumerComplete(unittest.TestCase):
    """Pruebas completas para RabbitMQConsumer - 100% cobertura"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer
            from config import Config
            from services import AWSServiceS3
            from processors import DocumentProcessor
            from extractors import (
                NameExtractor, CedulaExtractor, NameExtractorComprehend,
                SummarizeTextExtractorComprehend, CedulaExtractorComprehend,
                SummarizeTextExtractor
            )

            # Mocks de todas las dependencias
            self.config = Mock(spec=Config)
            self.config.rabbitmq_host = "localhost"
            self.config.rabbitmq_port = 5672
            self.config.rabbitmq_user = "user"
            self.config.rabbitmq_password = "pass"
            self.config.queue_name = "test_queue"

            self.aws_service = Mock(spec=AWSServiceS3)
            self.doc_processor = Mock(spec=DocumentProcessor)
            self.name_extractor = Mock(spec=NameExtractor)
            self.cedula_extractor = Mock(spec=CedulaExtractor)
            self.name_extractor_comprehend = Mock(spec=NameExtractorComprehend)
            self.summarize_text_comprehend = Mock(spec=SummarizeTextExtractorComprehend)
            self.cedula_extractor_comprehend = Mock(spec=CedulaExtractorComprehend)
            self.summarize_text_extractor = Mock(spec=SummarizeTextExtractor)

            self.consumer = RabbitMQConsumer(
                config=self.config,
                aws_service=self.aws_service,
                doc_processor=self.doc_processor,
                name_extractor=self.name_extractor,
                cedula_extractor=self.cedula_extractor,
                name_extractor_comprehend=self.name_extractor_comprehend,
                summarize_text_comprehend=self.summarize_text_comprehend,
                cedula_extractor_comprehend=self.cedula_extractor_comprehend,
                summarize_text_extractor=self.summarize_text_extractor
            )
            self.available = True
        except ImportError as e:
            self.available = False
            self.skipTest(f"RabbitMQConsumer not available: {e}")

    def test_init(self):
        """Prueba la inicialización del consumer"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        self.assertEqual(self.consumer.config, self.config)
        self.assertEqual(self.consumer.aws_service, self.aws_service)
        self.assertEqual(self.consumer.doc_processor, self.doc_processor)
        self.assertIsNone(self.consumer.connection)
        self.assertIsNone(self.consumer.channel)

    def test_decode_pdf_from_message_with_host_absolute_path_exists(self):
        """Prueba _decode_pdf_from_message con host_absolute_path existente"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(b'PDF content test')
            tmp_path = tmp.name

        try:
            msg = {"host_absolute_path": tmp_path}
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertEqual(result, b'PDF content test')
        finally:
            os.unlink(tmp_path)

    def test_decode_pdf_from_message_with_host_absolute_path_not_exists(self):
        """Prueba _decode_pdf_from_message con host_absolute_path inexistente"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        msg = {"host_absolute_path": "/path/that/does/not/exist.pdf"}

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertIsNone(result)
            mock_log.error.assert_called()

    def test_decode_pdf_from_message_with_host_absolute_path_read_error(self):
        """Prueba _decode_pdf_from_message con error de lectura"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        # El archivo existe pero simular error de lectura
        with patch('pathlib.Path.read_bytes', side_effect=PermissionError("Access denied")):
            msg = {"host_absolute_path": tmp_path}

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                result = self.consumer._decode_pdf_from_message(msg)
                self.assertIsNone(result)
                mock_log.error.assert_called()

        os.unlink(tmp_path)

    def test_decode_pdf_from_message_with_pdf_content_base64(self):
        """Prueba _decode_pdf_from_message con pdf_content en base64"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        pdf_data = b'PDF test content'
        encoded_data = base64.b64encode(pdf_data).decode()

        msg = {"pdf_content": encoded_data}

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertEqual(result, pdf_data)
            mock_log.info.assert_called()

    def test_decode_pdf_from_message_with_pdf_content_base64_error(self):
        """Prueba _decode_pdf_from_message con error en decodificación base64"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        msg = {"pdf_content": "invalid_base64_content!!!"}

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertIsNone(result)
            mock_log.error.assert_called()

    def test_decode_pdf_from_message_with_pdf_content_gzip(self):
        """Prueba _decode_pdf_from_message con pdf_content comprimido con gzip"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        pdf_data = b'PDF test content for gzip'
        compressed_data = gzip.compress(pdf_data)
        encoded_data = base64.b64encode(compressed_data).decode()

        msg = {"pdf_content": encoded_data}

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertEqual(result, pdf_data)

    def test_decode_pdf_from_message_with_pdf_content_gzip_error(self):
        """Prueba _decode_pdf_from_message con error en descompresión gzip"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        # Datos válidos en base64 pero no son gzip válido
        invalid_gzip = base64.b64encode(b'not gzip data').decode()
        msg = {"pdf_content": invalid_gzip}

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertEqual(result, b'not gzip data')  # Fallback a datos sin comprimir

    def test_decode_pdf_from_message_no_content(self):
        """Prueba _decode_pdf_from_message sin contenido PDF"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        msg = {"other_field": "value"}

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            result = self.consumer._decode_pdf_from_message(msg)
            self.assertIsNone(result)
            mock_log.error.assert_called()

    @patch('messaging.rabbitmq_consumer.pika')
    def test_connect_success(self, mock_pika):
        """Prueba conexión exitosa a RabbitMQ"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_pika.BlockingConnection.return_value = mock_connection

        result = self.consumer.connect()

        self.assertTrue(result)
        self.assertEqual(self.consumer.connection, mock_connection)
        self.assertEqual(self.consumer.channel, mock_channel)
        mock_channel.queue_declare.assert_called_once_with(queue=self.config.queue_name, durable=True)

    @patch('messaging.rabbitmq_consumer.pika')
    def test_connect_failure(self, mock_pika):
        """Prueba fallo en conexión a RabbitMQ"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_pika.BlockingConnection.side_effect = Exception("Connection failed")

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            result = self.consumer.connect()

            self.assertFalse(result)
            self.assertIsNone(self.consumer.connection)
            self.assertIsNone(self.consumer.channel)
            mock_log.error.assert_called()

    def test_disconnect_with_connection(self):
        """Prueba desconexión cuando hay conexión activa"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_connection = MagicMock()
        self.consumer.connection = mock_connection

        self.consumer.disconnect()

        mock_connection.close.assert_called_once()
        self.assertIsNone(self.consumer.connection)
        self.assertIsNone(self.consumer.channel)

    def test_disconnect_without_connection(self):
        """Prueba desconexión sin conexión activa"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        self.consumer.connection = None
        self.consumer.disconnect()  # No debería causar error

    def test_disconnect_with_exception(self):
        """Prueba desconexión con excepción"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_connection = MagicMock()
        mock_connection.close.side_effect = Exception("Close error")
        self.consumer.connection = mock_connection

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            self.consumer.disconnect()
            mock_log.error.assert_called()

    @patch('messaging.rabbitmq_consumer.uuid.uuid4')
    def test_process_message_success(self, mock_uuid):
        """Prueba procesamiento exitoso de mensaje"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_uuid.return_value.hex = "test123"

        # Mock del contenido PDF
        pdf_content = b'PDF test content'
        with patch.object(self.consumer, '_decode_pdf_from_message', return_value=pdf_content):

            # Mock del procesamiento
            self.doc_processor.extract_text_from_pdf.return_value = "Extracted text"
            self.name_extractor.extract.return_value = ["John Doe"]
            self.cedula_extractor.extract.return_value = ["12345678"]
            self.name_extractor_comprehend.extract.return_value = ["Jane Smith"]
            self.cedula_extractor_comprehend.extract.return_value = ["87654321"]
            self.summarize_text_comprehend.summarize.return_value = "Summary comprehend"
            self.summarize_text_extractor.summarize.return_value = "Summary extractor"

            # Mock del sanitize
            with patch('messaging.rabbitmq_consumer.sanitize_for_json', side_effect=lambda x: x):
                with patch('messaging.rabbitmq_consumer.summarize_text', return_value="Summarized"):

                    msg = {"file_id": "test_file"}
                    mock_channel = MagicMock()
                    mock_method = MagicMock()
                    mock_properties = MagicMock()
                    body = json.dumps(msg).encode()

                    self.consumer.process_message(mock_channel, mock_method, mock_properties, body)

                    # Verificar que se llamó ack
                    mock_channel.basic_ack.assert_called_once_with(delivery_tag=mock_method.delivery_tag)

    def test_process_message_decode_error(self):
        """Prueba procesamiento con error en decodificación PDF"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        with patch.object(self.consumer, '_decode_pdf_from_message', return_value=None):

            msg = {"file_id": "test_file"}
            mock_channel = MagicMock()
            mock_method = MagicMock()
            mock_properties = MagicMock()
            body = json.dumps(msg).encode()

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                self.consumer.process_message(mock_channel, mock_method, mock_properties, body)

                mock_log.error.assert_called()
                mock_channel.basic_ack.assert_called_once()

    def test_process_message_json_error(self):
        """Prueba procesamiento con error en JSON"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_properties = MagicMock()
        body = b'invalid json content'

        with patch('messaging.rabbitmq_consumer.log') as mock_log:
            self.consumer.process_message(mock_channel, mock_method, mock_properties, body)

            mock_log.error.assert_called()
            mock_channel.basic_ack.assert_called_once()

    def test_process_message_extraction_error(self):
        """Prueba procesamiento con error en extracción"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        pdf_content = b'PDF test content'
        with patch.object(self.consumer, '_decode_pdf_from_message', return_value=pdf_content):

            # Simular error en extracción
            self.doc_processor.extract_text_from_pdf.side_effect = Exception("Extraction error")

            msg = {"file_id": "test_file"}
            mock_channel = MagicMock()
            mock_method = MagicMock()
            mock_properties = MagicMock()
            body = json.dumps(msg).encode()

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                self.consumer.process_message(mock_channel, mock_method, mock_properties, body)

                mock_log.error.assert_called()
                mock_channel.basic_ack.assert_called_once()

    @patch('messaging.rabbitmq_consumer.pika')
    def test_start_consuming_success(self, mock_pika):
        """Prueba inicio exitoso de consumo"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_pika.BlockingConnection.return_value = mock_connection

        with patch.object(self.consumer, 'connect', return_value=True):
            self.consumer.channel = mock_channel

            # Simular interrupción después de configurar el consumo
            mock_channel.start_consuming.side_effect = KeyboardInterrupt()

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                self.consumer.start_consuming()

                mock_channel.basic_consume.assert_called_once()
                mock_log.info.assert_called()

    def test_start_consuming_connection_failed(self):
        """Prueba inicio de consumo con fallo de conexión"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        with patch.object(self.consumer, 'connect', return_value=False):

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                self.consumer.start_consuming()
                mock_log.error.assert_called()

    def test_start_consuming_exception(self):
        """Prueba inicio de consumo con excepción"""
        if not self.available:
            self.skipTest("RabbitMQConsumer not available")

        with patch.object(self.consumer, 'connect', return_value=True):
            mock_channel = MagicMock()
            mock_channel.start_consuming.side_effect = Exception("Consuming error")
            self.consumer.channel = mock_channel

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                self.consumer.start_consuming()
                mock_log.error.assert_called()

if __name__ == '__main__':
    unittest.main()
