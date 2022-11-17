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
)


from app.psifos.model.enums import ElectionStatusEnum, ElectionTypeEnum
from app.database import Base
from app.psifos import utils


class Election(Base):
    __tablename__ = "psifos_election"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("auth_user.id"))
    uuid = Column(String(50), nullable=False, unique=True)

    short_name = Column(String(100), nullable=False, unique=True)
    name = Column(String(250), nullable=False)
    election_type = Column(Enum(ElectionTypeEnum), nullable=False)
    election_status = Column(Enum(ElectionStatusEnum), default="setting_up")
    private_p = Column(Boolean, default=False, nullable=False)
    description = Column(Text)

    public_key = Column(Text, nullable=True)
    private_key = Column(Text, nullable=True)  # PsifosObject: EGSecretKey
    questions = Column(Text, nullable=True)

    obscure_voter_names = Column(Boolean, default=False, nullable=False)
    randomize_answer_order = Column(Boolean, default=False, nullable=False)
    normalization = Column(Boolean, default=False, nullable=False)
    max_weight = Column(Integer, nullable=False)

    total_voters = Column(Integer, default=0)
    total_trustees = Column(Integer, default=0)

    cast_url = Column(String(500))
    encrypted_tally = Column(Text, nullable=True)
    encrypted_tally_hash = Column(Text, nullable=True)

    decryptions_uploaded = Column(Integer, default=0)
    result = Column(Text, nullable=True)

    voting_started_at = Column(DateTime, nullable=True)
    voting_ended_at = Column(DateTime, nullable=True)

    voters_by_weight_init = Column(Text, nullable=True)
    voters_by_weight_end = Column(Text, nullable=True)

    # One-to-many relationships
    voters = relationship("Voter", cascade="all, delete", backref="psifos_election")
    trustees = relationship("Trustee", cascade="all, delete", backref="psifos_election")
    sharedpoints = relationship("SharedPoint", cascade="all, delete", backref="psifos_election")
    audited_ballots = relationship("AuditedBallot", cascade="all, delete", backref="psifos_election")


class Voter(Base):
    __tablename__ = "psifos_voter"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey("psifos_election.id", onupdate="CASCADE", ondelete="CASCADE"))
    uuid = Column(String(50), nullable=False, unique=True)

    voter_login_id = Column(String(100), nullable=False)
    voter_name = Column(String(200), nullable=False)
    voter_weight = Column(Integer, nullable=False)

    valid_cast_votes = Column(Integer, default=0)
    invalid_cast_votes = Column(Integer, default=0)
    
    # One-to-one relationship
    cast_vote = relationship("CastVote", cascade="all, delete", backref="psifos_voter", uselist=False)


class CastVote(Base):
    __tablename__ = "psifos_cast_vote"

    id = Column(Integer, primary_key=True, index=True)
    voter_id = Column(Integer, ForeignKey("psifos_voter.id", onupdate="CASCADE", ondelete="CASCADE"), unique=True)

    vote = Column(Text, nullable=False)
    vote_hash = Column(String(500), nullable=False)
    # vote_tinyhash = Column(String(500), nullable=False)

    is_valid = Column(Boolean, nullable=False)
    
    cast_ip = Column(Text, nullable=False)
    cast_ip_hash = Column(String(500), nullable=False)

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
    election_id = Column(Integer, ForeignKey("psifos_election.id", onupdate="CASCADE", ondelete="CASCADE"))
    trustee_id = Column(
        Integer, nullable=False
    )  # TODO: rename to index for deambiguation with trustee_id func. param at await crud.py
    uuid = Column(String(50), nullable=False, unique=True)

    name = Column(String(200), nullable=False)
    trustee_login_id = Column(String(100), nullable=False)
    email = Column(Text, nullable=False)
    secret = Column(String(100))

    current_step = Column(Integer, default=0)

    public_key = Column(Text, nullable=True)
    public_key_hash = Column(String(100), nullable=True)
    secret_key = Column(Text, nullable=True)  # PsifosObject: EGSecretKey
    pok = Column(Text, nullable=True)  # PsifosObject: DLogProof

    decryptions = Column(Text, nullable=True)

    certificate = Column(Text, nullable=True)
    coefficients = Column(Text, nullable=True)
    acknowledgements = Column(Text, nullable=True)


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
