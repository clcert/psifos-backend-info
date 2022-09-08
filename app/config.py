import configparser
from datetime import timedelta
from pydantic import BaseSettings

import os

# Retrieve enviroment variables from .env file
env = configparser.ConfigParser()
env.read(".env")

env["local"]["user"] = os.environ.get("USER", env["local"]["user"])
env["local"]["password"] = os.environ.get("PASSWORD", env["local"]["password"])
env["local"]["host"] = os.environ.get("HOST", env["local"]["host"])
env["local"]["database"] = os.environ.get("NAME_DATABASE", env["local"]["database"])


class Settings(BaseSettings):
    CORS_HEADERS: str = "Content-Type"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = True
    SECRET_KEY: str = "Th1s1ss3cr3t"
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1000)
    ORIGINS: list = [
        "*"
    ]


settings = Settings()