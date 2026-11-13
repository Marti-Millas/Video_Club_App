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
    """Configura el context SSL per requerir certificats de client (mTLS)"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="certs/server_cert.pem", keyfile="certs/server_key.pem")
    context.load_verify_locations(cafile="certs/CA_cert.pem")
    context.verify_mode = ssl.CERT_REQUIRED
    return context

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    addr = writer.get_extra_info('peername')
    
    # Obtenim el nom del client des del seu certificat
    peercert = writer.get_extra_info('peercert')
    client_name = "Desconegut"
    if peercert:
        for sub in peercert.get('subject', ()):
            for key, value in sub:
                if key == 'commonName':
                    client_name = value
                    
    logging.info(f"Connexió TLS establerta amb {addr} (Certificat: {client_name})")
    
    try:
        while True:
            # 1. Llegim l'encapçalament amb la mida i el hash
            header_bytes = await reader.readuntil(b'\n')
            if not header_bytes:
                break 
            
            header = json.loads(header_bytes.decode('utf-8'))
            body_length = header.get("length", 0)
            expected_hash = header.get("sha256")
            
            # 2. Llegim exactament els bytes del cos
            body_bytes = await reader.readexactly(body_length)
            
            # 3. VERIFICACIÓ D'INTEGRITAT SHA-256
            actual_hash = hashlib.sha256(body_bytes).hexdigest()
            if actual_hash != expected_hash:
                logging.error(f"Error d'integritat: SHA-256 invàlid de {client_name}")
                response_dict = {"status": "error", "message": "Integritat compromesa (SHA256)"}
            else:
                request_str = body_bytes.decode('utf-8')
                request = json.loads(request_str)
                logging.info(f"Petició íntegra rebuda: {request.get('action')}")
                
                # Processem la petició en un fil secundari
                response_dict = await asyncio.to_thread(route_request, request.get('action'), request.get('data', {}))
            
            # 4. Construïm i enviem la resposta segura
            res_body_bytes = json.dumps(response_dict).encode('utf-8')
            res_hash = hashlib.sha256(res_body_bytes).hexdigest()
            res_header = json.dumps({"length": len(res_body_bytes), "sha256": res_hash}).encode('utf-8') + b'\n'
            
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