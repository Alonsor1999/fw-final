# Dockerfile para PDF Consumer
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para PyMuPDF y otras librerías
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear directorios para datos si no existen
RUN mkdir -p /host/input_pdfs /host/output_json

# Exponer puerto si es necesario (opcional)
EXPOSE 8000

# Comando por defecto
CMD ["python", "main.py"]
