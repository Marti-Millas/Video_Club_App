from .config import ENVIRONMENT,DATABASE_URL
from .db import Base, engine
from .models import(
    Platform, 
    UserAccount, 
    UserProfile, 
    Game, 
    Tag,
    Review,
    game_tag
)

