import sys
from datetime import datetime, date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

# Importem la Unit of Work i els models del nostre projecte
from src.domain.unit_of_work import SqlAlchemyUnitOfWork
from src.domain.models import Platform, Game, UserAccount, UserProfile, Tag, Review

# Inicialitzem les eines de Rich i la Unit of Work per connectar a Aiven
console = Console()
uow = SqlAlchemyUnitOfWork()

# Funció per pintar el menú de colors a la terminal
def mostrar_menu_principal():
    console.print(Panel.fit(
        "[bold cyan]VIDEO CLUB BACK OFFICE[/bold cyan]\n\n"
        "[1] Gestionar Plataformes\n"
        "[2] Gestionar Jocs \n"
        "[3] Gestionar Usuaris i Perfils \n"
        "[4] Gestionar Etiquetes\n"
        "[5] Gestionar Ressenyes\n"
        "[6] Sortir", 
        title="Menú Principal", border_style="cyan"
    ))



# 1. SUBMENÚ: PLATAFORMES 

def menu_plataformes():
    while True:
        console.print("\n[bold magenta]-- INTERFÍCIE PLATAFORMES --[/bold magenta]")
        print("1. Llistar | 2. Crear | 3. Actualitzar | 4. Eliminar | 5. Tornar")
        opcio = Prompt.ask("Tria una opció", choices=["1", "2", "3", "4", "5"])
        
        with uow:
            # Opció per veure totes les plataformes en una taula
            if opcio == "1":
                llista = uow.platforms.list()
                tabla = Table(title="Plataformes a la Base de Dades")
                tabla.add_column("ID", style="cyan")
                tabla.add_column("Nom", style="green")
                tabla.add_column("Fabricant", style="yellow")
                for p in llista:
                    tabla.add_row(str(p.id), p.name, p.manufacturer or "N/A")
                console.print(tabla)
                
            # Opció per afegir una plataforma nova
            elif opcio == "2":
                nom = Prompt.ask("Nom de la plataforma")
                fab = Prompt.ask("Fabricant (Opcional)")
                try:
                    nova = Platform(name=nom, manufacturer=fab if fab else None)
                    uow.platforms.add(nova)
                    uow.commit() # Guardem a la base de dades
                    console.print("[green]Plataforma creada i guardada a Aiven![/green]")
                except Exception:
                    uow.rollback() # Si falla (per exemple nom repetit), desfem per seguretat
                    console.print("[red]No s'ha pogut crear. És possible que aquest nom de plataforma ja existeixi.[/red]")
                
            # Opció per canviar el nom d'una plataforma existent
            elif opcio == "3":
                id_p = int(Prompt.ask("ID de la plataforma a modificar"))
                p = uow.platforms.get(id_p)
                if p:
                    try:
                        p.name = Prompt.ask(f"Nou nom (actual: {p.name})")
                        uow.commit()
                        console.print("[green]Plataforma actualitzada![/green]")
                    except Exception:
                        uow.rollback()
                        console.print("[red]No s'ha pogut actualitzar. El nom introduït podria estar duplicat.[/red]")
                else:
                    console.print("[red]No s'ha trobat la plataforma.[/red]")
                    
            # Opció per esborrar una plataforma
            elif opcio == "4":
                id_p = int(Prompt.ask("ID de la plataforma a eliminar"))
                p = uow.platforms.get(id_p)
                if p:
                    try:
                        uow.platforms.delete(p)
                        uow.commit()
                        console.print("[green]Plataforma eliminada correctament![/green]")
                    except Exception:
                        uow.rollback() # Si té jocs lligats, saltarà l'escut per no penjar el programa
                        console.print("[red]No es pot esborrar aquesta plataforma perquè té jocs lligats a ella. Elimina primer els seus jocs.[/red]")
                else:
                    console.print("[red]No existeix aquesta plataforma.[/red]")
            elif opcio == "5":
                break



# 2. SUBMENÚ: JOCS 

