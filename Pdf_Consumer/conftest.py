"""
Configuración global para pytest que permite ejecutar todas las pruebas
independientemente del modo TEST_MODE o las credenciales de AWS.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

def pytest_configure(config):
    """Configuración que se ejecuta antes de cualquier prueba"""
    # Configurar variables de entorno necesarias para que todos los módulos se puedan importar
    os.environ['TEST_MODE'] = 'true'
    os.environ['S3_BUCKET'] = 'test-bucket'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/%2F'
    os.environ['QUEUE_NAME'] = 'test_queue'

@pytest.fixture(autouse=True)
def mock_aws_credentials():
    """Mock automático de credenciales AWS para todas las pruebas"""
    with patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret',
        'AWS_DEFAULT_REGION': 'us-east-1'
    }):
        yield

@pytest.fixture(autouse=True)
def mock_boto3_clients():
    """Mock automático de clientes boto3 para evitar errores de credenciales"""
    with patch('boto3.client') as mock_client:
        # Configurar mocks básicos para Comprehend
        comprehend_mock = MagicMock()
        comprehend_mock.detect_entities.return_value = {'Entities': []}
        comprehend_mock.detect_key_phrases.return_value = {'KeyPhrases': []}
        comprehend_mock.detect_dominant_language.return_value = {
            'Languages': [{'LanguageCode': 'es', 'Score': 0.99}]
        }
        comprehend_mock.detect_pii_entities.return_value = {'Entities': []}

        # Configurar mock para S3
        s3_mock = MagicMock()
        s3_mock.upload_fileobj.return_value = None

        def client_side_effect(service_name, **kwargs):
            if service_name == 'comprehend':
                return comprehend_mock
            elif service_name == 's3':
                return s3_mock
            else:
                return MagicMock()

        mock_client.side_effect = client_side_effect
        yield mock_client

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuración de ambiente de pruebas a nivel de sesión"""
    # Asegurar que el modo TEST esté activado para toda la sesión
    original_env = os.environ.copy()

    os.environ.update({
        'TEST_MODE': 'true',
        'S3_BUCKET': 'test-bucket',
        'AWS_REGION': 'us-east-1',
        'RABBITMQ_URL': 'amqp://test:test@localhost:5672/%2F',
        'QUEUE_NAME': 'test_queue',
        'LOG_LEVEL': 'INFO'
    })

    yield

    # Restaurar el ambiente original al finalizar
    os.environ.clear()
    os.environ.update(original_env)
