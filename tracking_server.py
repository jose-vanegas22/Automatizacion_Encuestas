from flask import Flask, request, send_file, redirect
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

SURVEY_BASE_URL = os.getenv("SURVEY_BASE_URL")


# Inicializar control.xlsx si no existe
def init_control():
    if not os.path.exists("control.xlsx"):
        df = pd.DataFrame(columns=[
            "ID Asegurado", "Asegurado", "Email",
            "Fecha Env Enviado", "Rebotado", "Entregado",
            "Abrió", "Fecha Ape", "Respondió",
            "Lleno Enc", "Fecha Enc", "Reenvíos", "Estado"
        ])
        df.to_excel("control.xlsx", index=False)

# Pixel de apertura
@app.route("/tracking")
def tracking():
    id_aseg = request.args.get("id")
    init_control()  # asegurar que el archivo existe

    if id_aseg:
        try:
            df = pd.read_excel("control.xlsx")

            for col in ["ID Asegurado", "Abrió", "Fecha Ape"]:
                if col not in df.columns:
                    df[col] = None

            try:
                id_aseg_int = int(id_aseg)
            except ValueError:
                id_aseg_int = id_aseg

            idx = df[df["ID Asegurado"] == id_aseg_int].index

            if not idx.empty:
                df.at[idx[0], "Abrió"] = True
                df.at[idx[0], "Fecha Ape"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            else:
                df = pd.concat([df, pd.DataFrame([{
                    "ID Asegurado": id_aseg_int,
                    "Abrió": True,
                    "Fecha Ape": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Estado": "Entregado"
                }])], ignore_index=True)

            df.to_excel("control.xlsx", index=False)
        except Exception as e:
            print("Error al actualizar control.xlsx:", e)

    return send_file("pixel.png", mimetype="image/png")

# Clic en el botón de encuesta
@app.route("/click")
def click():
    id_aseg = request.args.get("id")
    init_control()

    if id_aseg:
        try:
            df = pd.read_excel("control.xlsx")
            idx = df[df["ID Asegurado"] == id_aseg].index
            if not idx.empty:
                df.at[idx[0], "Respondió"] = True
                df.at[idx[0], "Fecha Enc"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                df.to_excel("control.xlsx", index=False)
        except Exception as e:
            print("Error al actualizar control.xlsx:", e)

    return redirect(SURVEY_BASE_URL, code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
