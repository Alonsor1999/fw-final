#!/bin/bash
# Script para ejecutar pruebas unitarias del módulo Pdf_Consumer
# Autor: Sistema automatizado
# Fecha: 2025-08-25

echo "=========================================="
echo "  EJECUTANDO PRUEBAS UNITARIAS"
echo "  Módulo: Pdf_Consumer"
echo "=========================================="

# Configurar variables de entorno para pruebas
export TEST_MODE=true
export S3_BUCKET=test-bucket
export AWS_REGION=us-east-1
export LOG_LEVEL=INFO

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  -h, --help          Mostrar esta ayuda"
    echo "  -v, --verbose       Ejecutar con salida detallada"
    echo "  -c, --coverage      Ejecutar con reporte de cobertura"
    echo "  -f, --fast          Ejecutar solo pruebas rápidas (sin integración)"
    echo "  -s, --specific TEST Ejecutar prueba específica"
    echo "  --html              Generar reporte HTML de cobertura"
    echo "  --xml               Generar reporte XML de cobertura"
    echo ""
    echo "Ejemplos:"
    echo "  $0                           # Ejecutar todas las pruebas"
    echo "  $0 -c                        # Ejecutar con cobertura"
    echo "  $0 -v --html                 # Ejecutar con salida detallada y reporte HTML"
    echo "  $0 -s test_document_processor # Ejecutar prueba específica"
}

# Configuración por defecto
VERBOSE=false
COVERAGE=false
FAST=false
SPECIFIC_TEST=""
HTML_REPORT=false
XML_REPORT=false

# Procesar argumentos de línea de comandos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -f|--fast)
            FAST=true
            shift
            ;;
        -s|--specific)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        --xml)
            XML_REPORT=true
            shift
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Verificar que estamos en el directorio correcto
if [ ! -f "pytest.ini" ]; then
    echo "Error: No se encontró pytest.ini. Asegúrate de ejecutar desde el directorio Pdf_Consumer"
    exit 1
fi

# Verificar que pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest no está instalado. Instálalo con: pip install pytest"
    exit 1
fi

# Construir comando pytest
PYTEST_CMD="python -m pytest"

# Agregar opciones según parámetros
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=processors --cov=extractors --cov=services --cov=messaging --cov=config"
    PYTEST_CMD="$PYTEST_CMD --cov-report=term-missing"

    if [ "$HTML_REPORT" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi

    if [ "$XML_REPORT" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=xml"
    fi
fi

if [ "$FAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not slow and not integration'"
fi

if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $SPECIFIC_TEST"
fi

# Agregar opciones adicionales para mejor output
PYTEST_CMD="$PYTEST_CMD --tb=short"

echo "Comando a ejecutar: $PYTEST_CMD"
echo ""

# Crear directorio de reportes si no existe
mkdir -p reports

# Ejecutar las pruebas
echo "Iniciando ejecución de pruebas..."
eval $PYTEST_CMD

# Capturar el código de salida
EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "  ✅ TODAS LAS PRUEBAS PASARON"
else
    echo "  ❌ ALGUNAS PRUEBAS FALLARON"
fi
echo "=========================================="

# Mostrar información adicional si se generaron reportes
if [ "$COVERAGE" = true ] && [ "$HTML_REPORT" = true ]; then
    echo ""
    echo "📊 Reporte de cobertura HTML generado en: htmlcov/index.html"
    echo "   Abre el archivo en tu navegador para ver el reporte detallado"
fi

if [ "$COVERAGE" = true ] && [ "$XML_REPORT" = true ]; then
    echo ""
    echo "📊 Reporte de cobertura XML generado en: coverage.xml"
fi

# Salir con el mismo código que pytest
exit $EXIT_CODE
