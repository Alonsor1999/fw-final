"""
Pruebas específicas para messaging/rabbitmq_consumer.py - Mejorar cobertura crítica
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

class TestRabbitMQConsumerCritical(unittest.TestCase):
    """Pruebas críticas para líneas específicas no cubiertas en RabbitMQConsumer"""

    def setUp(self):
        """Configuración básica para las pruebas"""
        self.mock_config = Mock()
        self.mock_config.rabbitmq_host = "localhost"
        self.mock_config.rabbitmq_port = 5672
        self.mock_config.rabbitmq_user = "user"
        self.mock_config.rabbitmq_password = "pass"
        self.mock_config.queue_name = "test_queue"

    def test_decode_pdf_host_path_read_error(self):
        """Prueba líneas 42-50: Error al leer archivo desde host_absolute_path"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, Mock(), Mock(), Mock(), Mock(),
                Mock(), Mock(), Mock(), Mock()
            )

            # Crear archivo temporal y luego simular error de lectura
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name

            # Cambiar permisos para causar error de lectura (Windows)
            try:
                os.chmod(tmp_path, 0o000)  # Sin permisos

                msg = {"host_absolute_path": tmp_path}

                with patch('messaging.rabbitmq_consumer.log') as mock_log:
                    result = consumer._decode_pdf_from_message(msg)
                    self.assertIsNone(result)
                    mock_log.error.assert_called()

            finally:
                try:
                    os.chmod(tmp_path, 0o777)  # Restaurar permisos
                    os.unlink(tmp_path)
                except:
                    pass

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_decode_pdf_host_path_not_exists(self):
        """Prueba líneas 64-72: Archivo host_absolute_path no existe"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, Mock(), Mock(), Mock(), Mock(),
                Mock(), Mock(), Mock(), Mock()
            )

            # Usar ruta que no existe
            msg = {"host_absolute_path": "/ruta/que/no/existe.pdf"}

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                result = consumer._decode_pdf_from_message(msg)
                self.assertIsNone(result)
                mock_log.error.assert_called()

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_decode_pdf_base64_error(self):
        """Prueba líneas 79-82: Error en decodificación base64"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, Mock(), Mock(), Mock(), Mock(),
                Mock(), Mock(), Mock(), Mock()
            )

            # Base64 inválido
            msg = {"pdf_content": "invalid_base64_content!!!"}

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                result = consumer._decode_pdf_from_message(msg)
                self.assertIsNone(result)
                mock_log.error.assert_called()

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_decode_pdf_no_content(self):
        """Prueba línea 92: Sin contenido PDF"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, Mock(), Mock(), Mock(), Mock(),
                Mock(), Mock(), Mock(), Mock()
            )

            # Mensaje sin contenido PDF
            msg = {"other_field": "value"}

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                result = consumer._decode_pdf_from_message(msg)
                self.assertIsNone(result)
                mock_log.error.assert_called()

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    @patch('messaging.rabbitmq_consumer.pika')
    def test_connect_method(self, mock_pika):
        """Prueba líneas 95-185: Método connect completo"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, Mock(), Mock(), Mock(), Mock(),
                Mock(), Mock(), Mock(), Mock()
            )

            # Mock conexión exitosa
            mock_connection = Mock()
            mock_channel = Mock()
            mock_connection.channel.return_value = mock_channel
            mock_pika.BlockingConnection.return_value = mock_connection

            result = consumer.connect()

            self.assertTrue(result)
            self.assertEqual(consumer.connection, mock_connection)
            self.assertEqual(consumer.channel, mock_channel)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    @patch('messaging.rabbitmq_consumer.pika')
    def test_connect_exception(self, mock_pika):
        """Prueba manejo de excepción en connect"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, Mock(), Mock(), Mock(), Mock(),
                Mock(), Mock(), Mock(), Mock()
            )

            # Simular error de conexión
            mock_pika.BlockingConnection.side_effect = Exception("Connection failed")

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                result = consumer.connect()
                self.assertFalse(result)
                mock_log.error.assert_called()

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_disconnect_with_connection(self):
        """Prueba líneas 215-216: Disconnect con conexión activa"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, Mock(), Mock(), Mock(), Mock(),
                Mock(), Mock(), Mock(), Mock()
            )

            # Mock conexión activa
            mock_connection = Mock()
            consumer.connection = mock_connection

            consumer.disconnect()

            mock_connection.close.assert_called_once()
            self.assertIsNone(consumer.connection)
            self.assertIsNone(consumer.channel)

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

    def test_disconnect_exception(self):
        """Prueba líneas 219-220: Exception en disconnect"""
        try:
            from messaging.rabbitmq_consumer import RabbitMQConsumer

            consumer = RabbitMQConsumer(
                self.mock_config, Mock(), Mock(), Mock(), Mock(),
                Mock(), Mock(), Mock(), Mock()
            )

            # Mock conexión que falla al cerrar
            mock_connection = Mock()
            mock_connection.close.side_effect = Exception("Close failed")
            consumer.connection = mock_connection

            with patch('messaging.rabbitmq_consumer.log') as mock_log:
                consumer.disconnect()
                mock_log.error.assert_called()

        except ImportError:
            self.skipTest("RabbitMQConsumer not available")

if __name__ == '__main__':
    unittest.main()
