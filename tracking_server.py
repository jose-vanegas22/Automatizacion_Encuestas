from flask import Flask, request, send_file
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

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

@app.route("/tracking")
def tracking():
    id_aseg = request.args.get("id")
    init_control()  # asegurar que el archivo existe

    if id_aseg:
        try:
            df = pd.read_excel("control.xlsx")

            # Validar que existan las columnas necesarias
            for col in ["ID Asegurado", "Abrió", "Fecha Ape"]:
                if col not in df.columns:
                    df[col] = None

            # Buscar el ID en la columna correcta
            try:
                id_aseg_int = int(id_aseg)
            except ValueError:
                id_aseg_int = id_aseg  # si no es número, usar texto

            idx = df[df["ID Asegurado"] == id_aseg_int].index

            if not idx.empty:
                # Actualizar registro existente
                df.at[idx[0], "Abrió"] = True
                df.at[idx[0], "Fecha Ape"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            else:
                # Agregar nuevo registro si el ID no existe
                df = pd.concat([df, pd.DataFrame([{
                    "ID Asegurado": id_aseg_int,
                    "Abrió": True,
                    "Fecha Ape": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Estado": "Entregado"
                }])], ignore_index=True)

            df.to_excel("control.xlsx", index=False)
        except Exception as e:
            print("Error al actualizar control.xlsx:", e)

    # Devolver pixel transparente
    return send_file("pixel.png", mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