def menu_jocs():
    while True:
        console.print("\n[bold magenta]-- INTERFÍCIE JOCS --[/bold magenta]")
        print("1. Llistar (Paginat) | 2. Crear | 3. Buscar per Títol | 4. Assignar Tag (N:M) | 5. Eliminar | 6. Tornar")
        opcio = Prompt.ask("Tria una opció", choices=["1", "2", "3", "4", "5", "6"])
        
        with uow:
            # Opció per llistar jocs triant la pàgina i quants en volem veure
            if opcio == "1":
                pag = int(Prompt.ask("Número de pàgina", default="1"))
                mida = int(Prompt.ask("Mida de la pàgina", default="3"))
                jocs = uow.games.get_paginated(page=pag, page_size=mida)
                
                tabla = Table(title=f"Catàleg de Jocs (Pàgina {pag})")
                tabla.add_column("ID", style="cyan")
                tabla.add_column("Títol", style="white")
                tabla.add_column("Preu", style="green")
                tabla.add_column("Plataforma (1:N)", style="yellow")
                tabla.add_column("Etiquetes (N:M)", style="magenta")
                
                for j in jocs:
                    nom_plat = j.platform.name if j.platform else "N/A"
                    # Ajuntem les etiquetes amb comes per ensenyar-les juntes
                    tags_vistos = ", ".join([t.tag_name for t in j.tags]) if j.tags else "Sense tags"
                    tabla.add_row(str(j.id), j.title, f"{j.price}€", nom_plat, tags_vistos)
                console.print(tabla)
                
            # Opció per crear un joc demanant una plataforma que ja existeixi 
            elif opcio == "2":
                titol = Prompt.ask("Títol del videojoc")
                preu = float(Prompt.ask("Preu (€)"))
                
                console.print("[yellow]Selecciona una plataforma existent:[/yellow]")
                for p in uow.platforms.list():
                    print(f"  [{p.id}] {p.name}")
                plat_id = int(Prompt.ask("Introdueix l'ID de la plataforma"))
                
                try:
                    nou_joc = Game(title=titol, price=preu, platform_id=plat_id)
                    uow.games.add(nou_joc)
                    uow.commit()
                    console.print("[green]Joc creat i enllaçat a la plataforma![/green]")
                except Exception:
                    uow.rollback()
                    console.print("[red]No s'ha pogut crear el joc. Comprova que l'ID de la plataforma sigui correcte.[/red]")
                
            # Opció de cerca per títol fent servir el mètode propi del repositori
            elif opcio == "3":
                cerca = Prompt.ask("Escriu el títol exacte a buscar")
                joc = uow.games.get_by_title(cerca)
                if joc:
                    console.print(Panel(f"[bold green]Trobat![/bold green]\nID: {joc.id}\nTítol: {joc.title}\nPreu: {joc.price}€\nPlataforma: {joc.platform.name}"))
                else:
                    console.print("[red]No s'ha trobat cap joc amb aquest títol.[/red]")
                    
            # Opció per enllaçar un Tag amb un Joc 
            elif opcio == "4":
                id_joc = int(Prompt.ask("ID del Joc"))
                id_tag = int(Prompt.ask("ID de la Etiqueta (Tag)"))
                
                joc_ex = uow.games.get(id_joc)
                tag_ex = uow.tags.get(id_tag)
                
                # Mirem primer que les dues IDs existeixin abans d'ajuntar-les
                if joc_ex and tag_ex:
                    try:
                        uow.games.add_tag_to_game(id_joc, id_tag)
                        uow.commit()
                        console.print("[green]Tag afegit al joc correctament (Relació N:M guardada)![/green]")
                    except Exception:
                        uow.rollback()
                        console.print("[red]Aquesta etiqueta ja està assignada a aquest joc.[/red]")
                else:
                    console.print("[red]L'ID del joc o del tag no existeixen a la base de dades.[/red]")
                    
            # Opció per esborrar un joc
            elif opcio == "5":
                id_j = int(Prompt.ask("ID del joc a esborrar"))
                j = uow.games.get(id_j)
                if j:
                    try:
                        uow.games.delete(j)
                        uow.commit()
                        console.print("[green]Joc eliminat.[/green]")
                    except Exception:
                        uow.rollback() # Si té ressenyes creades, frena l'error perquè no es pengi
                        console.print("[red]No es pot esborrar aquest joc perquè té ressenyes escrites. Elimina primer les seves ressenyes.[/red]")
                else:
                    console.print("[red]Joc no trobat.[/red]")
            elif opcio == "6":
                break



# 3. SUBMENÚ: USUARIS I PERFILS 

