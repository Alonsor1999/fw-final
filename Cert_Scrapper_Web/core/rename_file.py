from datetime import datetime,time
import os
from logger import setup_logger

logger = setup_logger("rename_file")

def renombrar_descarga(download_dir, nuevo_nombre, timeout=30):
    logger.info("Esperando archivo PDF descargado...")
    for _ in range(timeout):
        archivos = [f for f in os.listdir(download_dir) if f.endswith(".pdf")]
        if archivos:
            archivos = sorted(archivos, key=lambda f: os.path.getmtime(os.path.join(download_dir, f)), reverse=True)
            archivo_reciente = os.path.join(download_dir, archivos[0])
            nuevo_path = os.path.join(download_dir, nuevo_nombre)
            os.rename(archivo_reciente, nuevo_path)
            print(f"[✅] Archivo renombrado a: {nuevo_path}")
            logger.info(f"Archivo renombrado de '{archivo_reciente}' a '{nuevo_nombre}'")
            return nuevo_path
        time.sleep(1)
    logger.error("No se encontró archivo PDF dentro del tiempo esperado.")
    raise TimeoutError("❌ Descarga no detectada después del tiempo de espera.")
