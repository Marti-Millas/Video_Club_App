import asyncio
import json

HOST = '127.0.0.1'
PORT = 65432

async def send_request(action, data=None):
    """Funció asíncrona per comunicar-se amb el servidor"""
    if data is None:
        data = {}
        
    request = {
        "action": action,
        "data": data
    }
    
    try:
        # Obrim la connexió asíncrona en lloc del socket bloquejant
        reader, writer = await asyncio.open_connection(HOST, PORT)
        
        # Convertim a JSON i enviem per la xarxa
        request_bytes = json.dumps(request).encode('utf-8')
        writer.write(request_bytes)
        await writer.drain() # Ens assegurem que surt tot pel cable
        
        # Esperem la resposta del servidor
        response_bytes = await reader.read(1024)
        response_str = response_bytes.decode('utf-8')
        response_dict = json.loads(response_str)
        
        # Tanquem la connexió de manera neta
        writer.close()
        await writer.wait_closed()
        
        return response_dict
        
    except ConnectionRefusedError:
        print("\n[!] Error: No s'ha pogut connectar. Està el servidor obert?")
        return None
    except Exception as e:
        print(f"\n[!] Error de xarxa: {e}")
        return None

async def main():
    """Bucle principal asíncron del client"""
    while True:
        print("\n=== VIDEOCLUB (ASYNC TCP) ===")
        print("1. Crear Plataforma")
        print("2. Crear Joc")
        print("3. Llistar Jocs")
        print("4. Sortir")
        
        opcio = input("\nTria una opció: ")
        
        if opcio == "1":
            nom = input("Nom de la plataforma (ex: PS5): ")
            resposta = await send_request("create_platform", {"name": nom})
            if resposta and resposta.get("status") == "success":
                print(f"[+] Plataforma creada correctament.")
            else:
                print(f"[-] Error: {resposta.get('message') if resposta else 'Desconegut'}")
                
        elif opcio == "2":
            try:
                titol = input("Títol del joc: ")
                preu = float(input("Preu: "))
                plat_id = int(input("ID de la plataforma: "))
                
                dades = {"title": titol, "price": preu, "platform_id": plat_id}
                resposta = await send_request("create_game", dades)
                
                if resposta and resposta.get("status") == "success":
                    print("[+] Joc creat correctament!")
                else:
                    print(f"[-] Error: {resposta.get('message') if resposta else 'Desconegut'}")
            except ValueError:
                print("[!] Error: El preu i l'ID han de ser números.")
                
        elif opcio == "3":
            resposta = await send_request("list_games")
            if resposta and resposta.get("status") == "success":
                jocs = resposta.get("data", [])
                print(f"\n--- LLISTA DE JOCS ({len(jocs)}) ---")
                for joc in jocs:
                    print(f"ID: {joc.get('id')} | {joc.get('title')} | Preu: {joc.get('price')}€")
            else:
                print("[-] No s'han pogut carregar els jocs.")
                
        elif opcio == "4":
            print("Sortint de l'aplicació...")
            break
        else:
            print("Opció incorrecta, torna-ho a provar.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClient tancat manualment.")