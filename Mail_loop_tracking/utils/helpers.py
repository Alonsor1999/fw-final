from email.header import decode_header

def decodificar_header(valor):
    partes = decode_header(valor)
    resultado = ""
    for parte, cod in partes:
        if isinstance(parte, bytes):
            resultado += parte.decode(cod or 'utf-8', errors='ignore')
        else:
            resultado += parte
    return resultado