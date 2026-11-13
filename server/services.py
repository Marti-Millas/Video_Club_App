# server/services.py
from datetime import date, datetime
from decimal import Decimal
from server.domain.unit_of_work import SqlAlchemyUnitOfWork
from server.domain.models import Game
from server.domain.models import Platform

def model_to_dict(model_instance):
    """
    Converteix un objecte de la base de dades (SQLAlchemy) a un diccionari estàndard.
    Com que hi ha dates o decimals, els hem de passar a string o float perquè el JSON els pugui llegir.
    """
    if not model_instance:
        return None
    
    result = {}
    for c in model_instance.__table__.columns:
        value = getattr(model_instance, c.name)
        
        # El JSON no entén dates ni Decimals, els hem de formatar manualment
        if isinstance(value, (datetime, date)):
            result[c.name] = value.isoformat()
        elif isinstance(value, Decimal):
            result[c.name] = float(value)
        else:
            result[c.name] = value
            
    return result

def get_all_games():
    """Servei per obtenir tots els jocs"""
    uow = SqlAlchemyUnitOfWork()
    with uow:
        # Fem servir la funció list() del SqlAlchemyRepository
        games_db = uow.games.list() 
        
        # Convertim cada objecte de la llista a un diccionari 
        return [model_to_dict(game) for game in games_db]

def create_game(title, price, platform_id):
    """Servei per crear un nou joc validant la plataforma"""
    uow = SqlAlchemyUnitOfWork()
    with uow:
        # Comprovem si la plataforma existeix abans de crear el joc
        if not uow.platforms.get(platform_id):
            raise ValueError(f"La plataforma amb ID {platform_id} no existeix.")
            
        nou_joc = Game(title=title, price=price, platform_id=platform_id)
        uow.games.add(nou_joc)
        uow.commit() 
        return model_to_dict(nou_joc)

def delete_game(game_id):
    """Servei per esborrar un joc"""
    uow = SqlAlchemyUnitOfWork()
    with uow:
        joc = uow.games.get(game_id)
        if joc:
            uow.games.delete(joc)
            uow.commit()
            return True
        return False


def create_platform(name):
    uow = SqlAlchemyUnitOfWork()
    with uow:
        nova_plataforma = Platform(name=name)
        uow.platforms.add(nova_plataforma)
        uow.commit()
        return model_to_dict(nova_plataforma)

def get_all_platforms():
    """Servei per obtenir totes les plataformes"""
    uow = SqlAlchemyUnitOfWork()
    with uow:
        plats_db = uow.platforms.list()
        return [model_to_dict(p) for p in plats_db]

def delete_platform(platform_id):
    """Servei per esborrar una plataforma amb protecció d'orfenesa"""
    uow = SqlAlchemyUnitOfWork()
    with uow:
        plat = uow.platforms.get(platform_id)
        if plat:
            # Comprovem si té jocs lligats abans d'esborrar (com feies a la PAC 1)
            if plat.games:
                raise ValueError("No es pot esborrar aquesta plataforma perquè té jocs lligats a ella. Elimina primer els seus jocs.")
                
            uow.platforms.delete(plat)
            uow.commit()
            return True
        return False