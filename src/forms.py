import os
import pandas as pd
import requests
import logging

from config import ONEDRIVE_FOLDER, ENCUESTAS_FILE_NAME
from src.auth import get_token
from src.onedrive import obtener_drive_id, buscar_item_en_carpeta

log = logging.getLogger(__name__)

def cargar_form_prueba():
    result = get_token()
    if "access_token" not in result:
        log.error("❌ No se pudo obtener token")
        return None

    headers = {"Authorization": f"Bearer {result['access_token']}"}
    driveId = obtener_drive_id(headers)
    if not driveId:
        return None

    item = buscar_item_en_carpeta(headers, driveId, ONEDRIVE_FOLDER, ENCUESTAS_FILE_NAME)
    if not item:
        log.warning(f"No se encontró {ENCUESTAS_FILE_NAME} en la carpeta {ONEDRIVE_FOLDER}.")
        return None

    url = f"https://graph.microsoft.com/v1.0/drives/{driveId}/items/{item['id']}/content"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        log.error(f"Error descargando archivo: {r.status_code} {r.text}")
        return None

    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", item["name"])
    if os.path.exists(file_path):
        os.remove(file_path)

    with open(file_path, "wb") as f:
        f.write(r.content)

    log.info(f"✅ Archivo descargado en: {file_path}")
    df = pd.read_excel(file_path, dtype=str)
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace("\xa0", "", regex=True)

    log.info(f"Encuesta cargada: {len(df)} respuestas")
    return df
