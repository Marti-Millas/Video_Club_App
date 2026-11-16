import asyncio
import json
from typing import Optional, Dict, Any
# Importes 'rich' per fer taules i lletres de colors (més atractiu per l'usuari)
from rich.console import Console
from rich.table import Table

console = Console()
HOST = '127.0.0.1'
PORT = 65432

async def send_request(action: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Obre connexió, envia dades, rep resposta, i tanca connexió."""
    if data is None:
        data = {}
    
    # Empaquetem l'acció
    request = {"action": action, "data": data}
    try:
        # Obrim la connexió asíncrona amb el servidor
        reader, writer = await asyncio.open_connection(HOST, PORT)
        
        # Traduïm a bytes i enviem
        request_bytes = json.dumps(request).encode('utf-8')
        writer.write(request_bytes)
        await writer.drain() # "Assegura't de buidar la canonada, envia-ho tot JA"
        
        # Esperem la resposta (fins a 1024 bytes)
        response_bytes = await reader.read(1024)
        
        # Tanquem netament la connexió per no deixar "canonades obertes" al servidor
        writer.close()
        await writer.wait_closed()
        
        # Traduïm els bytes rebuts a un diccionari de Python
        return json.loads(response_bytes.decode('utf-8'))
        
    except ConnectionRefusedError:
        console.print("\n[bold red][!] Error: No s'ha pogut connectar al servidor.[/bold red]")
        return None
    except Exception as e:
        console.print(f"\n[bold red][!] Error de xarxa: {e}[/bold red]")
        return None

async def main() -> None:
    """Funció del menú. S'ha de declarar com 'async' perquè pugui fer 'await' a les trucades de xarxa"""
    while True:
        console.print("\n[bold cyan]=== VIDEOCLUB (ASYNC TCP) ===[/bold cyan]")
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
            # L'await atura aquesta línia esperant que el servidor respongui
            resposta = await send_request("create_platform", {"name": nom})
            if resposta and resposta.get("status") == "success":
                console.print("[bold green][+] Plataforma creada correctament.[/bold green]")
            else:
                console.print(f"[bold red][-] Error: {resposta.get('message')}[/bold red]")
                
        elif opcio == "2":
            resposta = await send_request("list_platforms")
            if resposta and resposta.get("status") == "success":
                plats = resposta.get("data", [])
                
                # Usem la llibreria 'rich' per crear una taula formatada
                taula = Table(title="Llista de Plataformes")
                taula.add_column("ID", style="cyan")
                taula.add_column("Nom", style="green")
                
                for p in plats:
                    # Afegim les files dinàmicament a la taula
                    taula.add_row(str(p.get('id')), str(p.get('name')))
                console.print(taula) # Imprimeix la taula de colors
            else:
                console.print("[bold red][-] Error carregant plataformes.[/bold red]")
                
        elif opcio == "3":
            try:
                id_plat = int(input("ID de la plataforma a esborrar: "))
                resposta = await send_request("delete_platform", {"platform_id": id_plat})
                if resposta and resposta.get("status") == "success":
                    console.print("[bold green][+] Plataforma esborrada![/bold green]")
                else:
                    console.print(f"[bold red][-] Error: {resposta.get('message')}[/bold red]")
            except ValueError:
                # Evita que el programa peti si l'usuari tecleja text en comptes d'un número
                console.print("[bold yellow][!] L'ID ha de ser un número.[/bold yellow]")

        # (Totes les altres opcions segueixen el mateix patró d'input -> await send_request() -> if success)
        
        elif opcio == "4":
            try:
                titol = input("Títol del joc: ")
                preu = float(input("Preu: "))
                plat_id = int(input("ID de la plataforma: "))
                resposta = await send_request("create_game", {"title": titol, "price": preu, "platform_id": plat_id})
                if resposta and resposta.get("status") == "success":
                    console.print("[bold green][+] Joc creat correctament![/bold green]")
                else:
                    console.print(f"[bold red][-] Error: {resposta.get('message')}[/bold red]")
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
                    console.print(f"[bold red][-] Error: {resposta.get('message')}[/bold red]")
            except ValueError:
                console.print("[bold yellow][!] L'ID ha de ser un número.[/bold yellow]")
                
        elif opcio == "7":
            print("Sortint...")
            break

if __name__ == "__main__":
    try:
        # A Python no pots cridar una funció asíncrona des de l'arrel lliurement, 
        # necessites instanciar el motor d'AsyncIO
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
