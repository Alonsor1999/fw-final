import os
import uuid
import base64
import config
from utils.helpers import decodificar_header

def extraer_info_mensaje(service, mensaje_id):
    mensaje = service.users().messages().get(userId='me', id=mensaje_id, format='full').execute()

    headers = mensaje['payload'].get('headers', [])
    asunto = remitente = ""
    for header in headers:
        if header['name'] == 'Subject':
            asunto = header['value']
        elif header['name'] == 'From':
            remitente = header['value']

    cuerpo = ""
    partes = mensaje['payload'].get('parts', [])
    for parte in partes:
        if parte['mimeType'] == 'text/plain':
            data = parte['body'].get('data')
            if data:
                cuerpo = base64.urlsafe_b64decode(data.encode()).decode(errors="ignore")

    return asunto, remitente, cuerpo


def descargar_adjuntos(service, mensaje_id, carpeta_destino):
    mensaje = service.users().messages().get(userId='me', id=mensaje_id).execute()
    partes = mensaje['payload'].get('parts', [])

    for parte in partes:
        if parte['filename'] and parte['body'] and 'attachmentId' in parte['body']:
            att_id = parte['body']['attachmentId']
            att = service.users().messages().attachments().get(userId='me', messageId=mensaje_id, id=att_id).execute()
            data = base64.urlsafe_b64decode(att['data'].encode())
            nombre_unico = f"{uuid.uuid4()}_{parte['filename'].replace(' ', '_')}"
            ruta = os.path.join(carpeta_destino, nombre_unico)
            with open(ruta, "wb") as f:
                f.write(data)
