from sqlalchemy.orm import Session
from .db import Session
from .repositories import GameRepository, PlatformRepository, ReviewRepository, TagRepository, UserProfileRepository, UserRepository

class SqlAlchemyUnitOfWork:
    def __init__(self):
        self.session = Session()

    def __enter__(self):
        # Inicialitzem els repositoris passant 'self' (la UoW)
        self.games = GameRepository(self)
        self.platforms = PlatformRepository(self)
        self.users = UserRepository(self)
        self.reviews = ReviewRepository(self)    
        self.tags = TagRepository(self)          
        self.profiles = UserProfileRepository(self) 
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()