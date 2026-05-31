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
POLIZAS_FILE = "data/polizas.xlsx"
CONTROL_FILE = "data/control.xlsx"
CREDS_FILE   = "credentials.json"  # lo generamos cuando configuremos Google

# Lógica de reenvíos
DIAS_REENVIO = 3  # reenviar si no ha llenado la encuesta en X días

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