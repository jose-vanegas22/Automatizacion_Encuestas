import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

def test_envio():
    # Leer template
    with open("templates/email.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Reemplazar variables con datos de prueba
    html = html.replace("{{NOMBRE}}", "Jose")
    html = html.replace("{{POLIZA}}", "POL-2026-001")
    html = html.replace("{{RAMO}}", "Automóvil")
    html = html.replace("{{ASEGURADORA}}", "Seguros XYZ")
    html = html.replace("{{INICIO}}", "2026-01-01")
    html = html.replace("{{FIN}}", "2027-01-01")
    html = html.replace("{{SURVEY_LINK}}", "https://google.com")  # link de prueba
    html = html.replace("{{ID}}", "123456789")

    message = Mail(
        from_email=(os.getenv("FROM_EMAIL"), os.getenv("FROM_NAME")),
        to_emails=os.getenv("FROM_EMAIL"),  # te lo envías a ti mismo
        subject="✅ Prueba — Sistema de encuestas pólizas",
        html_content=html
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(f"✅ Correo enviado! Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_envio()