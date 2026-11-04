import asyncio
import json
import logging
from server.router import route_request

# Configuració per veure missatges a la terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = '127.0.0.1'
PORT = 65432

async def handle_request(request_data):
    try:
        request = json.loads(request_data)
        logging.info(f"Petició rebuda: {request['action']}")
        
        action = request.get('action')
        data = request.get('data', {})
        
        # EL REPTE OPCIONAL DE LA PAC: 
        # Enviem la petició de la base de dades síncrona a un fil secundari 
        # perquè no bloquegi els altres clients.
        response = await asyncio.to_thread(route_request, action, data)
        return response
        
    except json.JSONDecodeError:
        return {"status": "error", "message": "Format de petició invàlid (no és JSON)", "data": None}
    except Exception as e:
        return {"status": "error", "message": f"Error del servidor: {str(e)}", "data": None}

async def handle_client(reader, writer):
    """Funció que gestiona el cicle de vida d'un client de manera asíncrona"""
    addr = writer.get_extra_info('peername')
    logging.info(f"Connectat amb {addr}")
    
    try:
        while True:
            # Llegim les dades de forma asíncrona (no bloquejant)
            data = await reader.read(1024)
            if not data:
                break # Si no hi ha dades, el client ha tancat amigablement
            
            request_str = data.decode('utf-8')
            response_dict = await handle_request(request_str)
            
            # Responem
            response_bytes = json.dumps(response_dict).encode('utf-8')
            writer.write(response_bytes)
            await writer.drain() # Ens assegurem que s'ha enviat tot
            
    except ConnectionResetError:
        logging.warning(f"El client {addr} s'ha desconnectat de cop.")
    except Exception as e:
        logging.error(f"Error inesperat amb el client {addr}: {e}")
    finally:
        # Prevenim fuites de memòria (Resource leaks) tancant bé la connexió
        logging.info(f"Tancant connexió amb {addr}")
        writer.close()
        await writer.wait_closed()

async def start_server():
    """Inicia el servidor TCP Asíncron"""
    server = await asyncio.start_server(handle_client, HOST, PORT)
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f"Servidor AsyncIO escoltant a {addrs}...")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logging.info("Servidor apagat manualment.")