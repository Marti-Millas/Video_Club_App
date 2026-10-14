import socket
import json
import logging
from server.router import route_request

# Configuració per veure missatges a la terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Port on escoltarà el servidor

def handle_request(request_data):
    try:
        request = json.loads(request_data)
        logging.info(f"Petició rebuda: {request}")
        
        action = request.get('action')
        data = request.get('data', {})
        
        # Deleguem al router que acabem de fer!
        response = route_request(action, data)
        return response
        
    except json.JSONDecodeError:
        return {"status": "error", "message": "Format de petició invàlid (no és JSON)", "data": None}
    except Exception as e:
        return {"status": "error", "message": f"Error del servidor: {str(e)}", "data": None}

def start_server():
    """Inicia el servidor TCP"""
    # Creem un socket IPv4 i TCP 
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen() # Comencem a escoltar connexions
        logging.info(f"Servidor escoltant a {HOST}:{PORT}...")

        while True:
            # Esperem que es connecti un client (bloquejant)
            conn, addr = s.accept()
            with conn:
                logging.info(f"Connectat amb {addr}")
                
                # Llegim les dades que envia el client (màxim 1024 bytes de moment)
                data = conn.recv(1024)
                if not data:
                    break # Si no hi ha dades, el client ha tancat
                
                # Descodifiquem de bytes a string i processem
                request_str = data.decode('utf-8')
                
                # Cridem al router per processar-ho
                response_dict = handle_request(request_str)
                
                # Convertim el diccionari de resposta a JSON i després a bytes per enviar
                response_bytes = json.dumps(response_dict).encode('utf-8')
                conn.sendall(response_bytes)

if __name__ == "__main__":
    start_server()