import logging
from server.services import get_all_games, create_game, delete_game, create_platform

def route_request(action, data):
    """
    Router principal. Patró de disseny 'Front Controller'. 
    Decideix quin servei executar en funció del text de l'action.
    """
    if action == "ping":
        return {"status": "success", "message": "Pong! Comunicació correcta.", "data": data}
    
    elif action == "list_games":
        try:
            # Crida a la capa de Serveis, que és qui sap parlar amb la Base de Dades
            games_list = get_all_games()
            return {"status": "success", "message": "Llista de jocs obtinguda", "data": games_list}
        except Exception as e:
            logging.error(f"Error a list_games: {e}")
            return {"status": "error", "message": f"Error intern de BD: {str(e)}", "data": None}
            
    elif action == "create_game":
        try:
            # Agafem les dades del diccionari 'data' que ha enviat el client
            nou_joc = create_game(
                title=data.get('title'),
                price=data.get('price'),
                platform_id=data.get('platform_id')
            )
            return {"status": "success", "message": "Joc creat correctament", "data": nou_joc}
        except Exception as e:
            logging.error(f"Error a create_game: {e}")
            return {"status": "error", "message": f"No s'ha pogut crear: {str(e)}", "data": None}
            
    # ... (les altres accions fan exactament el mateix patró)
    elif action == "delete_game":
        try:
            esborrat = delete_game(data.get('game_id'))
            if esborrat:
                return {"status": "success", "message": "Joc esborrat correctament", "data": None}
            else:
                return {"status": "error", "message": "Joc no trobat", "data": None}
        except Exception as e:
            logging.error(f"Error a delete_game: {e}")
            return {"status": "error", "message": f"Error esborrant: {str(e)}", "data": None}

    elif action == "create_platform":
        try:
            nova_plat = create_platform(data.get('name'))
            return {"status": "success", "message": "Plataforma creada", "data": nova_plat}
        except Exception as e:
            return {"status": "error", "message": f"Error creant plataforma: {str(e)}", "data": None}
    else:
        # Si arriba una action que no reconeixem, rebutgem netament
        return {"status": "error", "message": f"Acció '{action}' no implementada", "data": None}
