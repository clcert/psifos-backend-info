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
    trustee_login_id: str

# model (sqla) ModelElection -> SchemaElection


class TrusteeOut(TrusteeBase):
    """
    Schema for reading/returning trustee data.
    """

    id: int
    trustee_id: int
    uuid: str
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

    vote: str | None


class CastVoteOut(CastVoteBase):
    """
    Schema for reading/returning castvote data.
    """

    vote_hash: str | None
    hash_cast_ip: str | None
    cast_at: datetime | None

    class Config:
        orm_mode = True


#  Voter-related schemas


class VoterBase(BaseModel):
    """
    Basic election schema.
    """

    voter_login_id: str
    voter_weight: int
    voter_name: str


class VoterOut(VoterBase):
    """
    Schema for reading/returning voter data.
    """

    voter_login_id: str
    voter_name: str
    voter_weight: int
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
    q_num: int
    q_type: str
    q_text: str
    q_description: str | None
    total_options: int
    total_closed_options: int
    closed_options_list: List[str] | None
    max_answers: int
    min_answers: int
    include_blank_null: bool | None
    tally_type: str
    group_votes: bool | None
    num_of_winners: int | None

    class Config:
        orm_mode = True


class ElectionBase(BaseModel):
    """
    Basic election schema.
    """

    short_name: str = Field(max_length=100)
    name: str = Field(max_length=100)
    description: str | None
    election_type: ElectionTypeEnum = Field(max_length=100)
    max_weight: int
    obscure_voter_names: bool | None
    randomize_answer_order: bool | None
    election_login_type: ElectionLoginTypeEnum =Field(max_length=100)
    normalization: bool | None
    grouped: bool | None


class ElectionOut(ElectionBase):
    """
    Schema for reading/returning election data
    """

    id: int
    uuid: str
    election_status: ElectionStatusEnum
    decryptions_uploaded: int
    public_key: PublicKeyBase | None
    questions: list[QuestionBase] | None
    total_voters: int
    total_trustees: int
    encrypted_tally_hash: str | None
    result: object | None
    voters_by_weight_init: str | None
    voters_by_weight_end: str | None
    trustees: object | None


    class Config:
        orm_mode = True

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
    created_at: str

    class Config:
        orm_mode = True
