from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, UnexpectedAlertPresentException
from core.captcha_solver import solve_with_2captcha
#from core.captcha_solver_tesseract import solve_with_tesseract as solve_captcha
from logger import setup_logger
import time

logger = setup_logger("form_handler")


def fill_form(driver, cedula, fecha, retries=3):
    logger.info(f"Ingresando cédula: {cedula} | Fecha: {fecha}")
    MESES = {
    "Enero": "01", "Febrero": "02", "Marzo": "03",
    "Abril": "04", "Mayo": "05", "Junio": "06",
    "Julio": "07", "Agosto": "08", "Septiembre": "09",
    "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
}
    wait = WebDriverWait(driver, 15)
    try:
        # Espera por el campo cedula

        input_cedula = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_TextBox1")))
        input_cedula.clear()
        input_cedula.send_keys(cedula)

        # Esperar los selects
        select_dia_element = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_DropDownList1")))
        Select(select_dia_element).select_by_value(f"{int(fecha['dia']):02d}")  # ejemplo: "05"

        # Mes (mapeado de texto a número)
        try:
            num = int(fecha['mes'])
            mes_num = (f"{int(fecha['mes']):02d}")
            
        except ValueError:

            mes_nombre = fecha['mes']
            mes_num = MESES.get(mes_nombre)
        
        if not mes_num:
            logger.error(f"Mes inválido recibido: {fecha['mes']}")
            raise ValueError(f"Mes inválido: {fecha['mes']}")
        select_mes = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_DropDownList2")))
        Select(select_mes).select_by_value(mes_num)


        # Año
        anio = int(fecha['anio'])
        if anio < 1900:
            logger.error(f"Anio inválido recibido: {anio}")
            raise ValueError(f"Anio inválido: {anio}")

        select_anio = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_DropDownList3")))
        Select(select_anio).select_by_value(str(anio))
    except Exception as e:
        logger.error("Error al completar campos del formulario", exc_info=True)
        raise



    # CAPTCHA loop
    CAPTCHA_IMG_ID = "datos_contentplaceholder1_captcha1_CaptchaImage"
    CAPTCHA_INPUT_ID = "ContentPlaceHolder1_TextBox2"
    BTN_CONTINUAR_ID = "ContentPlaceHolder1_Button1"
    BTN_REGRESAR_ID = "ContentPlaceHolder1_Button2"
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Intento de CAPTCHA #{attempt}")
            captcha_img = wait.until(EC.presence_of_element_located((By.ID, CAPTCHA_IMG_ID)))
            captcha_bytes = captcha_img.screenshot_as_png
            
            captcha_text = solve_with_2captcha(captcha_bytes)
            #captcha_text = solve_captcha(captcha_bytes)

            logger.info(f"Texto del CAPTCHA leído: {captcha_text}")

            txt_captcha = wait.until(EC.element_to_be_clickable((By.ID, CAPTCHA_INPUT_ID)))
            txt_captcha.clear()
            txt_captcha.send_keys(captcha_text)

            driver.find_element(By.ID, BTN_CONTINUAR_ID).click()
            time.sleep(3)

            # Verificar si aparece popup de error
            try:
                alert = driver.switch_to.alert
                logger.warning(f"CAPTCHA inválido. Mensaje: '{alert.text.strip()}'")
                alert.accept()
                #driver.find_element(By.ID, BTN_REGRESAR_ID).click()
                time.sleep(1)
                continue
            except NoAlertPresentException:
                pass
            except UnexpectedAlertPresentException:
                logger.error("Alerta inesperada detectada. Cerrando.", exc_info=True)
                driver.switch_to.alert.accept()
                continue

            # ⚠️ Verificar si es un error por datos incorrectos
            if "no se encuentra en la base de datos" in driver.page_source.lower():
                logger.error("Cédula o fecha inválida detectada por el sistema.")
                raise Exception("Datos inválidos: La cédula o la fecha de expedición no coinciden con la base de datos.")


            # Si la página contiene el botón de certificado, éxito
            if "Generar Certificado" in driver.page_source:
                logger.info("CAPTCHA resuelto correctamente. Formulario completado con éxito.")
                return

            logger.warning("CAPTCHA fallido pero sin alerta. Reintentando...")

            # Si no hay alert pero tampoco éxito → retroceder e intentar de nuevo
            #driver.find_element(By.ID, BTN_REGRESAR_ID).click()
        except Exception as e:
            logger.error(f"Error durante intento #{attempt} del CAPTCHA", exc_info=True)

            time.sleep(1)
        logger.error("CAPTCHA fallido después de múltiples intentos")
        raise Exception("❌ CAPTCHA fallido después de múltiples intentos")
