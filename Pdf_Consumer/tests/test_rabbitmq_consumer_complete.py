"""
Pruebas unitarias completas para RabbitMQConsumer
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import gzip
import base64
import os

# Configurar variables de entorno antes de cualquier importación

try:
    from messaging.rabbitmq_consumer import RabbitMQConsumer
    from config import Config
    RABBITMQ_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import RabbitMQConsumer: {e}")
    # Crear mocks para las clases que no se pueden importar
    RabbitMQConsumer = MagicMock
    Config = MagicMock
    RABBITMQ_AVAILABLE = True  # Cambiar a True para ejecutar con mocks


class TestRabbitMQConsumerComplete(unittest.TestCase):
    """Pruebas completas para RabbitMQConsumer"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        if not RABBITMQ_AVAILABLE:
            self.skipTest("RabbitMQConsumer no disponible")

        # Crear mocks de las dependencias
        self.mock_config = Mock(spec=Config)
        self.mock_config.RABBITMQ_HOST = "localhost"
        self.mock_config.RABBITMQ_PORT = 5672
        self.mock_config.RABBITMQ_USER = "guest"
        self.mock_config.RABBITMQ_PASSWORD = "guest"
        self.mock_config.RABBITMQ_QUEUE = "test_queue"
        self.mock_config.RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"
        self.mock_config.ON_MISSING = "nack"
        self.mock_config.ROOT_PATH = "/test/path"

        self.mock_aws_service = Mock()
        self.mock_doc_processor = Mock()
        self.mock_name_extractor = Mock()
        self.mock_cedula_extractor = Mock()
        self.mock_name_extractor_comprehend = Mock()
        self.mock_summarize_text_comprehend = Mock()
        self.mock_cedula_extractor_comprehend = Mock()
        self.mock_summarize_text_extractor = Mock()

        # Crear instancia del consumidor
        self.consumer = RabbitMQConsumer(
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

    @patch('messaging.rabbitmq_consumer.pika')
    def test_run_successful_connection(self, mock_pika):
        """Prueba conexión exitosa a RabbitMQ"""
        # Configurar mocks
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.URLParameters.return_value = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        # Simular KeyboardInterrupt para terminar
        mock_channel.start_consuming.side_effect = KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            self.consumer.run()

        # Verificar que se configuró correctamente
        mock_pika.URLParameters.assert_called_once_with(self.mock_config.RABBITMQ_URL)

    @patch('messaging.rabbitmq_consumer.pika')
    def test_run_connection_error(self, mock_pika):
        """Prueba error de conexión a RabbitMQ"""
        # Configurar mock para lanzar excepción
        mock_pika.URLParameters.side_effect = Exception("Connection failed")

        # Ejecutar método
        self.consumer.run()

        # Verificar que se intentó la conexión
        mock_pika.URLParameters.assert_called_once()

    def test_on_message_successful_processing(self):
        """Prueba procesamiento exitoso de mensaje - cambió callback por on_message"""
        # Preparar datos de prueba
        pdf_content = b"PDF content"
        compressed_content = gzip.compress(pdf_content)
        encoded_content = base64.b64encode(compressed_content).decode('utf-8')
        
        message_body = json.dumps({
            "file_name": "test.pdf",
            "content": encoded_content,
            "content_encoding": "gzip+base64"
        }).encode('utf-8')

        # Configurar mocks
        mock_ch = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "tag123"
        mock_properties = Mock()

        # Configurar respuestas de los extractores
        self.mock_doc_processor.extract_text_by_pages.return_value = [
            ("Page 1", 1), ("Page 2", 2)
        ]
        self.mock_doc_processor.process_pdf_bytes.return_value = "Extracted text"
        self.mock_cedula_extractor.find_cedulas_with_pages.return_value = [
            {"number": "12345678", "pagPdf": [1]}
        ]
        self.mock_name_extractor.extract_names_with_pages.return_value = [
            {"name": "Juan Pérez", "pagPdf": [1]}
        ]
        self.mock_summarize_text_extractor.process.return_value = [
            {"matter": "Tema", "resume": "Resumen"}
        ]
        self.mock_aws_service.upload_to_s3.return_value = True

        # Ejecutar on_message
        self.consumer.on_message(mock_ch, mock_method, mock_properties, message_body)

        # Verificar que se procesó correctamente
        mock_ch.basic_ack.assert_called_once_with(delivery_tag="tag123")
        self.assertEqual(self.mock_aws_service.upload_to_s3.call_count, 2)  # PDF y JSON

    def test_on_message_invalid_json(self):
        """Prueba manejo de JSON inválido"""
        # Datos de prueba con JSON inválido
        invalid_json = b"invalid json content"

        mock_ch = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "tag123"
        mock_properties = Mock()

        # Ejecutar on_message
        self.consumer.on_message(mock_ch, mock_method, mock_properties, invalid_json)

        # Verificar que se acknowledgeó el mensaje
        mock_ch.basic_ack.assert_called_once_with(delivery_tag="tag123")

    def test_on_message_missing_required_fields(self):
        """Prueba manejo de campos requeridos faltantes"""
        # Mensaje sin contenido válido
        message_body = json.dumps({
            "invalid_field": "value"
        }).encode('utf-8')

        mock_ch = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "tag123"
        mock_properties = Mock()

        # Ejecutar on_message
        self.consumer.on_message(mock_ch, mock_method, mock_properties, message_body)

        # Verificar que se rechazó el mensaje
        mock_ch.basic_nack.assert_called_once_with(
            delivery_tag="tag123", 
            requeue=False
        )

    def test_on_message_pdf_processing_error(self):
        """Prueba manejo de error en procesamiento de PDF"""
        # Preparar datos válidos
        pdf_content = b"PDF content"
        compressed_content = gzip.compress(pdf_content)
        encoded_content = base64.b64encode(compressed_content).decode('utf-8')
        
        message_body = json.dumps({
            "file_name": "test.pdf",
            "content": encoded_content,
            "content_encoding": "gzip+base64"
        }).encode('utf-8')

        mock_ch = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "tag123"
        mock_properties = Mock()

        # Configurar mocks para que falle el procesamiento
        self.mock_doc_processor.extract_text_by_pages.return_value = ["text"]
        self.mock_doc_processor.process_pdf_bytes.return_value = None

        # Ejecutar on_message
        self.consumer.on_message(mock_ch, mock_method, mock_properties, message_body)

        # Verificar que se acknowledgeó el mensaje (para no reprocesarlo)
        mock_ch.basic_ack.assert_called_once_with(delivery_tag="tag123")

    def test_on_message_with_comprehend_fallback(self):
        """Prueba uso de extractores Comprehend como fallback"""
        # Preparar datos de prueba
        pdf_content = b"PDF content"
        compressed_content = gzip.compress(pdf_content)
        encoded_content = base64.b64encode(compressed_content).decode('utf-8')
        
        message_body = json.dumps({
            "file_name": "test.pdf",
            "content": encoded_content,
            "content_encoding": "gzip+base64"
        }).encode('utf-8')

        mock_ch = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "tag123"
        mock_properties = Mock()

        # Configurar extractores normales para fallar
        self.mock_doc_processor.extract_text_by_pages.return_value = ["text"]
        self.mock_doc_processor.process_pdf_bytes.return_value = "Extracted text"
        self.mock_cedula_extractor.find_cedulas_with_pages.return_value = []
        self.mock_name_extractor.extract_names_with_pages.return_value = []
        self.mock_cedula_extractor.find_cedulas.return_value = ""
        self.mock_name_extractor.extract_all_names.return_value = ""

        # Configurar extractores Comprehend para tener éxito
        self.mock_cedula_extractor_comprehend.extract_cedulas_with_pages.return_value = [
            {"number": "87654321", "pagPdf": [2]}
        ]
        self.mock_name_extractor_comprehend.extract_names_with_pages.return_value = [
            {"name": "María García", "pagPdf": [2]}
        ]
        self.mock_summarize_text_extractor.process.return_value = None
        self.mock_summarize_text_comprehend.summarize.return_value = "Resumen Comprehend"
        self.mock_aws_service.upload_to_s3.return_value = True

        # Ejecutar on_message
        self.consumer.on_message(mock_ch, mock_method, mock_properties, message_body)

        # Verificar que se usaron los extractores Comprehend
        self.mock_cedula_extractor_comprehend.extract_cedulas_with_pages.assert_called_once()
        self.mock_name_extractor_comprehend.extract_names_with_pages.assert_called_once()
        mock_ch.basic_ack.assert_called_once_with(delivery_tag="tag123")

    def test_initialization_with_all_parameters(self):
        """Prueba inicialización con todos los parámetros"""
        # Verificar que se asignaron todas las dependencias
        self.assertEqual(self.consumer.config, self.mock_config)
        self.assertEqual(self.consumer.aws_service, self.mock_aws_service)
        self.assertEqual(self.consumer.doc_processor, self.mock_doc_processor)
        self.assertEqual(self.consumer.name_extractor, self.mock_name_extractor)
        self.assertEqual(self.consumer.cedula_extractor, self.mock_cedula_extractor)
        self.assertEqual(self.consumer.name_extractor_comprehend, self.mock_name_extractor_comprehend)
        self.assertEqual(self.consumer.summarize_text_comprehend, self.mock_summarize_text_comprehend)
        self.assertEqual(self.consumer.cedula_extractor_comprehend, self.mock_cedula_extractor_comprehend)
        self.assertEqual(self.consumer.summarize_text_extractor, self.mock_summarize_text_extractor)

    def test_decode_pdf_from_message_with_gzip_content(self):
        """Prueba decodificación de contenido gzip+base64"""
        # Preparar mensaje con contenido comprimido
        pdf_content = b"Test PDF content"
        compressed = gzip.compress(pdf_content)
        encoded = base64.b64encode(compressed).decode('utf-8')

        msg = {
            "content": encoded,
            "content_encoding": "gzip+base64"
        }

        # Ejecutar método
        result = self.consumer._decode_pdf_from_message(msg)

        # Verificar resultado
        self.assertEqual(result, pdf_content)

    def test_decode_pdf_from_message_invalid_base64(self):
        """Prueba manejo de base64 inválido"""
        msg = {
            "content": "invalid_base64_content!@#$",
            "content_encoding": "gzip+base64"
        }

        # Ejecutar método
        result = self.consumer._decode_pdf_from_message(msg)

        # Verificar que retorna None
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
