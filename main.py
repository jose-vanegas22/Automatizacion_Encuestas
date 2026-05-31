
import os
import logging
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config import *
import os, json, requests, pandas as pd, msal


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 1. CONTROL EXCEL
# ─────────────────────────────────────────────
def cargar_control():
    if os.path.exists(CONTROL_FILE):
        df = pd.read_excel(CONTROL_FILE, dtype={
            COL_ID_POLIZAS: str,
            "Fecha Envio": str,
            "Fecha Apertura": str,
            "Fecha Encuesta": str,
            "Abrio": bool,
            "Respondió": bool,
            "Enviado": bool,
            "Rebotado": bool,
            "Entregado": bool,
            "Lleno Encuesta": bool,
            "Reenvios": str,
            "Estado": str
        })
    else:
        df = pd.DataFrame(columns=[
            COL_ID_POLIZAS, COL_NOMBRE_POLIZAS, COL_EMAIL_POLIZAS,
            "Fecha Envio", "Enviado", "Rebotado", "Entregado",
            "Abrio", "Fecha Apertura", "Respondió", "Lleno Encuesta",
            "Fecha Encuesta", "Reenvios", "Estado"
        ])
        log.info("Archivo de control creado desde cero.")
    return df


def guardar_control(df):
    def calcular_estado(row):
        if row["Respondió"] or row["Lleno Encuesta"]:
            return "✅ Respondió encuesta"
        elif row["Rebotado"]:
            return "❌ Rebotado"
        elif row["Abrio"]:
            return "👁️ Abrió sin responder"
        elif row["Entregado"]:
            return "📨 Entregado"
        else:
            return "⏳ Pendiente"

    df["Estado"] = df.apply(calcular_estado, axis=1)
    df.to_excel(CONTROL_FILE, index=False)
    log.info(f"Control guardado: {len(df)} registros.")

    total        = len(df)
    enviados     = len(df[df["Enviado"] == True])
    rebotados    = len(df[df["Rebotado"] == True])
    entregados   = len(df[df["Entregado"] == True])
    abiertos     = len(df[df["Abrio"] == True])
    respondieron = len(df[df["Respondió"] == True])

    log.info("═══════════════ RESUMEN ═══════════════")
    log.info(f"📨 Enviados:     {enviados}")
    log.info(f"❌ Rebotados:    {rebotados}")
    log.info(f"📨 Entregados:   {entregados}")
    log.info(f"👁️ Abiertos:     {abiertos}")
    log.info(f"✅ Respondieron: {respondieron}")
    log.info("═══════════════════════════════════════")


# ─────────────────────────────────────────────
# 2. LEER PÓLIZAS
# ─────────────────────────────────────────────
def cargar_polizas():
    df = pd.read_excel(POLIZAS_FILE, dtype=str)

    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace("\xa0", "", regex=True)

    # Filtrar solo registros con email válido
    df = df[df[COL_EMAIL_POLIZAS].notna() & df[COL_EMAIL_POLIZAS].str.contains("@", na=False)]

    # Asegurar que el ID esté limpio
    df[COL_ID_POLIZAS] = df[COL_ID_POLIZAS].astype(str).str.strip()

    log.info(f"Pólizas cargadas: {len(df)} con email válido.")
    return df
# ─────────────────────────────────────────────
# 3. TOKEN DE CGA
# ─────────────────────────────────────────────
def get_token():
    CLIENT_ID = os.getenv("CLIENT_ID")
    TENANT_ID = os.getenv("TENANT_ID")
    cache = msal.SerializableTokenCache()

    # 🔧 Cargar cache desde archivo si existe
    if os.path.exists("token_cache.json"):
        with open("token_cache.json", "r") as f:
            cache.deserialize(f.read())

    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=cache
    )

    # Intentar usar token guardado
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(
            ["Files.Read", "Mail.Send"], account=accounts[0]
        )
        if result:
            return result

    # Si no hay token válido, pedir login interactivo
    result = app.acquire_token_interactive(
        scopes=["Files.Read", "Mail.Send", "User.Read"]
    )
    if result:
        # Guardar cache actualizado
        with open("token_cache.json", "w") as f:
            f.write(cache.serialize())
    return result