def menu_usuaris():
    while True:
        console.print("\n[bold magenta]-- INTERFÍCIE USUARIS I PERFILS --[/bold magenta]")
        print("1. Llistar Usuaris + Perfil (1:1) | 2. Crear Usuari i Perfil | 3. Eliminar | 4. Tornar")
        opcio = Prompt.ask("Tria una opció", choices=["1", "2", "3", "4"])
        
        with uow:
            # Opció que llista l'usuari i el seu perfil junts 
            if opcio == "1":
                llista = uow.users.list()
                tabla = Table(title="Usuaris i Perfils Associats (1:1)")
                tabla.add_column("ID", style="cyan")
                tabla.add_column("Username", style="white")
                tabla.add_column("Email", style="yellow")
                tabla.add_column("Nom Complet (Perfil 1:1)", style="green")
                tabla.add_column("País", style="magenta")
                
                for u in llista:
                    nom_complet = f"{u.profile.first_name} {u.profile.last_name}" if u.profile else "[red]Sense perfil[/red]"
                    pais = u.profile.country if u.profile else "N/A"
                    tabla.add_row(str(u.id), u.username, u.email, nom_complet, pais)
                console.print(tabla)
                
            # Opció que crea el compte i tot seguit el seu perfil lligat 
            elif opcio == "2":
                username = Prompt.ask("Nom d'usuari (Username)")
                email = Prompt.ask("Correu electrònic")
                password = Prompt.ask("Contrasenya")
                
                try:
                    nou_usuari = UserAccount(username=username, email=email, password=password)
                    uow.users.add(nou_usuari)
                    uow.commit() # Fem commit primer per tenir la ID de l'usuari nova
                    
                    console.print("[yellow]Configuració del perfil d'usuari (Dades 1:1):[/yellow]")
                    nom = Prompt.ask("Prenom (First Name)")
                    cognom = Prompt.ask("Cognom (Last Name)")
                    pais = Prompt.ask("País")
                    
                    # Creem el perfil vinculant-lo exactament a la ID del compte pare
                    nou_perfil = UserProfile(user_id=nou_usuari.id, first_name=nom, last_name=cognom, country=pais)
                    uow.profiles.add(nou_perfil)
                    uow.commit()
                    console.print("[green]Usuari i perfil vinculat (1:1) creats amb èxit![/green]")
                except Exception:
                    uow.rollback()
                    console.print("[red]No s'ha pogut crear l'usuari. El nom d'usuari o el correu electrònic podrien estar duplicats.[/red]")
                
            # Opció per eliminar un usuari
            elif opcio == "3":
                id_u = int(Prompt.ask("ID de l'usuari a esborrar"))
                u = uow.users.get(id_u)
                if u:
                    try:
                        uow.users.delete(u) 
                        uow.commit() 
                        console.print("[green]Usuari i el seu perfil eliminats en cascada![/green]")
                    except Exception:
                        uow.rollback()
                        console.print("[red]No es pot eliminar l'usuari perquè ha deixat ressenyes escrites. Elimina primer les seves ressenyes.[/red]")
                else:
                    console.print("[red]Usuari no trobat.[/red]")
            elif opcio == "4":
                break



# 4. SUBMENÚ: TAGS (Etiquetes)

def menu_tags():
    while True:
        console.print("\n[bold magenta]-- INTERFÍCIE TAGS --[/bold magenta]")
        print("1. Llistar Tags | 2. Crear Tag | 3. Eliminar Tag | 4. Tornar")
        opcio = Prompt.ask("Tria una opció", choices=["1", "2", "3", "4"])
        
        with uow:
            # Opció per veure totes les etiquetes
            if opcio == "1":
                llista = uow.tags.list()
                tabla = Table(title="Etiquetes Disponibles")
                tabla.add_column("ID", style="cyan")
                tabla.add_column("Nom del Tag", style="magenta")
                for t in llista:
                    tabla.add_row(str(t.id), t.tag_name)
                console.print(tabla)
            # Opció per crear una etiqueta nova
            elif opcio == "2":
                nom = Prompt.ask("Nom de la nova etiqueta (Ex: RPG, Acció)")
                nou_tag = Tag(tag_name=nom)
                uow.tags.add(nou_tag)
                uow.commit()
                console.print("[green]Tag creat![/green]")
            # Opció per eliminar una etiqueta
            elif opcio == "3":
                id_t = int(Prompt.ask("ID del tag a eliminar"))
                t = uow.tags.get(id_t)
                if t:
                    try:
                        uow.tags.delete(t)
                        uow.commit()
                        console.print("[green]Tag eliminat correctament.[/green]")
                    except Exception:
                        uow.rollback()
                        console.print("[red]No es pot esborrar aquest tag perquè està assignat a algun joc.[/red]")
                else:
                    console.print("[red]No s'ha trobat cap tag com aquest ID.[/red]")
            elif opcio == "4":
                break



