@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Configuración de colores
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

:: Título del script
title Framework MVP - Gestor de Contenedores

echo %CYAN%===============================================%RESET%
echo %CYAN%    FRAMEWORK MVP - GESTOR DE CONTENEDORES    %RESET%
echo %CYAN%===============================================%RESET%
echo.

:: Verificar si Docker está ejecutándose
echo %YELLOW%Verificando Docker...%RESET%
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ Docker no está ejecutándose o no está instalado%RESET%
    echo %YELLOW%Por favor, inicia Docker Desktop y vuelve a ejecutar este script%RESET%
    pause
    exit /b 1
)
echo %GREEN%✅ Docker está ejecutándose%RESET%
echo.

:: Función para mostrar el menú
:menu
cls
echo %CYAN%===============================================%RESET%
echo %CYAN%    FRAMEWORK MVP - GESTOR DE CONTENEDORES    %RESET%
echo %CYAN%===============================================%RESET%
echo.
echo %WHITE%Selecciona una opción:%RESET%
echo.
echo %GREEN%1.%RESET% %WHITE%Iniciar todos los contenedores%RESET%
echo %GREEN%2.%RESET% %WHITE%Detener todos los contenedores%RESET%
echo %GREEN%3.%RESET% %WHITE%Reiniciar todos los contenedores%RESET%
echo %GREEN%4.%RESET% %WHITE%Ver estado de los contenedores%RESET%
echo %GREEN%5.%RESET% %WHITE%Ver logs de los contenedores%RESET%
echo %GREEN%6.%RESET% %WHITE%Limpiar contenedores y volúmenes%RESET%
echo %GREEN%7.%RESET% %WHITE%Abrir paneles de administración%RESET%
echo %GREEN%8.%RESET% %WHITE%Salir%RESET%
echo.
set /p choice="%YELLOW%Ingresa tu opción (1-8): %RESET%"

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto stop_all
if "%choice%"=="3" goto restart_all
if "%choice%"=="4" goto status
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto cleanup
if "%choice%"=="7" goto admin_panels
if "%choice%"=="8" goto exit
goto menu

:: Iniciar todos los contenedores
:start_all
echo.
echo %CYAN%🚀 Iniciando todos los contenedores...%RESET%
echo.

:: Construir la imagen si no existe
echo %YELLOW%📦 Construyendo imagen del framework...%RESET%
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo %RED%❌ Error construyendo la imagen%RESET%
    pause
    goto menu
)

:: Iniciar contenedores
echo %YELLOW%🔧 Iniciando contenedores...%RESET%
docker-compose up -d
if %errorlevel% neq 0 (
    echo %RED%❌ Error iniciando contenedores%RESET%
    pause
    goto menu
)

echo %GREEN%✅ Contenedores iniciados correctamente%RESET%
echo.
echo %CYAN%📊 Servicios disponibles:%RESET%
echo %WHITE%• Framework App:%RESET% http://localhost:8000
echo %WHITE%• PostgreSQL:%RESET% localhost:5432
echo %WHITE%• Redis:%RESET% localhost:6379
echo %WHITE%• RabbitMQ:%RESET% localhost:5672
echo %WHITE%• RabbitMQ Management:%RESET% http://localhost:15672
echo %WHITE%• Vault:%RESET% http://localhost:8200
echo.
echo %YELLOW%⏳ Esperando que los servicios estén listos...%RESET%
timeout /t 10 /nobreak >nul

:: Verificar estado
docker-compose ps
echo.
echo %GREEN%🎉 ¡Todos los servicios están ejecutándose!%RESET%
pause
goto menu

:: Detener todos los contenedores
:stop_all
echo.
echo %YELLOW%🛑 Deteniendo todos los contenedores...%RESET%
docker-compose down
if %errorlevel% neq 0 (
    echo %RED%❌ Error deteniendo contenedores%RESET%
) else (
    echo %GREEN%✅ Contenedores detenidos correctamente%RESET%
)
pause
goto menu

