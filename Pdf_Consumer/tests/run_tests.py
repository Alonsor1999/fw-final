"""
Script principal para ejecutar todas las pruebas unitarias con pytest.
"""
import sys
import os
import pytest

# Agregar el directorio del proyecto al path para asegurar que los módulos se encuentren
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == '__main__':
    """
    Ejecuta pytest para descubrir y correr todas las pruebas.

    Argumentos de línea de comandos se pasan directamente a pytest.
    Por ejemplo:
    - Para correr con cobertura: python run_tests.py --cov=.
    - Para correr un archivo específico: python run_tests.py test_main.py
    - Para más verbosidad: python run_tests.py -v
    """
    print("=" * 70)
    print("EJECUTANDO PRUEBAS UNITARIAS CON PYTEST")
    print("=" * 70)

    # Llama a pytest, pasando los argumentos de la línea de comandos
    # excepto el nombre del script.
    exit_code = pytest.main(sys.argv[1:])

    print("=" * 70)
    if exit_code == 0:
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    else:
        print(f"❌ ALGUNAS PRUEBAS FALLARON (código de salida: {exit_code})")
    print("=" * 70)

    sys.exit(exit_code)