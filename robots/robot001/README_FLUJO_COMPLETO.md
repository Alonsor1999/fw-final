# Robot001 - Flujo Completo de Procesamiento de Correos

## Descripción

El **Robot001** es un sistema automatizado que implementa un flujo completo de procesamiento de correos electrónicos de Outlook, específicamente diseñado para la carpeta "Iniciativa4". El robot lee correos, descarga adjuntos PDF, los envía a RabbitMQ y permite que el módulo **Pdf_Consumer** los procese a través de sus 5 capas de extracción.

## Arquitectura del Flujo

```
📧 Outlook (Iniciativa4) 
    ↓
🤖 Robot001 (Mail_loop_tracking)
    ↓ (Extrae: asunto, body, remitente, adjuntos)
📄 Descarga PDFs localmente
    ↓
🐰 RabbitMQ (pdf_processing_queue)
    ↓
📋 Pdf_Consumer (5 capas de procesamiento)
    ↓
📊 Resultados de extracción
```

## Componentes Principales

### 1. Mail_loop_tracking
- **`outlook/folder_reader.py`**: Lectura de correos de carpetas específicas
- **`outlook/attachment_downloader.py`**: Descarga de adjuntos PDF
- **`outlook/rabbitmq_sender.py`**: Envío de mensajes a RabbitMQ
- **`outlook/graph_client.py`**: Cliente para Microsoft Graph API

### 2. Robot001
- **`main.py`**: Orquestador principal del robot
- **`test_complete_flow.py`**: Script de pruebas del flujo completo

### 3. Pdf_Consumer
- Procesa los PDFs recibidos de RabbitMQ
- Aplica 5 capas de extracción de información
- Genera resultados estructurados

## Configuración

### Variables de Entorno Requeridas

```bash
# Microsoft Graph API (Mail_loop_tracking)
TENANT_ID=your_tenant_id
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
MAIL_USER=your_email@domain.com
GRAPH_SCOPE=https://graph.microsoft.com/.default

# RabbitMQ (Opcional - usa valores por defecto)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=pdf_processing_queue
```

### Configuración del Robot

```python
config = {
    'email_processing': {
        'enabled': True,
        'check_interval': 300,  # 5 minutos
        'max_emails': 100,
        'download_pdfs_only': True,  # Solo descargar PDFs
        'process_unread_only': True  # Solo procesar no leídos
    },
    'outlook_config': {
        'folder_name': 'Iniciativa4',
        'attachment_path': './robot001_attachments'
    },
    'rabbitmq_config': {
        'host': 'localhost',
        'port': 5672,
        'username': 'guest',
        'password': 'guest',
        'queue_name': 'pdf_processing_queue'
    }
}
```

## Funcionalidades

### 1. Lectura de Correos
- ✅ Acceso a carpeta específica "Iniciativa4"
- ✅ Filtrado por estado (leído/no leído)
- ✅ Extracción de metadatos (asunto, remitente, fecha)
- ✅ Detección de adjuntos

### 2. Descarga de Adjuntos
- ✅ Descarga automática de PDFs
- ✅ Nombres de archivo únicos con timestamp
- ✅ Organización por remitente y asunto
- ✅ Validación de tipos de archivo

### 3. Integración con RabbitMQ
- ✅ Envío de rutas de PDFs a cola
- ✅ Información del correo asociada
- ✅ Mensajes persistentes
- ✅ Cola de resúmenes de correos

### 4. Procesamiento Automático
- ✅ Monitoreo continuo cada 5 minutos
- ✅ Evita procesar mensajes duplicados
- ✅ Manejo de errores robusto
- ✅ Estadísticas de procesamiento

## Comandos Disponibles

### Comandos del Robot

```python
# Buscar correos en Iniciativa4
await robot.execute_command('search_iniciativa4', {'top': 50})

# Obtener resumen de la carpeta
await robot.execute_command('get_summary')

# Procesar correos automáticamente
await robot.execute_command('process_emails')

# Descargar adjuntos específicos
await robot.execute_command('download_attachments', {
    'message_ids': ['msg_id_1', 'msg_id_2']
})

# Obtener estado del robot
await robot.execute_command('get_status')
```

