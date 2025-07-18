import os

DATABASE_USER = os.environ.get("DATABASE_USER")
DATABASE_PASS = os.environ.get("DATABASE_PASS")
DATABASE_HOST = os.environ.get("DATABASE_HOST")
DATABASE_NAME = os.environ.get("DATABASE_NAME")

SECRET_KEY: str = os.environ.get("SECRET_KEY")

USE_ASYNC_ENGINE = bool(int(os.environ.get("USE_ASYNC_ENGINE", False)))
TIMEZONE = os.environ.get("TIMEZONE", "Chile/Continental")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")

TOKEN_ANALYTICS_INFO = os.environ.get("TOKEN_ANALYTICS_INFO")

ORIGINS: list = [
    "*"
]