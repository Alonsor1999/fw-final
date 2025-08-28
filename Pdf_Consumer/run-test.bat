@echo off
REM Script para ejecutar pruebas unitarias del módulo Pdf_Consumer
REM Autor: Sistema automatizado
REM Fecha: 2025-08-25

setlocal enabledelayedexpansion

echo ==========================================
echo   EJECUTANDO PRUEBAS UNITARIAS
echo   Módulo: Pdf_Consumer
echo ==========================================

REM Configurar variables de entorno para pruebas
set TEST_MODE=true
set S3_BUCKET=test-bucket
set AWS_REGION=us-east-1
set LOG_LEVEL=INFO

REM Configuración por defecto
set VERBOSE=false
set COVERAGE=false
set FAST=false
set SPECIFIC_TEST=
set HTML_REPORT=false
set XML_REPORT=false

REM Procesar argumentos de línea de comandos
:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="-h" goto :show_help
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-v" (
    set VERBOSE=true
    shift
    goto :parse_args
)
if /i "%~1"=="--verbose" (
    set VERBOSE=true
    shift
    goto :parse_args
)
if /i "%~1"=="-c" (
    set COVERAGE=true
    shift
    goto :parse_args
)
if /i "%~1"=="--coverage" (
    set COVERAGE=true
    shift
    goto :parse_args
)
if /i "%~1"=="-f" (
    set FAST=true
    shift
    goto :parse_args
)
if /i "%~1"=="--fast" (
    set FAST=true
    shift
    goto :parse_args
)
if /i "%~1"=="-s" (
    set SPECIFIC_TEST=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--specific" (
    set SPECIFIC_TEST=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--html" (
    set HTML_REPORT=true
    shift
    goto :parse_args
)
if /i "%~1"=="--xml" (
    set XML_REPORT=true
    shift
    goto :parse_args
)
echo Opción desconocida: %~1
goto :show_help

:args_done

REM Verificar que estamos en el directorio correcto
if not exist "pytest.ini" (
    echo Error: No se encontró pytest.ini. Asegúrate de ejecutar desde el directorio Pdf_Consumer
    exit /b 1
)

REM Verificar que pytest está instalado
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo Error: pytest no está instalado. Instálalo con: pip install pytest
    exit /b 1
)

REM Construir comando pytest
set PYTEST_CMD=python -m pytest

REM Agregar opciones según parámetros
if "%VERBOSE%"=="true" (
    set PYTEST_CMD=!PYTEST_CMD! -v
)

if "%COVERAGE%"=="true" (
    set PYTEST_CMD=!PYTEST_CMD! --cov=processors --cov=extractors --cov=services --cov=messaging --cov=config
    set PYTEST_CMD=!PYTEST_CMD! --cov-report=term-missing

    if "%HTML_REPORT%"=="true" (
        set PYTEST_CMD=!PYTEST_CMD! --cov-report=html
    )

    if "%XML_REPORT%"=="true" (
        set PYTEST_CMD=!PYTEST_CMD! --cov-report=xml
    )
)

if "%FAST%"=="true" (
    set PYTEST_CMD=!PYTEST_CMD! -m "not slow and not integration"
)

if not "%SPECIFIC_TEST%"=="" (
    set PYTEST_CMD=!PYTEST_CMD! -k %SPECIFIC_TEST%
)

REM Agregar opciones adicionales para mejor output
set PYTEST_CMD=!PYTEST_CMD! --tb=short

echo Comando a ejecutar: !PYTEST_CMD!
echo.

REM Crear directorio de reportes si no existe
if not exist "reports" mkdir reports

REM Ejecutar las pruebas
echo Iniciando ejecución de pruebas...
!PYTEST_CMD!

REM Capturar el código de salida
set EXIT_CODE=%errorlevel%

echo.
echo ==========================================
if %EXIT_CODE%==0 (
    echo   ✅ TODAS LAS PRUEBAS PASARON
) else (
    echo   ❌ ALGUNAS PRUEBAS FALLARON
)
echo ==========================================

REM Mostrar información adicional si se generaron reportes
if "%COVERAGE%"=="true" if "%HTML_REPORT%"=="true" (
    echo.
    echo 📊 Reporte de cobertura HTML generado en: htmlcov\index.html
    echo    Abre el archivo en tu navegador para ver el reporte detallado
)

if "%COVERAGE%"=="true" if "%XML_REPORT%"=="true" (
    echo.
    echo 📊 Reporte de cobertura XML generado en: coverage.xml
)

goto :end

:show_help
echo Uso: %~n0 [OPCIONES]
echo.
echo Opciones:
echo   -h, --help          Mostrar esta ayuda
echo   -v, --verbose       Ejecutar con salida detallada
echo   -c, --coverage      Ejecutar con reporte de cobertura
echo   -f, --fast          Ejecutar solo pruebas rápidas (sin integración)
echo   -s, --specific TEST Ejecutar prueba específica
echo   --html              Generar reporte HTML de cobertura
echo   --xml               Generar reporte XML de cobertura
echo.
echo Ejemplos:
echo   %~n0                           # Ejecutar todas las pruebas
echo   %~n0 -c                        # Ejecutar con cobertura
echo   %~n0 -v --html                 # Ejecutar con salida detallada y reporte HTML
echo   %~n0 -s test_document_processor # Ejecutar prueba específica
echo.
exit /b 0

:end
REM Salir con el mismo código que pytest
exit /b %EXIT_CODE%
