#!/usr/bin/env python3
"""
Script de ejecución para el proyecto pdf-consumer.
Ejecuta el proyecto como un módulo para resolver las importaciones relativas.
"""

import sys
import os

# Agregar el directorio actual al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from main import main
    main()
