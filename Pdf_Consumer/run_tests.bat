@echo off
echo =====================================================
echo EJECUTANDO PRUEBAS UNITARIAS Y COBERTURA
echo =====================================================

cd /d "C:\Users\crist\Documents\proyectos\iniciativa-4\Pdf_Consumer"

echo.
echo 1. Limpiando datos de cobertura anterior...
python -m coverage erase

echo.
echo 2. Ejecutando pruebas con cobertura...
python -m coverage run --source=. --omit="*/tests/*,*/venv/*,*/__pycache__/*" -m pytest tests/ -v

echo.
echo 3. Generando reporte de cobertura...
python -m coverage report -m

echo.
echo 4. Generando reporte HTML...
python -m coverage html

echo.
echo =====================================================
echo PROCESO COMPLETADO
echo =====================================================
echo Revisa el reporte HTML en: htmlcov/index.html
echo.

pause
