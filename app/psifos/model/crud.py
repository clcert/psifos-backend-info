"""
CRUD utils for Psifos
(Create - Read - Update - delete)

01/08/2022
"""

from sqlalchemy.orm import Session

from app.psifos.model import models


# ----- Voter CRUD Utils -----


def get_voters_by_election_id(db: Session, election_id: int, page=0, page_size=None):
    return (
        db.query(models.Voter)
        .filter(models.Voter.election_id == election_id)
        .offset(page)
        .limit(page_size)
        .all()
    )


def get_votes_by_ids(db: Session, voters_id: list):
    return (
        db.query(models.CastVote).filter(models.CastVote.voter_id.in_(voters_id)).all()
    )


# ----- CastVote CRUD Utils -----


def get_election_cast_votes(db: Session, election_uuid: str):
    return db.query(models.CastVote).filter(models.CastVote)


def get_cast_vote_by_hash(db: Session, election_uuid: str, hash_vote: str):
    return (
        db.query(models.CastVote)
        .join(models.Voter, models.Voter.id == models.CastVote.voter_id)
        .join(models.Election, models.Election.id == models.Voter.election_id)
        .filter(
            models.CastVote.vote_hash == hash_vote,
            models.Election.uuid == election_uuid,
        )
        .first()
    )


def get_hashes_vote(db: Session, election_uuid: str, voters_id: list):
    return (
        db.query(models.CastVote)
        .filter(models.CastVote.voter_id.in_(voters_id))
        .with_entities(models.CastVote.vote_hash)
        .all()
    )


# ----- AuditedBallot CRUD Utils -----
# (TODO)

# ----- Trustee CRUD Utils -----


def get_trustee_by_uuid(db: Session, trustee_uuid: str):
    return db.query(models.Trustee).filter(models.Trustee.uuid == trustee_uuid).first()


def get_trustees_by_election_id(db: Session, election_id: int, page=0, page_size=None):
    return (
        db.query(models.Trustee)
        .filter(models.Trustee.election_id == election_id)
        .offset(page)
        .limit(page_size)
        .all()
    )


# ----- SharedPoint CRUD Utils -----


# ----- Election CRUD Utils -----


def get_elections(db: Session, page: int = 0, page_size: int = None):
    return db.query(models.Election).offset(page).limit(page_size).all()


def get_election_by_short_name(db: Session, short_name: str):
    return (
        db.query(models.Election)
        .filter(models.Election.short_name == short_name)
        .first()
    )


def get_election_by_uuid(db: Session, uuid: str):
    return db.query(models.Election).filter(models.Election.uuid == uuid).first()
