import os
from pathlib import Path

class Config:
    def __init__(self):
        self._load_config()

    def _env(self, name, default=None):
        v = os.getenv(name, default)
        return v if v not in (None, "") else default

    def _load_config(self):
        self.RABBITMQ_URL = self._env("RABBITMQ_URL", "amqp://localhost:5672")
        self.QUEUE_NAME = self._env("QUEUE_NAME", "pdf_processing_queue")
        self.PREFETCH = int(self._env("PREFETCH", "8"))
        self.ROOT_PATH = Path(self._env("ROOT_PATH", "/data"))
        self.ON_MISSING = self._env("ON_MISSING_FILE", "nack").lower()
        self.AWS_REGION = self._env("AWS_REGION", "us-east-1")
        self.S3_BUCKET = self._env("S3_BUCKET", "test-bucket")

        # Nuevas configuraciones para modo test
        self.TEST_MODE = self._env("TEST_MODE", "false").lower() == "true"
        
        # Forzar modo test para procesar PDFs localmente
        self.TEST_MODE = True

        # Configuración especial para rutas en Docker
        if self.TEST_MODE:
            # En modo test, usar rutas de los PDFs descargados por Robot001
            # Usar ruta absoluta desde el directorio Pdf_Consumer hacia robot001_attachments
            current_dir = Path.cwd()
            
            # Si estamos ejecutando desde Pdf_Consumer, subir un nivel
            if current_dir.name == "Pdf_Consumer":
                project_root = current_dir.parent
            else:
                # Si estamos ejecutando desde fw-final (directorio raíz)
                project_root = current_dir
            
            self.PDF_INPUT_PATH = Path(self._env("PDF_INPUT_PATH", str(project_root / "robot001_attachments")))
            self.JSON_OUTPUT_PATH = Path(self._env("JSON_OUTPUT_PATH", "./output_json"))
        else:
            # En modo producción, usar rutas internas del contenedor
            self.PDF_INPUT_PATH = Path(self._env("PDF_INPUT_PATH", "./input_pdfs"))
            self.JSON_OUTPUT_PATH = Path(self._env("JSON_OUTPUT_PATH", "./output_json"))

        #if not self.TEST_MODE and not self.S3_BUCKET:
           # raise RuntimeError("S3_BUCKET no configurado.")

config = Config()
