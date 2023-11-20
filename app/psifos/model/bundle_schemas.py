from datetime import datetime
from pydantic import BaseModel, Field

from app.psifos.model.enums import ElectionTypeEnum, ElectionStatusEnum


class ElectionBundle(BaseModel):
    """
    Election schema for bundle file
    """

    short_name: str
    name: str
    description: str
    max_weight: int
    obscure_voter_names: bool
    normalization: bool
    uuid: str
    public_key: object
    questions: object

    class Config:
        orm_mode = True


class VoterBundle(BaseModel):
    """
    Voter schema for bundle file
    """

    voter_login_id: str
    voter_weight: int
    uuid: str
    voter_name: str

    class Config:
        orm_mode = True


class VoteBundle(BaseModel):
    """
    Vote schema for bundle file
    """

    vote: object
    vote_hash: str
    cast_at: datetime
    psifos_voter: VoterBundle

    class Config:
        orm_mode = True


class TrusteeBundle(BaseModel):
    """
    Trustee schema for bundle file
    """

    name: str
    email: str
    trustee_login_id: str
    trustee_id: int
    uuid: str
    public_key: object
    public_key_hash: str
    decryptions: list | None
    certificate: object
    coefficients: list
    acknowledgements: list

    class Config:
        orm_mode = True


class Bundle(BaseModel):
    """
    Election schema for bundle file
    """

    election: ElectionBundle
    voters: list[VoterBundle] = []
    votes: list
    result: object | None
    trustees: list[TrusteeBundle] = []

    class Config:
        orm_mode = True