# ─────────────────────────────────────────────
# 4. LEER RESPUESTAS MICROSOFT FORMS
# ─────────────────────────────────────────────
def cargar_form_prueba():
    result = get_token()

    if "access_token" in result:
        headers = {"Authorization": f"Bearer {result['access_token']}"}

        # 1. Obtener el driveId de OneDrive del usuario
        drives_resp = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers)
        drive_json = drives_resp.json()
        driveId = drive_json["id"]

        # 2. Buscar archivo EncuestasSatisfaccionZengu.xlsx en la raíz
        search_url = f"https://graph.microsoft.com/v1.0/drives/{driveId}/root/search(q='EncuestasSatisfaccionZengu.xlsx')"
        search_resp = requests.get(search_url, headers=headers)
        search_json = search_resp.json()

        if "value" in search_json and len(search_json["value"]) > 0:
            item = next((f for f in search_json["value"] if f["name"] == "EncuestasSatisfaccionZengu.xlsx"), None)
            if item:
                itemId = item["id"]

                # 3. Descargar archivo
                url = f"https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/content"
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    os.makedirs("data", exist_ok=True)
                    file_path = os.path.join("data", "EncuestasSatisfaccionZengu.xlsx")

                    # Eliminar archivo viejo si existe
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    with open(file_path, "wb") as f:
                        f.write(r.content)

                    print(f"✅ Archivo descargado en: {file_path}")
                    df = pd.read_excel(file_path, dtype=str)

                    # Normalizar nombres de columnas
                    df.columns = df.columns.str.strip()
                    df.columns = df.columns.str.replace("\xa0", "", regex=True)

                    print("Columnas limpias:", df.columns.tolist())
                    print("Encuesta cargada:", len(df), "respuestas")
                    return df
                else:
                    print("❌ Error descargando archivo:", r.status_code, r.text)
                    return None
            else:
                print("❌ Se encontró otro Excel, pero no el esperado EncuestasSatisfaccionZengu.xlsx.")
                return None
        else:
            print("❌ No se encontró EncuestasSatisfaccionZengu.xlsx en tu OneDrive.")
            return None
    else:
        print("❌ No se pudo obtener token")
        return None


# ─────────────────────────────────────────────
# 5. TRACKING DE APERTURAS — SendGrid API
# ─────────────────────────────────────────────
def obtener_aperturas_sendgrid():
    try:
        import requests
        headers = {"Authorization": f"Bearer {SENDGRID_API_KEY}"}

        desde = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        hasta = datetime.now().strftime("%Y-%m-%d")

        # Consultar emails con clics usando Email Activity
        url = f"https://api.sendgrid.com/v3/messages?limit=1000&query=clicks_count%3E0"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            emails_con_clic = set()
            for msg in data.get("messages", []):
                email = msg.get("to_email", "").lower().strip()
                if email:
                    emails_con_clic.add(email)
            log.info(f"Emails con clic detectados: {len(emails_con_clic)}")
            return emails_con_clic

        elif response.status_code == 403:
            # Plan gratuito no tiene Email Activity API
            # Usamos stats generales para saber si hubo clics
            url_stats = f"https://api.sendgrid.com/v3/stats?start_date={desde}&end_date={hasta}&aggregated_by=month"
            r2 = requests.get(url_stats, headers=headers)
            if r2.status_code == 200:
                data2 = r2.json()
                for period in data2:
                    for stat in period.get("stats", []):
                        clicks = stat.get("metrics", {}).get("clicks", 0)
                        log.info(f"Clics totales en periodo: {clicks}")
            log.warning("Plan gratuito: no se pueden obtener emails individuales con clic.")
            return set()
        else:
            log.warning(f"SendGrid API status: {response.status_code}")
            return set()

    except Exception as e:
        log.warning(f"Error consultando clics: {e}")
        return set()


