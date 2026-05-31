from flask import Flask, request, send_file
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Inicializar control.xlsx si no existe
def init_control():
    if not os.path.exists("control.xlsx"):
        df = pd.DataFrame(columns=["ID", "Abrio", "Fecha Apertura"])
        df.to_excel("control.xlsx", index=False)

@app.route("/tracking")
def tracking():
    id_aseg = request.args.get("id")
    init_control()  # asegurar que el archivo existe

    if id_aseg:
        try:
            df = pd.read_excel("control.xlsx")

            # Si faltan columnas, las agregamos
            for col in ["ID", "Abrio", "Fecha Apertura"]:
                if col not in df.columns:
                    df[col] = None

            idx = df[df["ID"] == id_aseg].index
            if not idx.empty:
                df.at[idx[0], "Abrio"] = True
                df.at[idx[0], "Fecha Apertura"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            else:
                # Si el ID no existe, lo agregamos como nuevo registro
                df = pd.concat([df, pd.DataFrame([{
                    "ID": id_aseg,
                    "Abrio": True,
                    "Fecha Apertura": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])], ignore_index=True)

            df.to_excel("control.xlsx", index=False)
        except Exception as e:
            print("Error al actualizar control.xlsx:", e)

    # Devolver pixel transparente
    return send_file("pixel.png", mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
