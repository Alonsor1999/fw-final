"""
Pruebas específicas para RabbitMQConsumer - Enfoque en líneas no cubiertas
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import gzip
import base64
import tempfile
import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRabbitMQConsumerTargeted(unittest.TestCase):
    """Pruebas dirigidas para cubrir líneas específicas de RabbitMQConsumer"""

    def setUp(self):
        """Configuración básica para las pruebas"""
        # Mock de todas las dependencias complejas
        self.mock_config = Mock()
        self.mock_aws_service = Mock()
        self.mock_doc_processor = Mock()
        self.mock_name_extractor = Mock()
        self.mock_cedula_extractor = Mock()
        self.mock_name_extractor_comprehend = Mock()
        self.mock_summarize_text_comprehend = Mock()
        self.mock_cedula_extractor_comprehend = Mock()
        self.mock_summarize_text_extractor = Mock()

    @patch('messaging.rabbitmq_consumer.pika')
    def test_rabbitmq_consumer_init(self, mock_pika):
        """Prueba la inicialización de RabbitMQConsumer"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                config=self.mock_config,
                aws_service=self.mock_aws_service,
                doc_processor=self.mock_doc_processor,
                name_extractor=self.mock_name_extractor,
                cedula_extractor=self.mock_cedula_extractor,
                name_extractor_comprehend=self.mock_name_extractor_comprehend,
                summarize_text_comprehend=self.mock_summarize_text_comprehend,
                cedula_extractor_comprehend=self.mock_cedula_extractor_comprehend,
                summarize_text_extractor=self.mock_summarize_text_extractor
            )

            # Verificar inicialización
            self.assertIsNotNone(consumer)
            self.assertEqual(consumer.config, self.mock_config)
            self.assertIsNone(consumer.connection)
            self.assertIsNone(consumer.channel)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_decode_pdf_from_message_host_path_exists(self):
        """Prueba _decode_pdf_from_message con archivo existente"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, self.mock_aws_service, self.mock_doc_processor,
                self.mock_name_extractor, self.mock_cedula_extractor,
                self.mock_name_extractor_comprehend, self.mock_summarize_text_comprehend,
                self.mock_cedula_extractor_comprehend, self.mock_summarize_text_extractor
            )

            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(b'PDF test content')
                tmp_path = tmp.name

            try:
                msg = {"host_absolute_path": tmp_path}
                result = consumer._decode_pdf_from_message(msg)
                self.assertEqual(result, b'PDF test content')
            finally:
                os.unlink(tmp_path)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_decode_pdf_from_message_host_path_not_exists(self):
        """Prueba _decode_pdf_from_message con archivo inexistente"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, self.mock_aws_service, self.mock_doc_processor,
                self.mock_name_extractor, self.mock_cedula_extractor,
                self.mock_name_extractor_comprehend, self.mock_summarize_text_comprehend,
                self.mock_cedula_extractor_comprehend, self.mock_summarize_text_extractor
            )

            msg = {"host_absolute_path": "/path/that/does/not/exist.pdf"}
            result = consumer._decode_pdf_from_message(msg)
            self.assertIsNone(result)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_decode_pdf_from_message_base64_content(self):
        """Prueba _decode_pdf_from_message con contenido base64"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, self.mock_aws_service, self.mock_doc_processor,
                self.mock_name_extractor, self.mock_cedula_extractor,
                self.mock_name_extractor_comprehend, self.mock_summarize_text_comprehend,
                self.mock_cedula_extractor_comprehend, self.mock_summarize_text_extractor
            )

            pdf_data = b'PDF content in base64'
            encoded_data = base64.b64encode(pdf_data).decode()

            msg = {"pdf_content": encoded_data}
            result = consumer._decode_pdf_from_message(msg)
            self.assertEqual(result, pdf_data)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_decode_pdf_from_message_gzip_content(self):
        """Prueba _decode_pdf_from_message con contenido comprimido"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, self.mock_aws_service, self.mock_doc_processor,
                self.mock_name_extractor, self.mock_cedula_extractor,
                self.mock_name_extractor_comprehend, self.mock_summarize_text_comprehend,
                self.mock_cedula_extractor_comprehend, self.mock_summarize_text_extractor
            )

            pdf_data = b'PDF content to compress'
            compressed_data = gzip.compress(pdf_data)
            encoded_data = base64.b64encode(compressed_data).decode()

            msg = {"pdf_content": encoded_data}
            result = consumer._decode_pdf_from_message(msg)
            self.assertEqual(result, pdf_data)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_decode_pdf_from_message_no_content(self):
        """Prueba _decode_pdf_from_message sin contenido"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, self.mock_aws_service, self.mock_doc_processor,
                self.mock_name_extractor, self.mock_cedula_extractor,
                self.mock_name_extractor_comprehend, self.mock_summarize_text_comprehend,
                self.mock_cedula_extractor_comprehend, self.mock_summarize_text_extractor
            )

            msg = {"other_field": "value"}
            result = consumer._decode_pdf_from_message(msg)
            self.assertIsNone(result)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    @patch('messaging.rabbitmq_consumer.pika')
    def test_connect_success(self, mock_pika):
        """Prueba conexión exitosa"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            # Mock de pika
            mock_connection = Mock()
            mock_channel = Mock()
            mock_connection.channel.return_value = mock_channel
            mock_pika.BlockingConnection.return_value = mock_connection

            self.mock_config.rabbitmq_host = "localhost"
            self.mock_config.rabbitmq_port = 5672
            self.mock_config.rabbitmq_user = "user"
            self.mock_config.rabbitmq_password = "pass"
            self.mock_config.queue_name = "test_queue"

            consumer = RabbitMQConsumer(
                self.mock_config, self.mock_aws_service, self.mock_doc_processor,
                self.mock_name_extractor, self.mock_cedula_extractor,
                self.mock_name_extractor_comprehend, self.mock_summarize_text_comprehend,
                self.mock_cedula_extractor_comprehend, self.mock_summarize_text_extractor
            )

            result = consumer.connect()
            self.assertTrue(result)
            self.assertEqual(consumer.connection, mock_connection)
            self.assertEqual(consumer.channel, mock_channel)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    @patch('messaging.rabbitmq_consumer.pika')
    def test_connect_failure(self, mock_pika):
        """Prueba fallo en conexión"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            # Mock que simula fallo
            mock_pika.BlockingConnection.side_effect = Exception("Connection failed")

            consumer = RabbitMQConsumer(
                self.mock_config, self.mock_aws_service, self.mock_doc_processor,
                self.mock_name_extractor, self.mock_cedula_extractor,
                self.mock_name_extractor_comprehend, self.mock_summarize_text_comprehend,
                self.mock_cedula_extractor_comprehend, self.mock_summarize_text_extractor
            )

            result = consumer.connect()
            self.assertFalse(result)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_disconnect_with_connection(self):
        """Prueba desconexión con conexión activa"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, self.mock_aws_service, self.mock_doc_processor,
                self.mock_name_extractor, self.mock_cedula_extractor,
                self.mock_name_extractor_comprehend, self.mock_summarize_text_comprehend,
                self.mock_cedula_extractor_comprehend, self.mock_summarize_text_extractor
            )

            mock_connection = Mock()
            consumer.connection = mock_connection

            consumer.disconnect()

            mock_connection.close.assert_called_once()
            self.assertIsNone(consumer.connection)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

if __name__ == '__main__':
    unittest.main()