# ─────────────────────────────────────────────
# 6. ENVIAR CORREO
# ─────────────────────────────────────────────
def enviar_correo(row):
    nombre = str(row[COL_NOMBRE_POLIZAS]).split()[0]
    email = str(row[COL_EMAIL_POLIZAS]).strip()
    id_aseg = str(row[COL_ID_POLIZAS]).strip()
    survey_link = SURVEY_BASE_URL

    with open("templates/email.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{NOMBRE}}", nombre)
    html = html.replace("{{SURVEY_LINK}}", survey_link)
    html = html.replace("{{ID}}", id_aseg)
    html = html.replace("{{id_aseg}}", id_aseg)

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        message = Mail(
            from_email='administrativo@zenguseguros.com',
            to_emails=email,
            subject='Tu póliza - Solicitud de información',
            html_content=html
        )
        response = sg.send(message)
        if response.status_code == 202:
            log.info(f"✅ Correo enviado a {email} ({id_aseg})")
            return {"Enviado": True, "Entregado": True, "Rebotado": False}
        else:
            log.warning(f"⚠️ SendGrid status: {response.status_code}")
            return {"Enviado": True, "Entregado": False, "Rebotado": True}
    except Exception as e:
        log.error(f"❌ Error enviando a {email}: {e}")
        return {"Enviado": True, "Entregado": False, "Rebotado": True}

