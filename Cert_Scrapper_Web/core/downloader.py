import time
from selenium.webdriver.common.by import By
from logger import setup_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

logger = setup_logger("downloader")
def descargar_certificado(driver):
    try:
        wait = WebDriverWait(driver, 15)
        logger.info("Haciendo clic en el botón de descarga del certificado...")
        boton = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_Button1")))
        boton = driver.find_element(By.ID, "ContentPlaceHolder1_Button1")
        boton.click()
        logger.info("Solicitud de descarga enviada. Esperando generación del archivo PDF...")
        time.sleep(5)  # Wait for download
    except Exception as e:
        logger.error("Error al iniciar descarga del certificado", exc_info=True)
        raise Exception("❌ Falló la descarga del certificado") from e  # ✔️ Lanzamos un nuevo error informativo