#!/usr/bin/env python
"""
Script para ejecutar pruebas y generar reporte de cobertura con salida a archivo
"""
import os
import sys
import subprocess
import datetime

def run_tests_and_coverage():
    # Cambiar al directorio del proyecto
    os.chdir(r"C:\Users\crist\Documents\proyectos\iniciativa-4\Pdf_Consumer")

    # Archivo de salida
    output_file = "test_coverage_results.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE PRUEBAS Y COBERTURA DE CÓDIGO\n")
        f.write(f"Fecha: {datetime.datetime.now()}\n")
        f.write("=" * 80 + "\n\n")

        # 1. Limpiar datos previos de cobertura
        f.write("1. Limpiando datos previos de cobertura...\n")
        try:
            result = subprocess.run([sys.executable, "-m", "coverage", "erase"],
                                  capture_output=True, text=True, timeout=30)
            f.write(f"   ✅ Limpieza completada (código: {result.returncode})\n")
        except Exception as e:
            f.write(f"   ❌ Error en limpieza: {e}\n")

        # 2. Ejecutar pruebas con coverage
        f.write("\n2. Ejecutando pruebas con cobertura...\n")
        try:
            cmd = [sys.executable, "-m", "coverage", "run", "--source=.",
                   "--omit=*/tests/*,*/venv/*,*/__pycache__/*,*/conftest.py",
                   "-m", "pytest", "tests/", "-v", "--tb=short"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            f.write(f"   Código de retorno: {result.returncode}\n")
            f.write(f"   STDOUT:\n{result.stdout}\n")
            if result.stderr:
                f.write(f"   STDERR:\n{result.stderr}\n")

        except subprocess.TimeoutExpired:
            f.write("   ❌ Las pruebas tardaron demasiado tiempo (timeout)\n")
        except Exception as e:
            f.write(f"   ❌ Error ejecutando pruebas: {e}\n")

        # 3. Generar reporte de cobertura
        f.write("\n3. Generando reporte de cobertura...\n")
        try:
            result = subprocess.run([sys.executable, "-m", "coverage", "report", "-m"],
                                  capture_output=True, text=True, timeout=60)

            f.write(f"   Código de retorno: {result.returncode}\n")
            f.write("   REPORTE DE COBERTURA:\n")
            f.write("-" * 40 + "\n")
            f.write(result.stdout)
            f.write("-" * 40 + "\n")

            if result.stderr:
                f.write(f"   STDERR:\n{result.stderr}\n")

        except Exception as e:
            f.write(f"   ❌ Error generando reporte: {e}\n")

        # 4. Generar reporte HTML
        f.write("\n4. Generando reporte HTML...\n")
        try:
            result = subprocess.run([sys.executable, "-m", "coverage", "html"],
                                  capture_output=True, text=True, timeout=60)

            f.write(f"   Código de retorno: {result.returncode}\n")
            f.write("   ✅ Reporte HTML generado en htmlcov/\n")

            if result.stderr:
                f.write(f"   STDERR:\n{result.stderr}\n")

        except Exception as e:
            f.write(f"   ❌ Error generando HTML: {e}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("PROCESO COMPLETADO\n")
        f.write("=" * 80 + "\n")

    print(f"Resultados guardados en: {output_file}")
    return output_file

if __name__ == "__main__":
    output_file = run_tests_and_coverage()

    # Mostrar el contenido del archivo
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            print(f.read())
    except Exception as e:
        print(f"Error leyendo archivo de resultados: {e}")
