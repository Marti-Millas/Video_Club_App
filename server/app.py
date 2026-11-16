import asyncio
import json
import logging
from typing import Dict, Any
from server.router import route_request

# Configuració per veure els logs a la terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = '127.0.0.1'
PORT = 65432

async def handle_request(request_data: str) -> Dict[str, Any]:
    """Tracta el paquet rebut i el passa al router per processar."""
    try:
        request = json.loads(request_data)
        logging.info(f"Petició rebuda: {request['action']}")
        
        action = request.get('action')
        data = request.get('data', {})
        
        # EL REPTE OPCIONAL DE LA PAC 2: 
        # La base de dades SQL (SQLite/SQLAlchemy) sol ser "síncrona" (bloqueja). 
        # Per evitar que bloquejar la base de dades aturi tota la xarxa, enviem la tasca de BD 
        # a un fil (Thread) secundari. El servidor pot seguir atenent altres clients!
        response = await asyncio.to_thread(route_request, action, data)
        return response
        
    except json.JSONDecodeError:
        return {"status": "error", "message": "Format de petició invàlid (no és JSON)", "data": None}
    except Exception as e:
        return {"status": "error", "message": f"Error del servidor: {str(e)}", "data": None}

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Funció clau de la PAC 2. Gestiona el cicle de vida d'UN client.
    Cada cop que es connecti un nou client, asyncio crearà una instància paral·lela d'aquesta funció.
    """
    addr = writer.get_extra_info('peername') # Obtenim la IP i Port del client connectat
    logging.info(f"Connectat amb {addr}")
    
    try:
        while True:
            # LLEGIR ASÍNCRONAMENT: La clau és l''await'. 
            # El servidor no es queda aturat esperant! Es va a atendre un altre client
            # i quan aquest client demani alguna cosa, ja tornarà.
            data = await reader.read(1024)
            if not data:
                break # Si rebem un paquet buit, vol dir que el client ha fet "Desconnectar"
            
            request_str = data.decode('utf-8')
            
            # Passem la petició a processar (a dalt)
            response_dict = await handle_request(request_str)
            
            # Responem convertint a bytes
            response_bytes = json.dumps(response_dict).encode('utf-8')
            writer.write(response_bytes) # Preparem les dades al buffer de sortida
            await writer.drain() # ESPEREM que les dades surtin efectivament pel cable
            
    except ConnectionResetError:
        logging.warning(f"El client {addr} s'ha desconnectat de cop.")
    except Exception as e:
        logging.error(f"Error inesperat amb el client {addr}: {e}")
    finally:
        # Quan trenquem el 'while' (el client marxa), hem de tancar les canonades.
        # Això evita fuites de memòria ("resource leaks") que farien petar el servidor.
        logging.info(f"Tancant connexió amb {addr}")
        writer.close()
        await writer.wait_closed()

async def start_server() -> None:
    """Inicia el servidor TCP Asíncron (substitueix l'antic bind(), listen(), accept() manual)"""
    # Aquesta única línia obre el port 65432 i li diu: 
    # "Cada cop que algú truqui a la porta, engega un handle_client nou per a ell"
    server = await asyncio.start_server(handle_client, HOST, PORT)
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f"Servidor AsyncIO escoltant a {addrs}...")

    # Mantenim el servidor obert i escoltant indefinidament
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        # Iniciem l'aplicació asíncrona creant un Event Loop
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logging.info("Servidor apagat manualment.")
