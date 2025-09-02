import os
from dotenv import load_dotenv
from logger import setup_logger

logger = setup_logger("config")
# Cargar variables desde archivo .env
load_dotenv()
logger.info("Archivo .env cargado correctamente")


# Variables requeridas
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")
TESSERACT_PATH = os.getenv("TESSERACT_PATH")
URL = os.getenv("URL")


# Variables opcionales con defaults seguros
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, ".", "downloads")
LOG_DIR = os.path.abspath(LOG_DIR)
DOWNLOAD_DIR = LOG_DIR #os.getenv("DOWNLOAD_DIR", ".\downloads")
CAPTCHA_SOLVER = os.getenv("CAPTCHA_SOLVER", "tesseract")
WAIT_TIMEOUT = int(os.getenv("WAIT_TIMEOUT", "10"))

logger.debug(f"DOWNLOAD_DIR: {DOWNLOAD_DIR}")
logger.debug(f"CAPTCHA_SOLVER: {CAPTCHA_SOLVER}")
logger.debug(f"TESSERACT_PATH: {TESSERACT_PATH}")
logger.debug(f"URL: {URL}")
logger.debug(f"WAIT_TIMEOUT: {WAIT_TIMEOUT}")

# Validación obligatoria
missing = []
if not CAPTCHA_API_KEY:
    missing.append("CAPTCHA_API_KEY")
if not TESSERACT_PATH:
    missing.append("TESSERACT_PATH")
if not URL:
    missing.append("URL")

if missing:
    logger.error(f"Variables faltantes: {missing}")
    raise EnvironmentError(f"❌ Las siguientes variables de entorno son obligatorias pero no están definidas: {', '.join(missing)}")

logger.info("Variables de entorno cargadas exitosamente.")