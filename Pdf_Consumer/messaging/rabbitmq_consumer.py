import pika
import json
import gzip
import base64
import uuid
import logging
from pathlib import Path

from extractors import (
    CedulaExtractorComprehend,
    NameExtractor,
    CedulaExtractor,
    NameExtractorComprehend,
    SummarizeTextExtractorComprehend,
    SummarizeTextExtractor
)
from config import Config
from services import AWSServiceS3
from processors import DocumentProcessor, summarize_text, sanitize_for_json

log = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(
            self, config: Config, aws_service: AWSServiceS3, doc_processor: DocumentProcessor, name_extractor: NameExtractor, cedula_extractor: CedulaExtractor, name_extractor_comprehend: NameExtractorComprehend, summarize_text_comprehend: SummarizeTextExtractorComprehend, cedula_extractor_comprehend: CedulaExtractorComprehend, summarize_text_extractor: SummarizeTextExtractor):
        self.config = config
        self.aws_service = aws_service
        self.doc_processor = doc_processor
        self.name_extractor = name_extractor
        self.cedula_extractor = cedula_extractor
        self.name_extractor_comprehend = name_extractor_comprehend
        self.summarize_text_comprehend = summarize_text_comprehend
        self.cedula_extractor_comprehend = cedula_extractor_comprehend
        self.summarize_text_extractor = summarize_text_extractor
        self.connection = None
        self.channel = None

    def _decode_pdf_from_message(self, msg: dict) -> bytes | None:
        # Priorizar host_absolute_path para el nuevo formato de evento
        host_abs_path = msg.get("host_absolute_path")
        if host_abs_path:
            p = Path(host_abs_path)
            if p.exists() and p.is_file():
                try:
                    log.info("Leyendo PDF desde host_absolute_path: %s", host_abs_path)
                    return p.read_bytes()
                except Exception as e:
                    log.error("No se pudo leer archivo en host_absolute_path %s: %s", p, e)
            else:
                log.error("El archivo en host_absolute_path no existe: %s", host_abs_path)

        # Fallback: intentar con content si existe (formato anterior)
        content = msg.get("content")
        if content and msg.get("content_encoding") == "gzip+base64":
            try:
                log.info("Decodificando contenido gzip+base64 (formato anterior)")
                return gzip.decompress(base64.b64decode(content))
            except Exception as e:
                log.error("Error decodificando contenido gzip+base64: %s", e)

        # Fallback: intentar con absolute_path (formato anterior)
        abs_path = msg.get("absolute_path")
        if abs_path:
            p = Path(abs_path)
            if not p.is_absolute():
                p = self.config.ROOT_PATH / p
            if p.exists() and p.is_file():
                try:
                    log.info("Leyendo PDF desde absolute_path: %s", abs_path)
                    return p.read_bytes()
                except Exception as e:
                    log.error("No se pudo leer archivo en ruta %s: %s", p, e)

        return None

    def on_message(self, ch, method, properties, body):
        try:
            msg = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            log.error("Mensaje no es JSON válido, descartando. Error: %s | body=%r", e, body[:200])
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        original_name = msg.get("file_name") or msg.get("original_name") or "unknown.pdf"
        pdf_bytes = self._decode_pdf_from_message(msg)

        if not pdf_bytes:
            log.error("No se pudo obtener bytes del PDF para: %s", original_name)
            if self.config.ON_MISSING == "ack":
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        try:
            new_id = uuid.uuid4().hex
            pdf_name = f"{new_id}.pdf"
            pdf_key = f"read-pdf/files/{pdf_name}"

            self.aws_service.upload_to_s3(pdf_key, pdf_bytes, "application/pdf")

            # Extraer contenido del PDF página por página (nueva funcionalidad)
            pages_text = self.doc_processor.extract_text_by_pages(pdf_bytes)

            # También extraer contenido completo para mantener compatibilidad
            content = self.doc_processor.process_pdf_bytes(pdf_bytes)
            if not content:
                log.error("El contenido del PDF está vacío o no se pudo extraer para: %s", original_name)
                ch.basic_ack(delivery_tag=method.delivery_tag) # Acknowledge to avoid reprocessing failed PDFs
                return

            # Extraer cédulas con información de página (nueva funcionalidad)
            cedulas_with_pages = []
            if pages_text:
                cedulas_with_pages = self.cedula_extractor.find_cedulas_with_pages(pages_text)
                if not cedulas_with_pages:
                    cedulas_with_pages = self.cedula_extractor_comprehend.extract_cedulas_with_pages(pages_text)

            # Extraer nombres con información de página (nueva funcionalidad)
            names_with_pages = []
            if pages_text:
                names_with_pages = self.name_extractor.extract_names_with_pages(pages_text)
                if not names_with_pages:
                    names_with_pages = self.name_extractor_comprehend.extract_names_with_pages(pages_text)

            # Mantener compatibilidad con el formato anterior
            documents = ",".join([cedula["number"] for cedula in cedulas_with_pages]) if cedulas_with_pages else ""

            # Si no se encontraron cédulas con la nueva función, usar el método anterior
            if not documents:
                documents = self.cedula_extractor.find_cedulas(content)
                if not documents:
                    documents = self.cedula_extractor_comprehend.extract_cedulas(content)

            # Mantener compatibilidad con el formato anterior para nombres
            names = ",".join([name["name"] for name in names_with_pages]) if names_with_pages else ""

            # Si no se encontraron nombres con la nueva función, usar el método anterior
            if not names:
                names = self.name_extractor.extract_all_names(content)
                if not names:
                    names = self.name_extractor_comprehend.find_nombres_str(content, use_comprehend=True, use_regex_fallback=True)

            matter = self.summarize_text_extractor.process(raw_text=content, top_k=8, sentences=10)

            if not matter:
                matter = self.summarize_text_comprehend.summarize(content, idioma="es")
            else :
                if isinstance(matter, str):
                    try:
                        matter = json.loads(matter)  # ahora 'matter' es list[dict]
                    except json.JSONDecodeError:
                        # Si no parsea, al menos envuélvelo lindo
                        matter = [{"matter": "Resumen", "resume": matter}]

            meta = {
                "original-name-file": sanitize_for_json(original_name),
                "name-file": pdf_name,
                "documents": documents,
                "cedulas_detalle": cedulas_with_pages,  # Nueva estructura JSON con páginas para cédulas
                "names": sanitize_for_json(names),
                "nombres_detalle": names_with_pages,  # Nueva estructura JSON con páginas para nombres
                "matter": matter
            }

            json_payload = json.dumps(meta, ensure_ascii=False)
            json_bytes = json_payload.encode("utf-8")
            json_key = f"read-pdf/json/{new_id}.json"

            self.aws_service.upload_to_s3(json_key, json_bytes, "application/json")

            # Log de las cédulas y nombres encontrados con páginas
            log.info("Cédulas encontradas en %s: %d", original_name, len(cedulas_with_pages))
            for cedula in cedulas_with_pages:
                log.info("  - Cédula %s en páginas %s", cedula["number"], cedula["pagPdf"])

            log.info("Nombres encontrados en %s: %d", original_name, len(names_with_pages))
            for nombre in names_with_pages:
                log.info("  - Nombre '%s' en páginas %s", nombre["name"], nombre["pagPdf"])

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            log.exception("Error procesando mensaje: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def run(self):
        """Ejecuta el consumidor de RabbitMQ"""
        try:
            log.info("Iniciando consumidor de RabbitMQ...")

            # Configurar conexión
            params = pika.URLParameters(self.config.RABBITMQ_URL)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

            # Declarar cola
            self.channel.queue_declare(queue=self.config.QUEUE_NAME, durable=True)

            # Configurar consumidor
            self.channel.basic_qos(prefetch_count=self.config.PREFETCH)
            self.channel.basic_consume(
                queue=self.config.QUEUE_NAME,
                on_message_callback=self.on_message
            )

            log.info("Esperando mensajes. Para salir presiona CTRL+C")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            log.info("Deteniendo consumidor...")
            if self.channel:
                self.channel.stop_consuming()
            raise
        except Exception as e:
            log.error("Error en la conexión con RabbitMQ: %s", e)
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                log.info("Conexión cerrada")