# 5. SUBMENÚ: RESSENYES 

def menu_ressenyes():
    while True:
        console.print("\n[bold magenta]-- INTERFÍCIE RESSENYES (N:M AMB ATRIBUTS) --[/bold magenta]")
        print("1. Llistar Ressenyes | 2. Crear Ressenya | 3. Eliminar Ressenya | 4. Tornar")
        opcio = Prompt.ask("Tria una opció", choices=["1", "2", "3", "4"])
        
        with uow:
            # Opció que ensenya la relació molts a molts guardant la nota i el comentari com a atributs de la unió
            if opcio == "1":
                llista = uow.reviews.list()
                tabla = Table(title="Ressenyes del Sistema (Objecte d'Associació)")
                tabla.add_column("Usuari", style="cyan")
                tabla.add_column("Videojoc", style="white")
                tabla.add_column("Puntuació (Atribut)", style="green")
                tabla.add_column("Comentari (Atribut)", style="yellow")
                
                for r in llista:
                    user_str = r.user.username if r.user else f"ID:{r.user_id}"
                    game_str = r.game.title if r.game else f"ID:{r.game_id}"
                    tabla.add_row(user_str, game_str, f"{r.score}/10", r.comment or "")
                console.print(tabla)
                
            # Opció per fer una ressenya connectant un usuari i un joc
            elif opcio == "2":
                console.print("[yellow]Usuaris disponibles:[/yellow]")
                for u in uow.users.list():
                    print(f"  [{u.id}] {u.username}")
                u_id = int(Prompt.ask("ID de l'Usuari que opina"))
                
                console.print("[yellow]Jocs disponibles:[/yellow]")
                for j in uow.games.list():
                    print(f"  [{j.id}] {j.title}")
                j_id = int(Prompt.ask("ID del Videojoc ressenyat"))
                
                nota = int(Prompt.ask("Puntuació del joc (De l'1 al 10)"))
                if nota < 1 or nota > 10:
                    console.print("[red]La nota ha d'estar entre 1 i 10 pels valors permesos.[/red]")
                    continue
                    
                comentari = Prompt.ask("Escriu el comentari de la ressenya")
                
                try:
                    nova_review = Review(game_id=j_id, user_id=u_id, score=nota, comment=comentari)
                    uow.reviews.add(nova_review)
                    uow.commit()
                    console.print("[green]Ressenya guardada! S'han desat els atributs de la unió N:M.[/green]")
                except Exception:
                    uow.rollback()
                    console.print("[red]No s'ha pogut guardar. És possible que aquest usuari ja hagi fet una ressenya d'aquest joc.[/red]")
                
            # Opció per esborrar una ressenya fent servir la seva clau composta (game_id, user_id)
            elif opcio == "3":
                u_id = int(Prompt.ask("ID de l'usuari de la ressenya"))
                j_id = int(Prompt.ask("ID del joc de la ressenya"))
                r = uow.reviews.get((j_id, u_id))
                if r:
                    try:
                        uow.reviews.delete(r)
                        uow.commit()
                        console.print("[green]Ressenya eliminada correctament.[/green]")
                    except Exception:
                        uow.rollback()
                        console.print("[red]Error no esperat en esborrar la ressenya.[/red]")
                else:
                    console.print("[red]No s'ha trobat cap ressenya amb aquesta clau composta.[/red]")
            elif opcio == "4":
                break



# EXECUCIÓ DE L'APLICACIÓ 

if __name__ == "__main__":
    while True:
        mostrar_menu_principal()
        opcio = Prompt.ask("Selecciona un menú (1-6)", choices=["1", "2", "3", "4", "5", "6"])
        
        if opcio == "1":
            menu_plataformes()
        elif opcio == "2":
            menu_jocs()
        elif opcio == "3":
            menu_usuaris()
        elif opcio == "4":
            menu_tags()
        elif opcio == "5":
            menu_ressenyes()
        elif opcio == "6":
            console.print("[bold red] Sortint de l'aplicació.[/bold red]")
            sys.exit()