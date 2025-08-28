# 📄 PDF Consumer

Sistema avanzado de procesamiento de documentos PDF con extracción inteligente de información utilizando tecnologías de AWS Comprehend y procesamiento local.

## 🚀 Características Principales

- **Procesamiento Dual**: Modo TEST (procesamiento local) y modo NORMAL (consumo desde RabbitMQ).
- **Extracción Inteligente**: Detección de cédulas, nombres y resúmenes usando IA.
- **AWS Integration**: Integración con S3 y AWS Comprehend para procesamiento avanzado.
- **Procesamiento por Páginas**: Extracción de información con referencia específica a páginas.
- **Alta Cobertura de Pruebas**: 89% de cobertura en pruebas unitarias.
- **Fallback Inteligente**: Sistema de respaldo entre extractores locales y AWS Comprehend.
- **Normalización de Texto**: Limpieza y estandarización de texto para mejorar la calidad de la extracción.

## 🏗️ Arquitectura

```
PDF Consumer
├── 📁 config/          # Configuración y constantes del sistema
├── 📁 extractors/      # Extractores de información (local + AWS Comprehend)
├── 📁 messaging/       # Consumidor RabbitMQ para modo normal
├── 📁 processors/      # Procesadores de documentos y utilidades de texto
├── 📁 services/        # Servicios AWS (S3)
├── 📁 tests/           # Suite completa de pruebas unitarias
└── 📄 main.py          # Punto de entrada principal
```

## 🔧 Componentes del Sistema

### 📋 Extractores de Información

#### Extractores Locales
- **CedulaExtractor**: Extracción de números de cédula con patrones regex avanzados.
- **NameExtractor**: Detección de nombres usando patrones y contexto.
- **SummarizeTextExtractor**: Generación de resúmenes usando algoritmos locales.

#### Extractores AWS Comprehend
- **CedulaExtractorComprehend**: Extracción de cédulas usando AWS Comprehend.
- **NameExtractorComprehend**: Detección de nombres con IA de AWS.
- **SummarizeTextExtractorComprehend**: Resúmenes avanzados con AWS.

### 🔄 Procesadores

- **DocumentProcessor**: Procesamiento básico de PDFs con PyMuPDF.
- **LocalPDFProcessor**: Procesamiento batch para modo TEST.

### 📨 Mensajería

- **RabbitMQConsumer**: Consumidor para procesamiento en tiempo real desde colas.

### ☁️ Servicios Cloud

- **AWSServiceS3**: Gestión de archivos en Amazon S3.

### 🛠️ Utilidades

- **text_utils**: Funciones para la limpieza y normalización del texto extraído de los PDFs (`normalize_text`) y para garantizar la correcta serialización de metadatos a JSON (`sanitize_for_json`).

## ⚙️ Configuración

### Variables de Entorno

#### Configuración General
```bash
# Modo de operación
TEST_MODE=false                    # true: modo test local, false: modo RabbitMQ

# Logging
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR. Nota: los logs de Pika (RabbitMQ) se silencian a WARNING.

# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=your-s3-bucket-name
```

#### Configuración RabbitMQ (Modo Normal)
```bash
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/%2F
QUEUE_NAME=pdf_ingest_q
PREFETCH=8
ON_MISSING_FILE=nack               # ack o nack
```

#### Configuración Modo Test
```bash
TEST_MODE=true
PDF_INPUT_PATH=/host/input_pdfs    # Carpeta de PDFs de entrada
JSON_OUTPUT_PATH=/host/output_json # Carpeta de salida para JSONs
```

## 🐳 Ejecución con Docker

### Modo Test (Procesamiento Local)
```bash
# Configurar variables de entorno
export TEST_MODE=true
export PDF_INPUT_PATH=/ruta/a/tus/pdfs
export JSON_OUTPUT_PATH=/ruta/de/salida

# Ejecutar contenedor
./run-docker.sh
```

### Modo Normal (RabbitMQ Consumer)
```bash
# Configurar variables de entorno para producción
export TEST_MODE=false
export RABBITMQ_URL=amqp://usuario:password@host:5672/
export S3_BUCKET=tu-bucket-s3

# Ejecutar contenedor
docker-compose up
```

