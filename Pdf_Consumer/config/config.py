import os
from pathlib import Path

class Config:
    def __init__(self):
        self._load_config()

    def _env(self, name, default=None):
        v = os.getenv(name, default)
        return v if v not in (None, "") else default

    def _load_config(self):
        self.RABBITMQ_URL = self._env("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")
        self.QUEUE_NAME = self._env("QUEUE_NAME", "pdf_ingest_q")
        self.PREFETCH = int(self._env("PREFETCH", "8"))
        self.ROOT_PATH = Path(self._env("ROOT_PATH", "/data"))
        self.ON_MISSING = self._env("ON_MISSING_FILE", "nack").lower()
        self.AWS_REGION = self._env("AWS_REGION", "us-east-1")
        self.S3_BUCKET = self._env("S3_BUCKET")

        # Nuevas configuraciones para modo test
        self.TEST_MODE = self._env("TEST_MODE", "false").lower() == "true"

        # Configuración especial para rutas en Docker
        if self.TEST_MODE:
            # En modo test, usar rutas del host (montadas como volúmenes)
            self.PDF_INPUT_PATH = Path(self._env("PDF_INPUT_PATH", "/host/input_pdfs"))
            self.JSON_OUTPUT_PATH = Path(self._env("JSON_OUTPUT_PATH", "/host/output_json"))
        else:
            # En modo producción, usar rutas internas del contenedor
            self.PDF_INPUT_PATH = Path(self._env("PDF_INPUT_PATH", "./input_pdfs"))
            self.JSON_OUTPUT_PATH = Path(self._env("JSON_OUTPUT_PATH", "./output_json"))

        if not self.TEST_MODE and not self.S3_BUCKET:
            raise RuntimeError("S3_BUCKET no configurado.")

config = Config()
