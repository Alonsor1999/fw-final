import boto3
import os
import re
import time
from typing import List, Tuple
from botocore.exceptions import ClientError


class SummarizeTextExtractorComprehend:
    """
    Una clase para resumir texto usando AWS Comprehend.
    """
    MAX_BYTES = 4800  # Margen de seguridad bajo el límite de 5000 bytes de Comprehend
    MIN_SCORE = 0.8   # Umbral para frases clave

    def __init__(self, region: str = None, max_frases: int = 5, debug: bool = True):
        """
        Inicializa el resumidor.
        - region: Región de AWS para el cliente de Comprehend.
        - max_frases: Número máximo de frases en el resumen final.
        - debug: Imprime detalles de error.
        """
        self.region = region or os.getenv("AWS_REGION") or "us-east-1"
        self.comprehend = boto3.client("comprehend", region_name=self.region)
        self.max_frases = max_frases
        self.debug = debug

    def _normalize_whitespace(self, s: str) -> str:
        """Elimina caracteres invisibles problemáticos y compacta los espacios en blanco."""
        s = s.replace("\u00AD", "").replace("\u200B", "").replace("\u200C", "").replace("\u200D", "").replace("\uFEFF", "")
        s = re.sub(r"[ \t]+", " ", s)
        s = re.sub(r"\\s*\\n\\s*", "\\n", s)
        return s.strip()

    def _split_by_bytes(self, text: str) -> List[str]:
        """
        Divide el texto en fragmentos, respetando un límite de bytes.
        Intenta dividir primero por oraciones, luego por bytes si una oración es demasiado larga.
        """
        sentences = re.split(r"(?<=[\.\!\?\\n])\\s+", text)
        chunks: List[str] = []
        current = ""

        def byte_len(s: str) -> int:
            return len(s.encode("utf-8"))

        for sent in sentences:
            if byte_len(current) + byte_len(sent) + 1 > self.MAX_BYTES:
                if current:
                    chunks.append(current.strip())
                    current = ""

                while byte_len(sent) > self.MAX_BYTES:
                    b = sent.encode("utf-8")
                    piece = b[:self.MAX_BYTES]
                    # Evita cortar a mitad de un carácter multibyte
                    piece_str = piece.decode("utf-8", errors="ignore")
                    chunks.append(piece_str.strip())
                    sent = b[self.MAX_BYTES:].decode("utf-8", errors="ignore")

            current += (" " if current else "") + sent

        if current.strip():
            chunks.append(current.strip())

        return [c for c in chunks if c]

    def _detect_language(self, text: str, default_lang: str = "es") -> str:
        """Detecta el idioma dominante en el texto."""
        try:
            resp = self.comprehend.detect_dominant_language(Text=text[:4500])
            langs = sorted(resp.get("Languages", []), key=lambda x: x.get("Score", 0), reverse=True)
            if langs:
                return langs[0].get("LanguageCode", default_lang)
        except ClientError:
            pass  # Vuelve al idioma predeterminado en caso de error
        return default_lang

    def _call_with_retries(self, fn, **kwargs):
        """Llama a una función con reintentos simples en excepciones de throttling/servicio."""
        delays = [0.5, 1.0, 2.0]
        for d in delays + [None]:
            try:
                return fn(**kwargs)
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "Unknown")
                if code in ("ThrottlingException", "TooManyRequestsException", "ServiceUnavailableException") and d is not None:
                    time.sleep(d)
                    continue
                raise

    def summarize(self, texto: str, idioma: str = None) -> str:
        """
        Resume un texto usando AWS Comprehend (detect_key_phrases).
        - texto: El contenido a resumir.
        - idioma: 'es' o 'en'; si es None, se autodetecta.
        """
        if not texto or not texto.strip():
            return ""

        texto_normalizado = self._normalize_whitespace(texto)
        chunks = self._split_by_bytes(texto_normalizado)
        if not chunks:
            return ""

        lang = idioma or self._detect_language(chunks[0], default_lang="es")

        key_phrases: List[Tuple[str, float]] = []

        for idx, chunk in enumerate(chunks, start=1):
            try:
                resp = self._call_with_retries(
                    self.comprehend.detect_key_phrases,
                    Text=chunk,
                    LanguageCode=lang
                )
            except ClientError as e:
                if self.debug:
                    err = e.response.get("Error", {})
                    print(f"[Comprehend ERROR] chunk={idx}/{len(chunks)} Code={err.get('Code')} Message={err.get('Message')}")
                continue

            for kp in resp.get("KeyPhrases", []):
                frase_texto = kp.get("Text", "").strip()
                score = kp.get("Score", 0.0)
                if frase_texto and score >= self.MIN_SCORE:
                    key_phrases.append((frase_texto, score))

        if not key_phrases:
            lineas = [ln.strip() for ln in texto_normalizado.splitlines() if ln.strip()]
            return " ".join(lineas[:3])[:500]

        # Ordenar por puntuación (desc) y luego por aparición (estable)
        seen = set()
        frases_ordenadas: List[str] = []
        for frase_texto, score in sorted(key_phrases, key=lambda x: x[1], reverse=True):
            tnorm = frase_texto.lower()
            if tnorm not in seen:
                seen.add(tnorm)
                frases_ordenadas.append(frase_texto)

        resumen = ". ".join(frases_ordenadas[:self.max_frases])
        return resumen
