import re
import unicodedata
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
from typing import List

from config.constants import SUMMARY_SENT_SPLIT_RE, SUMMARY_WORD_RE

class SimpleTokenizer:
    """Clase interna para el tokenizador de sumy."""
    def to_sentences(self, text: str) -> List[str]:
        text = (text or "").replace("\n", " ").strip()
        if not text:
            return []
        sents = SUMMARY_SENT_SPLIT_RE.split(text) if any(p in text for p in ".!?") else text.split(".")
        return [s.strip() for s in sents if s.strip()]

    def to_words(self, sentence: str) -> List[str]:
        return SUMMARY_WORD_RE.findall(sentence or "")

def normalize_text(t: str) -> str:
    """Limpia y normaliza el texto extraído de los PDFs."""
    t = (t or "")
    t = t.replace("\r", "\n")
    t = t.replace("ﬁ", "fi").replace("ﬂ", "fl")
    t = t.replace("\u00A0", " ").replace("\u200B", "")
    t = t.replace("®", " ")
    t = t.translate(str.maketrans({"«": '"', "»": '"', "“": '"', "”": '"', "‘": "'", "’": "'"}))
    
    ocr_fixes = {
        r"\bSefior(?:a)?\b": "señor",
        r"\bSenor(?:a)?\b": "señor",
        r"\bSeñora\b": "señora",
        r"\bSefior\.\b": "señor.",
        r"\bSefiora\.\b": "señora.",
    }
    for pat, rep in ocr_fixes.items():
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)
    
    t = re.sub(r"-\s*\n\s*", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def summarize_text(text: str, sentence_count: int = 5) -> str:
    """Genera un resumen extractivo de un texto largo."""
    text = (text or "").strip()
    if not text:
        return ""
    
    parser = PlaintextParser.from_string(text, SimpleTokenizer())
    summarizer = LsaSummarizer()
    
    try:
        summary = list(summarizer(parser.document, sentence_count))
    except Exception:
        summary = []
        
    if not summary:
        sents = SimpleTokenizer().to_sentences(text)[:sentence_count]
        return " ".join(sents) if sents else text[:800]
        
    return " ".join(str(s) for s in summary)

def sanitize_for_json(text: str | None) -> str:
    """Prepara un string para que sea seguro para serializar a JSON."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\x00", "")
    text = text.encode("utf-8", "replace").decode("utf-8")
    return text