## Formato de Mensajes RabbitMQ

### Mensaje de PDF
```json
{
    "host_absolute_path": "/path/to/file.pdf",
    "file_name": "20241201_123456_sender_subject_document.pdf",
    "original_name": "document.pdf",
    "email_info": {
        "subject": "Asunto del correo",
        "sender": "remitente@domain.com",
        "received_date": "2024-12-01T12:34:56Z",
        "folder": "Iniciativa4",
        "message_id": "msg_id_123",
        "has_attachments": true,
        "attachment_count": 1
    },
    "processing_info": {
        "source": "robot001_outlook",
        "timestamp": "2024-12-01T12:34:56Z",
        "robot_id": "robot001"
    }
}
```

### Mensaje de Resumen
```json
{
    "type": "email_summary",
    "data": {
        "subject": "Asunto del correo",
        "sender": "remitente@domain.com",
        "pdfs_downloaded": 1,
        "pdfs_sent": 1,
        "processing_timestamp": "2024-12-01T12:34:56Z"
    },
    "timestamp": "2024-12-01T12:34:56Z",
    "robot_id": "robot001"
}
```

## Instalación y Uso

### 1. Instalar Dependencias

```bash
# Dependencias de Mail_loop_tracking
cd Mail_loop_tracking
pip install -r requirements.txt

# Dependencias del framework
cd ../framework
pip install -r requirements.txt

# Dependencias de Pdf_Consumer
cd ../Pdf_Consumer
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

```bash
# Crear archivo .env en Mail_loop_tracking/
TENANT_ID=your_tenant_id
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
MAIL_USER=your_email@domain.com
```

### 3. Ejecutar Robot

```bash
# Ejecutar robot principal
cd robots/robot001
python main.py

# Ejecutar pruebas
python test_complete_flow.py
```

### 4. Ejecutar Pdf_Consumer

```bash
# En otra terminal
cd Pdf_Consumer
python main.py
```

## Monitoreo y Logs

### Logs del Robot
- 📧 Lectura de correos
- 📄 Descarga de adjuntos
- 📤 Envío a RabbitMQ
- 📊 Estadísticas de procesamiento

### Estadísticas Disponibles
- Total de mensajes procesados
- PDFs descargados y enviados
- Errores de procesamiento
- Uso de almacenamiento

## Solución de Problemas

### Error de Autenticación
```bash
# Verificar configuración de Microsoft Graph API
cd Mail_loop_tracking
python test_iniciativa4.py
```

### Error de Conexión RabbitMQ
```bash
# Verificar que RabbitMQ esté ejecutándose
# Verificar configuración de conexión
```

### Error de Descarga de Adjuntos
```bash
# Verificar permisos de escritura en directorio de adjuntos
# Verificar espacio en disco
```

## Estructura de Archivos

```
robots/robot001/
├── main.py                    # Robot principal
├── test_complete_flow.py      # Pruebas del flujo
└── README_FLUJO_COMPLETO.md   # Esta documentación

Mail_loop_tracking/
├── outlook/
│   ├── folder_reader.py       # Lectura de carpetas
│   ├── attachment_downloader.py # Descarga de adjuntos
│   ├── rabbitmq_sender.py     # Envío a RabbitMQ
│   └── graph_client.py        # Cliente Graph API
├── config.py                  # Configuración
└── test_iniciativa4.py        # Pruebas de Iniciativa4

Pdf_Consumer/
├── main.py                    # Consumidor principal
├── messaging/
│   └── rabbitmq_consumer.py   # Consumidor RabbitMQ
└── processors/                # 5 capas de procesamiento
```

## Contribución

Para contribuir al desarrollo:

1. Crear una rama para tu feature
2. Implementar cambios
3. Ejecutar pruebas completas
4. Crear pull request con documentación

## Licencia

Este proyecto está bajo la licencia MIT.
