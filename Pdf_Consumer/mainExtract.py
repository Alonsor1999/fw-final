import logging
import os
import json
import sys
from pathlib import Path

from config import Config
# No usar AWS S3 - procesar solo localmente
# from services import AWSServiceS3
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

def process_specific_pdfs(pdf_paths: list, config: Config, doc_processor: DocumentProcessor, 
                         name_extractor: NameExtractor, cedula_extractor: CedulaExtractor,
                         name_extractor_comprehend: NameExtractorComprehend,
                         summarize_text_comprehend: SummarizeTextExtractorComprehend,
                         cedula_extractor_comprehend: CedulaExtractorComprehend,
                         summarize_text_extractor: SummarizeTextExtractor):
    """Procesa PDFs específicos desde rutas absolutas"""
    log = logging.getLogger(__name__)
    
    log.info(f"Procesando {len(pdf_paths)} PDFs específicos...")
    
    # Crear procesador local
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
    
    success_count = 0
    total_count = len(pdf_paths)
    
    for pdf_path_str in pdf_paths:
        try:
            pdf_path = Path(pdf_path_str)
            
            if not pdf_path.exists():
                log.error(f"PDF no encontrado: {pdf_path}")
                continue
                
            log.info(f"Procesando PDF específico: {pdf_path.name}")
            
            # Procesar el PDF usando el método del LocalPDFProcessor
            if local_processor.process_single_pdf(pdf_path):
                success_count += 1
                log.info(f"✅ PDF procesado exitosamente: {pdf_path.name}")
            else:
                log.error(f"❌ Error procesando PDF: {pdf_path.name}")
                
        except Exception as e:
            log.error(f"❌ Error procesando PDF {pdf_path_str}: {e}")
    
    log.info(f"Procesamiento completado: {success_count}/{total_count} PDFs procesados exitosamente")
    return success_count, total_count

def main():
    """Punto de entrada principal de la aplicación."""
    setup_logging()
    log = logging.getLogger(__name__)

    try:
        # 1. Cargar configuración
        log.info("Cargando configuración...")
        config = Config()
        
        # Forzar modo test para procesar solo localmente
        config.TEST_MODE = True

        # 2. Inicializar servicios
        log.info("Inicializando servicios...")

        # No usar AWS S3 - procesar solo localmente
        aws_service = None

        doc_processor = DocumentProcessor()
        name_extractor = NameExtractor()
        cedula_extractor = CedulaExtractor()
        name_extractor_comprehend = NameExtractorComprehend()
        summarize_text_comprehend = SummarizeTextExtractorComprehend()
        cedula_extractor_comprehend = CedulaExtractorComprehend()
        summarize_text_extractor = SummarizeTextExtractor()

        # 3. Verificar si se pasó un mensaje JSON de RabbitMQ como argumento
        if len(sys.argv) > 1:
            try:
                # Intentar parsear el primer argumento como JSON
                potential_json = sys.argv[1]
                if potential_json.startswith('{') and potential_json.endswith('}'):
                    # Es un mensaje JSON de RabbitMQ
                    message = json.loads(potential_json)
                    log.info("=== MODO MENSAJE RABBITMQ ACTIVADO ===")
                    
                    # 🎯 SOPORTE PARA AMBOS FORMATOS DE MENSAJE
                    # Formato nuevo del robot001: {"local_paths": [...], "primary_route_name": "..."}
                    # Formato anterior: {"pdf_rutas": [...], "clasificacion": "..."}
                    
                    if "local_paths" in message:
                        # 🔥 FORMATO NUEVO - robot001
                        pdf_rutas = message.get("local_paths", [])
                        guid = message.get("guid", "sin-guid")
                        clasificacion = message.get("primary_route_name", "Sin clasificación")
                        total_pdfs = len(pdf_rutas)
                        log.info("📤 Formato robot001 detectado")
                    else:
                        # 📋 FORMATO ANTERIOR - legacy
                        pdf_rutas = message.get("pdf_rutas", [])
                        guid = message.get("guid", "sin-guid")
                        clasificacion = message.get("clasificacion", "Sin clasificación")
                        total_pdfs = message.get("total_pdfs", len(pdf_rutas))
                        log.info("📋 Formato legacy detectado")
                    
                    log.info(f"GUID: {guid}")
                    log.info(f"Clasificación: {clasificacion}")
                    log.info(f"Total PDFs: {total_pdfs}")
                    log.info(f"PDFs a procesar: {len(pdf_rutas)}")
                    
                    for i, pdf_path in enumerate(pdf_rutas, 1):
                        log.info(f"  {i}. {pdf_path}")
                    
                    if pdf_rutas:
                        success_count, total_count = process_specific_pdfs(
                            pdf_rutas, config, doc_processor, name_extractor, cedula_extractor,
                            name_extractor_comprehend, summarize_text_comprehend,
                            cedula_extractor_comprehend, summarize_text_extractor
                        )
                        log.info(f"✅ Procesamiento de mensaje RabbitMQ completado: {success_count}/{total_count}")
                    else:
                        log.error("❌ No se encontraron rutas de PDFs en el mensaje")
                        
                else:
                    # No es JSON, son rutas de archivos individuales
                    pdf_paths = sys.argv[1:]
                    log.info(f"=== MODO PDFs ESPECÍFICOS ACTIVADO ===")
                    log.info(f"PDFs a procesar: {len(pdf_paths)}")
                    
                    for pdf_path in pdf_paths:
                        log.info(f"  - {pdf_path}")
                    
                    success_count, total_count = process_specific_pdfs(
                        pdf_paths, config, doc_processor, name_extractor, cedula_extractor,
                        name_extractor_comprehend, summarize_text_comprehend,
                        cedula_extractor_comprehend, summarize_text_extractor
                    )
                    
                    log.info(f"✅ Procesamiento de PDFs específicos completado: {success_count}/{total_count}")
                    
            except json.JSONDecodeError:
                # No es JSON válido, tratar como rutas de archivos
                pdf_paths = sys.argv[1:]
                log.info(f"=== MODO PDFs ESPECÍFICOS ACTIVADO ===")
                log.info(f"PDFs a procesar: {len(pdf_paths)}")
                
                for pdf_path in pdf_paths:
                    log.info(f"  - {pdf_path}")
                
                success_count, total_count = process_specific_pdfs(
                    pdf_paths, config, doc_processor, name_extractor, cedula_extractor,
                    name_extractor_comprehend, summarize_text_comprehend,
                    cedula_extractor_comprehend, summarize_text_extractor
                )
                
                log.info(f"✅ Procesamiento de PDFs específicos completado: {success_count}/{total_count}")
        
        else:
            # 4. Modo test original: procesar todos los PDFs de la carpeta
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

    except Exception as e:
        log.critical("Error fatal al iniciar la aplicación: %s", e, exc_info=True)

if __name__ == "__main__":
    main()