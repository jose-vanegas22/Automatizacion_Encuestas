from flask import Flask, request, send_file
import pandas as pd
from datetime import datetime

app = Flask(__name__)

@app.route("/tracking")
def tracking():
    id_aseg = request.args.get("id")
    if id_aseg:
        # Abrir control.xlsx y marcar Abrio=True
        df = pd.read_excel("control.xlsx")
        idx = df[df["ID"] == id_aseg].index
        if not idx.empty:
            df.at[idx[0], "Abrio"] = True
            df.at[idx[0], "Fecha Apertura"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            df.to_excel("control.xlsx", index=False)

    # Devolver una imagen transparente 1x1
    return send_file("pixel.png", mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
