#!/bin/bash

# Script para ejecutar contenedores Docker en macOS
# Framework Final - Docker Management Script

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar el banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    FRAMEWORK FINAL                           ║"
    echo "║                 Docker Management Script                     ║"
    echo "║                        macOS Edition                         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Función para mostrar ayuda
show_help() {
    echo -e "${YELLOW}Uso: $0 [COMANDO]${NC}"
    echo ""
    echo "Comandos disponibles:"
    echo "  start     - Iniciar todos los contenedores"
    echo "  stop      - Detener todos los contenedores"
    echo "  restart   - Reiniciar todos los contenedores"
    echo "  status    - Mostrar estado de los contenedores"
    echo "  logs      - Mostrar logs de los contenedores"
    echo "  build     - Reconstruir la imagen de la aplicación"
    echo "  clean     - Limpiar contenedores e imágenes no utilizadas"
    echo "  shell     - Acceder al shell del contenedor principal"
    echo "  backup    - Crear backup de la base de datos"
    echo "  help      - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

# Función para verificar si Docker está ejecutándose
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker no está ejecutándose. Por favor inicia Docker Desktop.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker está ejecutándose${NC}"
}

# Función para iniciar contenedores
start_containers() {
    echo -e "${BLUE}🚀 Iniciando contenedores...${NC}"
    
    # Crear directorios necesarios si no existen
    mkdir -p logs backups
    
    # Iniciar contenedores en background
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contenedores iniciados correctamente${NC}"
        echo ""
        echo -e "${YELLOW}📋 URLs de acceso:${NC}"
        echo "  🌐 Framework App: http://localhost:8000"
        echo "  🗄️  PostgreSQL: localhost:5432"
        echo "  🔴 Redis: localhost:6379"
        echo "  🐰 RabbitMQ: localhost:5672"
        echo "  🐰 RabbitMQ Admin: http://localhost:15672 (admin/admin)"
        echo "  🔐 Vault: http://localhost:8200"
        echo ""
        echo -e "${YELLOW}📊 Para ver el estado: $0 status${NC}"
        echo -e "${YELLOW}📝 Para ver logs: $0 logs${NC}"
    else
        echo -e "${RED}❌ Error al iniciar contenedores${NC}"
        exit 1
    fi
}

# Función para detener contenedores
stop_containers() {
    echo -e "${YELLOW}🛑 Deteniendo contenedores...${NC}"
    docker-compose down
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contenedores detenidos correctamente${NC}"
    else
        echo -e "${RED}❌ Error al detener contenedores${NC}"
        exit 1
    fi
}

# Función para reiniciar contenedores
restart_containers() {
    echo -e "${BLUE}🔄 Reiniciando contenedores...${NC}"
    docker-compose restart
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contenedores reiniciados correctamente${NC}"
    else
        echo -e "${RED}❌ Error al reiniciar contenedores${NC}"
        exit 1
    fi
}

# Función para mostrar estado
show_status() {
    echo -e "${BLUE}📊 Estado de los contenedores:${NC}"
    echo ""
    docker-compose ps
    echo ""
    
    # Mostrar uso de recursos
    echo -e "${BLUE}💾 Uso de recursos:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Función para mostrar logs
show_logs() {
    echo -e "${BLUE}📝 Mostrando logs de los contenedores...${NC}"
    echo -e "${YELLOW}Presiona Ctrl+C para salir de los logs${NC}"
    echo ""
    docker-compose logs -f
}

# Función para reconstruir imagen
build_image() {
    echo -e "${BLUE}🔨 Reconstruyendo imagen de la aplicación...${NC}"
    docker-compose build --no-cache
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Imagen reconstruida correctamente${NC}"
        echo -e "${YELLOW}💡 Ejecuta '$0 start' para iniciar con la nueva imagen${NC}"
    else
        echo -e "${RED}❌ Error al reconstruir la imagen${NC}"
        exit 1
    fi
}

# Función para limpiar
clean_docker() {
    echo -e "${YELLOW}🧹 Limpiando Docker...${NC}"
    
    # Preguntar confirmación
    read -p "¿Estás seguro de que quieres limpiar contenedores e imágenes no utilizadas? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -f
        docker volume prune -f
        echo -e "${GREEN}✅ Limpieza completada${NC}"
    else
        echo -e "${YELLOW}❌ Limpieza cancelada${NC}"
    fi
}

# Función para acceder al shell
access_shell() {
    echo -e "${BLUE}🐚 Accediendo al shell del contenedor principal...${NC}"
    docker-compose exec framework-app /bin/bash
}

# Función para crear backup
create_backup() {
    echo -e "${BLUE}💾 Creando backup de la base de datos...${NC}"
    
    # Crear directorio de backups si no existe
    mkdir -p backups
    
    # Crear nombre del archivo con timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="backups/framework_db_backup_${TIMESTAMP}.sql"
    
    # Crear backup
    docker-compose exec -T postgres pg_dump -U framework_user framework_db > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup creado: $BACKUP_FILE${NC}"
        echo -e "${YELLOW}📁 Ubicación: $(pwd)/$BACKUP_FILE${NC}"
    else
        echo -e "${RED}❌ Error al crear backup${NC}"
        exit 1
    fi
}

# Función principal
main() {
    show_banner
    
    # Verificar Docker
    check_docker
    
    # Procesar comando
    case "${1:-help}" in
        start)
            start_containers
            ;;
        stop)
            stop_containers
            ;;
        restart)
            restart_containers
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        build)
            build_image
            ;;
        clean)
            clean_docker
            ;;
        shell)
            access_shell
            ;;
        backup)
            create_backup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ Comando no válido: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@" 