import re
import unicodedata
from typing import List, Tuple, Dict, Any
import boto3

class CedulaExtractorComprehend:
    # --- Config ---
    _MAX_CHARS = 4500  # margen seguro para detect_pii_entities
    CTX_KEYWORDS = (
        "cedula", "cédula", "ciudadania", "ciudadanía",
        "c.c", "cc", "número", "numero", "no", "nº", "n°"
    )

    # Regex: 6–10 dígitos, con o sin separadores (puntos o espacios)
    # Evita capturar dentro de cifras más largas
    RE_CEDULA = re.compile(r"(?<!\d)(?:\d{1,3}(?:[.\s]\d{3}){1,3}|\d{6,10})(?!\d)")

    @staticmethod
    def _normalize(s: str) -> str:
        # quita diacríticos y caracteres invisibles/comunes en OCR
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        for bad in ("\u00AD", "\u200B", "\u200C", "\u200D", "\uFEFF"):
            s = s.replace(bad, "")
        return s

    @staticmethod
    def _chunk_text(s: str, max_chars: int = _MAX_CHARS) -> List[Tuple[str, int]]:
        """Devuelve [(chunk, start_index)] respetando finales de oración/línea."""
        if len(s) <= max_chars:
            return [(s, 0)]
        parts = re.split(r"(?<=[\.\?\!\n])\s+", s)
        chunks, buf, cur = [], [], 0
        acc = 0
        for p in parts:
            if cur + len(p) + 1 > max_chars and buf:
                chunk = " ".join(buf).strip()
                start = acc - len(chunk)
                chunks.append((chunk, start))
                buf, cur = [p], len(p)
            else:
                buf.append(p); cur += len(p) + 1
            acc += len(p) + 1
        if buf:
            chunk = " ".join(buf).strip()
            start = acc - len(chunk)
            chunks.append((chunk, start))
        return chunks

    @classmethod
    def _regex_candidates(cls, text_norm: str) -> List[str]:
        """Extrae por regex y filtra por longitud y contexto cercano (palabras clave)."""
        found = []
        for m in cls.RE_CEDULA.finditer(text_norm):
            raw = m.group(0)
            digits = re.sub(r"[^\d]", "", raw)
            if not (6 <= len(digits) <= 10):
                continue
            # filtro por contexto: busca keywords 40 chars antes
            start = max(0, m.start() - 40)
            ctx = text_norm[start:m.start()].lower()
            if any(k in ctx for k in cls.CTX_KEYWORDS):
                found.append(digits)
            else:
                # si no hay contexto, igual lo aceptamos pero con menor prioridad
                # para no perder casos como "Identificado con 4.879.385"
                found.append(digits)
        # mantiene orden de aparición y quita duplicados
        seen, ordered = set(), []
        for d in found:
            if d not in seen:
                seen.add(d); ordered.append(d)
        return ordered

    def extract_cedulas(self, texto: str, region_name: str = "us-east-1") -> str:
        """
        Devuelve cédulas colombianas como string separado por coma. Si no hay: "".
        1) Intenta AWS Comprehend (detect_pii_entities) con troceo.
        2) Si no hay resultados o falla, usa regex robusto.
        """
        if not texto or not texto.strip():
            return ""

        text_norm = self._normalize(texto)

        # --- 1) Intento con Comprehend ---
        cedulas = []
        used_comprehend = False
        if boto3 is not None:
            try:
                client = boto3.client("comprehend", region_name=region_name)
                for chunk, base in self._chunk_text(text_norm):
                    if not chunk:
                        continue
                    resp = client.detect_pii_entities(Text=chunk, LanguageCode="es")
                    for ent in resp.get("Entities", []):
                        etype = ent.get("Type", "")
                        if etype not in ("ID_NUMBER", "NATIONAL_ID"):
                            continue
                        # Recorta el fragmento y busca patrón de cédula dentro
                        b = int(ent.get("BeginOffset", 0))
                        e = int(ent.get("EndOffset", 0))
                        frag = chunk[b:e]
                        # Escaneo por regex dentro del fragmento y también ventana extendida
                        around_start = max(0, b - 20)
                        around_end = min(len(chunk), e + 20)
                        for candidate in self.RE_CEDULA.findall(chunk[around_start:around_end] or frag):
                            digits = re.sub(r"[^\d]", "", candidate)
                            if 6 <= len(digits) <= 10:
                                cedulas.append(digits)
                used_comprehend = True
            except Exception as e:
                # Si hay permisos/límites/otros errores, caemos a regex puro
                pass

        # --- 2) Fallback o refuerzo con regex puro ---
        # Si Comprehend no encontró nada, o para añadir las que se le escaparon.
        if not cedulas:
            cedulas = self._regex_candidates(text_norm)
        else:
            extra = self._regex_candidates(text_norm)
            cedulas = list(dict.fromkeys(cedulas + extra))  # merge manteniendo orden

        return ", ".join(cedulas) if cedulas else ""

    def extract_cedulas_with_pages(self, pages_text: List[Tuple[str, int]], region_name: str = "us-east-1") -> List[Dict[str, Any]]:
        """
        Extrae números de cédula página por página y retorna un array JSON
        con la estructura: [{"number": "", "pagPdf": []}]
        """
        if not pages_text:
            return []

        cedulas_pages = {}  # {numero_cedula: [paginas]}

        for page_text, page_num in pages_text:
            if not page_text or not page_text.strip():
                continue

            text_norm = self._normalize(page_text)
            page_cedulas = []

            # --- 1) Intento con Comprehend ---
            if boto3 is not None:
                try:
                    client = boto3.client("comprehend", region_name=region_name)
                    for chunk, base in self._chunk_text(text_norm):
                        if not chunk:
                            continue
                        resp = client.detect_pii_entities(Text=chunk, LanguageCode="es")
                        for ent in resp.get("Entities", []):
                            etype = ent.get("Type", "")
                            if etype not in ("ID_NUMBER", "NATIONAL_ID"):
                                continue
                            # Recorta el fragmento y busca patrón de cédula dentro
                            b = int(ent.get("BeginOffset", 0))
                            e = int(ent.get("EndOffset", 0))
                            frag = chunk[b:e]
                            # Escaneo por regex dentro del fragmento y también ventana extendida
                            around_start = max(0, b - 20)
                            around_end = min(len(chunk), e + 20)
                            for candidate in self.RE_CEDULA.findall(chunk[around_start:around_end] or frag):
                                digits = re.sub(r"[^\d]", "", candidate)
                                if 6 <= len(digits) <= 10:
                                    page_cedulas.append(digits)
                except Exception as e:
                    # Si hay permisos/límites/otros errores, caemos a regex puro
                    pass

            # --- 2) Fallback o refuerzo con regex puro ---
            if not page_cedulas:
                page_cedulas = self._regex_candidates(text_norm)
            else:
                extra = self._regex_candidates(text_norm)
                page_cedulas = list(dict.fromkeys(page_cedulas + extra))  # merge manteniendo orden

            # Agregar cédulas encontradas en esta página al diccionario
            for cedula in page_cedulas:
                if cedula not in cedulas_pages:
                    cedulas_pages[cedula] = []
                if page_num not in cedulas_pages[cedula]:
                    cedulas_pages[cedula].append(page_num)

        # Convertir a la estructura final con páginas ordenadas
        cedulas_found = []
        for numero, paginas in cedulas_pages.items():
            cedulas_found.append({
                "number": numero,
                "pagPdf": sorted(paginas)  # Ordenar páginas
            })

        return cedulas_found
