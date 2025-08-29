#!/bin/bash

# Script simple para iniciar contenedores Docker en macOS
# Framework Final - Quick Start

echo "🚀 Iniciando Framework Final en Docker..."

# Verificar si Docker está ejecutándose
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está ejecutándose. Por favor inicia Docker Desktop."
    exit 1
fi

# Crear directorios necesarios
mkdir -p logs backups

# Iniciar contenedores
echo "📦 Iniciando contenedores..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Framework Final iniciado correctamente!"
    echo ""
    echo "🌐 URLs de acceso:"
    echo "  • Framework App: http://localhost:8000"
    echo "  • RabbitMQ Admin: http://localhost:15672 (admin/admin)"
    echo "  • Vault: http://localhost:8200"
    echo ""
    echo "📊 Para ver estado: ./run-docker.sh status"
    echo "📝 Para ver logs: ./run-docker.sh logs"
    echo "🛑 Para detener: ./run-docker.sh stop"
else
    echo "❌ Error al iniciar contenedores"
    exit 1
fi 