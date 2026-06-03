import os
import base64
import logging
from datetime import datetime
import pandas as pd
import requests
from config import REPORT_EMAIL
from src.auth import get_token
log = logging.getLogger(__name__)

def generar_reporte(df):
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M")
    reporte_file = f"data/reporte_{timestamp}.xlsx"
    # Asegurar carpeta de destino
    os.makedirs(os.path.dirname(reporte_file), exist_ok=True)

    with pd.ExcelWriter(reporte_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Todos", index=False)
        df[df["Enviado"] == True].to_excel(writer, sheet_name="Enviados", index=False)
        df[df["Rebotado"] == True].to_excel(writer, sheet_name="Rebotados", index=False)
        df[df["Entregado"] == True].to_excel(writer, sheet_name="Entregados", index=False)
        df[df["Respondió"] == True].to_excel(writer, sheet_name="Respondieron", index=False)

    log.info(f"📊 Reporte generado: {reporte_file}")
    return reporte_file



def enviar_reporte_por_correo(reporte_file):
    hoy = datetime.now().strftime("%Y-%m-%d %H:%M")

    df = pd.read_excel(reporte_file, sheet_name="Todos")
    enviados     = len(df[df["Enviado"] == True])
    rebotados    = len(df[df["Rebotado"] == True])
    entregados   = len(df[df["Entregado"] == True])
    respondieron = len(df[df["Respondió"] == True])

    cuerpo_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #1a3c6e;">📊 Reporte de Encuestas — {hoy}</h2>
        <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
            <tr><td>📨 Enviados</td><td>{enviados}</td></tr>
            <tr><td>❌ Rebotados</td><td>{rebotados}</td></tr>
            <tr><td>📨 Entregados</td><td>{entregados}</td></tr>
            <tr><td>✅ Respondieron</td><td>{respondieron}</td></tr>
        </table>
    </div>
    """

    with open(reporte_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()

    result = get_token()
    if "access_token" not in result:
        log.error("❌ No se pudo obtener token para enviar reporte")
        return

    headers = {
        "Authorization": f"Bearer {result['access_token']}",
        "Content-Type": "application/json"
    }

    message = {
        "message": {
            "subject": f"📊 Reporte Encuestas Pólizas — {hoy}",
            "body": {"contentType": "HTML", "content": cuerpo_html},
            "toRecipients": [{"emailAddress": {"address": REPORT_EMAIL}}],
            "attachments": [{
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": os.path.basename(reporte_file),
                "contentBytes": encoded
            }]
        },
        "saveToSentItems": "true"
    }

    r = requests.post("https://graph.microsoft.com/v1.0/me/sendMail", headers=headers, json=message)
    if r.status_code in [200, 202]:
        log.info(f"📧 Reporte enviado a {REPORT_EMAIL}")
    else:
        log.error(f"❌ Error enviando reporte: {r.status_code} {r.text}")