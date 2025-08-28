@echo off
REM Script para ejecutar PDF Consumer en modo TEST con Docker (sin docker-compose)

echo 🚀 Ejecutando PDF Consumer en modo TEST (solo Docker)...

echo 📁 Carpetas creadas:
echo    - C:\Users\crist\Documents\read_pdf\pdfs\ (para PDFs de entrada)
echo    - C:\Users\crist\Documents\read_pdf\json\ (para JSONs de salida)

REM Verificar si Docker está disponible
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker no está instalado
    echo 💡 Instala Docker Desktop desde https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Docker está instalado

REM Verificar si Docker daemon está corriendo
docker info >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Docker daemon no está corriendo
    echo 🚀 Intentando iniciar Docker Desktop...

    REM Intentar iniciar Docker Desktop
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    echo ⏳ Esperando a que Docker Desktop se inicie...
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 (
        echo 📡 Aún esperando Docker...
        goto wait_docker
    )
    echo ✅ Docker Desktop está corriendo
) else (
    echo ✅ Docker daemon está corriendo
)

REM Construir la imagen
echo 🔨 Construyendo la imagen Docker...
docker build -t pdf-consumer .

if errorlevel 1 (
    echo ❌ Error al construir la imagen Docker
    pause
    exit /b 1
)

echo ✅ Imagen construida exitosamente

REM Ejecutar el contenedor con volúmenes montados
echo 🚀 Ejecutando el contenedor PDF Consumer...
docker run --rm ^
    -e TEST_MODE=true ^
    -e AWS_REGION=us-east-1 ^
    -e LOG_LEVEL=INFO ^
    -e PDF_INPUT_PATH=/host/input_pdfs ^
    -e JSON_OUTPUT_PATH=/host/output_json ^
    -v "C:\Users\crist\Documents\read_pdf\pdfs:/host/input_pdfs" ^
    -v "C:\Users\crist\Documents\read_pdf\json:/host/output_json" ^
    pdf-consumer

echo.
echo ✅ Proceso completado
pause
