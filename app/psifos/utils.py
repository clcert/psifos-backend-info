"""
Utilities for Psifos.

08-04-2022
"""

import json

import pydantic
import pytz

from app.psifos.model.enums import ElectionLoginTypeEnum

from datetime import datetime
from app.config import TIMEZONE, REDIS_URL
from functools import reduce, wraps
from aiocache import Cache, AIOCACHE_CACHES
from fastapi import HTTPException
from app.psifos.model import schemas
from fastapi.encoders import jsonable_encoder

from pyinstrument import Profiler
from pyinstrument.renderers.html import HTMLRenderer
from pyinstrument.renderers.speedscope import SpeedscopeRenderer
from functools import wraps


# -- JSON manipulation --


def to_json(d: dict):
    return json.dumps(d, sort_keys=True)


def from_json(value):
    if value == "" or value is None:
        return None

    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception as e:
            raise Exception(
                "psifos.utils error: in from_json, value is not JSON parseable"
            ) from e

    return value


# -- Election utils --


def generate_election_pk(trustees):
    a_combined_pk = trustees[0].coefficients.instances[0].coefficient
    for t in trustees[1:]:
        a_combined_pk = combined_pk * t.coefficients.instances[0].coefficient

    t_first_coefficients = [t.coefficients.instances[0].coefficient for t in trustees]

    combined_pk = reduce((lambda x, y: x * y), t_first_coefficients)
    return trustees[0].public_key.clone_with_new_y(combined_pk)


# -- CastVote validation --


def do_cast_vote_checks(request, election, voter):
    if not election.voting_has_started():
        return False, "Error al enviar el voto: la eleccion aun no comienza"

    if election.voting_has_ended():
        return False, "Error al enviar el voto: el proceso de voto ha concluido"

    if request.get_json().get("encrypted_vote") is None:
        return False, "Error al enviar el voto: no se envio el encrypted vote"

    if election.voters_login_type == ElectionLoginTypeEnum.close_p:
        if voter is None:
            return False, "Error al enviar el voto: votante no encontrado"
    return True, None


# -- Datetime --
def tz_now():
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)


def paginate(data_json: dict):
    """
    Handles pagination
    
    """

    page = data_json.get("page", 0)

    page_size = data_json.get("page_size", 500)
    page_size = page_size if page_size <= 50 else 50
    page = page_size * page

    return page, page_size

def profile_route(profile_format: str = "html"):
    """Decorador para perfilar rutas específicas."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            profile_type_to_ext = {"html": "html", "speedscope": "speedscope.json"}
            profile_type_to_renderer = {
                "html": HTMLRenderer,
                "speedscope": SpeedscopeRenderer,
            }

            # Configurar el profiler
            with Profiler(interval=0.001, async_mode="enabled") as profiler:
                response = await func(*args, **kwargs)

            # Guardar el perfil en archivo
            extension = profile_type_to_ext.get(profile_format, "html")
            renderer = profile_type_to_renderer.get(profile_format, HTMLRenderer)()
            name_function = func.__name__
            with open(f"profile_{name_function}.{extension}", "w") as out:
                out.write(profiler.output(renderer=renderer))

            return response

        return wrapper

    return decorator

## -- Handle cache --
# Example for caching election route
def cache_election_response(ttl: int = 60, namespace: str = "main"):
    """
    Caching decorator for FastAPI endpoints.

    ttl: Time to live for the cache in seconds.
    namespace: Namespace for cache keys in Redis.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            element_id = kwargs.get('short_name')  # Assuming the element ID is the first argument 
            cache_key = f"{namespace}:{element_id}"

            # cache = Cache.REDIS(endpoint="redis", port=6379, namespace=namespace)
            cache = Cache.from_url(REDIS_URL)

            # Try to retrieve data from cache
            cached_value = await cache.get(cache_key)
            if cached_value:
                return cached_value  # Return cached data

            # Call the actual function if cache is not hit
            response = await func(*args, **kwargs)
            response_serialized = jsonable_encoder(response)
            print(response_serialized)
            response_serialized["public_key"]["p"] = response_serialized["public_key"]["_p"]
            response_serialized["public_key"]["y"] = response_serialized["public_key"]["_y"]
            response_serialized["public_key"]["g"] = response_serialized["public_key"]["_g"]
            response_serialized["public_key"]["q"] = response_serialized["public_key"]["_q"]
            response_as_schema = schemas.ElectionOut.parse_obj(response_serialized).json()
            
            try:
                # Store the response in Redis with a TTL
                await cache.set(cache_key, json.loads(response_as_schema), ttl=ttl)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error caching data: {e}")

            return response
        return wrapper
    return decorator
