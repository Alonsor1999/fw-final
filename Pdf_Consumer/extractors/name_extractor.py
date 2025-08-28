import re
import unicodedata
from typing import List, Optional, Dict, Any, Tuple

from config.constants import (
    CONNECTORS, INSTITUTION_NOISE, DISQUALIFY_TERMS, NON_NAME_COMMON,
    BLACKLIST_PHRASES, BLACKLIST_REGEXES, BLACKLIST_TOKENS,
    RE_FIELD_LINE, RE_NAME_TOKENS, RE_CONTRA, RE_A_NOMBRE, RE_SENOR,
    RE_SLP, RE_SIG_PERSONAS, RE_NOMBRE_DEL_SENOR, RE_ACCIONANTE,
    RE_TUTELA_PROMOVIDA, RE_CONTRA_HEREDEROS, RE_MAYOR_IDENT,
    PRE_CONTEXT_BLOCK, PRE_CONTEXT_AUTH, RE_NUM_LINE, RE_UPPER_TOKEN,
    RE_GENERIC
)
from processors.text_utils import normalize_text

class NameExtractor:
    """
    Encapsula la lógica para extraer nombres de personas de un texto.
    """

    def _norm_phrase(self, s: str) -> str:
        s = "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))
        s = s.lower()
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _contains_blacklisted_phrase(self, cand: str) -> bool:
        n = self._norm_phrase(cand)
        if n in BLACKLIST_PHRASES:
            return True
        return any(rx.search(cand) for rx in BLACKLIST_REGEXES)

    def smart_title(self, name: str) -> str:
        parts = re.split(r"(\s+)", (name or "").strip().lower())
        def fix(w: str) -> str:
            return w if w in CONNECTORS else w.capitalize()
        return "".join(fix(p) if p.strip() else p for p in parts)

    def clean_name_frag(self, s: str) -> str:
        s = re.sub(r"[\,;:]+", " ", s or "")
        s = re.sub(r"\s{2,}", " ", s)
        s = re.sub(r"\(\s*q\.?\s*e\.?\s*p\.?\s*d\.?\s*\)", "", s, flags=re.IGNORECASE)
        return s.strip(" .,'``´-").strip()

    def plausible_person(self, name: str) -> bool:
        toks = [t for t in name.split() if re.fullmatch(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü'``´\\-]{2,}", t)]
        if len(toks) < 2:
            return False
        if toks[0].lower() in CONNECTORS or toks[-1].lower() in CONNECTORS:
            return False
        uppers = {t.upper() for t in toks}
        if (uppers & INSTITUTION_NOISE) or (uppers & DISQUALIFY_TERMS):
            return False
        return True

    def _tokens_from_value(self, s: str) -> List[str]:
        s = (s or "").replace("\u00A0"," ").replace("\u200B","").strip()
        toks = RE_NAME_TOKENS.findall(s)
        return [t for t in toks if t.upper() not in {"NINGUNA","NINGUNO"}]

    def _extract_by_field_lines_robusto(self, text: str) -> List[str]:
        lines = text.splitlines()
        out = []
        current = {"Primer Apellido": "", "Segundo Apellido": "", "Primer Nombre": "", "Segundo Nombre": ""}

        def flush_current() -> str:
            n1 = current["Primer Nombre"].strip()
            n2 = current["Segundo Nombre"].strip()
            a1 = current["Primer Apellido"].strip()
            a2 = current["Segundo Apellido"].strip()
            parts = [n1, n2, a1, a2]
            full = " ".join(p for p in parts if p)
            return self.smart_title(re.sub(r"\s{2,}"," ", full).strip()) if full else ""

        i = 0
        while i < len(lines):
            m = RE_FIELD_LINE.match(lines[i])
            if m:
                pos  = f"{m.group(1).capitalize()} {m.group(2).capitalize()}"
                rawv = (m.group(3) or "").strip()

                toks = self._tokens_from_value(rawv)
                if not toks and i+1 < len(lines):
                    lookahead = lines[i+1].strip()
                    if not RE_FIELD_LINE.match(lookahead):
                        toks = self._tokens_from_value(lookahead)
                        if toks:
                            i += 1

                val = " ".join(toks)
                current[pos] = self.smart_title(val) if val else ""

                if i+1 < len(lines) and RE_FIELD_LINE.match(lines[i+1]):
                    nm = flush_current()
                    if nm:
                        out.append(nm)
                    current = {"Primer Apellido": "", "Segundo Apellido": "", "Primer Nombre": "", "Segundo Nombre": ""}
            i += 1

        nm = flush_current()
        if nm:
            out.append(nm)

        seen, clean = set(), []
        for n in out:
            k = n.lower()
            if n and k not in seen and len(n.split()) >= 2:
                seen.add(k); clean.append(n)
        return clean

    def _is_authority_context(self, text: str, start_idx: int) -> bool:
        pre = text[max(0, start_idx-100):start_idx]
        return PRE_CONTEXT_AUTH.search(pre) is not None

    def _extract_blocks_after_numbers(self, text: str, window_lines: int = 8) -> List[str]:
        lines = text.splitlines()
        idxs = [i for i, ln in enumerate(lines) if RE_NUM_LINE.search(ln)]
        out = []
        for i in idxs:
            block = []
            for j in range(i+1, min(i+1+window_lines, len(lines))):
                tok = re.sub(r"[:;,\''`´.]+$", "", lines[j].strip().upper())
                if not tok:
                    continue
                if RE_NUM_LINE.search(tok):
                    break
                if RE_UPPER_TOKEN.match(tok) and tok not in INSTITUTION_NOISE and tok not in {"NINGUNA","NINGUNO"}:
                    block.append(tok)
            if 3 <= len(block) <= 6:
                name1 = " ".join(block)
                half  = len(block) // 2
                name2 = " ".join(block[half:] + block[:half])
                for nm in (name1, name2):
                    nm = self.smart_title(self.clean_name_frag(nm))
                    if self.plausible_person(nm):
                        out.append(nm)
        return out

    def _extract_generic_anywhere(self, text: str) -> List[str]:
        out = []
        for m in RE_GENERIC.finditer(text):
            cand = self.clean_name_frag(m.group(0))
            tokens = [t for t in cand.split() if t.lower() not in CONNECTORS]
            if len(tokens) < 2 or len(tokens) > 6:
                continue

            start = m.start()
            pre = text[max(0, start-100):start]
            if PRE_CONTEXT_BLOCK.search(pre) or PRE_CONTEXT_AUTH.search(pre):
                continue

            uppers = {t.upper().strip(".,;:") for t in tokens}
            if uppers & (INSTITUTION_NOISE | DISQUALIFY_TERMS | NON_NAME_COMMON):
                continue

            if self._contains_blacklisted_phrase(cand):
                continue

            if any(tok in BLACKLIST_TOKENS for tok in uppers):
                continue

            if any(re.search(r"(?i)(ando|endo)$", t) for t in tokens):
                continue

            nm = self.smart_title(cand)
            if self.plausible_person(nm):
                out.append(nm)
        return out

    def _extract_by_phrase_patterns(self, text: str) -> List[str]:
        out = []
        patterns = (
            RE_MAYOR_IDENT, RE_TUTELA_PROMOVIDA, RE_CONTRA_HEREDEROS,
            RE_ACCIONANTE, RE_A_NOMBRE, RE_NOMBRE_DEL_SENOR, RE_CONTRA,
            RE_SENOR, RE_SLP, RE_SIG_PERSONAS
        )
        for rx in patterns:
            for m in rx.finditer(text):
                if self._is_authority_context(text, m.start()):
                    continue
                cand = self.clean_name_frag(m.group("name"))
                if self.plausible_person(cand):
                    out.append(cand)
        return out

    def extract_all_names(self, raw_text: str) -> str:
        """
        Devuelve TODOS los nombres encontrados, sin duplicados y en orden de aparición,
        como un string separado por comas.
        """
        t = normalize_text(raw_text or "")
        seen = set()
        found = []  # (pos, nombre)

        def _push(pos: int, cand: str):
            nm = self.smart_title(self.clean_name_frag(cand))
            if self.plausible_person(nm):
                key = re.sub(r"\s+", " ", nm.lower()).strip()
                if key and key not in seen:
                    seen.add(key)
                    found.append((pos, nm))

        # 1) Patrones con nombre "nombrado"
        patterns_named = (
            RE_MAYOR_IDENT, RE_TUTELA_PROMOVIDA, RE_CONTRA_HEREDEROS,
            RE_ACCIONANTE, RE_A_NOMBRE, RE_NOMBRE_DEL_SENOR, RE_CONTRA,
            RE_SENOR, RE_SLP, RE_SIG_PERSONAS
        )
        for rx in patterns_named:
            for m in rx.finditer(t):
                if self._is_authority_context(t, m.start()):
                    continue
                _push(m.start(), m.group("name"))

        # 2) Fallback genérico
        for mg in RE_GENERIC.finditer(t):
            start = mg.start()
            pre = t[max(0, start-100):start]
            if PRE_CONTEXT_BLOCK.search(pre) or PRE_CONTEXT_AUTH.search(pre):
                continue
            raw = self.clean_name_frag(mg.group(0))
            toks = [tok for tok in raw.split() if tok.lower() not in CONNECTORS]
            if not (2 <= len(toks) <= 6):
                continue

            uppers = {tok.upper().strip(".,;:") for tok in toks}
            if uppers & (INSTITUTION_NOISE | DISQUALIFY_TERMS | NON_NAME_COMMON):
                continue
            
            if self._contains_blacklisted_phrase(raw):
                continue
            if any(tok in BLACKLIST_TOKENS for tok in uppers):
                continue
            if any(re.search(r"(?i)(ando|endo)$", tok) for tok in toks):
                continue

            _push(start, raw)

        # 3) Campos "Primer/Segundo …"
        for idx, nm in enumerate(self._extract_by_field_lines_robusto(t)):
            pos = t.lower().find(nm.lower())
            if pos < 0:
                pos = 10**9 + idx
            _push(pos, nm)

        # 4) Bloques después de números
        for idx, nm in enumerate(self._extract_blocks_after_numbers(t)):
            pos = t.lower().find(nm.lower())
            if pos < 0:
                pos = 2*(10**9) + idx
            _push(pos, nm)

        found.sort(key=lambda x: x[0])
        return ", ".join(nm for _, nm in found)

    def extract_names_with_pages(self, pages_text: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        """
        Extrae nombres página por página y retorna un array JSON
        con la estructura: [{"name": "", "pagPdf": []}]
        """
        if not pages_text:
            return []

        names_pages = {}  # {nombre: [paginas]}

        for page_text, page_num in pages_text:
            if not page_text.strip():
                continue

            t = normalize_text(page_text)
            seen_on_page = set()

            def _add_name(cand: str):
                nm = self.smart_title(self.clean_name_frag(cand))
                if self.plausible_person(nm):
                    key = re.sub(r"\s+", " ", nm.lower()).strip()
                    if key and key not in seen_on_page:
                        seen_on_page.add(key)
                        if nm not in names_pages:
                            names_pages[nm] = []
                        if page_num not in names_pages[nm]:
                            names_pages[nm].append(page_num)

            # 1) Patrones con nombre "nombrado"
            patterns_named = (
                RE_MAYOR_IDENT, RE_TUTELA_PROMOVIDA, RE_CONTRA_HEREDEROS,
                RE_ACCIONANTE, RE_A_NOMBRE, RE_NOMBRE_DEL_SENOR, RE_CONTRA,
                RE_SENOR, RE_SLP, RE_SIG_PERSONAS
            )
            for rx in patterns_named:
                for m in rx.finditer(t):
                    if self._is_authority_context(t, m.start()):
                        continue
                    _add_name(m.group("name"))

            # 2) Fallback genérico
            for mg in RE_GENERIC.finditer(t):
                start = mg.start()
                pre = t[max(0, start-100):start]
                if PRE_CONTEXT_BLOCK.search(pre) or PRE_CONTEXT_AUTH.search(pre):
                    continue
                raw = self.clean_name_frag(mg.group(0))
                toks = [tok for tok in raw.split() if tok.lower() not in CONNECTORS]
                if not (2 <= len(toks) <= 6):
                    continue

                uppers = {tok.upper().strip(".,;:") for tok in toks}
                if uppers & (INSTITUTION_NOISE | DISQUALIFY_TERMS | NON_NAME_COMMON):
                    continue

                if self._contains_blacklisted_phrase(raw):
                    continue
                if any(tok in BLACKLIST_TOKENS for tok in uppers):
                    continue
                if any(re.search(r"(?i)(ando|endo)$", tok) for tok in toks):
                    continue

                _add_name(raw)

            # 3) Campos "Primer/Segundo …"
            for nm in self._extract_by_field_lines_robusto(t):
                _add_name(nm)

            # 4) Bloques después de números
            for nm in self._extract_blocks_after_numbers(t):
                _add_name(nm)

        # Convertir a la estructura final con páginas ordenadas
        names_found = []
        for nombre, paginas in names_pages.items():
            names_found.append({
                "name": nombre,
                "pagPdf": sorted(paginas)  # Ordenar páginas
            })

        return names_found
