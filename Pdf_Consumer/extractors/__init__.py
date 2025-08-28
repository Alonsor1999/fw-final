# Configurar variables de entorno antes de cualquier importación
import os
os.environ.setdefault('TEST_MODE', 'true')
os.environ.setdefault('S3_BUCKET', 'test-bucket')

try:
    from .cedula_extractor import CedulaExtractor
    from .name_extractor import NameExtractor
except ImportError as e:
    print(f"Warning: Could not import basic extractors: {e}")
    CedulaExtractor = None
    NameExtractor = None

try:
    from .cedula_extractor_comprehend import CedulaExtractorComprehend
    from .name_extractor_comprehend import NameExtractorComprehend
    from .summarize_text_extractor_comprehend import SummarizeTextExtractorComprehend
except ImportError as e:
    print(f"Warning: Could not import Comprehend extractors: {e}")
    CedulaExtractorComprehend = None
    NameExtractorComprehend = None
    SummarizeTextExtractorComprehend = None

try:
    from .summarize_text_extractor import SummarizeTextExtractor
except ImportError as e:
    print(f"Warning: Could not import SummarizeTextExtractor: {e}")
    SummarizeTextExtractor = None

__all__ = [
    'CedulaExtractor',
    'NameExtractor',
    'CedulaExtractorComprehend',
    'NameExtractorComprehend',
    'SummarizeTextExtractorComprehend',
    'SummarizeTextExtractor'
]
