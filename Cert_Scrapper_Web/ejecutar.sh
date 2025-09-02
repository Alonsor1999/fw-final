#!/bin/bash

# Activar modo seguro
set -e

# Definir ruta base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Crear entorno si no existe
if [ ! -d "venv" ]; then
  echo "[INFO] Creando entorno virtual..."
  python3 -m venv venv
fi

# Activar entorno
source venv/bin/activate

# Instalar requerimientos
echo "[INFO] Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Ejecutar proceso
echo "[INFO] Ejecutando main.py..."
python main.py

echo "[FINALIZADO] Presiona Enter para salir..."
read
