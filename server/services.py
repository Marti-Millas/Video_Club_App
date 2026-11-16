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
    # Recorrem totes les columnes de la taula (id, title, price...)
    for c in model_instance.__table__.columns:
        # Obtenim el valor real que té aquell camp en aquest objecte
        value = getattr(model_instance, c.name)
        
        # El JSON no entén dates ni Decimals, els hem de formatar manualment
        if isinstance(value, (datetime, date)):
            # isoformat() passa la data a text (ex: "2026-11-14")
            result[c.name] = value.isoformat()
        elif isinstance(value, Decimal):
            # float() passa el preu a un número decimal que JSON entén (ex: 60.5)
            result[c.name] = float(value)
        else:
            # Si és un string o int normal (com el títol o l'ID), el guardem tal qual
            result[c.name] = value
            
    return result

def get_all_games():
    """Servei per obtenir tots els jocs"""
    # Iniciem el Unit of Work (UoW). Aquest patró s'encarrega d'obrir la sessió amb la BD
    uow = SqlAlchemyUnitOfWork()
    
    # El 'with' assegura que en sortir d'aquest bloc, la sessió de BD es tancarà de forma segura
    with uow:
        # Fem servir la funció list() del SqlAlchemyRepository per portar tots els registres
        games_db = uow.games.list() 
        
        # Convertim cada objecte de la llista a un diccionari perquè el Router ho pugui enviar per JSON
        return [model_to_dict(game) for game in games_db]

def create_game(title, price, platform_id):
    """Servei per crear un nou joc"""
    uow = SqlAlchemyUnitOfWork()
    with uow:
        # 1. Instanciem el Model (creem l'objecte en memòria de Python, encara NO a la BD)
        nou_joc = Game(title=title, price=price, platform_id=platform_id)
        
        # 2. Ho afegim al repositori (prepara l'INSERT de SQL)
        uow.games.add(nou_joc)
        
        # 3. Guardem els canvis a la BD. Si falla, el UoW farà rollback (desfà els canvis).
        uow.commit() 
        
        # Tornem el joc creat com a diccionari
        return model_to_dict(nou_joc)

def delete_game(game_id):
    """Servei per esborrar un joc"""
    uow = SqlAlchemyUnitOfWork()
    with uow:
        # Busquem el joc per ID (fa un SELECT a la base de dades)
        joc = uow.games.get(game_id)
        if joc:
            # Si el trobem, li diem al repositori que el borri (fa un DELETE)
            uow.games.delete(joc)
            uow.commit() # Consolidem el canvi
            return True
        return False

def create_platform(name):
    uow = SqlAlchemyUnitOfWork()
    with uow:
        nova_plataforma = Platform(name=name)
        uow.platforms.add(nova_plataforma)
        uow.commit()
        return model_to_dict(nova_plataforma)
