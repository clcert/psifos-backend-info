"""
SQLAlchemy Models for Psifos.

01-04-2022
"""

from __future__ import annotations

from sqlalchemy.orm import relationship
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum,
    DateTime,
    JSON,
)
from sqlalchemy.dialects.mysql import LONGTEXT


from app.psifos.model.enums import ElectionStatusEnum, ElectionTypeEnum, ElectionLoginTypeEnum, TrusteeStepEnum
from app.database import Base
from app.psifos import utils

import enum
import json


class Election(Base):
    __tablename__ = "psifos_election"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("auth_user.id"))

    short_name = Column(String(50), nullable=False, unique=True)
    long_name = Column(String(150), nullable=False)
    type = Column(Enum(ElectionTypeEnum), nullable=False)
    status = Column(Enum(ElectionStatusEnum), default="setting_up")
    voters_login_type =  Column(Enum(ElectionLoginTypeEnum), default="close_p")
    description = Column(Text)
    
    public_key_id = Column(Integer, ForeignKey("psifos_public_keys.id", ondelete="CASCADE"), nullable=True, unique=True)
    public_key = relationship("PublicKey", back_populates="elections", uselist=False, cascade="all, delete")

    questions = relationship("AbstractQuestion", cascade="all, delete", back_populates="election")

    obscure_voter_names = Column(Boolean, default=False, nullable=False) # Lo eliminamos?
    randomized_options = Column(Boolean, default=False, nullable=False)
    normalized = Column(Boolean, default=False, nullable=False)
    grouped_voters = Column(Boolean, default=False, nullable=False)
    max_weight = Column(Integer, nullable=False)

    decryptions_uploaded = Column(Integer, default=0)

    result = relationship("Results",uselist=False, cascade="all, delete", backref="psifos_election")


    # One-to-many relationships
    voters = relationship("Voter", cascade="all, delete",
                          backref="psifos_election")
    trustees = relationship(
        "TrusteeCrypto", cascade="all, delete", backref="psifos_election")
    sharedpoints = relationship(
        "SharedPoint", cascade="all, delete", backref="psifos_election"
    ) # TODO: Check 
    audited_ballots = relationship(
        "AuditedBallot", cascade="all, delete", backref="psifos_election"
    )

    @property
    def total_trustees(self):
        return len(self.trustees)
    
    @property
    def decryptions_uploaded(self):
        sent_decryptions_trustees = [t for t in self.trustees if t.current_step == TrusteeStepEnum.decryptions_sent]
        return len(sent_decryptions_trustees)
    
    @property
    def total_questions(self):
        return len(self.questions)

class Voter(Base):
    __tablename__ = "psifos_voter"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(
        Integer,
        ForeignKey("psifos_election.id",
                   onupdate="CASCADE", ondelete="CASCADE"),
    )
    username = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)

    username_election_id = Column(String(50), nullable=False, unique=True)
    weight_init = Column(Integer, nullable=False)
    weight_end = Column(Integer, nullable=True)

    group = Column(String(200), nullable=True)
    # One-to-one relationship
    cast_vote = relationship(
        "CastVote", cascade="all, delete", backref="psifos_voter", uselist=False
    )

class CastVote(Base):
    __tablename__ = "psifos_cast_vote"

    id = Column(Integer, primary_key=True, index=True)
    voter_id = Column(
        Integer,
        ForeignKey("psifos_voter.id", onupdate="CASCADE", ondelete="CASCADE"),
        unique=True,
    )

    encrypted_ballot = Column(Text, nullable=False)
    encrypted_ballot_hash = Column(String(500), nullable=False)

    is_valid = Column(Boolean, nullable=False)
    cast_at = Column(DateTime, nullable=False)

class AuditedBallot(Base):
    __tablename__ = "psifos_audited_ballot"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("psifos_election.id", onupdate="CASCADE", ondelete="CASCADE"))

    raw_vote = Column(Text)
    vote_hash = Column(String(500))
    added_at = Column(DateTime, default=utils.tz_now())


class Trustee(Base):
    __tablename__ = "psifos_trustee"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(Text, nullable=False)
    trustee_crypto = relationship(
        "TrusteeCrypto", cascade="all, delete",
        back_populates="trustee"
    ) 

