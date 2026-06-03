import time
import logging
from datetime import datetime, timedelta
import pandas as pd

from config import DIAS_REENVIO, EMAIL_SEND_DELAY_SECONDS, FECHA_INICIO_CAMPANA, LOTE_ENVIO_HOY, NUM_LOTES_ENVIO
log = logging.getLogger(__name__)

# Archivo util.py con funciones auxiliares para manejo de fechas, lotes y conversiones

def es_dia_habil(fecha):
    return fecha.weekday() < 5


def contar_dias_habiles(inicio, fin):
    dias = 0
    actual = inicio.date()
    fin_date = fin.date()
    while actual <= fin_date:
        if actual.weekday() < 5:
            dias += 1
        actual += timedelta(days=1)
    return dias


def lote_del_dia(fecha):
    if LOTE_ENVIO_HOY:
        return int(LOTE_ENVIO_HOY)

    if FECHA_INICIO_CAMPANA:
        inicio = datetime.strptime(FECHA_INICIO_CAMPANA, "%Y-%m-%d")
    else:
        inicio = fecha

    dias_habiles = contar_dias_habiles(inicio, fecha)
    return ((max(dias_habiles, 1) - 1) % NUM_LOTES_ENVIO) + 1


def lote_por_posicion(posicion):
    return (posicion % NUM_LOTES_ENVIO) + 1


def fecha_proximo_reenvio(fecha):
    return (fecha + timedelta(days=DIAS_REENVIO)).strftime("%Y-%m-%d %H:%M")


def esperar_entre_envios():
    if EMAIL_SEND_DELAY_SECONDS <= 0:
        return
    log.info(f"Esperando {EMAIL_SEND_DELAY_SECONDS:g} segundos antes del siguiente envio.")
    time.sleep(EMAIL_SEND_DELAY_SECONDS)


def parse_fecha(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return None

    if isinstance(valor, pd.Timestamp):
        return valor.to_pydatetime()

    if isinstance(valor, datetime):
        return valor

    texto = str(valor).strip()
    for fmt in (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue

    fecha = pd.to_datetime(texto, errors="coerce")
    if pd.isna(fecha):
        return None
    return fecha.to_pydatetime()


def as_bool(valor):
    if isinstance(valor, bool):
        return valor
    if pd.isna(valor):
        return False
    return str(valor).strip().lower() in ("true", "1", "si", "sí", "yes")


def as_int(valor, default=0):
    try:
        if pd.isna(valor) or str(valor).strip() == "":
            return default
        return int(float(valor))
    except (TypeError, ValueError):
        return default