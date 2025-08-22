"""
Módulo de RabbitMQ - Reutilizable para cualquier robot
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path para importar el framework
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from framework.modules.base_module import BaseModule

logger = logging.getLogger(__name__)

class RabbitMQModule(BaseModule):
    """Módulo de RabbitMQ reutilizable para cualquier robot"""
    
    def __init__(self, module_id: str, robot_id: str, config: Dict[str, Any] = None):
        # Configuración mínima - las variables de entorno se cargarán después
        default_config = {
            # Configuración de operaciones (no dependen de .env)
            'auto_ack': False,
            'durable': True,
            'prefetch_count': 1,
            'reconnect_interval': 5,
            'max_retries': 3,
            'message_ttl': 3600000,  # 1 hora en ms
            'max_priority': 10,
            'persistent': True
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(module_id, robot_id, default_config)
        self.connection = None
        self.channel = None
        self.consumer_tag = None
        self.message_handlers: Dict[str, Callable] = {}
        self.is_consuming = False
    
    async def _initialize_module(self):
        """Inicialización específica del módulo de RabbitMQ"""
        logger.info("Inicializando módulo de RabbitMQ")
        
        # Cargar variables de entorno si existen
        self._load_env_variables()
        
        # Establecer conexión
        await self._connect()
        
        # Configurar exchange y queue
        await self._setup_exchange_queue()
        
        logger.info("Módulo de RabbitMQ inicializado correctamente")
    
    def _load_env_variables(self):
        """Cargar variables de entorno para RabbitMQ desde .env global"""
        import os
        from dotenv import load_dotenv
        
        # Cargar variables de entorno desde .env en el directorio raíz del proyecto
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        env_path = os.path.join(project_root, '.env')
        
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Variables de entorno cargadas desde: {env_path}")
        else:
            logger.warning(f"Archivo .env no encontrado en: {env_path}")
        
        # Mapeo de variables de entorno
        env_mapping = { 
            'RABBITMQ_HOST': 'host',
            'RABBITMQ_PORT': 'port',
            'RABBITMQ_USERNAME': 'username',
            'RABBITMQ_PASSWORD': 'password',
            'RABBITMQ_VHOST': 'virtual_host',
            'RABBITMQ_EXCHANGE': 'exchange_name',
            'RABBITMQ_QUEUE': 'queue_name',
            'RABBITMQ_ROUTING_KEY': 'routing_key'
        }
        
        # Cargar variables de entorno
        loaded_vars = 0
        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                if config_key in ['port']:
                    self.config[config_key] = int(value)
                else:
                    self.config[config_key] = value
                loaded_vars += 1
                logger.debug(f"Variable {env_var} cargada: {value}")
        
        # Establecer valores por defecto solo si no existen en .env
        if not self.config.get('host'):
            self.config['host'] = 'localhost'
            logger.info("Usando host por defecto: localhost")
        
        if not self.config.get('port'):
            self.config['port'] = 5672
            logger.info("Usando puerto por defecto: 5672")
        
        if not self.config.get('username'):
            self.config['username'] = 'guest'
            logger.info("Usando username por defecto: guest")
        
        if not self.config.get('password'):
            self.config['password'] = 'guest'
            logger.info("Usando password por defecto: guest")
        
        if not self.config.get('virtual_host'):
            self.config['virtual_host'] = '/'
            logger.info("Usando virtual_host por defecto: /")
        
        # Configurar nombres de canales basados en robot_id si no están en .env
        if not self.config.get('exchange_name'):
            self.config['exchange_name'] = 'robot_exchange'
            logger.info("Usando exchange por defecto: robot_exchange")
        
        if not self.config.get('queue_name'):
            self.config['queue_name'] = f'robot_{self.robot_id}_queue'
            logger.info(f"Usando queue por defecto: robot_{self.robot_id}_queue")
        
        if not self.config.get('routing_key'):
            self.config['routing_key'] = f'robot.{self.robot_id}'
            logger.info(f"Usando routing_key por defecto: robot.{self.robot_id}")
        
        logger.info(f"Variables de entorno RabbitMQ: {loaded_vars} cargadas del .env, resto con valores por defecto")
    
    async def _connect(self):
        """Establecer conexión con RabbitMQ"""
        try:
            # Simular conexión (en implementación real usarías aio_pika)
            self.connection = {
                'host': self.config['host'],
                'port': self.config['port'],
                'status': 'connected',
                'connected_at': datetime.now().isoformat()
            }
            
            self.channel = {
                'exchange': self.config['exchange_name'],
                'queue': self.config['queue_name'],
                'routing_key': self.config['routing_key'],
                'status': 'open'
            }
            
            logger.info(f"Conectado a RabbitMQ en {self.config['host']}:{self.config['port']}")
            
        except Exception as e:
            logger.error(f"Error al conectar con RabbitMQ: {e}")
            raise
    
    async def _setup_exchange_queue(self):
        """Configurar exchange y queue"""
        try:
            # Simular configuración de exchange y queue
            logger.info(f"Configurando exchange: {self.config['exchange_name']}")
            logger.info(f"Configurando queue: {self.config['queue_name']}")
            logger.info(f"Routing key: {self.config['routing_key']}")
            
        except Exception as e:
            logger.error(f"Error al configurar exchange/queue: {e}")
            raise
    
    async def _execute_module(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar operaciones de RabbitMQ según los parámetros"""
        try:
            operation = params.get('operation', 'send_message')
            
            if operation == 'send_message':
                return await self._send_message(params)
            elif operation == 'receive_message':
                return await self._receive_message(params)
            elif operation == 'start_consumer':
                return await self._start_consumer(params)
            elif operation == 'stop_consumer':
                return await self._stop_consumer(params)
            elif operation == 'declare_queue':
                return await self._declare_queue(params)
            elif operation == 'purge_queue':
                return await self._purge_queue(params)
            else:
                raise ValueError(f"Operación no soportada: {operation}")
                
        except Exception as e:
            logger.error(f"Error en operación de RabbitMQ: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enviar mensaje a RabbitMQ"""
        try:
            message = params.get('message')
            routing_key = params.get('routing_key', self.config['routing_key'])
            exchange = params.get('exchange', self.config['exchange_name'])
            priority = params.get('priority', 0)
            headers = params.get('headers', {})
            
            if not message:
                raise ValueError("message es requerido para enviar")
            
            # Simular envío de mensaje
            message_id = f"msg_{datetime.now().timestamp()}"
            
            message_data = {
                'id': message_id,
                'body': message,
                'routing_key': routing_key,
                'exchange': exchange,
                'priority': priority,
                'headers': headers,
                'timestamp': datetime.now().isoformat(),
                'status': 'sent'
            }
            
            # Guardar mensaje en base de datos
            await self._save_message(message_data, 'sent')
            
            logger.info(f"Mensaje enviado: {message_id}")
            
            return {
                'success': True,
                'operation': 'send_message',
                'message_id': message_id,
                'routing_key': routing_key,
                'exchange': exchange,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al enviar mensaje: {e}")
            raise
    
    async def _receive_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recibir un mensaje de RabbitMQ"""
        try:
            queue = params.get('queue', self.config['queue_name'])
            timeout = params.get('timeout', 5)
            auto_ack = params.get('auto_ack', self.config['auto_ack'])
            
            # Simular recepción de mensaje
            message_data = {
                'id': f"recv_{datetime.now().timestamp()}",
                'body': f"Mensaje de prueba recibido de {queue}",
                'queue': queue,
                'timestamp': datetime.now().isoformat(),
                'status': 'received'
            }
            
            # Guardar mensaje en base de datos
            await self._save_message(message_data, 'received')
            
            logger.info(f"Mensaje recibido: {message_data['id']}")
            
            return {
                'success': True,
                'operation': 'receive_message',
                'message': message_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al recibir mensaje: {e}")
            raise
    
    async def _start_consumer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Iniciar consumidor de mensajes"""
        try:
            queue = params.get('queue', self.config['queue_name'])
            handler_name = params.get('handler', 'default_handler')
            
            if self.is_consuming:
                logger.warning("Consumidor ya está activo")
                return {
                    'success': True,
                    'operation': 'start_consumer',
                    'status': 'already_running',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Simular inicio de consumidor
            self.is_consuming = True
            self.consumer_tag = f"consumer_{datetime.now().timestamp()}"
            
            logger.info(f"Consumidor iniciado en queue: {queue}")
            
            return {
                'success': True,
                'operation': 'start_consumer',
                'consumer_tag': self.consumer_tag,
                'queue': queue,
                'status': 'started',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al iniciar consumidor: {e}")
            raise
    
    async def _stop_consumer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detener consumidor de mensajes"""
        try:
            if not self.is_consuming:
                logger.warning("Consumidor no está activo")
                return {
                    'success': True,
                    'operation': 'stop_consumer',
                    'status': 'not_running',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Simular detención de consumidor
            consumer_tag = self.consumer_tag
            self.is_consuming = False
            self.consumer_tag = None
            
            logger.info(f"Consumidor detenido: {consumer_tag}")
            
            return {
                'success': True,
                'operation': 'stop_consumer',
                'consumer_tag': consumer_tag,
                'status': 'stopped',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al detener consumidor: {e}")
            raise
    
    async def _declare_queue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Declarar una nueva queue"""
        try:
            queue_name = params.get('queue_name')
            durable = params.get('durable', self.config['durable'])
            auto_delete = params.get('auto_delete', False)
            arguments = params.get('arguments', {})
            
            if not queue_name:
                raise ValueError("queue_name es requerido")
            
            # Simular declaración de queue
            logger.info(f"Queue declarada: {queue_name}")
            
            return {
                'success': True,
                'operation': 'declare_queue',
                'queue_name': queue_name,
                'durable': durable,
                'auto_delete': auto_delete,
                'arguments': arguments,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al declarar queue: {e}")
            raise
    
    async def _purge_queue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Purgar mensajes de una queue"""
        try:
            queue_name = params.get('queue_name', self.config['queue_name'])
            
            # Simular purga de queue
            purged_count = 5  # Simular 5 mensajes purgados
            
            logger.info(f"Queue purgada: {queue_name} ({purged_count} mensajes)")
            
            return {
                'success': True,
                'operation': 'purge_queue',
                'queue_name': queue_name,
                'purged_count': purged_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al purgar queue: {e}")
            raise
    
    async def _save_message(self, message_data: Dict[str, Any], message_type: str):
        """Guardar mensaje en la base de datos"""
        try:
            case_data = {
                'case_id': f"rabbitmq_{message_data['id']}",
                'transaction_type': f'rabbitmq_{message_type}',
                'status': 'completed',
                'data': message_data,
                'priority': message_data.get('priority', 1),
                'assigned_to': self.module_id,
                'notes': f"Mensaje RabbitMQ {message_type}"
            }
            
            success = await self.db_manager.insert_case_transaction(
                self.robot_id, case_data
            )
            
            if success:
                logger.debug(f"Mensaje RabbitMQ guardado: {message_data['id']}")
            else:
                logger.warning(f"No se pudo guardar mensaje RabbitMQ: {message_data['id']}")
        
        except Exception as e:
            logger.error(f"Error al guardar mensaje RabbitMQ: {e}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Registrar un manejador de mensajes"""
        self.message_handlers[message_type] = handler
        logger.info(f"Manejador registrado para tipo: {message_type}")
    
    async def get_rabbitmq_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del módulo de RabbitMQ"""
        return {
            'module_id': self.module_id,
            'robot_id': self.robot_id,
            'connection_status': self.connection.get('status') if self.connection else 'disconnected',
            'consumer_status': 'running' if self.is_consuming else 'stopped',
            'consumer_tag': self.consumer_tag,
            'message_handlers_count': len(self.message_handlers),
            'config': {
                'host': self.config.get('host'),
                'port': self.config.get('port'),
                'exchange': self.config.get('exchange_name'),
                'queue': self.config.get('queue_name'),
                'routing_key': self.config.get('routing_key')
            }
        }
    
    @staticmethod
    def get_module_info() -> Dict[str, Any]:
        """Información del módulo"""
        return {
            'name': 'Módulo de RabbitMQ',
            'description': 'Módulo para manejar mensajería con RabbitMQ',
            'version': '1.0.0',
            'operations': [
                'send_message', 'receive_message', 'start_consumer', 
                'stop_consumer', 'declare_queue', 'purge_queue'
            ]
        }