class TrusteeCrypto(Base):
    __tablename__ = "psifos_trustee_crypto"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(
        Integer,
        ForeignKey("psifos_election.id",
                   onupdate="CASCADE", ondelete="CASCADE"),
    )
    trustee_id = Column(
        Integer,
        ForeignKey("psifos_trustee.id",
                   onupdate="CASCADE", ondelete="CASCADE"),
    )

    trustee_election_id = Column(
        Integer, nullable=False
    )  # TODO: rename to index for deambiguation with trustee_id func. param at await crud.py

    current_step = Column(Integer, default=0)

    public_key = relationship("PublicKey", back_populates="trustees", uselist=False, single_parent=True)
    public_key_id = Column(Integer, ForeignKey("psifos_public_keys.id"), nullable=True, unique=True)

    public_key_hash = Column(String(100), nullable=True)
    decryptions_homomorphic = relationship(
        "HomomorphicDecryption", cascade="all, delete", back_populates="trustee_crypto"
    )
    decryptions_mixnet = relationship(
        "MixnetDecryption", cascade="all, delete", back_populates="trustee_crypto"
    )
    certificate = Column(Text, nullable=True)
    coefficients = Column(Text, nullable=True)
    acknowledgements = Column(Text, nullable=True)

    trustee = relationship("Trustee", back_populates="trustee_crypto")

    def get_decryptions_group(self, group):
        if self.decryptions:
            decryptions_group = filter(
                lambda dic: dic.group == group, self.decryptions.instances
            )
            return next(decryptions_group)
        return None
class SharedPoint(Base):
    __tablename__ = "psifos_shared_point"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("psifos_election.id", onupdate="CASCADE", ondelete="CASCADE"))

    sender = Column(Integer, nullable=False)
    recipient = Column(Integer, nullable=False)
    point = Column(Text, nullable=True)


class ElectionLog(Base):
    __tablename__ = "election_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("psifos_election.id", onupdate="CASCADE", ondelete="CASCADE"))
    
    log_level = Column(String(200), nullable=False)
    
    event = Column(String(200), nullable=False)
    event_params = Column(String(200), nullable=False)
    
    created_at = Column(String(200), nullable=False)

class Results(Base):
    __tablename__ = "psifos_results"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("psifos_election.id"), nullable=False, unique=True)
    total_result = Column(JSON, nullable=False)
    grouped_result = Column(JSON, nullable=True)

    election = relationship("Election", back_populates="result")

    def __init__(self, *args, **kwargs):
        super(Results, self).__init__(*args, **kwargs)

class QuestionTypeEnum(str, enum.Enum):
    CLOSED = "CLOSED"
    MIXNET = "MIXNET"
    STVNC = "STVNC"

