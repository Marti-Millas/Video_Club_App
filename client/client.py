import socket
import json

HOST = '127.0.0.1' # La IP on ens connectem (localhost, el nostre propi ordinador)
PORT = 65432       # El port exacte on el servidor està escoltant

def send_request(action, data=None):
    """Funció per enviar una petició JSON al servidor i esperar resposta"""
    
    # 1. Construïm el paquet de dades amb l'estructura que demana el nostre protocol
    request_dict = {
        "action": action,
        "data": data or {}
    }
    
    # Convertim a JSON (text pla) i després a bytes (zeros i uns codificats en UTF-8)
    # Això és obligatori perquè per la xarxa només hi poden viatjar 'bytes', no diccionaris de Python.
    request_bytes = json.dumps(request_dict).encode('utf-8')
    
    # AF_INET = Utilitzarem adreces de xarxa IPv4.
    # SOCK_STREAM = Utilitzarem protocol TCP (orientat a connexió, assegura que els paquets arribin en ordre).
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Intentem connectar-nos al servidor
            s.connect((HOST, PORT))
            
            # Enviem tota la cadena de bytes de cop
            s.sendall(request_bytes)
            
            # Esperem la resposta del servidor (bloquegem l'execució fins que rebem dades).
            # 1024 és la mida del buffer (el màxim de bytes que llegirem de cop).
            response_bytes = s.recv(1024)
            
            # Descodifiquem els bytes rebuts per tornar-los a format text (String UTF-8)
            response_str = response_bytes.decode('utf-8')
            
            # Transformem el string JSON a diccionari Python i el retornem perquè l'app el llegeixi
            return json.loads(response_str)
            
        except ConnectionRefusedError:
            print("Error: No es pot connectar al servidor. Està en marxa?")
            return None
        except Exception as e:
            print(f"Error de connexió: {e}")
            return None

def main():
    print("--- Client Video Club ---")
    
    # Bucle infinit per mantenir el menú obert fins que l'usuari triï "0"
    while True:
        print("\nOpcions:")
        print("1. Provar connexió ")
        print("2. Veure tots els jocs ")
        print("3. Afegir un joc ")
        print("4. Esborrar un joc ")
        print("5. Afegir una plataforma (Necessari abans de crear un joc)")
        print("0. Sortir")
        
        opcio = input("Tria una opció: ")
        
        if opcio == '1':
            resposta = send_request("ping", {"missatge": "Hola servidor!"})
            print("\nResposta del servidor:", json.dumps(resposta, indent=2))
            
        elif opcio == '2':
            resposta = send_request("list_games") 
            if resposta and resposta.get("status") == "success":
                print("\n--- LLISTA DE JOCS ---")
                # Iterem sobre l'array "data" del JSON que ens ha tornat el servidor
                for game in resposta.get("data", []):
                    print(f"- ID: {game.get('id')} | Títol: {game.get('title')} | Preu: {game.get('price')}€")
            else:
                print(f"\nError: {resposta.get('message')}")
                
        elif opcio == '3':
            titol = input("Títol del joc: ")
            preu = float(input("Preu: "))
            platform = int(input("ID de la Plataforma (ex: 1): "))
            
            # Enviem l'acció amb les dades cridant a la nostra funció de dalt
            resposta = send_request("create_game", {"title": titol, "price": preu, "platform_id": platform})
            print("\nResposta del servidor:", resposta.get('message'))
            
        elif opcio == '4':
            id_joc = int(input("Introdueix l'ID del joc a esborrar: "))
            resposta = send_request("delete_game", {"game_id": id_joc})
            print("\nResposta del servidor:", resposta.get('message'))

        elif opcio == '5':
            nom = input("Nom de la plataforma (ex: PlayStation 5): ")
            resposta = send_request("create_platform", {"name": nom})
            print("\nResposta del servidor:", resposta.get('message'))
            
        elif opcio == '0':
            print("Adéu!")
            break # Trenquem el bucle infinit i el programa acaba
        else:
            print("Opció incorrecta.")

# Això evita que s'executi el codi automàticament si algun altre arxiu importa aquest per error
if __name__ == "__main__":
    main()
