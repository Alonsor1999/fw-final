# Framework MVP - Gestión de Contenedores

Este proyecto incluye scripts para gestionar fácilmente todos los contenedores Docker del Framework MVP.

## 🚀 Scripts Disponibles

### 1. `start-containers.bat` - Gestor Completo
Script interactivo con menú para gestionar todos los contenedores.

**Funcionalidades:**
- ✅ Iniciar todos los contenedores
- 🛑 Detener todos los contenedores
- 🔄 Reiniciar contenedores
- 📊 Ver estado y estadísticas
- 📋 Ver logs de servicios
- 🧹 Limpiar contenedores y volúmenes
- 🌐 Abrir paneles de administración

**Uso:**
```bash
start-containers.bat
```

### 2. `quick-start.bat` - Inicio Rápido
Script simple para iniciar rápidamente todos los servicios.

**Uso:**
```bash
quick-start.bat
```

### 3. `stop-containers.bat` - Detener Servicios
Script para detener todos los contenedores.

**Uso:**
```bash
stop-containers.bat
```

## 📊 Servicios Incluidos

| Servicio | Puerto | URL | Credenciales |
|----------|--------|-----|--------------|
| **Framework App** | 8000 | http://localhost:8000 | - |
| **PostgreSQL** | 5432 | localhost:5432 | framework_user/framework_pass |
| **Redis** | 6379 | localhost:6379 | - |
| **RabbitMQ** | 5672 | localhost:5672 | admin/admin |
| **RabbitMQ Management** | 15672 | http://localhost:15672 | admin/admin |
| **Vault** | 8200 | http://localhost:8200 | Token: root |

## 🔧 Comandos Manuales

Si prefieres usar comandos manuales:

### Iniciar servicios
```bash
docker-compose up -d
```

### Detener servicios
```bash
docker-compose down
```

### Ver logs
```bash
docker-compose logs -f
```

### Ver estado
```bash
docker-compose ps
```

### Reconstruir contenedores
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 🐳 Requisitos

- **Docker Desktop** instalado y ejecutándose
- **Docker Compose** (incluido en Docker Desktop)
- Mínimo 4GB de RAM disponible
- 10GB de espacio libre en disco

## 🔍 Solución de Problemas

### Error: "Docker no está ejecutándose"
1. Abre Docker Desktop
2. Espera a que se inicie completamente
3. Ejecuta el script nuevamente

### Error: "Puerto ya en uso"
```bash
# Ver qué está usando el puerto
netstat -ano | findstr :8000

# Detener contenedores existentes
docker-compose down
```

### Error: "No hay espacio en disco"
```bash
# Limpiar imágenes no utilizadas
docker system prune -a

# Limpiar volúmenes
docker volume prune
```

### Error: "Permisos insuficientes"
Ejecuta el script como administrador.

## 📁 Estructura de Volúmenes

Los datos se almacenan en volúmenes Docker:

- `postgres_data`: Base de datos PostgreSQL
- `redis_data`: Cache de Redis
- `rabbitmq_data`: Colas de RabbitMQ

## 🔐 Variables de Entorno

Las variables de entorno están configuradas en `docker-compose.yml`:

```yaml
DATABASE_URL=postgresql://framework_user:framework_pass@postgres:5432/framework_db
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://framework_user:framework_pass@rabbitmq:5672/
VAULT_ADDR=http://vault:8200
```

## 🚨 Notas Importantes

1. **Primera ejecución**: La construcción inicial puede tomar varios minutos
2. **Memoria**: Los contenedores requieren al menos 4GB de RAM
3. **Persistencia**: Los datos se mantienen entre reinicios
4. **Logs**: Los logs se pueden ver con `docker-compose logs -f [servicio]`

## 🆘 Soporte

Si encuentras problemas:

1. Verifica que Docker Desktop esté ejecutándose
2. Ejecuta `docker-compose down` para limpiar
3. Reconstruye con `docker-compose build --no-cache`
4. Inicia con `docker-compose up -d`

## 📝 Logs y Monitoreo

### Ver logs en tiempo real
```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f framework-app
docker-compose logs -f postgres
docker-compose logs -f rabbitmq
```

### Estadísticas de recursos
```bash
docker stats
```

### Estado de salud
```bash
docker-compose ps
```
