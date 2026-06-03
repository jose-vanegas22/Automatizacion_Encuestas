import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ── Importar funciones de módulos ──
from src.utils import (
    es_dia_habil, esperar_entre_envios, lote_del_dia, lote_por_posicion,
    parse_fecha, as_bool, as_int, fecha_proximo_reenvio
)
from src.control import asegurar_columnas_control, descargar_control, subir_control
from src.polizas import descargar_polizas
from src.forms import cargar_form_prueba
from src.envio_email import enviar_correo
from src.reportes import generar_reporte, enviar_reporte_por_correo
from src.rebotes import procesar_rebotes
from src.onedrive import subir_archivo_onedrive

# ── Importar constantes de configuración ──
from config import (
    POLIZAS_FILE, CONTROL_FILE, NUM_LOTES_ENVIO, PERMITIR_ENVIOS_FIN_SEMANA,
    FROM_EMAIL, REPORTES_FOLDER, DIAS_REENVIO, MAX_REENVIOS, PROCESAR_REBOTES,
    COL_ID_POLIZAS, COL_EMAIL_POLIZAS, COL_NOMBRE_POLIZAS, COL_ID_ENCUESTAS
)

# ── Inicializar entorno y logger ──
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


def main():
    log.info("═══════════════ INICIANDO PROCESO ═══════════════")

    # Asegurar carpetas
    os.makedirs(os.path.dirname(POLIZAS_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(CONTROL_FILE), exist_ok=True)

    # 1. Descargar encuestas
    encuestas_df = cargar_form_prueba()
    encuestas = set(encuestas_df[COL_ID_ENCUESTAS].astype(str).tolist()) if encuestas_df is not None else set()

    # 2. Cargar pólizas y control
    polizas = descargar_polizas()
    control = descargar_control()
    hoy = datetime.now()
    puede_enviar = es_dia_habil(hoy) or PERMITIR_ENVIOS_FIN_SEMANA

    if not puede_enviar:
        log.info("Hoy no es día hábil. Se actualizará el control, pero no se enviarán correos ni reenvíos.")

    # 🔧 Actualizar control con encuestas nuevas
    for idx in control.index:
        id_aseg = str(control.at[idx, COL_ID_POLIZAS]).strip()
        if id_aseg in encuestas and not control.at[idx, "Lleno Encuesta"]:
            control.at[idx, "Respondió"] = True
            control.at[idx, "Lleno Encuesta"] = True
            control.at[idx, "Fecha Encuesta"] = hoy.strftime("%Y-%m-%d %H:%M")
            control.at[idx, "Estado"] = "Respondió encuesta"
            log.info(f"✅ Encuesta completada: {id_aseg}")

    # ── Lógica de envío y reenvío ──
    control = asegurar_columnas_control(control)
    lote_hoy = lote_del_dia(hoy)
    log.info(f"Lote programado para hoy: {lote_hoy}/{NUM_LOTES_ENVIO}")

    ids_en_control = set(control[COL_ID_POLIZAS].astype(str).str.strip().tolist())
    nuevos_registros = []

    for posicion, row in polizas.reset_index(drop=True).iterrows():
        id_aseg = str(row[COL_ID_POLIZAS]).strip()
        email   = str(row[COL_EMAIL_POLIZAS]).strip().lower()
        nombre  = str(row[COL_NOMBRE_POLIZAS])

        # Caso 1: ID nuevo
        if id_aseg not in ids_en_control:
            lote = lote_por_posicion(posicion)
            resultado_envio = None
            estado = "Pendiente por lote"

            if puede_enviar and lote == lote_hoy:
                resultado_envio = enviar_correo(row)
                esperar_entre_envios()
                if resultado_envio and resultado_envio["Enviado"]:
                    estado = "Enviado"
                elif resultado_envio:
                    estado = "Error de envío"

            nuevos_registros.append({
                COL_ID_POLIZAS: id_aseg,
                COL_NOMBRE_POLIZAS: nombre,
                COL_EMAIL_POLIZAS: email,
                "Lote": lote,
                "Enviado": bool(resultado_envio and resultado_envio["Enviado"]),
                "Rebotado": bool(resultado_envio and resultado_envio["Rebotado"]),
                "Entregado": bool(resultado_envio and resultado_envio["Entregado"]),
                "Reenvios": 0,
                "Fecha Envio": hoy.strftime("%Y-%m-%d %H:%M") if resultado_envio and resultado_envio["Enviado"] else "",
                "Fecha Proximo Reenvio": fecha_proximo_reenvio(hoy) if resultado_envio and resultado_envio["Enviado"] else "",
                "Estado": estado,
                "Correo Remitente": FROM_EMAIL if resultado_envio else "",
                "Error Ultimo Envio": resultado_envio.get("Error", "") if resultado_envio else ""
            })
            ids_en_control.add(id_aseg)

        # Caso 2: Ya existe → actualizar estado
        else:
            idx = control[control[COL_ID_POLIZAS] == id_aseg].index[0]
            reenvios = as_int(control.at[idx, "Reenvios"])
            fecha_envio = parse_fecha(control.at[idx, "Fecha Envio"])
            fecha_proxima = parse_fecha(control.at[idx, "Fecha Proximo Reenvio"])

            if puede_enviar and not as_bool(control.at[idx, "Lleno Encuesta"]):
                if reenvios >= MAX_REENVIOS:
                    control.at[idx, "Estado"] = "Máximo de reenvíos alcanzado"
                    continue

                if fecha_proxima is None and fecha_envio is not None:
                    fecha_proxima = fecha_envio + timedelta(days=DIAS_REENVIO)
                    control.at[idx, "Fecha Proximo Reenvio"] = fecha_proxima.strftime("%Y-%m-%d %H:%M")

                if fecha_proxima and hoy >= fecha_proxima:
                    resultado_envio = enviar_correo(row)
                    esperar_entre_envios()
                    if resultado_envio and resultado_envio["Enviado"]:
                        control.at[idx, "Fecha Envio"] = hoy.strftime("%Y-%m-%d %H:%M")
                        control.at[idx, "Reenvios"] = reenvios + 1
                        control.at[idx, "Fecha Proximo Reenvio"] = (
                            fecha_proximo_reenvio(hoy) if reenvios + 1 < MAX_REENVIOS else ""
                        )
                        control.at[idx, "Estado"] = "Reenviado"
                    else:
                        control.at[idx, "Estado"] = "Error de envío"

    # Agregar nuevos al control
    if nuevos_registros:
        import pandas as pd
        nuevos_df = pd.DataFrame(nuevos_registros)
        control = pd.concat([control, nuevos_df], ignore_index=True)
        control = asegurar_columnas_control(control)

    # Procesar rebotes si está activado
    if PROCESAR_REBOTES:
        control = procesar_rebotes(control)

    # Subir control y generar reporte
    subir_control(control)
    reporte_file = generar_reporte(control)
    subir_archivo_onedrive(reporte_file, REPORTES_FOLDER)
    enviar_reporte_por_correo(reporte_file)

    log.info("═══════════════ PROCESO FINALIZADO ═══════════════")


if __name__ == "__main__":
    main()
