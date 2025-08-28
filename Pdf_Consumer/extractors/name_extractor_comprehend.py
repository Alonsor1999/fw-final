import boto3
import os
import re
import unicodedata
from typing import Iterable, Optional, List, Dict, Any, Tuple

from config.constants import (
    ALLOWED_PARTICLES,
    CHUNK_SIZE,
    DEMONYM_STOPWORDS,
    FRASES_PROHIBIDAS,
    HEADERS_BLACKLIST,
    LANG,
    PHRASES_BLACKLIST,
    SOFT_SPLIT,
    THRESHOLD,
    TITLE_PAT,
    UPPER_PAT,
)


class NameExtractorComprehend:
    def __init__(self):
        self.client = boto3.client("comprehend", region_name=os.getenv("AWS_REGION", "us-east-1"))

    def _chunk_text(self, text: str, size: int = CHUNK_SIZE) -> Iterable[str]:
        text = text.strip()
        if len(text) <= size:
            yield text
            return
        parts = re.split(SOFT_SPLIT, text)
        buf, curr_len = [], 0
        for p in parts:
            if curr_len + len(p) + 1 <= size:
                buf.append(p)
                curr_len += len(p) + 1
            else:
                yield " ".join(buf).strip()
                buf, curr_len = [p], len(p)
        if buf:
            yield " ".join(buf).strip()

    def _sanitize(self, s: str) -> str:
        s = s.replace("\xa0", " ")
        s = re.sub(r"[\u200B\u200C\u200D\uFEFF]", "", s)
        s = re.sub(r"\s+", " ", s)
        s = s.strip().strip(",;:()[]{}<>""''\"'|/\\")
        s = re.sub(r"\s{2,}", " ", s)
        return s

    def _valid_token(self, tok: str) -> bool:
        if not tok:
            return False
        if any(ch.isdigit() for ch in tok):
            return False
        if len(tok) <= 2 and tok.lower() not in ALLOWED_PARTICLES:
            return False
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü][A-Za-zÁÉÍÓÚÑÜáéíóúñü''\-\.]*", tok):
            return False
        return True

    def _looks_like_person(self, name: str) -> bool:
        if not name:
            return False
        name = self._sanitize(name)
        low = name.lower()
        if any(p in low for p in PHRASES_BLACKLIST):
            return False

        tokens = re.split(r"\s+", name)
        if len(tokens) < 2:
            return False
        if tokens[0].upper() in HEADERS_BLACKLIST:
            return False
        if any(t.lower() in DEMONYM_STOPWORDS for t in tokens):
            return False

        if any(not self._valid_token(t) for t in tokens):
            return False

        if not any(any(ch.isupper() for ch in tok) for tok in tokens):
            return False
        return True

    def _context_forbidden(self, prefix: str) -> bool:
        low = prefix.lower()
        return any(frase in low for frase in FRASES_PROHIBIDAS)

    def _grab_field(self, text: str, label: str) -> Optional[str]:
        pattern = rf"{label}\s*:?\s*(?:\n|\r\n)?\s*([^\n\r]+)"
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if not m:
            return None
        val = self._sanitize(m.group(1))
        if not val or val.lower() in {"", "ninguna", "none", "-"}:
            return None
        return val

    def _extract_labeled_fullname(self, text: str) -> Optional[str]:
        pa = self._grab_field(text, r"Primer\s+Apellido")
        sa = self._grab_field(text, r"Segundo\s+Apellido")
        pn = self._grab_field(text, r"Primer\s+Nombre")
        sn = self._grab_field(text, r"Segundo\s+Nombre")

        if pn and (pa or sa):
            parts = [pn]
            if sn:
                parts.append(sn)
            if sa:
                parts.append(sa)
            if pa:
                parts.append(pa)
            fullname = self._sanitize(" ".join(parts))
            return fullname if self._looks_like_person(fullname) else None
        return None

    def _regex_fallback(self, text: str) -> Optional[str]:
        patron = re.compile(r"\b([A-ZÁÉÍÓÚÑÜ]{2,}(?:\s+[A-ZÁÉÍÓÚÑÜ]{2,}){1,5})\b")
        for m in patron.finditer(text):
            cand = self._sanitize(m.group(1))
            if not self._looks_like_person(cand):
                continue
            ctx = text[max(0, m.start() - 80) : m.start()]
            if self._context_forbidden(ctx):
                continue
            return cand
        return None

    def find_nombre(self, text: str, use_comprehend: bool = True, use_regex_fallback: bool = True) -> Optional[str]:
        if not text or not text.strip():
            return None

        labeled = self._extract_labeled_fullname(text)
        if labeled:
            return labeled

        if use_comprehend:
            try:
                best, best_off = None, None
                for chunk in self._chunk_text(text):
                    resp = self.client.detect_entities(Text=chunk, LanguageCode=LANG)
                    for ent in resp.get("Entities", []):
                        if ent.get("Type") != "PERSON" or (ent.get("Score") or 0) < THRESHOLD:
                            continue
                        name = self._sanitize(ent.get("Text", ""))
                        if not self._looks_like_person(name):
                            continue
                        start = ent.get("BeginOffset", 0)
                        ctx = chunk[max(0, start - 80) : start]
                        if self._context_forbidden(ctx):
                            continue
                        if best_off is None or start < best_off:
                            best, best_off = name, start
                    if best:
                        break
                if best:
                    return best
            except Exception:
                pass

        if use_regex_fallback:
            return self._regex_fallback(text)

        return None

    def _norm_key(self, s: str) -> str:
        s = self._sanitize(s).lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = re.sub(r"[^a-z\s]", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    def _extract_people_from_fragment(self, s: str) -> list[str]:
        cands = []
        if not s:
            return cands
        for line in re.split(r"[\r\n]+", s):
            for pat in (UPPER_PAT, TITLE_PAT):
                for m in pat.finditer(line):
                    cand = self._sanitize(m.group(1))
                    if self._looks_like_person(cand):
                        cands.append(cand)
            cand_line = self._sanitize(line)
            if self._looks_like_person(cand_line):
                cands.append(cand_line)
        return cands

    def find_nombres(self, text: str, use_comprehend: bool = True, use_regex_fallback: bool = True) -> list[str]:
        if not text or not text.strip():
            return []

        resultados: list[str] = []
        vistos: set[str] = set()

        def _push(cand: str):
            cand = self._sanitize(cand)
            if not self._looks_like_person(cand):
                return
            key = self._norm_key(cand)
            if key in vistos:
                return
            vistos.add(key)
            resultados.append(cand)

        try:
            labeled = self._extract_labeled_fullname(text)
            if labeled:
                _push(labeled)
        except Exception:
            pass

        if use_comprehend:
            try:
                for chunk in self._chunk_text(text):
                    resp = self.client.detect_entities(Text=chunk, LanguageCode=LANG)
                    ents = resp.get("Entities", [])
                    ents.sort(key=lambda e: e.get("BeginOffset", 0))
                    for ent in ents:
                        if ent.get("Type") != "PERSON" or (ent.get("Score") or 0) < THRESHOLD:
                            continue
                        raw = ent.get("Text", "")
                        start = ent.get("BeginOffset", 0)
                        ctx = chunk[max(0, start - 80) : start]
                        if self._context_forbidden(ctx):
                            continue
                        for cand in self._extract_people_from_fragment(raw):
                            _push(cand)
            except Exception:
                pass

        if use_regex_fallback:
            for m in UPPER_PAT.finditer(text):
                span = m.group(1)
                ctx = text[max(0, m.start() - 80) : m.start()]
                if self._context_forbidden(ctx):
                    continue
                for cand in self._extract_people_from_fragment(span):
                    _push(cand)
            for m in TITLE_PAT.finditer(text):
                span = m.group(1)
                ctx = text[max(0, m.start() - 80) : m.start()]
                if self._context_forbidden(ctx):
                    continue
                for cand in self._extract_people_from_fragment(span):
                    _push(cand)

        return resultados

    def find_nombres_str(self, text: str, use_comprehend: bool = True, use_regex_fallback: bool = True) -> str:
        nombres = self.find_nombres(text, use_comprehend=use_comprehend, use_regex_fallback=use_regex_fallback)
        return ", ".join(nombres) if nombres else ""

    def extract_names_with_pages(self, pages_text: List[Tuple[str, int]], use_comprehend: bool = True, use_regex_fallback: bool = True) -> List[Dict[str, Any]]:
        """
        Extrae nombres página por página y retorna un array JSON
        con la estructura: [{"name": "", "pagPdf": []}]
        """
        if not pages_text:
            return []

        names_pages = {}  # {nombre: [paginas]}

        for page_text, page_num in pages_text:
            if not page_text or not page_text.strip():
                continue

            seen_on_page = set()

            def _add_name(cand: str):
                cand = self._sanitize(cand)
                if not self._looks_like_person(cand):
                    return
                key = self._norm_key(cand)
                if key and key not in seen_on_page:
                    seen_on_page.add(key)
                    if cand not in names_pages:
                        names_pages[cand] = []
                    if page_num not in names_pages[cand]:
                        names_pages[cand].append(page_num)

            # 1) Extraer nombres con campos etiquetados
            try:
                labeled = self._extract_labeled_fullname(page_text)
                if labeled:
                    _add_name(labeled)
            except Exception:
                pass

            # 2) Usar AWS Comprehend si está disponible
            if use_comprehend:
                try:
                    for chunk in self._chunk_text(page_text):
                        resp = self.client.detect_entities(Text=chunk, LanguageCode=LANG)
                        ents = resp.get("Entities", [])
                        ents.sort(key=lambda e: e.get("BeginOffset", 0))
                        for ent in ents:
                            if ent.get("Type") != "PERSON" or (ent.get("Score") or 0) < THRESHOLD:
                                continue
                            raw = ent.get("Text", "")
                            start = ent.get("BeginOffset", 0)
                            ctx = chunk[max(0, start - 80) : start]
                            if self._context_forbidden(ctx):
                                continue
                            for cand in self._extract_people_from_fragment(raw):
                                _add_name(cand)
                except Exception:
                    pass

            # 3) Fallback con regex si está habilitado
            if use_regex_fallback:
                for m in UPPER_PAT.finditer(page_text):
                    span = m.group(1)
                    ctx = page_text[max(0, m.start() - 80) : m.start()]
                    if self._context_forbidden(ctx):
                        continue
                    for cand in self._extract_people_from_fragment(span):
                        _add_name(cand)
                for m in TITLE_PAT.finditer(page_text):
                    span = m.group(1)
                    ctx = page_text[max(0, m.start() - 80) : m.start()]
                    if self._context_forbidden(ctx):
                        continue
                    for cand in self._extract_people_from_fragment(span):
                        _add_name(cand)

        # Convertir a la estructura final con páginas ordenadas
        names_found = []
        for nombre, paginas in names_pages.items():
            names_found.append({
                "name": nombre,
                "pagPdf": sorted(paginas)  # Ordenar páginas
            })

        return names_found