# ─────────────────────────────────────────────
# 7. GENERAR REPORTE EXCEL DETALLADO
# ─────────────────────────────────────────────
def generar_reporte(df):
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M")
    reporte_file = f"data/reporte_{timestamp}.xlsx"

    with pd.ExcelWriter(reporte_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Todos", index=False)
        df[df["Enviado"] == True].to_excel(writer, sheet_name="Enviados", index=False)
        df[df["Rebotado"] == True].to_excel(writer, sheet_name="Rebotados", index=False)
        df[df["Entregado"] == True].to_excel(writer, sheet_name="Entregados", index=False)
        df[df["Abrio"] == True].to_excel(writer, sheet_name="Abiertos", index=False)
        df[df["Respondió"] == True].to_excel(writer, sheet_name="Respondieron", index=False)

    log.info(f"📊 Reporte generado: {reporte_file}")
    return reporte_file


# ─────────────────────────────────────────────
# 8. ENVIAR REPORTE POR CORREO
# ─────────────────────────────────────────────
def enviar_reporte_por_correo(reporte_file):
    hoy = datetime.now().strftime("%Y-%m-%d %H:%M")

    df = pd.read_excel(reporte_file, sheet_name="Todos")
    enviados     = len(df[df["Enviado"] == True])
    rebotados    = len(df[df["Rebotado"] == True])
    entregados   = len(df[df["Entregado"] == True])
    abiertos     = len(df[df["Abrio"] == True])
    respondieron = len(df[df["Respondió"] == True])

    cuerpo_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #1a3c6e;">📊 Reporte de Encuestas — {hoy}</h2>
        <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
            <tr><td>📨 Enviados</td><td>{enviados}</td></tr>
            <tr><td>❌ Rebotados</td><td>{rebotados}</td></tr>
            <tr><td>📨 Entregados</td><td>{entregados}</td></tr>
            <tr><td>👁️ Abiertos</td><td>{abiertos}</td></tr>
            <tr><td>✅ Respondieron</td><td>{respondieron}</td></tr>
        </table>
    </div>
    """

    # 🔧 Leer y codificar el archivo en base64
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






# ─────────────────────────────────────────────
# 9. LÓGICA PRINCIPAL
# ─────────────────────────────────────────────
def main():
    log.info("═══════════════ INICIANDO PROCESO ═══════════════")

    # 1. Descargar y cargar encuestas desde OneDrive
    encuestas_df = cargar_form_prueba()
    encuestas = set(encuestas_df[COL_ID_ENCUESTAS].astype(str).tolist()) if encuestas_df is not None else set()

    # 2. Cargar pólizas y control
    polizas         = cargar_polizas()
    control         = cargar_control()
    emails_abiertos = obtener_aperturas_sendgrid()
    hoy             = datetime.now()

    # 🔧 Actualizar control con encuestas nuevas
    for idx in control.index:
        id_aseg = str(control.at[idx, COL_ID_POLIZAS]).strip()
        if id_aseg in encuestas and not control.at[idx, "Lleno Encuesta"]:
            control.at[idx, "Lleno Encuesta"] = True
            control.at[idx, "Fecha Encuesta"] = hoy.strftime("%Y-%m-%d %H:%M")
            log.info(f"✅ Encuesta completada: {id_aseg}")


    ids_en_control  = set(control[COL_ID_POLIZAS].astype(str).tolist())
    nuevos_registros = []

    for _, row in polizas.iterrows():
        id_aseg = str(row[COL_ID_POLIZAS]).strip()
        email   = str(row[COL_EMAIL_POLIZAS]).strip().lower()
        nombre  = str(row[COL_NOMBRE_POLIZAS])

        # ── CASO 1: ID nuevo → enviar por primera vez
        if id_aseg not in ids_en_control:
            log.info(f"Nuevo: {id_aseg} — {nombre}")
            exito = enviar_correo(row)
            if exito:
                abrio = email in emails_abiertos
                resultado_envio = enviar_correo(row)
                nuevos_registros.append({
                    COL_ID_POLIZAS: id_aseg,
                    COL_NOMBRE_POLIZAS: nombre,
                    COL_EMAIL_POLIZAS: email,
                    "Fecha Envio": hoy.strftime("%Y-%m-%d %H:%M"),
                    "Enviado": resultado_envio["Enviado"],
                    "Rebotado": resultado_envio["Rebotado"],
                    "Entregado": resultado_envio["Entregado"],
                    "Abrio": abrio,
                    "Fecha Apertura": hoy.strftime("%Y-%m-%d %H:%M") if abrio else "",
                    "Respondió": id_aseg in encuestas,
                    "Lleno Encuesta": id_aseg in encuestas,
                    "Fecha Encuesta": hoy.strftime("%Y-%m-%d %H:%M") if id_aseg in encuestas else "",
                    "Reenvios": 0,
                    "Estado": ""
                })

        # ── CASO 2: Ya existe → actualizar estado
        else:
            idx = control[control[COL_ID_POLIZAS] == id_aseg].index[0]

            # Actualizar si abrió
            if email in emails_abiertos and not control.at[idx, "Abrio"]:
                control.at[idx, "Abrio"] = True
                control.at[idx, "Fecha Apertura"] = hoy.strftime("%Y-%m-%d %H:%M")
                log.info(f"👁️  Apertura detectada: {id_aseg}")

            # Actualizar si llenó encuesta
            if id_aseg in encuestas and not control.at[idx, "Lleno Encuesta"]:
                control.at[idx, "Lleno Encuesta"] = True
                control.at[idx, "Fecha Encuesta"] = hoy.strftime("%Y-%m-%d %H:%M")
                log.info(f"✅ Encuesta completada: {id_aseg}")
                continue

            # Si ya llenó → no hacer nada
            if control.at[idx, "Lleno Encuesta"]:
                log.info(f"⏭️  Ya completó encuesta: {id_aseg}")
                continue

            # Reenviar si han pasado 3 días y no ha llenado
            fecha_envio_str = control.at[idx, "Fecha Envio"]
            try:
                fecha_envio = datetime.strptime(str(fecha_envio_str), "%Y-%m-%d %H:%M")
            except:
                continue

            dias_pasados = (hoy - fecha_envio).days
            reenvios     = int(control.at[idx, "Reenvios"])

            if dias_pasados >= DIAS_REENVIO:
                log.info(f"🔁 Reenviando a {id_aseg} ({dias_pasados} días sin respuesta)")
                exito = enviar_correo(row)
                if exito:
                    control.at[idx, "Fecha Envio"] = hoy.strftime("%Y-%m-%d %H:%M")
                    control.at[idx, "Reenvios"]    = reenvios + 1
            else:
                log.info(f"⏳ Esperando: {id_aseg} ({dias_pasados}/{DIAS_REENVIO} días)")

    # Agregar nuevos al control
    if nuevos_registros:
        nuevos_df = pd.DataFrame(nuevos_registros)
        control   = pd.concat([control, nuevos_df], ignore_index=True)

    # Guardar control y generar reporte
    guardar_control(control)
    reporte_file = generar_reporte(control)
    enviar_reporte_por_correo(reporte_file)

    log.info("═══════════════ PROCESO FINALIZADO ═══════════════")



if __name__ == "__main__":
    main()