from fastapi import FastAPI

from app.config import settings

from .database import Base, engine
from .psifos.routes import api_router

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from starlette_context import middleware, plugins

import os

Base.metadata.create_all(engine)

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    middleware.ContextMiddleware,
    plugins=(
        plugins.ForwardedForPlugin(),
    ),
)

# Routes
app.include_router(api_router)