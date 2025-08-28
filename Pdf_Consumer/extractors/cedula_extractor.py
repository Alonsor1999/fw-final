import re
import unicodedata
from typing import List, Optional, Dict, Any, Tuple
import json

from config.constants import (
    CEDULA_NUM_ANY, CEDULA_VERIF_PAT, CEDULA_BLACKLIST_FIELDS,
    CEDULA_PRIMARY_TOKENS, CEDULA_RAD_LABEL
)

class CedulaExtractor:
    """
    Encapsula la lógica para extraer números de cédula de un texto.
    """

    def find_cedulas(self, pdf_text: str) -> str:
        if not pdf_text:
            return ""

        def normalize(s: str) -> str:
            s = unicodedata.normalize("NFKD", s)
            s = "".join(ch for ch in s if not unicodedata.combining(ch))
            for bad in ("\u00AD", "\u200B", "\u200C", "\u200D", "\uFEFF"):
                s = s.replace(bad, "")
            s = (s.replace("\u00A0", " ").replace("\u202F", " ").replace("\u2009", " ").replace("\u2007", " ")
                   .replace("–", "-").replace("—", "-")
                   .replace("'", "'").replace("'","'").replace(""", '"').replace(""", '"'))
            return s.lower()

        def clean_digits(s: str) -> str:
            return re.sub(r"\D", "", s)

        def valid_len(num: str) -> bool:
            return 6 <= len(num) <= 10

        text = normalize(pdf_text)
        found = set()
        banned_numbers = set()

        for mr in CEDULA_RAD_LABEL.finditer(text):
            chain = re.sub(r"[^\d]", "", mr.group(1))
            for L in range(6, 11):
                for i in range(0, max(0, len(chain) - L + 1)):
                    banned_numbers.add(chain[i:i+L])

        for mm in CEDULA_NUM_ANY.finditer(text):
            digits = clean_digits(mm.group(0))
            if 8 <= len(digits) <= 12 and digits.startswith("0"):
                left = text[max(0, mm.start() - 60): mm.start()]
                right = text[mm.end(): min(len(text), mm.end() + 60)]
                if re.search(CEDULA_VERIF_PAT, left + right):
                    banned_numbers.add(digits)

        for nm in CEDULA_NUM_ANY.finditer(text):
            raw = nm.group(0)
            digits = clean_digits(raw)
            if not valid_len(digits) or digits in banned_numbers:
                continue

            left = text[max(0, nm.start()-90):nm.start()]
            right = text[nm.end():min(len(text), nm.end()+90)]

            if re.search(CEDULA_BLACKLIST_FIELDS, left+right):
                continue

            if re.search(CEDULA_PRIMARY_TOKENS, left) or "identificado con" in left or "cedula de" in left:
                found.add(digits)

        return ",".join(sorted(found))

    def find_cedulas_with_pages(self, pages_text: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        """
        Extrae números de cédula página por página y retorna un array JSON
        con la estructura: [{"number": "", "pagPdf": []}]
        """
        if not pages_text:
            return []

        def normalize(s: str) -> str:
            s = unicodedata.normalize("NFKD", s)
            s = "".join(ch for ch in s if not unicodedata.combining(ch))
            for bad in ("\u00AD", "\u200B", "\u200C", "\u200D", "\uFEFF"):
                s = s.replace(bad, "")
            s = (s.replace("\u00A0", " ").replace("\u202F", " ").replace("\u2009", " ").replace("\u2007", " ")
                   .replace("–", "-").replace("—", "-")
                   .replace("'", "'").replace("'","'").replace(""", '"').replace(""", '"'))
            return s.lower()

        def clean_digits(s: str) -> str:
            return re.sub(r"\D", "", s)

        def valid_len(num: str) -> bool:
            return 6 <= len(num) <= 10

        # Primero, obtener números prohibidos de todo el documento
        full_text = normalize(" ".join([page_text for page_text, _ in pages_text]))
        banned_numbers = set()

        for mr in CEDULA_RAD_LABEL.finditer(full_text):
            chain = re.sub(r"[^\d]", "", mr.group(1))
            for L in range(6, 11):
                for i in range(0, max(0, len(chain) - L + 1)):
                    banned_numbers.add(chain[i:i+L])

        for mm in CEDULA_NUM_ANY.finditer(full_text):
            digits = clean_digits(mm.group(0))
            if 8 <= len(digits) <= 12 and digits.startswith("0"):
                left = full_text[max(0, mm.start() - 60): mm.start()]
                right = full_text[mm.end(): min(len(full_text), mm.end() + 60)]
                if re.search(CEDULA_VERIF_PAT, left + right):
                    banned_numbers.add(digits)

        # Ahora procesar página por página y mantener todas las páginas por cédula
        cedulas_pages = {}  # {numero_cedula: [paginas]}

        for page_text, page_num in pages_text:
            if not page_text.strip():
                continue

            text = normalize(page_text)

            for nm in CEDULA_NUM_ANY.finditer(text):
                raw = nm.group(0)
                digits = clean_digits(raw)
                if not valid_len(digits) or digits in banned_numbers:
                    continue

                left = text[max(0, nm.start()-90):nm.start()]
                right = text[nm.end():min(len(text), nm.end()+90)]

                if re.search(CEDULA_BLACKLIST_FIELDS, left+right):
                    continue

                if re.search(CEDULA_PRIMARY_TOKENS, left) or "identificado con" in left or "cedula de" in left:
                    if digits not in cedulas_pages:
                        cedulas_pages[digits] = []
                    if page_num not in cedulas_pages[digits]:
                        cedulas_pages[digits].append(page_num)

        # Convertir a la estructura final con páginas ordenadas
        cedulas_found = []
        for numero, paginas in cedulas_pages.items():
            cedulas_found.append({
                "number": numero,
                "pagPdf": sorted(paginas)  # Ordenar páginas
            })

        return cedulas_found
