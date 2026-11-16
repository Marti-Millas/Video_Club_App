import socket
import json
import logging
from server.router import route_request

# Configurem el registre (log) per veure a la terminal què passa sense fer servir simples 'print'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = '127.0.0.1'  # Localhost: El servidor només escolta connexions d'aquest mateix ordinador
PORT = 65432        # Port on escoltarà el servidor (ha de ser > 1024 per no requerir permisos d'administrador)

def handle_request(request_data):
    """S'encarrega de transformar el text pla a JSON i extreure'n l'acció i les dades."""
    try:
        # 1. Converteix l'string rebut en un diccionari de Python
        request = json.loads(request_data)
        logging.info(f"Petició rebuda: {request}")
        
        # 2. Extreu el nom de l'acció i els paràmetres
        action = request.get('action')
        data = request.get('data', {})
        
        # 3. CRIDA AL ROUTER: No processa res, només ho passa a la següent capa
        response = route_request(action, data)
        return response
        
    except json.JSONDecodeError:
        return {"status": "error", "message": "Format de petició invàlid (no és JSON)", "data": None}
    except Exception as e:
        return {"status": "error", "message": f"Error del servidor: {str(e)}", "data": None}

def start_server():
    """Inicia el servidor TCP clàssic (síncron)"""
    # socket.AF_INET = Especifica que farem servir adreces IPv4
    # socket.SOCK_STREAM = Especifica que el protocol serà TCP (orientat a connexió i fiable)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        
        # Vinculem el socket a la IP i Port especificats
        s.bind((HOST, PORT))
        
        # Posem el socket en mode escolta (esperant trucades)
        s.listen() 
        logging.info(f"Servidor escoltant a {HOST}:{PORT}...")

        while True:
            # .accept() BLOQUEJA el programa fins que un client es connecta
            conn, addr = s.accept()
            with conn:
                logging.info(f"Connectat amb {addr}")
                
                # Llegim les dades que envia el client (en paquets de màxim 1024 bytes)
                data = conn.recv(1024)
                if not data:
                    break # Si data està buit, el client ha tancat la connexió
                
                # DECODIFICACIÓ: Passem de Bytes (zeros i uns de la xarxa) a text (String UTF-8)
                request_str = data.decode('utf-8')
                
                # Processem la petició a la funció de dalt
                response_dict = handle_request(request_str)
                
                # CODIFICACIÓ: Transformem el diccionari Python a JSON, i de JSON a Bytes per enviar per la xarxa
                response_bytes = json.dumps(response_dict).encode('utf-8')
                conn.sendall(response_bytes)

if __name__ == "__main__":
    start_server()
