"""
Módulo para enviar mensajes a RabbitMQ desde el procesador de correos
"""

import pika
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class RabbitMQSender:
    """Clase para enviar mensajes a RabbitMQ"""
    
    def __init__(self, rabbitmq_config: Dict[str, Any]):
        """
        Inicializar el sender de RabbitMQ
        
        Args:
            rabbitmq_config: Configuración de RabbitMQ
                - host: Host de RabbitMQ
                - port: Puerto de RabbitMQ
                - username: Usuario
                - password: Contraseña
                - queue_name: Nombre de la cola
                - exchange: Exchange (opcional)
                - routing_key: Routing key (opcional)
        """
        self.config = rabbitmq_config
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """Conectar a RabbitMQ"""
        try:
            # Crear credenciales
            credentials = pika.PlainCredentials(
                self.config.get('username', 'guest'),
                self.config.get('password', 'guest')
            )
            
            # Crear parámetros de conexión
            parameters = pika.ConnectionParameters(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5672),
                credentials=credentials,
                virtual_host=self.config.get('virtual_host', '/')
            )
            
            # Establecer conexión
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declarar cola
            queue_name = self.config.get('queue_name', 'pdf_processing_queue')
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            # Declarar exchange si se especifica
            exchange = self.config.get('exchange')
            if exchange:
                self.channel.exchange_declare(exchange=exchange, exchange_type='direct')
            
            logger.info(f"✅ Conectado a RabbitMQ en {self.config.get('host')}:{self.config.get('port')}")
            
        except Exception as e:
            logger.error(f"❌ Error conectando a RabbitMQ: {e}")
            raise
    
    def send_pdf_message(self, pdf_path: str, email_info: Dict[str, Any]) -> bool:
        """
        Enviar mensaje con información del PDF y correo
        
        Args:
            pdf_path: Ruta local del PDF descargado
            email_info: Información del correo (asunto, remitente, etc.)
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Verificar que el archivo existe
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                logger.error(f"❌ El archivo PDF no existe: {pdf_path}")
                return False
            
            # Crear mensaje
            message = {
                "host_absolute_path": str(pdf_file.absolute()),
                "file_name": pdf_file.name,
                "original_name": pdf_file.name,
                "email_info": {
                    "subject": email_info.get('subject', ''),
                    "sender": email_info.get('sender', ''),
                    "received_date": email_info.get('received_date', ''),
                    "folder": email_info.get('folder', ''),
                    "message_id": email_info.get('message_id', ''),
                    "has_attachments": email_info.get('has_attachments', False),
                    "attachment_count": email_info.get('attachment_count', 0)
                },
                "processing_info": {
                    "source": "robot001_outlook",
                    "timestamp": datetime.now().isoformat(),
                    "robot_id": "robot001"
                }
            }
            
            # Convertir a JSON
            message_json = json.dumps(message, ensure_ascii=False)
            
            # Enviar mensaje
            queue_name = self.config.get('queue_name', 'pdf_processing_queue')
            routing_key = self.config.get('routing_key', queue_name)
            
            self.channel.basic_publish(
                exchange=self.config.get('exchange', ''),
                routing_key=routing_key,
                body=message_json.encode('utf-8'),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                    content_type='application/json'
                )
            )
            
            logger.info(f"✅ Mensaje enviado a RabbitMQ: {pdf_file.name}")
            logger.debug(f"Mensaje: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje a RabbitMQ: {e}")
            return False
    
    def send_email_summary(self, email_summary: Dict[str, Any]) -> bool:
        """
        Enviar resumen de correo procesado
        
        Args:
            email_summary: Resumen del correo procesado
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            message = {
                "type": "email_summary",
                "data": email_summary,
                "timestamp": datetime.now().isoformat(),
                "robot_id": "robot001"
            }
            
            message_json = json.dumps(message, ensure_ascii=False)
            
            # Enviar a cola de resúmenes
            summary_queue = self.config.get('summary_queue', 'email_summary_queue')
            self.channel.queue_declare(queue=summary_queue, durable=True)
            
            self.channel.basic_publish(
                exchange='',
                routing_key=summary_queue,
                body=message_json.encode('utf-8'),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info(f"✅ Resumen de correo enviado a RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando resumen a RabbitMQ: {e}")
            return False
    
    def close(self):
        """Cerrar conexión con RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("✅ Conexión con RabbitMQ cerrada")
        except Exception as e:
            logger.error(f"❌ Error cerrando conexión con RabbitMQ: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