class AbstractQuestion(Base):
    __tablename__ = "psifos_questions"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("psifos_election.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    index = Column(Integer, nullable=False)
    type = Column(Enum(QuestionTypeEnum), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    formal_options = Column(JSON, nullable=True)
    max_answers = Column(Integer, nullable=False)
    min_answers = Column(Integer, nullable=False) 
    include_informal_options = Column(String(50), nullable=True)
    tally_type = Column(String(50), nullable=False)
    grouped_options = Column(String(50), nullable=True)
    num_of_winners = Column(Integer, nullable=True)
    excluded_options = Column(Boolean, nullable=True)
    options_specifications = Column(JSON, nullable=True)
    open_option_max_size = Column(Integer, nullable=True)
    total_open_options = Column(Integer, nullable=True)

    election = relationship("Election", back_populates="questions", cascade="all, delete")
    encrypted_tally = relationship("Tally", back_populates="question")

    decryptions_homomorphic = relationship(
        "HomomorphicDecryption", cascade="all, delete", back_populates="question"
    )
    decryptions_mixnet = relationship(
        "MixnetDecryption", cascade="all, delete", back_populates="question"
    )

    TALLY_TYPE_MAP = {
        QuestionTypeEnum.CLOSED: "HOMOMORPHIC",
        QuestionTypeEnum.MIXNET: "MIXNET",
        QuestionTypeEnum.STVNC: "STVNC"
    }

    def __init__(self, *args, **kwargs):
        super(AbstractQuestion, self).__init__(*args, **kwargs)
        self.tally_type = self.TALLY_TYPE_MAP.get(self.type, "CLOSED")
    
    @property
    def total_options(self):
        """Calculate the length of formal_options if it exists, otherwise return 0."""
        if not self.formal_options:
            return 0

        informal_options_count = 2 if self.include_informal_options else 0
        return len(self.formal_options) + informal_options_count
class PublicKey(Base):
    __tablename__ = "psifos_public_keys"

    id = Column(Integer, primary_key=True, index=True)
    _y = Column('y', Text, nullable=False)  # Usa un nombre interno para la columna en la base de datos
    _p = Column('p', Text, nullable=False)
    _g = Column('g', Text, nullable=False)
    _q = Column('q', Text, nullable=False)

    trustees = relationship("TrusteeCrypto", back_populates="public_key")
    elections = relationship("Election", back_populates="public_key")

    @property
    def y(self):
        return int(self._y)

    @y.setter
    def y(self, value):
        self._y = str(value)

    @property
    def p(self):
        return int(self._p)

    @p.setter
    def p(self, value):
        self._p = str(value)

    @property
    def g(self):
        return int(self._g)

    @g.setter
    def g(self, value):
        self._g = str(value)

    @property
    def q(self):
        return int(self._q)

    @q.setter
    def q(self, value):
        self._q = str(value)
    
    def __repr__(self):
        return f"PublicKey(id={self.id}, y={self.y}, p={self.p}, g={self.g}, q={self.q})"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'y': (self._y),
            'p': (self._p),
            'g': (self._g),
            'q': (self._q)
        }

class TallyTypeEnum(str, enum.Enum):
    HOMOMORPHIC = "HOMOMORPHIC"
    MIXNET = "MIXNET"
    STVNC = "STVNC"

class Tally(Base):
    __tablename__ = "psifos_tallies"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("psifos_questions.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    group = Column(Text, nullable=False)
    with_votes = Column(Boolean, default=False)
    tally_type = Column(Enum(TallyTypeEnum), nullable=False)
    computed = Column(Boolean, default=False)
    num_tallied = Column(Integer, nullable=False, default=0)
    encrypted_tally = Column(LONGTEXT, nullable=False, default=[])

    question = relationship("AbstractQuestion", cascade="all, delete", back_populates="encrypted_tally")

    @property
    def index(self):
        """Calculate the length of formal_options if it exists, otherwise return 0."""
        if not self.question:
            return None
        return self.question.index
    
    @property
    def num_options(self):
        """Calculate the length of formal_options if it exists, otherwise return 0."""
        if not self.question:
            return 0
        return self.question.total_options

class HomomorphicTally(Tally):
    """
    Homomorhic tally implementation for closed questions.
    """

    __mapper_args__ = {
        'polymorphic_identity': TallyTypeEnum.HOMOMORPHIC,
    }

    def __init__(self, tally=None, **kwargs) -> None:
        """
        HomomorphicTally constructor, allows the creation of this tally.
        
        If computed==False then questions cannot be None.
        Else, tally cannot be None
        """
        super(HomomorphicTally, self).__init__(**kwargs)

class MixnetTally(Tally):
    """
    Mixnet tally implementation for open questions.
    """
    __mapper_args__ = {
        'polymorphic_identity': TallyTypeEnum.MIXNET,
    }


    def __init__(self, tally=None, **kwargs) -> None:
        super(MixnetTally, self).__init__(**kwargs)
        self.tally_type = "mixnet"

class STVTally(MixnetTally):

    __mapper_args__ = {
        'polymorphic_identity': TallyTypeEnum.STVNC,
    }

    def __init__(self, tally=None, **kwargs) -> None:
        MixnetTally.__init__(self, tally, **kwargs)
        self.tally_type = "stvnc"
        self.num_of_winners = int(kwargs["num_of_winners"])
        self.include_blank_null = kwargs["include_blank_null"]
        self.max_answers = int(kwargs["max_answers"])

class HomomorphicDecryption(Base):
    """
    Implementation of a Trustee's partial decryption
    of an election question with an homomorphic tally.
    """

    __tablename__ = "psifos_decryptions_homomorphic"

    id = Column(Integer, primary_key=True, index=True)
    trustee_crypto_id = Column(Integer, ForeignKey("psifos_trustee_crypto.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("psifos_questions.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    group = Column(Text, nullable=False)

    trustee_crypto = relationship("TrusteeCrypto", back_populates="decryptions_homomorphic", cascade="all, delete")
    question = relationship("AbstractQuestion", cascade="all, delete", back_populates="decryptions_homomorphic")

    decryption_factors = Column(Text, nullable=True)
    decryption_proofs = Column(Text, nullable=True)

    @property
    def index(self):
        return self.question.index


class MixnetDecryption(Base):
    """
    Implementation of a Trustee's partial decryption
    of an election question with an mixnet tally.

    # TODO: Implement this type of decryption.
    """

    __tablename__ = "psifos_decryptions_mixnet"

    id = Column(Integer, primary_key=True, index=True)
    trustee_crypto_id = Column(Integer, ForeignKey("psifos_trustee_crypto.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("psifos_questions.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    group = Column(Text, nullable=False)

    trustee_crypto = relationship("TrusteeCrypto", back_populates="decryptions_mixnet", cascade="all, delete")
    question = relationship("AbstractQuestion", cascade="all, delete", back_populates="decryptions_mixnet")

    decryption_factors = Column(Text, nullable=True)
    decryption_proofs = Column(Text, nullable=True)

    @property
    def index(self):
        return self.question.index