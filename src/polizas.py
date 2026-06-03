import os
import pandas as pd
import requests
import logging

from config import POLIZAS_FILE, COL_ID_POLIZAS, COL_NOMBRE_POLIZAS, COL_EMAIL_POLIZAS, ONEDRIVE_FOLDER, BASE_DATOS_FILE_NAME
from src.auth import get_token
from src.onedrive import obtener_drive_id, buscar_item_en_carpeta
log = logging.getLogger(__name__)


# Funciones para cargar y preparar pólizas desde Excel o OneDrive


def preparar_polizas(df):
    df = df.copy()
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace("\xa0", "", regex=True)

    df = df[df[COL_EMAIL_POLIZAS].notna() & df[COL_EMAIL_POLIZAS].str.contains("@", na=False)]
    df[COL_ID_POLIZAS] = df[COL_ID_POLIZAS].astype(str).str.strip()
    df[COL_EMAIL_POLIZAS] = df[COL_EMAIL_POLIZAS].astype(str).str.strip().str.lower()

    total_validos = len(df)
    df["_clave_envio"] = df[COL_ID_POLIZAS]
    sin_id = df["_clave_envio"].isin(["", "nan", "None"])
    df.loc[sin_id, "_clave_envio"] = df.loc[sin_id, COL_EMAIL_POLIZAS]
    df = df.drop_duplicates(subset=["_clave_envio"], keep="first").drop(columns=["_clave_envio"])

    duplicados = total_validos - len(df)
    if duplicados:
        log.info(f"Pólizas deduplicadas: {duplicados} registros repetidos omitidos por ID/correo.")

    return df



def cargar_polizas():
    if not os.path.exists(POLIZAS_FILE):
        log.warning(f"Archivo de pólizas no encontrado: {POLIZAS_FILE}")
        return pd.DataFrame(columns=[COL_ID_POLIZAS, COL_NOMBRE_POLIZAS, COL_EMAIL_POLIZAS])

    df = preparar_polizas(pd.read_excel(POLIZAS_FILE, dtype=str))

    log.info(f"Pólizas cargadas: {len(df)} con email válido.")
    return df



def descargar_polizas():
    """Descarga BasesDatos desde OneDrive/Encuestas y lo procesa.
    Si no se puede descargar, usa la copia local como fallback.
    """
    result = get_token()
    if result and "access_token" in result:
        headers = {"Authorization": f"Bearer {result['access_token']}"}
        driveId = obtener_drive_id(headers)
        if driveId:
            item = buscar_item_en_carpeta(headers, driveId, ONEDRIVE_FOLDER, BASE_DATOS_FILE_NAME)
            if item:
                url = f"https://graph.microsoft.com/v1.0/drives/{driveId}/items/{item['id']}/content"
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    os.makedirs(os.path.dirname(POLIZAS_FILE), exist_ok=True)
                    if os.path.exists(POLIZAS_FILE):
                        os.remove(POLIZAS_FILE)
                    with open(POLIZAS_FILE, "wb") as f:
                        f.write(r.content)
                    log.info(f"Base de datos descargada desde OneDrive ({ONEDRIVE_FOLDER}/{item['name']})")
                    df = preparar_polizas(pd.read_excel(POLIZAS_FILE, dtype=str))
                    log.info(f"Base de datos cargada: {len(df)} registros con email valido.")
                    return df
                log.error(f"Error descargando base de datos: {r.status_code} {r.text}")
            else:
                log.warning(f"No se encontro {BASE_DATOS_FILE_NAME} en la carpeta {ONEDRIVE_FOLDER}.")
    else:
        log.warning("No se obtuvo token para descargar base de datos desde OneDrive.")

    log.info("Usando copia local de base de datos como fallback.")
    return cargar_polizas()