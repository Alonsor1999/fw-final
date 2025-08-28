"""
Pruebas para el sistema de filtrado de mensajes
"""
import unittest
from unittest.mock import Mock, patch
from mail_reader import MessageFilter, get_messages
from mail_filters_config import get_predefined_filter, combine_filters
from utils.logger_config import setup_logger

logger = setup_logger("test_mail_filtering")

class TestMessageFilter(unittest.TestCase):
    """Pruebas para la clase MessageFilter"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.sample_message = {
            'id': 'test-123',
            'subject': 'Test Subject',
            'from': {
                'emailAddress': {
                    'address': 'test@empresa.com',
                    'name': 'Test User'
                }
            },
            'receivedDateTime': '2024-01-15T10:30:00Z'
        }
    
    def test_filter_allowed_senders(self):
        """Prueba filtrado por remitentes permitidos"""
        # Configurar filtro con remitentes permitidos
        filtro = MessageFilter(allowed_senders=["@empresa.com", "jefe@"])
        
        # Mensaje de remitente permitido
        mensaje_permitido = {
            'from': {'emailAddress': {'address': 'jefe@empresa.com'}},
            'subject': 'Test'
        }
        self.assertTrue(filtro.filter_message(mensaje_permitido))
        
        # Mensaje de remitente no permitido
        mensaje_no_permitido = {
            'from': {'emailAddress': {'address': 'spam@otro.com'}},
            'subject': 'Test'
        }
        self.assertFalse(filtro.filter_message(mensaje_no_permitido))
    
    def test_filter_blocked_senders(self):
        """Prueba filtrado por remitentes bloqueados"""
        # Configurar filtro con remitentes bloqueados
        filtro = MessageFilter(blocked_senders=["@spam.com", "noreply@"])
        
        # Mensaje de remitente bloqueado
        mensaje_bloqueado = {
            'from': {'emailAddress': {'address': 'noreply@empresa.com'}},
            'subject': 'Test'
        }
        self.assertFalse(filtro.filter_message(mensaje_bloqueado))
        
        # Mensaje de remitente no bloqueado
        mensaje_no_bloqueado = {
            'from': {'emailAddress': {'address': 'usuario@empresa.com'}},
            'subject': 'Test'
        }
        self.assertTrue(filtro.filter_message(mensaje_no_bloqueado))
    
    def test_filter_subject_keywords(self):
        """Prueba filtrado por palabras clave en el subject"""
        # Configurar filtro con palabras clave
        filtro = MessageFilter(subject_keywords=["urgente", "importante"])
        
        # Mensaje con palabra clave
        mensaje_con_keyword = {
            'from': {'emailAddress': {'address': 'test@empresa.com'}},
            'subject': 'Mensaje urgente para revisar'
        }
        self.assertTrue(filtro.filter_message(mensaje_con_keyword))
        
        # Mensaje sin palabra clave
        mensaje_sin_keyword = {
            'from': {'emailAddress': {'address': 'test@empresa.com'}},
            'subject': 'Mensaje normal'
        }
        self.assertFalse(filtro.filter_message(mensaje_sin_keyword))
    
    def test_filter_subject_exclude_keywords(self):
        """Prueba filtrado por palabras excluidas en el subject"""
        # Configurar filtro con palabras excluidas
        filtro = MessageFilter(subject_exclude_keywords=["spam", "publicidad"])
        
        # Mensaje con palabra excluida
        mensaje_con_excluida = {
            'from': {'emailAddress': {'address': 'test@empresa.com'}},
            'subject': 'Oferta de publicidad'
        }
        self.assertFalse(filtro.filter_message(mensaje_con_excluida))
        
        # Mensaje sin palabra excluida
        mensaje_sin_excluida = {
            'from': {'emailAddress': {'address': 'test@empresa.com'}},
            'subject': 'Mensaje normal'
        }
        self.assertTrue(filtro.filter_message(mensaje_sin_excluida))
    
    def test_filter_combined(self):
        """Prueba filtrado combinado"""
        # Configurar filtro combinado
        filtro = MessageFilter(
            allowed_senders=["@empresa.com"],
            blocked_senders=["@spam.com"],
            subject_keywords=["urgente"],
            subject_exclude_keywords=["spam"]
        )
        
        # Mensaje que cumple todos los criterios
        mensaje_valido = {
            'from': {'emailAddress': {'address': 'jefe@empresa.com'}},
            'subject': 'Mensaje urgente importante'
        }
        self.assertTrue(filtro.filter_message(mensaje_valido))
        
        # Mensaje que no cumple criterios (remitente bloqueado)
        mensaje_invalido_remitente = {
            'from': {'emailAddress': {'address': 'spam@spam.com'}},
            'subject': 'Mensaje urgente'
        }
        self.assertFalse(filtro.filter_message(mensaje_invalido_remitente))
        
        # Mensaje que no cumple criterios (palabra excluida)
        mensaje_invalido_subject = {
            'from': {'emailAddress': {'address': 'jefe@empresa.com'}},
            'subject': 'Mensaje spam urgente'
        }
        self.assertFalse(filtro.filter_message(mensaje_invalido_subject))
    
    def test_empty_filters(self):
        """Prueba filtros vacíos (deberían permitir todos los mensajes)"""
        filtro = MessageFilter()
        
        mensaje = {
            'from': {'emailAddress': {'address': 'cualquier@email.com'}},
            'subject': 'Cualquier subject'
        }
        self.assertTrue(filtro.filter_message(mensaje))
    
    def test_extract_sender_email(self):
        """Prueba la extracción del email del remitente"""
        filtro = MessageFilter()
        
        # Caso normal
        mensaje_normal = {
            'from': {'emailAddress': {'address': 'test@empresa.com'}}
        }
        email = filtro._extract_sender_email(mensaje_normal)
        self.assertEqual(email, 'test@empresa.com')
        
        # Caso con estructura diferente
        mensaje_diferente = {
            'from': 'test@empresa.com'
        }
        email = filtro._extract_sender_email(mensaje_diferente)
        self.assertEqual(email, 'test@empresa.com')

class TestPredefinedFilters(unittest.TestCase):
    """Pruebas para filtros predefinidos"""
    
    def test_get_predefined_filter(self):
        """Prueba obtener filtros predefinidos"""
        # Probar filtro existente
        filtro_urgente = get_predefined_filter("urgent_business")
        self.assertIsInstance(filtro_urgente, MessageFilter)
        self.assertIn("@empresa.com", filtro_urgente.allowed_senders)
        self.assertIn("urgente", filtro_urgente.subject_keywords)
        
        # Probar filtro inexistente
        with self.assertRaises(ValueError):
            get_predefined_filter("filtro_inexistente")
    
    def test_combine_filters(self):
        """Prueba combinar filtros"""
        filtro1 = MessageFilter(allowed_senders=["@empresa.com"])
        filtro2 = MessageFilter(subject_keywords=["urgente"])
        
        filtro_combinado = combine_filters(filtro1, filtro2)
        
        self.assertIn("@empresa.com", filtro_combinado.allowed_senders)
        self.assertIn("urgente", filtro_combinado.subject_keywords)
    
    def test_get_available_filters(self):
        """Prueba obtener lista de filtros disponibles"""
        from mail_filters_config import get_available_filters
        
        filtros_disponibles = get_available_filters()
        self.assertIsInstance(filtros_disponibles, list)
        self.assertIn("urgent_business", filtros_disponibles)
        self.assertIn("reports", filtros_disponibles)

class TestIntegration(unittest.TestCase):
    """Pruebas de integración"""
    
    @patch('mail_reader.get_authenticated_session')
    @patch('mail_reader.GRAPH_API_ENDPOINT', 'https://test.com')
    @patch('mail_reader.MAIL_USER', 'test@empresa.com')
    def test_get_messages_with_filter(self, mock_session):
        """Prueba obtener mensajes con filtro"""
        # Mock de la respuesta de la API
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "value": [
                {
                    'id': '1',
                    'from': {'emailAddress': {'address': 'jefe@empresa.com'}},
                    'subject': 'Mensaje urgente',
                    'receivedDateTime': '2024-01-15T10:30:00Z'
                },
                {
                    'id': '2',
                    'from': {'emailAddress': {'address': 'spam@spam.com'}},
                    'subject': 'Publicidad',
                    'receivedDateTime': '2024-01-15T10:30:00Z'
                }
            ]
        }
        mock_session.return_value.get.return_value = mock_response
        
        # Crear filtro
        filtro = MessageFilter(
            allowed_senders=["@empresa.com"],
            subject_keywords=["urgente"]
        )
        
        # Obtener mensajes con filtro
        mensajes = get_messages(top=10, message_filter=filtro)
        
        # Verificar que solo se devuelve el mensaje que cumple los criterios
        self.assertEqual(len(mensajes), 1)
        self.assertEqual(mensajes[0]['id'], '1')

def run_tests():
    """Ejecutar todas las pruebas"""
    logger.info("Iniciando pruebas del sistema de filtrado de mensajes")
    
    # Crear suite de pruebas
    test_suite = unittest.TestSuite()
    
    # Agregar pruebas
    test_suite.addTest(unittest.makeSuite(TestMessageFilter))
    test_suite.addTest(unittest.makeSuite(TestPredefinedFilters))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Reportar resultados
    if result.wasSuccessful():
        logger.info("Todas las pruebas pasaron exitosamente")
    else:
        logger.error(f"Algunas pruebas fallaron: {len(result.failures)} fallos, {len(result.errors)} errores")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests() 