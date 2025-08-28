import json
import uuid
import logging
from pathlib import Path
from typing import List

from extractors import (
    CedulaExtractorComprehend,
    NameExtractor,
    CedulaExtractor,
    NameExtractorComprehend,
    SummarizeTextExtractorComprehend,
    SummarizeTextExtractor
)
from config import Config
from processors.document_processor import DocumentProcessor
from processors.text_utils import sanitize_for_json

log = logging.getLogger(__name__)

class LocalPDFProcessor:
    """Procesador de PDFs locales para modo test."""

    def __init__(
        self,
        config: Config,
        doc_processor: DocumentProcessor,
        name_extractor: NameExtractor,
        cedula_extractor: CedulaExtractor,
        name_extractor_comprehend: NameExtractorComprehend,
        summarize_text_comprehend: SummarizeTextExtractorComprehend,
        cedula_extractor_comprehend: CedulaExtractorComprehend,
        summarize_text_extractor: SummarizeTextExtractor
    ):
        self.config = config
        self.doc_processor = doc_processor
        self.name_extractor = name_extractor
        self.cedula_extractor = cedula_extractor
        self.name_extractor_comprehend = name_extractor_comprehend
        self.summarize_text_comprehend = summarize_text_comprehend
        self.cedula_extractor_comprehend = cedula_extractor_comprehend
        self.summarize_text_extractor = summarize_text_extractor

    def find_pdf_files(self) -> List[Path]:
        """Busca todos los archivos PDF en la carpeta de entrada."""
        pdf_files = []
        input_path = self.config.PDF_INPUT_PATH

        if not input_path.exists():
            log.warning("La carpeta de PDFs de entrada no existe: %s", input_path)
            return pdf_files

        try:
            # Buscar archivos .pdf recursivamente
            pdf_files = list(input_path.rglob("*.pdf"))
            log.info("Encontrados %d archivos PDF en %s", len(pdf_files), input_path)
        except Exception as e:
            log.error("Error buscando archivos PDF: %s", e)

        return pdf_files

    def process_single_pdf(self, pdf_path: Path) -> bool:
        """Procesa un solo archivo PDF y guarda el resultado JSON."""
        try:
            log.info("Procesando PDF: %s", pdf_path.name)

            # Leer el archivo PDF
            pdf_bytes = pdf_path.read_bytes()

            # Extraer contenido del PDF página por página
            pages_text = self.doc_processor.extract_text_by_pages(pdf_bytes)
            if not pages_text:
                log.error("No se pudo extraer texto página por página para: %s", pdf_path.name)
                return False

            # Extraer contenido completo del PDF para mantener compatibilidad
            content = self.doc_processor.process_pdf_bytes(pdf_bytes)
            if not content:
                log.error("El contenido del PDF está vacío o no se pudo extraer para: %s", pdf_path.name)
                return False

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

            # Extraer resumen/materia
            matter = self.summarize_text_extractor.process(raw_text=content, top_k=8, sentences=10)

            if not matter:
                matter = self.summarize_text_comprehend.summarize(content, idioma="es")
            else:
                if isinstance(matter, str):
                    try:
                        matter = json.loads(matter)  # ahora 'matter' es list[dict]
                    except json.JSONDecodeError:
                        # Si no parsea, al menos envuélvelo lindo
                        matter = [{"matter": "Resumen", "resume": matter}]

            # Crear metadatos
            new_id = uuid.uuid4().hex

            # En modo test, usar el nombre original del PDF para el JSON
            json_filename = pdf_path.stem  # Nombre del archivo sin extensión

            meta = {
                "original-name-file": sanitize_for_json(pdf_path.name),
                "name-file": f"{new_id}.pdf",
                "documents": documents,
                "documents_detail": cedulas_with_pages,  # Nueva estructura JSON con páginas para cédulas
                "names": names,
                "names_detail": names_with_pages,  # Nueva estructura JSON con páginas para nombres
                "matter": matter
            }

            # Guardar JSON en carpeta de salida con nombre original del PDF
            self._save_json_result(meta, json_filename)

            log.info("PDF procesado exitosamente: %s -> %s.json", pdf_path.name, json_filename)
            log.info("Cédulas encontradas: %d", len(cedulas_with_pages))
            for cedula in cedulas_with_pages:
                log.info("  - Cédula %s en páginas %s", cedula["number"], cedula["pagPdf"])

            log.info("Nombres encontrados: %d", len(names_with_pages))
            for nombre in names_with_pages:
                log.info("  - Nombre '%s' en páginas %s", nombre["name"], nombre["pagPdf"])

            return True

        except Exception as e:
            log.exception("Error procesando PDF %s: %s", pdf_path.name, e)
            return False

    def _save_json_result(self, meta: dict, file_id: str):
        """Guarda el resultado JSON en la carpeta de salida."""
        output_path = self.config.JSON_OUTPUT_PATH

        # Crear carpeta si no existe
        output_path.mkdir(parents=True, exist_ok=True)

        # Guardar archivo JSON
        json_file_path = output_path / f"{file_id}.json"
        json_content = json.dumps(meta, ensure_ascii=False, indent=2)

        json_file_path.write_text(json_content, encoding="utf-8")
        log.info("JSON guardado en: %s", json_file_path)

    def process_all_pdfs(self):
        """Procesa todos los PDFs encontrados en la carpeta de entrada."""
        pdf_files = self.find_pdf_files()

        if not pdf_files:
            log.warning("No se encontraron archivos PDF para procesar.")
            return

        success_count = 0
        total_count = len(pdf_files)

        log.info("Iniciando procesamiento de %d archivos PDF...", total_count)

        for pdf_path in pdf_files:
            if self.process_single_pdf(pdf_path):
                success_count += 1

        log.info("Procesamiento completado: %d/%d PDFs procesados exitosamente", success_count, total_count)
