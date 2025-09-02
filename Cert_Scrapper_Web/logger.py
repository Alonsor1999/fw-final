# logger_config.py
import logging
from logging.handlers import TimedRotatingFileHandler
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, ".", "logs")
LOG_DIR = os.path.abspath(LOG_DIR)
COMBINED_LOG_FILE = os.path.join(LOG_DIR, "WS_RNEC.log")

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

class LevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno == self.level

def setup_logger(name="app"):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # ✅ Handler combinado (todos los niveles)
        combined_handler = TimedRotatingFileHandler(
            filename=COMBINED_LOG_FILE,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        combined_handler.setFormatter(formatter)
        logger.addHandler(combined_handler)

        # ✅ Handlers separados por nivel
        for level_name, level_value in LOG_LEVELS.items():
            file_path = os.path.join(LOG_DIR, f"{level_name.lower()}.log")
            handler = TimedRotatingFileHandler(
                filename=file_path,
                when="midnight",
                interval=1,
                backupCount=7,
                encoding='utf-8'
            )
            handler.setLevel(level_value)
            handler.setFormatter(formatter)
            handler.addFilter(LevelFilter(level_value))
            logger.addHandler(handler)

        # ✅ Consola
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    return logger
