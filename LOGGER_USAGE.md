# Sistema de Logging del Framework

## Descripción

El sistema de logging del framework está diseñado para manejar logs de auditoría y errores de manera organizada y eficiente. Los logs se almacenan en la estructura `files/logs/` con subdirectorios separados para auditoría y errores.

## Estructura de Directorios

```
files/
└── logs/
    ├── audit/          # Logs de auditoría e información
    └── error/          # Logs de errores
```

## Características Principales

- **Separación por niveles**: Los logs de información van a `audit/`, los errores van a `error/`
- **Archivos por fecha**: Los archivos se nombran con timestamp (formato: `ddmmyy`)
- **Prefijos opcionales**: Se pueden agregar prefijos para robots y módulos específicos
- **Encoding UTF-8**: Soporte completo para caracteres especiales
- **Formato estructurado**: Timestamp, nivel, módulo, línea y mensaje

## Uso Básico

### Importar el Logger

```python
from framework.shared.logger import Logger
```

### Métodos Disponibles

#### 1. Métodos de Nivel Básico

```python
# Log de información (va a audit/)
Logger.info("Mensaje de información")

# Log de error (va a error/)
Logger.error("Mensaje de error")

# Log de debug (va a audit/)
Logger.debug("Mensaje de debug")

# Log de advertencia (va a audit/)
Logger.warning("Mensaje de advertencia")

# Log crítico (va a audit/)
Logger.critical("Mensaje crítico")
```

#### 2. Métodos con Parámetros Opcionales

```python
# Con robot_id y module_name
Logger.info(
    "Mensaje de información",
    robot_id="robot_001",
    module_name="scraping_module"
)

Logger.error(
    "Error en el proceso",
    robot_id="robot_001",
    module_name="scraping_module"
)
```

#### 3. Métodos Específicos

```python
# Log específico de robot
Logger.robot_log("robot_001", "info", "Robot iniciando proceso")

# Log específico de módulo
Logger.module_log("scraping_module", "info", "Módulo cargado")

# Log del framework
Logger.framework_log("info", "Framework iniciado")
```

## Ejemplo de Integración en Robot

```python
import sys
import os
from framework.shared.logger import Logger

class MiRobot:
    def __init__(self):
        # Asegurar que los directorios de logs existan
        Logger.ensure_log_directories()
        self.robot_id = None
    
    async def initialize(self, robot_id: str):
        self.robot_id = robot_id
        
        Logger.info(
            f"Inicializando robot con ID: {robot_id}",
            robot_id=robot_id,
            module_name="MiRobot"
        )
        
        try:
            # Lógica de inicialización
            Logger.info(
                "Robot inicializado exitosamente",
                robot_id=robot_id,
                module_name="MiRobot"
            )
        except Exception as e:
            Logger.error(
                f"Error en inicialización: {e}",
                robot_id=robot_id,
                module_name="MiRobot"
            )
            raise
    
    async def execute_task(self):
        Logger.info(
            "Ejecutando tarea principal",
            robot_id=self.robot_id,
            module_name="MiRobot"
        )
        
        try:
            # Lógica de la tarea
            Logger.info(
                "Tarea completada exitosamente",
                robot_id=self.robot_id,
                module_name="MiRobot"
            )
        except Exception as e:
            Logger.critical(
                f"Error crítico en la tarea: {e}",
                robot_id=self.robot_id,
                module_name="MiRobot"
            )
            raise
```

## Formato de los Logs

Los logs se escriben con el siguiente formato:

```
2024-12-20 14:30:25 | INFO | business:45 | Mensaje de información
2024-12-20 14:30:26 | ERROR | business:67 | Error en el proceso
```

### Campos del Formato

- **Timestamp**: Fecha y hora del evento
- **Level**: Nivel del log (INFO, ERROR, DEBUG, WARNING, CRITICAL)
- **Module**: Nombre del módulo y número de línea
- **Message**: Mensaje del log

## Nombres de Archivos

### Archivos de Auditoría
- `LogAudit_201224.log` - Log general de auditoría
- `Robot_robot_001_LogAudit_201224.log` - Log específico de robot
- `Module_scraping_LogAudit_201224.log` - Log específico de módulo

### Archivos de Error
- `LogError_201224.log` - Log general de errores
- `Robot_robot_001_LogError_201224.log` - Error específico de robot
- `Module_scraping_LogError_201224.log` - Error específico de módulo

## Configuración

### Rutas de Logs

```python
# Las rutas se configuran automáticamente
LOG_BASE_DIR = "files/logs"
AUDIT_LOG_DIR = "files/logs/audit"
ERROR_LOG_DIR = "files/logs/error"
```

### Crear Directorios

```python
# Asegurar que los directorios existan
Logger.ensure_log_directories()
```

### Obtener Rutas

```python
# Obtener las rutas de los directorios de logs
log_paths = Logger.get_log_paths()
print(log_paths)
# Output: {'base_dir': 'files/logs', 'audit_dir': 'files/logs/audit', 'error_dir': 'files/logs/error'}
```

## Mejores Prácticas

1. **Siempre incluir robot_id y module_name** cuando sea posible para mejor trazabilidad
2. **Usar niveles apropiados**: INFO para información general, ERROR para errores, CRITICAL para errores fatales
3. **Mensajes descriptivos**: Incluir contexto relevante en los mensajes
4. **Manejo de excepciones**: Usar Logger.error() en bloques except
5. **Inicialización**: Llamar Logger.ensure_log_directories() al inicio de la aplicación

## Ejemplo Completo

```python
import asyncio
import sys
import os
from framework.shared.logger import Logger

async def main():
    # Configurar path del framework
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Asegurar directorios de logs
    Logger.ensure_log_directories()
    
    robot_id = "robot_001"
    
    try:
        Logger.info(
            f"Iniciando ejecución del robot {robot_id}",
            robot_id=robot_id,
            module_name="main"
        )
        
        # Lógica del robot
        await process_robot_task(robot_id)
        
        Logger.info(
            "Robot ejecutado exitosamente",
            robot_id=robot_id,
            module_name="main"
        )
        
    except Exception as e:
        Logger.critical(
            f"Error fatal en la ejecución: {e}",
            robot_id=robot_id,
            module_name="main"
        )
        raise

async def process_robot_task(robot_id: str):
    Logger.info(
        "Procesando tarea del robot",
        robot_id=robot_id,
        module_name="process_robot_task"
    )
    
    # Simular trabajo
    await asyncio.sleep(1)
    
    Logger.info(
        "Tarea completada",
        robot_id=robot_id,
        module_name="process_robot_task"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

Este sistema de logging proporciona una base sólida para el seguimiento y depuración de los robots en el framework.
