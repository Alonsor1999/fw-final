from unittest.mock import MagicMock, patch
from core.form_handler import fill_form

def test_fill_form_success():
    driver = MagicMock()
    driver.find_element().screenshot_as_png = b"fake_image_data"
    driver.page_source = "Generar Certificado"

    with patch("core.form_handler.solve_with_2captcha", return_value="captcha123"):
        fill_form(driver, "123456789", {"dia": 1, "mes": 1, "anio": 2000})
