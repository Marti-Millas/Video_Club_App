import asyncio
import json
import logging
import ssl
import hashlib
from typing import Dict, Any
from server.router import route_request

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = '127.0.0.1'
PORT = 65432

def get_ssl_context():
    """Configura el context SSL per requerir certificats de client (mTLS). Això és 'el vigilant'."""
    # CLIENT_AUTH: Li diem al servidor que demani identificar-se a qui es connecti.
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    # El servidor carrega el seu propi DNI (server_cert) i la clau per obrir missatges (server_key)
    context.load_cert_chain(certfile="certs/server_cert.pem", keyfile="certs/server_key.pem")
    
    # Càrrega de la CA: Li diem "Només acceptis DNIs signats per aquesta policia"
    context.load_verify_locations(cafile="certs/CA_cert.pem")
    
    # CERT_REQUIRED: Si algú ve sense certificat, se li tanca la porta directament.
    context.verify_mode = ssl.CERT_REQUIRED
    return context

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    addr = writer.get_extra_info('peername')
    
    # Com que tenim mTLS, podem llegir les dades del "DNI" de la persona connectada
    peercert = writer.get_extra_info('peercert')
    client_name = "Desconegut"
    if peercert:
        for sub in peercert.get('subject', ()):
            for key, value in sub:
                if key == 'commonName': # Agafem el nom del client (ex: client1)
                    client_name = value
                    
    logging.info(f"Connexió TLS establerta amb {addr} (Certificat: {client_name})")
    
    try:
        while True:
            # 1. FRAMING: Llegim primer l'encapçalament (Header) fins al salt de línia (\n)
            header_bytes = await reader.readuntil(b'\n')
            if not header_bytes:
                break 
            
            # Desempaquetem l'encapçalament per saber quants bytes vénen i quin és el hash original
            header = json.loads(header_bytes.decode('utf-8'))
            body_length = header.get("length", 0)
            expected_hash = header.get("sha256")
            
            # 2. Llegim EXACTAMENT la quantitat de bytes que diu l'encapçalament (el Cos)
            body_bytes = await reader.readexactly(body_length)
            
            # 3. VERIFICACIÓ D'INTEGRITAT SHA-256 (El precinte de garantia)
            actual_hash = hashlib.sha256(body_bytes).hexdigest()
            
            if actual_hash != expected_hash:
                # Si no coincideix, el paquet ha estat manipulat
                logging.error(f"Error d'integritat: SHA-256 invàlid de {client_name}")
                response_dict = {"status": "error", "message": "Integritat compromesa (SHA256)"}
            else:
                # Si coincideixen, el processem passant-ho al fil secundari
                request_str = body_bytes.decode('utf-8')
                request = json.loads(request_str)
                logging.info(f"Petició íntegra rebuda: {request.get('action')}")
                
                response_dict = await asyncio.to_thread(route_request, request.get('action'), request.get('data', {}))
            
            # 4. Construïm i enviem la resposta segura fent el mateix procés
            res_body_bytes = json.dumps(response_dict).encode('utf-8')
            res_hash = hashlib.sha256(res_body_bytes).hexdigest() # Generem el nostre precinte
            
            res_header = json.dumps({"length": len(res_body_bytes), "sha256": res_hash}).encode('utf-8') + b'\n'
            
            # Enviem Encapçalament + Cos
            writer.write(res_header + res_body_bytes)
            await writer.drain()
            
    except asyncio.IncompleteReadError:
        logging.warning(f"El client {client_name} ha tancat la connexió abruptament.")
    except Exception as e:
        logging.error(f"Error inesperat amb el client {client_name}: {e}")
    finally:
        logging.info(f"Tancant connexió amb {client_name}")
        writer.close()
        await writer.wait_closed()

async def start_server() -> None:
    ssl_context = get_ssl_context()
    
    # Això converteix el sòcol TCP normal en un Túnel TLS xifrat.
    server = await asyncio.start_server(handle_client, HOST, PORT, ssl=ssl_context)
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f"Servidor AsyncIO (TLS) escoltant a {addrs}...")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logging.info("Servidor apagat manualment.")
