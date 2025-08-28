import logging
import os

from config import Config
from services import AWSServiceS3
from processors import DocumentProcessor, LocalPDFProcessor
from extractors import (
    NameExtractor,
    CedulaExtractor,
    NameExtractorComprehend,
    SummarizeTextExtractorComprehend,
    CedulaExtractorComprehend,
    SummarizeTextExtractor
)
from messaging import RabbitMQConsumer

def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Pika es muy verboso en INFO, lo subimos a WARNING
    logging.getLogger("pika").setLevel(logging.WARNING)

def main():
    """Punto de entrada principal de la aplicación."""
    setup_logging()
    log = logging.getLogger(__name__)

    try:
        # 1. Cargar configuración
        log.info("Cargando configuración...")
        config = Config()

        # 2. Inicializar servicios
        log.info("Inicializando servicios...")

        # Solo inicializar AWS si no estamos en modo test
        aws_service = None
        if not config.TEST_MODE:
            aws_service = AWSServiceS3(aws_region=config.AWS_REGION, s3_bucket=config.S3_BUCKET)

        doc_processor = DocumentProcessor()
        name_extractor = NameExtractor()
        cedula_extractor = CedulaExtractor()
        name_extractor_comprehend = NameExtractorComprehend()
        summarize_text_comprehend = SummarizeTextExtractorComprehend()
        cedula_extractor_comprehend = CedulaExtractorComprehend()
        summarize_text_extractor = SummarizeTextExtractor()

        # 3. Decidir entre modo test o modo normal
        if config.TEST_MODE:
            log.info("=== MODO TEST ACTIVADO ===")
            log.info("Carpeta de PDFs de entrada: %s", config.PDF_INPUT_PATH)
            log.info("Carpeta de JSONs de salida: %s", config.JSON_OUTPUT_PATH)

            # Procesar PDFs locales
            local_processor = LocalPDFProcessor(
                config=config,
                doc_processor=doc_processor,
                name_extractor=name_extractor,
                cedula_extractor=cedula_extractor,
                name_extractor_comprehend=name_extractor_comprehend,
                summarize_text_comprehend=summarize_text_comprehend,
                cedula_extractor_comprehend=cedula_extractor_comprehend,
                summarize_text_extractor=summarize_text_extractor
            )

            local_processor.process_all_pdfs()
            log.info("Procesamiento en modo test completado.")

        else:
            log.info("=== MODO NORMAL ACTIVADO ===")
            log.info("Conectando a RabbitMQ y subiendo a S3...")

            # 3. Iniciar el consumidor de RabbitMQ (modo normal)
            consumer = RabbitMQConsumer(
                config=config,
                aws_service=aws_service,
                doc_processor=doc_processor,
                name_extractor=name_extractor,
                cedula_extractor=cedula_extractor,
                name_extractor_comprehend=name_extractor_comprehend,
                summarize_text_comprehend=summarize_text_comprehend,
                cedula_extractor_comprehend=cedula_extractor_comprehend,
                summarize_text_extractor=summarize_text_extractor
            )

            log.info("Iniciando consumidor de RabbitMQ...")
            consumer.run()

    except Exception as e:
        log.critical("Error fatal al iniciar la aplicación: %s", e, exc_info=True)

if __name__ == "__main__":
    main()
