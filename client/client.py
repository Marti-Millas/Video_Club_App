import asyncio
import json
import ssl
import hashlib
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table

console = Console()
HOST = '127.0.0.1'
PORT = 65432

def get_client_context():
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="certs/CA_cert.pem")
    context.load_cert_chain(certfile="certs/client1_cert.pem", keyfile="certs/client1_key.pem")
    context.check_hostname = False
    return context

async def send_request(action: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if data is None:
        data = {}
    
    request_dict = {"action": action, "data": data}
    body_bytes = json.dumps(request_dict).encode('utf-8')
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    header_bytes = json.dumps({"length": len(body_bytes), "sha256": body_hash}).encode('utf-8') + b'\n'

    try:
        ssl_ctx = get_client_context()
        reader, writer = await asyncio.open_connection(HOST, PORT, ssl=ssl_ctx)
        
        writer.write(header_bytes + body_bytes)
        await writer.drain()
        
        header_line = await reader.readuntil(b'\n')
        res_header = json.loads(header_line.decode('utf-8'))
        
        res_body_bytes = await reader.readexactly(res_header["length"])
        
        actual_hash = hashlib.sha256(res_body_bytes).hexdigest()
        if actual_hash != res_header["sha256"]:
            console.print("[bold red][!] Alerta: El SHA-256 del servidor no coincideix![/bold red]")
            return None
            
        writer.close()
        await writer.wait_closed()
        
        return json.loads(res_body_bytes.decode('utf-8'))
        
    except ssl.SSLError as e:
        console.print(f"\n[bold red][!] Error de certificats SSL: {e}[/bold red]")
        return None
    except ConnectionRefusedError:
        console.print("\n[bold red][!] Error: No s'ha pogut connectar al servidor.[/bold red]")
        return None
    except Exception as e:
        console.print(f"\n[bold red][!] Error de xarxa: {e}[/bold red]")
        return None

async def main() -> None:
    while True:
        console.print("\n[bold cyan]=== VIDEOCLUB (ASYNC TCP + TLS) ===[/bold cyan]")
        print("1. Crear Plataforma")
        print("2. Llistar Plataformes")
        print("3. Esborrar Plataforma")
        print("4. Crear Joc")
        print("5. Llistar Jocs")
        print("6. Esborrar Joc")
        print("7. Sortir")
        
        opcio = input("\nTria una opció: ")
        
        if opcio == "1":
            nom = input("Nom de la plataforma (ex: PS5): ")
            resposta = await send_request("create_platform", {"name": nom})
            if resposta and resposta.get("status") == "success":
                console.print("[bold green][+] Plataforma creada correctament.[/bold green]")
            else:
                msg = resposta.get('message') if resposta else "Petició fallida"
                console.print(f"[bold red][-] Error: {msg}[/bold red]")
                
        elif opcio == "2":
            resposta = await send_request("list_platforms")
            if resposta and resposta.get("status") == "success":
                plats = resposta.get("data", [])
                taula = Table(title="Llista de Plataformes")
                taula.add_column("ID", style="cyan")
                taula.add_column("Nom", style="green")
                for p in plats:
                    taula.add_row(str(p.get('id')), str(p.get('name')))
                console.print(taula)
            else:
                console.print("[bold red][-] Error carregant plataformes.[/bold red]")
                
        elif opcio == "3":
            try:
                id_plat = int(input("ID de la plataforma a esborrar: "))
                resposta = await send_request("delete_platform", {"platform_id": id_plat})
                if resposta and resposta.get("status") == "success":
                    console.print("[bold green][+] Plataforma esborrada![/bold green]")
                else:
                    msg = resposta.get('message') if resposta else "Petició fallida"
                    console.print(f"[bold red][-] Error: {msg}[/bold red]")
            except ValueError:
                console.print("[bold yellow][!] L'ID ha de ser un número.[/bold yellow]")

        elif opcio == "4":
            try:
                titol = input("Títol del joc: ")
                preu = float(input("Preu: "))
                plat_id = int(input("ID de la plataforma: "))
                resposta = await send_request("create_game", {"title": titol, "price": preu, "platform_id": plat_id})
                if resposta and resposta.get("status") == "success":
                    console.print("[bold green][+] Joc creat correctament![/bold green]")
                else:
                    msg = resposta.get('message') if resposta else "Petició fallida"
                    console.print(f"[bold red][-] Error: {msg}[/bold red]")
            except ValueError:
                console.print("[bold yellow][!] El preu i l'ID han de ser números.[/bold yellow]")
                
        elif opcio == "5":
            resposta = await send_request("list_games")
            if resposta and resposta.get("status") == "success":
                jocs = resposta.get("data", [])
                taula = Table(title="Llista de Jocs")
                taula.add_column("ID", style="cyan")
                taula.add_column("Títol", style="white")
                taula.add_column("Preu", style="green")
                taula.add_column("ID Plat.", style="yellow")
                for joc in jocs:
                    taula.add_row(str(joc.get('id')), str(joc.get('title')), f"{joc.get('price')}€", str(joc.get('platform_id')))
                console.print(taula)
            else:
                console.print("[bold red][-] Error carregant jocs.[/bold red]")
                
        elif opcio == "6":
            try:
                id_joc = int(input("ID del joc a esborrar: "))
                resposta = await send_request("delete_game", {"game_id": id_joc})
                if resposta and resposta.get("status") == "success":
                    console.print("[bold green][+] Joc esborrat correctament![/bold green]")
                else:
                    msg = resposta.get('message') if resposta else "Petició fallida"
                    console.print(f"[bold red][-] Error: {msg}[/bold red]")
            except ValueError:
                console.print("[bold yellow][!] L'ID ha de ser un número.[/bold yellow]")
                
        elif opcio == "7":
            print("Sortint...")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass