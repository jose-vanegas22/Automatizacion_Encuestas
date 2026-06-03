import os
from dotenv import load_dotenv

load_dotenv()

# SendGrid
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL       = os.getenv("FROM_EMAIL")
FROM_NAME        = os.getenv("FROM_NAME")
REPORT_EMAIL     = os.getenv("REPORT_EMAIL")

# Encuesta
SURVEY_BASE_URL  = os.getenv("SURVEY_BASE_URL")  # el ID del asegurado se concatena al final

# Google Sheets (respuestas de la encuesta)
GOOGLE_SHEET_ID  = os.getenv("GOOGLE_SHEET_ID")

# Archivos
POLIZAS_FILE = os.getenv("BASE_DATOS_LOCAL_FILE", "data/BasesDatos.xlsx")
CONTROL_FILE = "data/control.xlsx"
ONEDRIVE_FOLDER = os.getenv("ONEDRIVE_FOLDER", "Encuestas")
REPORTES_FOLDER = os.getenv("REPORTES_FOLDER", f"{ONEDRIVE_FOLDER}/Reportes_Encuestas")
BASE_DATOS_FILE_NAME = os.getenv("BASE_DATOS_FILE_NAME", "BasesDatos.xlsx")
ENCUESTAS_FILE_NAME = os.getenv(
    "ENCUESTAS_FILE_NAME",
    "ENCUESTA DE _SATISFACCIÓN ZENGU SEGUROS.xlsx",
)
CREDS_FILE   = "credentials.json"  # lo generamos cuando configuremos Google

# Lógica de envíos y reenvíos
NUM_LOTES_ENVIO = int(os.getenv("NUM_LOTES_ENVIO", "10"))
DIAS_REENVIO = int(os.getenv("DIAS_REENVIO", "14"))
MAX_REENVIOS = int(os.getenv("MAX_REENVIOS", "2"))
EMAIL_SEND_DELAY_SECONDS = float(os.getenv("EMAIL_SEND_DELAY_SECONDS", "5"))
FECHA_INICIO_CAMPANA = os.getenv("FECHA_INICIO_CAMPANA", "")
LOTE_ENVIO_HOY = os.getenv("LOTE_ENVIO_HOY", "")
PERMITIR_ENVIOS_FIN_SEMANA = os.getenv("PERMITIR_ENVIOS_FIN_SEMANA", "false").lower() == "true"
PROCESAR_REBOTES = os.getenv("PROCESAR_REBOTES", "false").lower() == "true"

# Columnas que usamos del Excel de pólizas
COL_ID_POLIZAS = "ID Asegurado"
COL_NOMBRE_POLIZAS = "Asegurado"
COL_EMAIL_POLIZAS = "Email"

# Columnas que usamos del Excel de respuestas
COL_ID_ENCUESTAS = "# de Identificación (Sin puntos):"
COL_NOMBRE_ENCUESTAS = "Nombre Completo:"
COL_EMAIL_ENCUESTAS = "Correo electrónico"

RESPUESTAS_FILE = r"C:\Users\vaneg\OneDrive - CGA\RESPUESTAS ENCUESTA ZENGU\respuestas.xlsx"
COL_ID_ENCUESTA  = "Número de identificación (Sin puntos)"

MS_EMAIL    = os.getenv("MS_EMAIL")
MS_PASSWORD = os.getenv("MS_PASSWORD")

