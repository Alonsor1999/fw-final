from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from logger import setup_logger

logger = setup_logger("browser")

def get_driver(download_dir):
    try:
        logger.info(f"Inicializando navegador Chrome con directorio de descarga: {download_dir}")
        options = Options()
        ##options.add_argument('--headless')  # Descomenta si lo activas
        options.add_argument('--no-sandbox')
        logger.info(f"Enviando parametros de inicializacion al navegador Chrome: {download_dir}")
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
                }
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)
        logger.info("Driver de Chrome inicializado correctamente")
        return driver
    except Exception as e:
            logger.error("Error al inicializar el navegador", exc_info=True)
            raise
