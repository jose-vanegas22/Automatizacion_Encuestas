import os
import pandas as pd
import requests
import logging

from config import COL_EMAIL_POLIZAS, COL_NOMBRE_POLIZAS, CONTROL_FILE, COL_ID_POLIZAS, ONEDRIVE_FOLDER
from src.auth import get_token
from src.onedrive import obtener_drive_id, graph_root_path
log = logging.getLogger(__name__)

# Funciones para manejar el archivo de control de envíos, que registra el estado de cada póliza en el proceso de envío y respuesta a la encuesta


CONTROL_COLUMNS = [
    COL_ID_POLIZAS, COL_NOMBRE_POLIZAS, COL_EMAIL_POLIZAS,
    "Lote", "Fecha Primer Envio", "Fecha Envio", "Fecha Proximo Reenvio",
    "Enviado", "Rebotado", "Entregado", "Abrio", "Fecha Apertura",
    "Respondió", "Lleno Encuesta", "Fecha Encuesta", "Reenvios", "Estado",
    "Correo Remitente", "Error Ultimo Envio"
]

def asegurar_columnas_control(df):
    defaults = {
        "Lote": "",
        "Fecha Primer Envio": "",
        "Fecha Envio": "",
        "Fecha Proximo Reenvio": "",
        "Enviado": False,
        "Rebotado": False,
        "Entregado": False,
        "Abrio": False,
        "Fecha Apertura": "",
        "Respondió": False,
        "Lleno Encuesta": False,
        "Fecha Encuesta": "",
        "Reenvios": 0,
        "Estado": "",
        "Correo Remitente": "",
        "Error Ultimo Envio": "",
    }

    for col in CONTROL_COLUMNS:
        if col not in df.columns:
            df[col] = defaults.get(col, "")
        df[col] = df[col].astype("object")

    return df


def inicializar_control():
    if os.path.exists(CONTROL_FILE):
        df = pd.read_excel(CONTROL_FILE, dtype={
            COL_ID_POLIZAS: str,
            "Fecha Envio": str,
            "Fecha Encuesta": str,
            "Respondió": bool,
            "Enviado": bool,
            "Rebotado": bool,
            "Entregado": bool,
            "Lleno Encuesta": bool,
            "Reenvios": str,
            "Estado": str
        })
    else:
        df = pd.DataFrame(columns=CONTROL_COLUMNS)
        os.makedirs(os.path.dirname(CONTROL_FILE), exist_ok=True)
        df.to_excel(CONTROL_FILE, index=False)
        log.info("Archivo de control creado desde cero y guardado en disco.")
    return asegurar_columnas_control(df)



def guardar_control(df):
    def calcular_estado(row):
        if row["Respondió"] or row["Lleno Encuesta"]:
            return "✅ Respondió encuesta"
        elif row["Rebotado"]:
            return "❌ Rebotado"
        elif row["Entregado"]:
            return "📨 Entregado"
        else:
            return "⏳ Pendiente"

    df["Estado"] = df.apply(calcular_estado, axis=1)
    df.to_excel(CONTROL_FILE, index=False)
    log.info(f"Control guardado: {len(df)} registros.")

    enviados     = len(df[df["Enviado"] == True])
    rebotados    = len(df[df["Rebotado"] == True])
    entregados   = len(df[df["Entregado"] == True])
    respondieron = len(df[df["Respondió"] == True])

    log.info("═══════════════ RESUMEN ═══════════════")
    log.info(f"📨 Enviados:     {enviados}")
    log.info(f"❌ Rebotados:    {rebotados}")
    log.info(f"📨 Entregados:   {entregados}")
    log.info(f"✅ Respondieron: {respondieron}")
    log.info("═══════════════════════════════════════")


def descargar_control():
    """Descarga control.xlsx desde OneDrive en la carpeta configurada. Si no existe, inicializa vacio."""
    filename = os.path.basename(CONTROL_FILE)
    folder_path = ONEDRIVE_FOLDER
    result = get_token()
    if result and "access_token" in result:
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        driveId = obtener_drive_id(headers)
        if driveId:

            url = graph_root_path(driveId, folder_path, filename, action="content")
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(CONTROL_FILE), exist_ok=True)
                if os.path.exists(CONTROL_FILE):
                    os.remove(CONTROL_FILE)
                with open(CONTROL_FILE, "wb") as f:
                    f.write(r.content)
                log.info(f"✅ Control descargado desde OneDrive ({folder_path}/{filename})")
                df = pd.read_excel(CONTROL_FILE, dtype={
                    COL_ID_POLIZAS: str,
                    "Fecha Envio": str,
                    "Fecha Encuesta": str,
                    "Respondió": bool,
                    "Enviado": bool,
                    "Rebotado": bool,
                    "Entregado": bool,
                    "Lleno Encuesta": bool,
                    "Reenvios": str,
                    "Estado": str
                })
                return asegurar_columnas_control(df)
            else:
                log.warning(f"Control no encontrado en {folder_path}/{filename} ({r.status_code})")
    else:
        log.warning("No se obtuvo token para descargar control desde OneDrive.")

    log.info("Inicializando control vacío.")
    return inicializar_control()



def subir_control(df):
    """Sube control.xlsx a OneDrive en la carpeta configurada (actualiza si existe, crea si no)."""
    filename = os.path.basename(CONTROL_FILE)
    folder_path = ONEDRIVE_FOLDER
    result = get_token()
    if not result or "access_token" not in result:
        log.error("❌ No se pudo obtener token para subir control a OneDrive")
        return False

    headers = {"Authorization": f"Bearer {result['access_token']}"}

    # Guardar localmente primero
    os.makedirs(os.path.dirname(CONTROL_FILE), exist_ok=True)
    df.to_excel(CONTROL_FILE, index=False)

    driveId = obtener_drive_id(headers)
    if not driveId:
        return False

    # Leer archivo local
    with open(CONTROL_FILE, "rb") as f:
        file_content = f.read()

    # Subir usando ruta directa (crea o actualiza)
    upload_url = graph_root_path(driveId, folder_path, filename, action="content")
    r = requests.put(upload_url, headers=headers, data=file_content)
    if r.status_code in [200, 201]:
        log.info(f"✅ Control guardado en OneDrive ({folder_path}/{filename})")
        return True
    else:
        log.error(f"❌ Error guardando control en OneDrive: {r.status_code} {r.text}")
        return False