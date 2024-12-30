"""
Pydantic schemas (FastAPI) for Psifos.

25-07-22


Pydantic schemas are a way to give a 'type' to a group
of related data.

When we deal with SQLAlchemy we must note the following:

    Let 'TestModel' be a SQLAlchemy model, the API can:
        - Create/modify an instance of TestModel.
        - Out an instance of TestModel.
    
    To achieve this we must create 3 schemas:
        - TestModelBase: Inherits from Pydantic's PsifosSchema
          and holds the common data from both creating and
          returning an instance of TestModel.

        - TestModelIn: Inherits from TestModelBase and
          contains the specific data needed to create/modify an
          instance of TestModel.

        - TestModelOut: Inherits from TestModelBase and contains
          the data that we want the API to return to the user.
    
    By doing this we explicitly separate between creation data,
    which could be sensitive, and return data, improving the
    overall security of the API.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List

from app.psifos.model.enums import ElectionTypeEnum, ElectionStatusEnum, ElectionLoginTypeEnum


# ------------------ model-related schemas ------------------

class PublicKeyBase(BaseModel):
    """
    Basic public key schema.
    """

    y: str
    p: str
    g: str
    q: str

    class Config:
        orm_mode = True

#  Trustee-related schemas


class TrusteeBase(BaseModel):
    """
    Basic trustee schema.
    """

    name: str
    email: str
    username: str

# model (sqla) ModelElection -> SchemaElection


class TrusteeOut(TrusteeBase):
    """
    Schema for reading/returning trustee data.
    """

    id: int
    trustee_id: int
    current_step: int
    public_key: object | None
    public_key_hash: str | None
    decryptions: object | None
    certificate: object | None
    coefficients: object | None
    acknowledgements: object | None

    class Config:
        orm_mode = True


#  CastVote-related schemas


class CastVoteBase(BaseModel):
    """
    Basic castvote schema.
    """

    encrypted_ballot: str | None


class CastVoteOut(CastVoteBase):
    """
    Schema for reading/returning castvote data.
    """

    encrypted_ballot_hash: str | None
    cast_at: datetime | None

    class Config:
        orm_mode = True


#  Voter-related schemas


class VoterBase(BaseModel):
    """
    Basic election schema.
    """

    username: str
    weight_init: int
    name: str


class VoterOut(VoterBase):
    """
    Schema for reading/returning voter data.
    """

    group: str | None

    class Config:
        orm_mode = True


class VoterCastVote(VoterOut):

    cast_vote: object | None
    class Config:
        orm_mode = True

#  Election-related schemas

class QuestionBase(BaseModel):
    """
    Schema for creating a question.
    """
    index: int
    type: str
    title: str
    description: str | None
    formal_options: List[str] | None
    max_answers: int
    min_answers: int
    include_informal_options: bool | None
    tally_type: str
    grouped_options: bool | None
    num_of_winners: int | None

    class Config:
        orm_mode = True


class ElectionBase(BaseModel):
    """
    Basic election schema.
    """

    short_name: str = Field(max_length=100)
    long_name: str = Field(max_length=100)
    description: str | None
    type: ElectionTypeEnum = Field(max_length=100)
    max_weight: int
    randomize_answer_order: bool | None
    voters_login_type: ElectionLoginTypeEnum =Field(max_length=100)
    normalized: bool | None
    grouped_voters: bool | None


class ElectionOut(ElectionBase):
    """
    Schema for reading/returning election data
    """

    id: int
    status: ElectionStatusEnum
    public_key: PublicKeyBase | None
    questions: list[QuestionBase] | None
    encrypted_tally_hash: str | None
    result: object | None
    voters_by_weight_init: str | None
    voters_by_weight_end: str | None
    trustees: object | None

    class Config:
        orm_mode = True


# ------------------ response-related schemas ------------------
class PublicKeyData(BaseModel):
    public_key_json: str


class KeyGenStep1Data(BaseModel):
    coefficients: str
    points: str


class KeyGenStep2Data(BaseModel):
    acknowledgements: str


class KeyGenStep3Data(BaseModel):
    verification_key: str


class DecryptionIn(BaseModel):
    decryptions: object


class TrusteeHome(BaseModel):
    trustee: TrusteeOut
    election: ElectionOut


class UrnaOut(BaseModel):
    voters: list[VoterCastVote] = []
    position: int
    more_votes: bool
    total_votes: int

    class Config:
        orm_mode = True


class ElectionLogOut(BaseModel):

    election_id: int
    log_level: str
    event: str
    event_params: str
    created_at: datetime

    class Config:
        orm_mode = True
