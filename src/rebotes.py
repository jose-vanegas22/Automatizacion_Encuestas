import requests
import logging
import pandas as pd
from config import CONTROL_FILE, COL_EMAIL_POLIZAS
from src.auth import get_token
log = logging.getLogger(__name__)

def procesar_rebotes(df):
    result = get_token()
    if "access_token" not in result:
        log.error("No se pudo obtener token para leer bandeja")
        return df

    headers = {"Authorization": f"Bearer {result['access_token']}"}
    url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top=50"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        log.error(f"Error leyendo bandeja: {r.status_code} {r.text}")
        return df

    mensajes = r.json().get("value", [])
    patrones_rebote = (
        "no se pudo entregar",
        "undeliverable",
        "delivery has failed",
        "delivery status notification",
        "failure notice",
    )

    for msg in mensajes:
        asunto = msg.get("subject", "").lower()
        cuerpo = msg.get("body", {}).get("content", "").lower()
        if not any(texto in asunto for texto in patrones_rebote):
            continue

        for _, row in df.iterrows():
            email = str(row[COL_EMAIL_POLIZAS]).lower().strip()
            if email and email in cuerpo:
                idx = df[df[COL_EMAIL_POLIZAS].astype(str).str.lower().str.strip() == email].index
                if not idx.empty:
                    df.at[idx[0], "Rebotado"] = True
                    df.at[idx[0], "Entregado"] = False
                    df.at[idx[0], "Estado"] = "Rebotado"
                    log.info(f"Rebote detectado: {email}")

    return df