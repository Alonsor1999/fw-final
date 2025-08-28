#!/bin/bash
# Script para ejecutar PDF Consumer en modo TEST con Docker (sin docker-compose)

echo "🚀 Ejecutando PDF Consumer en modo TEST (solo Docker)..."

# Crear carpetas locales si no existen
mkdir -p /home/cristiansrc/Descargas/archivos/pdfs/
mkdir -p /home/cristiansrc/Descargas/archivos/jsons/

echo "📁 Carpetas creadas:"
echo "   - /home/cristiansrc/Descargas/archivos/pdfs/ (para PDFs de entrada)"
echo "   - /home/cristiansrc/Descargas/archivos/jsons/ (para JSONs de salida)"

# Verificar si Docker está disponible
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "💡 Instala Docker primero: https://docs.docker.com/engine/install/"
    exit 1
fi

# Verificar si Docker daemon está corriendo
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon no está corriendo"
    echo "💡 Inicia Docker con: sudo systemctl start docker"
    exit 1
fi

echo "✅ Docker está disponible y corriendo"

# Construir la imagen
echo "🔨 Construyendo la imagen Docker..."
docker build -t pdf-consumer .

if [ $? -ne 0 ]; then
    echo "❌ Error al construir la imagen Docker"
    exit 1
fi

echo "✅ Imagen construida exitosamente"

# Ejecutar el contenedor con volúmenes montados
echo "🚀 Ejecutando el contenedor..."
docker run --rm \
    -e TEST_MODE=true \
    -e AWS_REGION=us-east-1 \
    -e LOG_LEVEL=INFO \
    -e PDF_INPUT_PATH=/host/input_pdfs \
    -e JSON_OUTPUT_PATH=/host/output_json \
    -v "/home/cristiansrc/Descargas/archivos/pdfs:/host/input_pdfs" \
    -v "/home/cristiansrc/Descargas/archivos/jsons:/host/output_json" \
    pdf-consumer

echo "✅ Ejecución completada. Revisa /home/cristiansrc/Descargas/archivos/jsons/ para los resultados."
