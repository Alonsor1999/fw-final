import json
from datetime import datetime
from core.browser import get_driver
from core.form_handler import fill_form
from core.downloader import descargar_certificado
from core.rename_file import renombrar_descarga
import config,os
from logger import setup_logger

logger = setup_logger("WS RNEC")

def run(driver, cedula, fecha):
    logger.info(f"Iniciando proceso para cédula: {cedula} | Fecha: {fecha}")
    try:
        logger.info("Abriendo página de la Registraduría")
        driver.get(config.URL)

        logger.info("Diligenciando formulario")
        fill_form(driver, cedula, fecha)

        logger.info("Formulario diligenciado, iniciando descarga del certificado")
        descargar_certificado(driver)

        logger.info("Descarga iniciada, renombrando archivo")
        ruta_final = renombrar_descarga(
            config.DOWNLOAD_DIR,
            f"CertificadoVigencia_{cedula}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        logger.info(f"Proceso finalizado exitosamente. Archivo guardado en: {ruta_final}")

    except Exception as e:
        logger.error(f"Error durante el proceso para la cédula {cedula}: {e}", exc_info=True)

def cargar_personas():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_DIR = os.path.join(BASE_DIR, ".")
    LOG_DIR = os.path.abspath(LOG_DIR)
    COMBINED_LOG_FILE = os.path.join(LOG_DIR, "lote_personas.json")
    try:
        with open(COMBINED_LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            raise ValueError("El archivo debe contener una lista de personas.")
        return data
    except Exception as e:
        logger.error(f"Error al cargar el archivo de personas: {e}", exc_info=True)
        return []

if __name__ == "__main__":
    personas = cargar_personas()

    if not personas:
        logger.warning("No se encontraron personas para procesar. Terminando ejecución.")
    elif len(personas) == 1:
        logger.info("Modo individual detectado")
        driver = get_driver(config.DOWNLOAD_DIR)
        try:
            run(driver, personas[0]["cedula"], personas[0]["fecha"])
        finally:
            driver.quit()
            logger.info("Navegador cerrado.")
    else:
        logger.info(f"Modo lote detectado. Total personas: {len(personas)}")
        driver = get_driver(config.DOWNLOAD_DIR)
        try:
            for persona in personas:
                run(driver, persona["cedula"], persona["fecha"])
        finally:
            driver.quit()
            logger.info("Navegador cerrado tras finalizar lote.")
