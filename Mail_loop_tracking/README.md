# 📬 Mail Loop Tracking

Sistema de automatización para procesamiento de correos de Outlook usando Microsoft Graph API con capacidades avanzadas de filtrado, descarga de adjuntos y gestión de carpetas.

## 🎯 Características

- ✅ **Autenticación segura** con Microsoft Graph API (MSAL)
- ✅ **Filtrado avanzado** por remitente y palabras clave en asunto
- ✅ **Descarga automática** de adjuntos con gestión de errores
- ✅ **Movimiento inteligente** de correos procesados
- ✅ **Logging detallado** con rotación automática por niveles
- ✅ **Configuración flexible** con filtros predefinidos
- ✅ **Manejo robusto** de errores y reintentos

## 🏗️ Arquitectura

```
Mail loop tracking/
├── main.py                    # Punto de entrada principal
├── config.py                  # Configuración centralizada
├── .env                       # Variables de entorno (credenciales)
├── outlook/
│   ├── graph_client.py        # Cliente autenticado MS Graph
│   ├── mail_reader.py         # Lectura y filtrado de mensajes
│   ├── attachments.py         # Descarga de adjuntos
│   ├── move_mail.py           # Gestión de carpetas
│   ├── mail_filters_config.py # Configuración de filtros
│   └── mail_filter_examples.py # Ejemplos de uso
├── utils/
│   ├── logger_config.py       # Configuración de logging
│   └── helpers.py             # Utilidades comunes
├── credentials/               # Tokens persistentes
├── adjuntos/                  # Archivos descargados
├── logs/                      # Logs rotados por nivel
└── requirements.txt           # Dependencias
```

## 🚀 Instalación

### Prerrequisitos
Python 3.8+
- Cuenta de Microsoft 365 con permisos de correo
- Aplicación registrada en Azure AD

### Configuración

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd Mail-loop-tracking
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
# Crear archivo .env
cp .env .env

# Editar .env con tus credenciales
TENANT_ID=your_tenant_id
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
MAIL_USER=user@domain.com
GRAPH_SCOPE=https://graph.microsoft.com/.default
```

4. **Configurar permisos de Azure AD**
   - Mail.ReadWrite.All
   - User.Read.All (si aplica)

## 📖 Uso

### Uso Básico

```python
# Ejecutar procesamiento completo
python main.py
```

### Uso Programático

```python
from outlook.mail_reader import get_messages_by_sender, get_messages_by_subject_keywords

# Obtener mensajes de remitentes específicos
mensajes = get_messages_by_sender(["@empresa.com", "jefe@"], top=10)

# Obtener mensajes con palabras clave
mensajes_urgentes = get_messages_by_subject_keywords(
    keywords=["urgente", "importante"],
    exclude_keywords=["spam"],
    top=5
)
```

### Filtros Predefinidos

```python
from outlook.mail_filters_config import get_predefined_filter

# Usar filtro para mensajes urgentes
filtro_urgente = get_predefined_filter("urgent_business")
mensajes = get_messages_with_filter(top=20, message_filter=filtro_urgente)
```

### Filtros Personalizados

```python
from outlook.mail_reader import MessageFilter

# Crear filtro personalizado
filtro = MessageFilter(
    allowed_senders=["@miempresa.com"],
    blocked_senders=["@spam.com"],
    subject_keywords=["proyecto", "reporte"],
    subject_exclude_keywords=["completado"]
)
```

## ⚙️ Configuración

### Variables de Entorno

| Variable | Descripción | Obligatoria |
|----------|-------------|-------------|
| `TENANT_ID` | ID del tenant de Azure AD | ✅ |
| `CLIENT_ID` | ID de la aplicación registrada | ✅ |
| `CLIENT_SECRET` | Secreto de la aplicación | ✅ |
| `MAIL_USER` | Usuario de correo a procesar | ✅ |
| `GRAPH_SCOPE` | Scope de Microsoft Graph | ❌ |

### Filtros Disponibles

- `urgent_business`: Mensajes urgentes de la empresa
- `reports`: Reportes e informes
- `meetings`: Reuniones y eventos
- `projects`: Mensajes de proyectos
- `system_notifications`: Notificaciones del sistema
- `important_clients`: Clientes importantes
- `no_spam`: Excluir spam y publicidad
- `development`: Mensajes de desarrollo

## 📊 Logging

El sistema genera logs en diferentes niveles:

- **DEBUG**: Información detallada de filtrado y procesamiento
- **INFO**: Resumen de operaciones completadas
- **WARNING**: Casos especiales y advertencias
- **ERROR**: Errores de procesamiento
- **CRITICAL**: Errores críticos del sistema

Los logs se guardan en `logs/` con rotación automática diaria.

## 🔧 Desarrollo

### Estructura de Desarrollo

```python
# Ejemplo de extensión con nuevo filtro
from outlook.mail_reader import MessageFilter

class CustomFilter(MessageFilter):
    def __init__(self, custom_criteria):
        super().__init__()
        self.custom_criteria = custom_criteria
    
    def filter_message(self, message):
        # Lógica personalizada
        return super().filter_message(message) and self.custom_logic(message)
```

### Ejecutar Pruebas

```bash
# Pruebas unitarias
python -m pytest tests/

# Pruebas específicas
python outlook/test_mail_filtering.py
```

## 🚨 Solución de Problemas

### Errores Comunes

1. **Error de autenticación**
   - Verificar credenciales en `.env`
   - Confirmar permisos en Azure AD

2. **No se encuentran mensajes**
   - Revisar filtros aplicados
   - Verificar permisos de lectura

3. **Error al descargar adjuntos**
   - Verificar espacio en disco
   - Revisar permisos de escritura

### Logs de Debug

```bash
# Ver logs detallados
tail -f logs/debug.log

# Ver errores
tail -f logs/error.log
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en el repositorio
- Revisar la documentación de Microsoft Graph API
- Consultar los logs de debug

---

**Desarrollado con ❤️ para automatización de correos empresariales**
