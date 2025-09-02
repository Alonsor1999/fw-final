"""
Procesador de documentos PDF
"""
import pdfplumber
import io
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Clase para procesar documentos PDF"""

    def __init__(self):
        """Inicializa el procesador de documentos"""
        self.logger = logging.getLogger(__name__)

    def _extract_text_from_pdf_bytes(self, pdf_bytes):
        """
        Extrae texto de bytes de un PDF

        Args:
            pdf_bytes (bytes): Contenido del PDF en bytes

        Returns:
            str: Texto extraído del PDF, None si hay error
        """
        try:
            # Crear un stream de bytes
            pdf_stream = io.BytesIO(pdf_bytes)
            text_content = ""

            # Abrir el PDF con pdfplumber
            with pdfplumber.open(pdf_stream) as pdf:
                # Extraer texto de cada página
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"

            return text_content.strip() if text_content.strip() else None

        except Exception as e:
            self.logger.error(f"Error al extraer texto del PDF: {str(e)}")
            return None

    def process_document(self, file_path=None, pdf_bytes=None):
        """
        Procesa un documento PDF desde archivo o bytes

        Args:
            file_path (str): Ruta al archivo PDF
            pdf_bytes (bytes): Contenido del PDF en bytes

        Returns:
            dict: Resultado del procesamiento
        """
        try:
            if pdf_bytes:
                text = self._extract_text_from_pdf_bytes(pdf_bytes)
            elif file_path:
                with open(file_path, 'rb') as file:
                    pdf_bytes = file.read()
                    text = self._extract_text_from_pdf_bytes(pdf_bytes)
            else:
                raise ValueError("Debe proporcionar file_path o pdf_bytes")

            return {
                'success': True,
                'text': text,
                'error': None
            }

        except Exception as e:
            self.logger.error(f"Error al procesar documento: {str(e)}")
            return {
                'success': False,
                'text': None,
                'error': str(e)
            }

    def process_pdf_bytes(self, pdf_bytes):
        """
        Procesa bytes de un PDF y extrae el texto

        Args:
            pdf_bytes (bytes): Contenido del PDF en bytes

        Returns:
            str: Texto extraído del PDF, None si hay error
        """
        return self._extract_text_from_pdf_bytes(pdf_bytes)

    def extract_text_by_pages(self, pdf_bytes):
        """
        Extrae texto de un PDF página por página

        Args:
            pdf_bytes (bytes): Contenido del PDF en bytes

        Returns:
            list: Lista de tuplas (page_text, page_number), None si hay error
        """
        try:
            if not pdf_bytes:
                return []

            # Crear un stream de bytes
            pdf_stream = io.BytesIO(pdf_bytes)
            pages_with_numbers = []

            # Abrir el PDF con pdfplumber
            with pdfplumber.open(pdf_stream) as pdf:
                # Extraer texto de cada página con su número
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        page_text = page_text.strip()
                    else:
                        page_text = ""
                    
                    # Los extractores esperan tuplas (page_text, page_number)
                    # page_number empieza en 1, no en 0
                    pages_with_numbers.append((page_text, page_num + 1))

            return pages_with_numbers

        except Exception as e:
            self.logger.error(f"Error al extraer texto por páginas del PDF: {str(e)}")
            return None

    def validate_pdf(self, pdf_bytes):
        """
        Valida si los bytes corresponden a un PDF válido

        Args:
            pdf_bytes (bytes): Contenido a validar

        Returns:
            bool: True si es un PDF válido, False en caso contrario
        """
        try:
            if not pdf_bytes:
                return False

            # Crear un stream de bytes
            pdf_stream = io.BytesIO(pdf_bytes)
            
            # Intentar abrir el PDF con pdfplumber
            with pdfplumber.open(pdf_stream) as pdf:
                # Si se puede abrir y tiene al menos una página, es válido
                return len(pdf.pages) > 0
                
        except Exception as e:
            self.logger.error(f"PDF inválido: {str(e)}")
            return False
