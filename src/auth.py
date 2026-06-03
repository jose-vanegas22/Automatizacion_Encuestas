import os
import msal
import logging
from config import PROCESAR_REBOTES
log = logging.getLogger(__name__)


def get_token():
    CLIENT_ID = os.getenv("CLIENT_ID")
    TENANT_ID = os.getenv("TENANT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    # Si se provee CLIENT_SECRET, usar Client Credentials (aplicación confidencial)
    if CLIENT_SECRET:
        app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}"
        )
        # Usamos el scope .default para los permisos de la app
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        return result

    # Modo interactivo/developer: mantener comportamiento anterior con cache y login interactivo
    cache = msal.SerializableTokenCache()
    if os.path.exists("token_cache.json"):
        with open("token_cache.json", "r") as f:
            cache.deserialize(f.read())

    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=cache
    )

    accounts = app.get_accounts()
    scopes = ["Files.ReadWrite", "Mail.Send", "User.Read"]
    if PROCESAR_REBOTES:
        scopes.append("Mail.Read")

    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result:
            return result

    result = app.acquire_token_interactive(scopes=scopes)
    if result:
        with open("token_cache.json", "w") as f:
            f.write(cache.serialize())
    return result