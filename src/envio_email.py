import os
import requests
import logging

from config import COL_NOMBRE_POLIZAS, COL_EMAIL_POLIZAS, COL_ID_POLIZAS, SURVEY_BASE_URL, FROM_EMAIL, FROM_NAME
from src.auth import get_token
log = logging.getLogger(__name__)

def enviar_correo(row):
    nombre      = str(row[COL_NOMBRE_POLIZAS]).split()[0]
    email       = str(row[COL_EMAIL_POLIZAS]).strip()
    id_aseg     = str(row[COL_ID_POLIZAS]).strip()
    survey_link = SURVEY_BASE_URL

    with open("templates/email.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{NOMBRE}}", nombre)
    html = html.replace("{{SURVEY_LINK}}", survey_link)
    html = html.replace("{{ID}}", id_aseg)
    html = html.replace("{{id_aseg}}", id_aseg)

    result = get_token()
    if "access_token" not in result:
        log.error("❌ No se pudo obtener token para enviar correo")
        return False

    headers = {
        "Authorization": f"Bearer {result['access_token']}",
        "Content-Type": "application/json"
    }

    message = {
        "message": {
            "subject": "Tu opinión transforma nuestro servicio.",
            "body": {"contentType": "HTML", "content": html},
            "toRecipients": [{"emailAddress": {"address": email}}],
            "replyTo": [{"emailAddress": {"address": FROM_EMAIL}}],
            "internetMessageHeaders": [
                {"name": "X-List-Unsubscribe", "value": f"<mailto:{FROM_EMAIL}>"},
            ],
            "from": {
                "emailAddress": {
                    "address": FROM_EMAIL,
                    "name": FROM_NAME
                }
            }
        },
        "saveToSentItems": "true"
    }

    r = requests.post("https://graph.microsoft.com/v1.0/me/sendMail", headers=headers, json=message)

    # Loguear respuesta completa para depuración (headers + body)
    try:
        hdrs = dict(r.headers)
    except Exception:
        hdrs = {}
    log.debug(f"Graph sendMail status: {r.status_code}")
    log.debug(f"Graph sendMail headers: {hdrs}")
    log.debug(f"Graph sendMail body: {r.text}")

    if r.status_code in [200, 202]:
        log.info(f"✅ Correo enviado a {email} ({id_aseg})")
        return {"Enviado": True, "Entregado": True, "Rebotado": False}
    else:
        log.error(f"❌ Error enviando a {email}: {r.status_code} {r.text}")
        return {"Enviado": False, "Entregado": False, "Rebotado": False, "Error": f"{r.status_code} {r.text}"}