## 🧪 Pruebas Unitarias

El proyecto cuenta con una suite completa de pruebas unitarias con **89% de cobertura**.

### Ejecutar Todas las Pruebas
```bash
# Linux/Unix/macOS
./run-test.sh

# Windows
run-test.bat
```

### Opciones Avanzadas
```bash
# Ejecutar con cobertura y reporte HTML
./run-test.sh -c --html

# Ejecutar prueba específica
./run-test.sh -s test_document_processor

# Ejecutar solo pruebas rápidas
./run-test.sh -f

# Mostrar ayuda completa
./run-test.sh --help
```

### Cobertura por Módulos
- **processors/**: 93-98%
- **extractors/**: 80-93%
- **messaging/**: 89%
- **services/**: 100%
- **config/**: 100%

## 📊 Formato de Salida

### Estructura JSON Generada
```json
{
  "original-name-file": "documento.pdf",
  "name-file": "uuid-generado.pdf",
  "documents": "12345678,87654321",
  "documents_detail": [
    {
      "number": "12345678",
      "pagPdf": [1, 3]
    }
  ],
  "names": "Juan Pérez,María García",
  "names_detail": [
    {
      "name": "Juan Pérez",
      "pagPdf": [1]
    }
  ],
  "matter": [
    {
      "matter": "Tema del documento",
      "resume": "Resumen inteligente del contenido"
    }
  ]
}
```

## 🔄 Flujo de Procesamiento

### Modo Test
1. **Escaneo**: Busca archivos PDF en `PDF_INPUT_PATH`.
2. **Extracción y Limpieza**: Procesa cada PDF, normalizando el texto extraído.
3. **Análisis**: Extrae cédulas, nombres y genera resúmenes.
4. **Fallback**: Usa AWS Comprehend si extractores locales fallan.
5. **Salida**: Genera JSON en `JSON_OUTPUT_PATH`.

### Modo Normal
1. **Consumo**: Escucha mensajes de RabbitMQ.
2. **Decodificación**: Descomprime contenido PDF (gzip+base64).
3. **Procesamiento**: Extrae y limpia información usando IA.
4. **Almacenamiento**: Sube PDF y JSON a S3.
5. **Confirmación**: Confirma procesamiento a RabbitMQ.

## 🛠️ Instalación Local

### Prerrequisitos
- Python 3.8+
- pip o conda
- Tesseract OCR (opcional)

### Instalación
```bash
# Clonar repositorio
git clone <repository-url>
cd Pdf_Consumer

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar dependencias de pruebas
pip install -r requirements-test.txt
```

## 📋 Dependencias Principales

- **boto3**: Integración con AWS
- **pika**: Cliente RabbitMQ
- **PyMuPDF**: Procesamiento de PDFs
- **pytesseract**: OCR para textos en imágenes
- **sumy**: Generación de resúmenes
- **nltk**: Procesamiento de lenguaje natural

## 🚨 Troubleshooting

### Errores Comunes

#### Error de Variables de Entorno
```
Error: S3_BUCKET no configurado
```
**Solución**: Configurar `TEST_MODE=true` para pruebas locales o definir `S3_BUCKET`.

#### Error de Formato de Datos
```
too many values to unpack (expected 2)
```
**Solución**: Verificar que `extract_text_by_pages()` devuelve tuplas `(text, page_number)`.

#### Error de Conexión RabbitMQ
```
Connection failed
```
**Solución**: Verificar `RABBITMQ_URL` y conectividad de red.

## 📈 Métricas de Rendimiento

- **Cobertura de Pruebas**: 89%
- **Extractores Disponibles**: 6 (3 locales + 3 AWS)
- **Formatos Soportados**: PDF (texto e imágenes)
- **Procesamiento**: Página por página con referencia
- **Fallback**: Sistema automático entre extractores

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para la funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Commit los cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para reportar problemas o solicitar funcionalidades, crear un issue en el repositorio del proyecto.

---

**Última actualización**: 2024-08-26  
**Versión**: 2.1.0  
**Estado**: Producción
