@echo off
chcp 65001 >nul

echo 🛑 Deteniendo Framework MVP...
echo.

docker-compose down

echo.
echo ✅ Contenedores detenidos
echo.
pause
