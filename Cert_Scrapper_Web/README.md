# TIGO---Registradur-a---iniciativa-4

# 🧾 Proyecto: Scraper Certificado de Cédula – Registraduría Nacional

Automatiza la descarga del **Certificado de Estado de Cédula** desde el sitio oficial de la Registraduría Nacional de Colombia.

## 📁 Estructura del Proyecto

```
cert_scraper/
├── core/
│   ├── browser.py           # Inicialización del navegador con Selenium
│   ├── captcha_solver.py    # Integración con 2Captcha
│   ├── form_handler.py      # Llenado y envío del formulario web
│   └── downloader.py        # Gestión de descarga del PDF
├── tests/
│   ├── test_captcha_solver.py  # Pruebas unitarias con mocks de 2Captcha
│   └── test_form_handler.py    # Pruebas de flujo con mocks de Selenium
├── main.py                  # Script de ejecución principal
├── config.py                # Configuraciones del sistema
├── requirements.txt         # Dependencias del entorno
└── README.md
```

## ⚙️ Configuración del Entorno

1. **Crear entorno virtual:**

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate   # Windows
```

2. **Instalar dependencias:**

```bash
pip install -r requirements.txt
```

3. **Agregar tu API Key de 2Captcha a `config.py`:**

```python
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"
```

## 📦 Descripción de Módulos

### `core/browser.py`
- Inicializa el navegador Chrome en modo headless y configura el directorio de descarga.

### `core/captcha_solver.py`
- Envia la imagen del captcha a 2Captcha y devuelve el texto resuelto.

### `core/form_handler.py`
- Llena y envía el formulario de verificación, resolviendo el captcha en varios intentos.

### `core/downloader.py`
- Clic en "Generar Certificado" y espera que se descargue el PDF.

### `main.py`
- Controla el flujo completo de scraping.

## 🧪 Pruebas Unitarias

Ubicadas en `tests/`, utilizan `pytest` y `unittest.mock`:

```bash
pytest tests/
```

- `test_captcha_solver.py`: Mocks para 2Captcha.
- `test_form_handler.py`: Mocks para Selenium.





