"""
Utilities for Psifos.

08-04-2022
"""

import json
import pytz

from app.psifos.model.enums import ElectionLoginTypeEnum

from datetime import datetime
from app.config import TIMEZONE
from functools import reduce

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

    if election.election_login_type == ElectionLoginTypeEnum.close_p:
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
