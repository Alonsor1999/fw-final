@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: Ruta base
SET BASE_DIR=%~dp0
cd /d %BASE_DIR%

:: Nombre del entorno
SET VENV_DIR=vMail

:: Crear entorno si no existe
IF NOT EXIST %VENV_DIR% (
    echo [INFO] Creando entorno virtual...
    python -m venv %VENV_DIR%
)

:: Activar entorno
call %VENV_DIR%\Scripts\activate.bat

:: Instalar requisitos
echo [INFO] Instalando requerimientos...
pip install --upgrade pip
pip install -r requirements.txt

:: Ejecutar el proceso
echo [INFO] Ejecutando automatización...
python main.py

:: Finalizar
echo.
echo [FINALIZADO] Presiona una tecla para cerrar...
pause >nul