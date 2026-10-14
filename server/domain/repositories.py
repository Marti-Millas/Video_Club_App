from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Sequence, List
from sqlalchemy import select, func
from .models import Game, Platform, Review, UserAccount, Tag, UserProfile

T = TypeVar("T")       # Tipus de l'entitat
ID = TypeVar("ID")     # Tipus de la clau primària (normalment int)


class AbstractRepository(ABC, Generic[T, ID]):
    @abstractmethod
    def add(self, entity: T) -> None:
        pass

    @abstractmethod
    def update(self, entity: T) -> None:
        pass

    @abstractmethod
    def get(self, id: ID) -> Optional[T]:
        pass

    @abstractmethod
    def list(self) -> Sequence[T]:
        pass

    @abstractmethod
    def delete(self, entity: T) -> None:
        pass

# --- IMPLEMENTACIÓ SQLALCHEMY  ---
class SqlAlchemyRepository(AbstractRepository[T, ID]):
    def __init__(self, unit_of_work, model_class: T):
        self.model_class = model_class
        self.session = unit_of_work.session # Agafem la sessió de la UoW
    
    def add(self, entity: T):
        self.session.add(entity)

    def update(self, entity: T):
        # SQLAlchemy gestiona els updates automàticament en fer commit
        # però es pot afegir un merge si fos necessari
        self.session.merge(entity)

    def get(self, entity_id: ID) -> Optional[T]:
        return self.session.get(self.model_class, entity_id)

    def list(self) -> Sequence[T]:
        return self.session.query(self.model_class).all()

    def delete(self, entity: T):
        self.session.delete(entity)

# --- REPOSITORIS CONCRETS ---
class GameRepository(SqlAlchemyRepository[Game, int]):
    def __init__(self, unit_of_work):
        super().__init__(unit_of_work, Game)

    def get_by_title(self, title: str) -> Optional[Game]:
        return self.session.query(Game).filter(Game.title == title).first()

    def get_paginated(self, page: int, page_size: int) -> List[Game]:
        offset = (page - 1) * page_size
        return self.session.query(Game).offset(offset).limit(page_size).all()
    
    def add_tag_to_game(self, game_id: int, tag_id: int):
        game = self.get(game_id)
        tag = self.session.get(Tag, tag_id)
        if game and tag:
            game.tags.append(tag)
   
class PlatformRepository(SqlAlchemyRepository[Platform, int]):
    def __init__(self, unit_of_work):
        super().__init__(unit_of_work, Platform)

class UserRepository(SqlAlchemyRepository[UserAccount, int]):
    def __init__(self, unit_of_work):
        super().__init__(unit_of_work, UserAccount)

class ReviewRepository(SqlAlchemyRepository[Review, tuple]):
    def __init__(self, unit_of_work):
        # Nota: La clau primària de Review és composta (game_id, user_id)
        super().__init__(unit_of_work, Review)

class TagRepository(SqlAlchemyRepository[Tag, int]):
    def __init__(self, unit_of_work):
        super().__init__(unit_of_work, Tag)

class UserProfileRepository(SqlAlchemyRepository[UserProfile, int]):
    def __init__(self, unit_of_work):
        super().__init__(unit_of_work, UserProfile)