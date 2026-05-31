import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()  # Esto carga tu .env
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

message = Mail(
    from_email='asistenteproyectos@cgaestrate5ica.com',
    to_emails='destinatario@example.com',
    subject='Prueba integración SendGrid',
    html_content='<strong>Hola Jose, este es un correo de prueba con tracking activado.</strong>'
)

try:
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(response.status_code)
except Exception as e:
    print(e)