:: Reiniciar todos los contenedores
:restart_all
echo.
echo %YELLOW%🔄 Reiniciando todos los contenedores...%RESET%
docker-compose down
docker-compose up -d
if %errorlevel% neq 0 (
    echo %RED%❌ Error reiniciando contenedores%RESET%
) else (
    echo %GREEN%✅ Contenedores reiniciados correctamente%RESET%
)
pause
goto menu

:: Ver estado de los contenedores
:status
echo.
echo %CYAN%📊 Estado de los contenedores:%RESET%
echo.
docker-compose ps
echo.
echo %CYAN%📈 Estadísticas de recursos:%RESET%
docker stats --no-stream
pause
goto menu

:: Ver logs de los contenedores
:logs
echo.
echo %CYAN%📋 Selecciona el servicio para ver logs:%RESET%
echo.
echo %GREEN%1.%RESET% %WHITE%Framework App%RESET%
echo %GREEN%2.%RESET% %WHITE%PostgreSQL%RESET%
echo %GREEN%3.%RESET% %WHITE%Redis%RESET%
echo %GREEN%4.%RESET% %WHITE%RabbitMQ%RESET%
echo %GREEN%5.%RESET% %WHITE%Vault%RESET%
echo %GREEN%6.%RESET% %WHITE%Todos los servicios%RESET%
echo %GREEN%7.%RESET% %WHITE%Volver al menú%RESET%
echo.
set /p log_choice="%YELLOW%Ingresa tu opción (1-7): %RESET%"

if "%log_choice%"=="1" (
    echo %CYAN%📋 Logs del Framework App:%RESET%
    docker-compose logs -f framework-app
)
if "%log_choice%"=="2" (
    echo %CYAN%📋 Logs de PostgreSQL:%RESET%
    docker-compose logs -f postgres
)
if "%log_choice%"=="3" (
    echo %CYAN%📋 Logs de Redis:%RESET%
    docker-compose logs -f redis
)
if "%log_choice%"=="4" (
    echo %CYAN%📋 Logs de RabbitMQ:%RESET%
    docker-compose logs -f rabbitmq
)
if "%log_choice%"=="5" (
    echo %CYAN%📋 Logs de Vault:%RESET%
    docker-compose logs -f vault
)
if "%log_choice%"=="6" (
    echo %CYAN%📋 Logs de todos los servicios:%RESET%
    docker-compose logs -f
)
if "%log_choice%"=="7" goto menu
goto logs

:: Limpiar contenedores y volúmenes
:cleanup
echo.
echo %RED%⚠️  ADVERTENCIA: Esta acción eliminará todos los datos%RESET%
echo %YELLOW%¿Estás seguro de que quieres continuar? (s/N):%RESET%
set /p confirm=""
if /i not "%confirm%"=="s" goto menu

echo %YELLOW%🧹 Limpiando contenedores y volúmenes...%RESET%
docker-compose down -v
docker system prune -f
echo %GREEN%✅ Limpieza completada%RESET%
pause
goto menu

:: Abrir paneles de administración
:admin_panels
echo.
echo %CYAN%🌐 Abriendo paneles de administración...%RESET%
echo.

:: Framework App
echo %GREEN%🔗 Abriendo Framework App...%RESET%
start http://localhost:8000

:: RabbitMQ Management
echo %GREEN%🔗 Abriendo RabbitMQ Management...%RESET%
start http://localhost:15672

:: Vault
echo %GREEN%🔗 Abriendo Vault...%RESET%
start http://localhost:8200

echo %GREEN%✅ Paneles abiertos en el navegador%RESET%
echo.
echo %YELLOW%Credenciales por defecto:%RESET%
echo %WHITE%• RabbitMQ Management:%RESET% admin / admin
echo %WHITE%• Vault Token:%RESET% root
echo.
pause
goto menu

:: Salir
:exit
echo.
echo %CYAN%👋 ¡Gracias por usar el Framework MVP!%RESET%
echo %YELLOW%Recuerda detener los contenedores cuando termines:%RESET%
echo %WHITE%docker-compose down%RESET%
echo.
pause
exit /b 0
