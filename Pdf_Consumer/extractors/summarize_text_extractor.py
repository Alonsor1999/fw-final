"""
Extractor de resumen de texto usando técnicas básicas de NLP
"""
import re
import json
import unicodedata
from typing import List, Dict


class SummarizeTextExtractor:
    """
    Extrae secciones 'importantes' de un texto (p. ej., de un PDF ya extraído)
    y genera resúmenes por sección.

    Uso:
      ste = SummarizeTextExtractor()
      payload = ste.process(raw_text, top_k=8, sentences=3)
      json_str = ste.to_json(payload)
    """

    # --- encabezados robustos (romanos/números y puntuación opcional) ---
    HEADER_TOKENS = [
        r"HECHOS",
        r"ANTECEDENTES",
        r"CAUSANTE\s+DEL\s+AGRAVIO(?:\s+O\s+AMENAZA)?",
        r"NORMAS\s+VIOLADAS",
        r"FUNDAMENTOS\s+DE\s+HECHOS?\s+Y\s+CONCEPTO\s+DE\s+VIOLACI[ÓO]N",
        r"FUNDAMENTOS\s+CONSTITUCIONALES\s+Y\s+LEGALES",
        r"FUNDAMENTOS\s+JURISPRUDENCIALES",
        r"PETICI[ÓO]N(?:ES)?",
        r"PRUEBAS\s+Y\s+ANEXOS",
        r"JURAMENTO",
        r"NOTIFICACIONES?",
    ]
    HEADER_RE = re.compile(
        r"^\s*(?:[IVXLCDM]+\.?|[0-9]+[.)])?\s*(%s)\s*[:.\-]?\s*$" % "|".join(HEADER_TOKENS),
        re.IGNORECASE | re.MULTILINE
    )

    def __init__(self):
        # Ajustes futuros (pesos, flags) podrían colgarse aquí
        pass

    # ---------- API PÚBLICA ----------
    def process(self, raw_text: str, top_k: int = 8, sentences: int = 3) -> List[Dict[str, str]]:
        """
        Devuelve lista de dicts: [{"matter": str, "resume": str}, ...]
        - top_k: máximo de secciones a devolver.
        - sentences: nº de frases por resumen.
        """
        text = self._normalize(raw_text)
        sections = self._split_sections(text)

        scored = []
        for (title, content) in sections:
            content = content.strip()
            if len(content) < 80:
                continue
            s = self._score(title, content)
            scored.append((s, title.strip().title(), content))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = scored[:top_k]

        payload = []
        for _, matter, content in selected:
            resume = self._summarize_section(matter, content, sentences=sentences)
            payload.append({"matter": matter, "resume": resume})
        return payload

    def to_json(self, payload: List[Dict[str, str]]) -> str:
        """Serializa el resultado a JSON sin romper comillas ni caracteres especiales."""
        return json.dumps(payload, ensure_ascii=False)

    # ---------- INTERNOS ----------
    def _normalize(self, s: str) -> str:
        s = unicodedata.normalize("NFKC", s)
        for bad in ("\u00ad", "\u200b", "\u200c", "\u200d", "\ufeff"):
            s = s.replace(bad, "")
        s = re.sub(r"\u00A0", " ", s)
        s = re.sub(r"[ \t]+", " ", s)
        s = re.sub(r"\r", "", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()

    def _split_sections(self, text: str):
        sections, last_title, last_idx = [], "INICIAL", 0
        for m in self.HEADER_RE.finditer(text):
            if last_idx < m.start():
                sections.append((last_title, text[last_idx:m.start()].strip()))
            last_title = m.group(1).upper()
            last_idx = m.end()
        if last_idx < len(text):
            sections.append((last_title, text[last_idx:].strip()))
        # filtra vacíos
        return [(t, c) for t, c in sections if c.strip()]

    def _sents(self, text: str):
        # tokenizador simple con algunas abreviaturas
        abbr = r"(Sr|Sra|Dr|Dra|No|Art|Arts|p\.ej|ej)\."
        text = re.sub(rf"\b{abbr}", lambda m: m.group(0).replace(".", "§"), text, flags=re.IGNORECASE)
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p.replace("§", ".").strip() for p in parts if p.strip()]

    def _score(self, title: str, content: str) -> float:
        s = 0.0
        if re.search(self.HEADER_RE, title):
            s += 2.5
        cues = ["hechos", "petición", "pretensiones", "fundamentos", "jurisprudenciales",
                "normas", "pruebas", "resuelve", "notificaci", "antecedentes"]
        s += sum(1 for c in cues if c in title.lower())

        for w in ["resolución", "pmt", "registro civil", "pensión", "defunción", "cedula", "cédula"]:
            if w in content.lower():
                s += 0.5

        L = len(content)
        s += 0.6 if 400 <= L <= 15000 else 0.2
        return s

    def _summarize_section(self, title: str, content: str, sentences: int = 3) -> str:
        sents = self._sents(content)
        if not sents:
            return content[:500]
        t = title.lower()

        def pick(keys, n):
            scored = []
            for s in sents:
                score = sum(1 for k in keys if re.search(k, s, re.IGNORECASE))
                if score:
                    score += max(0, 2.0 - len(s) / 180.0)  # favorece concisas
                    scored.append((score, s))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [s for _, s in scored[:n]]

        # Heurísticas por tipo de sección
        if "hecho" in t:
            keys = [r"\bfalleci", r"\bresoluci[óo]n", r"\bPMT\b", r"\bregistro civil\b",
                    r"\bcorrecci", r"\bcedul", r"\bdefunci", r"\b\d{4}\b"]
            chosen = pick(keys, sentences) or sents[:sentences]
            return " ".join(chosen)

        if "petici" in t or "pretension" in t:
            keys = [r"\bsolicit", r"\bord[ée]nese", r"\bproteg", r"\bcorrecci", r"\bPMT\b"]
            chosen = pick(keys, sentences) or sents[:sentences]
            return " ".join(chosen)

        if "normas" in t or "constitucionales" in t or "legales" in t:
            refs = re.findall(
                r"(Artículo[s]?\s+\d+|Decreto\s+\d+\/?\d*|Resoluci[óo]n\s+\d+|Pacto\s+Internacional.+?Pol[ií]ticos)",
                content, flags=re.IGNORECASE)
            ref_line = "; ".join(dict.fromkeys([r.strip() for r in refs]))[:300]
            return (ref_line or " ".join(sents[:sentences]))[:600]

        if "jurisprudenciales" in t:
            refs = re.findall(r"\bT[-\s]?\d{1,4}\/\d{2,4}", content)
            base = ("Citas: " + ", ".join(refs[:5]) + ". ") if refs else ""
            chosen = pick([r"\bcorrecci", r"\bescritura p", r"\bdecisi[óo]n judicial", r"\bestado civil"], sentences)
            return (base + " ".join(chosen or sents[:sentences]))[:800]

        if "causante" in t or "agravio" in t or "amenaza" in t:
            s = " ".join(sents[:2])
            s = re.sub(r"\S+@\S+", "[correo]", s)
            return s[:600]

        if "pruebas" in t or "anexos" in t:
            items = re.findall(r"^\s*(?:[\-\*]|\d+\.)\s*(.+)$", content, flags=re.MULTILINE)
            if not items:
                items = [s for s in sents if len(s) < 200][:sentences]
            return ("; ".join(items[:10]))[:800]

        if "juramento" in t or "notificaci" in t:
            return " ".join(sents[:min(sentences, 2)])[:500]

        # Genérico
        keywords = ["registro", "corrección", "cedula", "cédula", "defunción", "PMT", "resolución", "derechos",
                    "pensión"]
        scored = []
        for s in sents:
            sc = sum(1 for k in keywords if re.search(k, s, re.IGNORECASE)) + max(0, 1.5 - len(s) / 200.0)
            scored.append((sc, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = [s for _, s in scored[:sentences]] or sents[:sentences]
        return " ".join(chosen)

