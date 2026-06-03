import os
import requests
import logging

from config import ONEDRIVE_FOLDER
from src.auth import get_token
log = logging.getLogger(__name__)

def onedrive_path(*parts):
    return "/".join(str(part).strip("/") for part in parts if str(part).strip("/"))


def graph_root_path(drive_id, *parts, action="content"):
    path = requests.utils.quote(onedrive_path(*parts), safe="/")
    return f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path}:/{action}"


def obtener_drive_id(headers):
    drives_resp = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers)
    if drives_resp.status_code != 200:
        log.error(f"Error obteniendo drive: {drives_resp.status_code} {drives_resp.text}")
        return None
    return drives_resp.json().get("id")


def buscar_item_en_carpeta(headers, drive_id, folder_path, filename):
    folder_url = graph_root_path(drive_id, folder_path, action="children")
    folder_resp = requests.get(folder_url, headers=headers)
    if folder_resp.status_code != 200:
        log.error(f"No se pudo leer la carpeta {folder_path}: {folder_resp.status_code} {folder_resp.text}")
        return None

    expected_name = filename.lower()
    expected_stem = os.path.splitext(expected_name)[0]
    for item in folder_resp.json().get("value", []):
        item_name = item.get("name", "")
        item_name_lower = item_name.lower()
        item_stem = os.path.splitext(item_name_lower)[0]
        if item_name_lower == expected_name or item_stem == expected_stem:
            return item

    return None


def asegurar_carpeta_onedrive(headers, drive_id, folder_path):
    parent_path = ""
    for folder_name in onedrive_path(folder_path).split("/"):
        if not folder_name:
            continue

        children_url = (
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
            if not parent_path
            else graph_root_path(drive_id, parent_path, action="children")
        )
        children_resp = requests.get(children_url, headers=headers)
        if children_resp.status_code != 200:
            log.error(f"No se pudo leer la carpeta {parent_path or '/'}: {children_resp.status_code} {children_resp.text}")
            return False

        folder = next(
            (
                item for item in children_resp.json().get("value", [])
                if item.get("name", "").lower() == folder_name.lower() and "folder" in item
            ),
            None,
        )
        if not folder:
            create_resp = requests.post(
                children_url,
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "name": folder_name,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "fail",
                },
            )
            if create_resp.status_code not in [200, 201]:
                log.error(f"No se pudo crear la carpeta {folder_name}: {create_resp.status_code} {create_resp.text}")
                return False

        parent_path = onedrive_path(parent_path, folder_name)

    return True


def subir_archivo_onedrive(local_file, folder_path=ONEDRIVE_FOLDER):
    result = get_token()
    if not result or "access_token" not in result:
        log.error("No se pudo obtener token para subir archivo a OneDrive")
        return False

    headers = {"Authorization": f"Bearer {result['access_token']}"}
    drive_id = obtener_drive_id(headers)
    if not drive_id:
        return False

    if not asegurar_carpeta_onedrive(headers, drive_id, folder_path):
        return False

    filename = os.path.basename(local_file)
    with open(local_file, "rb") as f:
        file_content = f.read()

    upload_url = graph_root_path(drive_id, folder_path, filename, action="content")
    r = requests.put(upload_url, headers=headers, data=file_content)
    if r.status_code in [200, 201]:
        log.info(f"Archivo guardado en OneDrive ({folder_path}/{filename})")
        return True

    log.error(f"Error guardando archivo en OneDrive: {r.status_code} {r.text}")
    return False