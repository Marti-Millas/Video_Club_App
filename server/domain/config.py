import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

DATABASE_URL = {
    "development": os.getenv("DB_URL_DEVELOPMENT","sqlite:///./videoclub_dev.db"),
    "test": os.getenv("DB_URL_TEST","sqlite:///./videoclub_dev.db"),
    "production": os.getenv("DB_URL_PRODUCTION")
}.get(ENVIRONMENT)