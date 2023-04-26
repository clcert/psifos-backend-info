"""
CRUD utils for Psifos
(Create - Read - Update - delete)

01/08/2022
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.psifos.model import models
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import db_handler
from sqlalchemy import and_


ELECTION_QUERY_OPTIONS = [
    selectinload(models.Election.voters).selectinload(
        models.Voter.cast_vote
    ),
    selectinload(models.Election.trustees),
    selectinload(models.Election.sharedpoints),
    selectinload(models.Election.audited_ballots)
]

VOTER_QUERY_OPTIONS = selectinload(
    models.Voter.cast_vote
)

# ----- Voter CRUD Utils -----


async def get_voters_by_election_id(session: Session | AsyncSession, election_id: int, page=0, page_size=None):
    offset_value = page*page_size if page_size else None
    query = select(models.Voter).outerjoin(models.CastVote).where(
        models.Voter.election_id == election_id
    ).offset(offset_value).limit(page_size).options(
        VOTER_QUERY_OPTIONS
    )

    result = await db_handler.execute(session, query)
    return result.scalars().all()

async def get_voters_with_valid_vote(session: Session | AsyncSession, election_id: int, page=0, page_size=None):
    offset_value = page*page_size if page_size else None
    query = select(models.Voter).outerjoin(models.CastVote).where(
        models.Voter.election_id == election_id, and_(models.Voter.valid_cast_votes != 0)
    ).offset(offset_value).limit(page_size).options(
        VOTER_QUERY_OPTIONS
    )

    result = await db_handler.execute(session, query)
    return result.scalars().all()


async def get_votes_by_ids(session: Session | AsyncSession, voters_id: list):
    query = select(models.CastVote).where(models.CastVote.voter_id.in_(voters_id))
    result = await db_handler.execute(session, query)
    return result.scalars().all()


# ----- CastVote CRUD Utils -----

async def get_cast_vote_by_hash(session: Session | AsyncSession, hash_vote: str):
    query = select(models.CastVote).where(
        models.CastVote.vote_hash == hash_vote
    )
    result = await db_handler.execute(session, query)
    return result.scalars().first()


async def get_hashes_vote(session: Session | AsyncSession, voters_id: list):
    query = select(models.CastVote.vote_hash).where(
        models.CastVote.voter_id.in_(voters_id)
    )
    result = await db_handler.execute(session, query)
    return result.scalars().all()
    


# ----- AuditedBallot CRUD Utils -----
# (TODO)

# ----- Trustee CRUD Utils -----


async def get_trustee_by_uuid(session: Session | AsyncSession, trustee_uuid: str):
    query = select(models.Trustee).where(models.Trustee.uuid == trustee_uuid)
    result = await db_handler.execute(session, query)
    return result.scalars().first()


async def get_trustees_by_election_id(session: Session | AsyncSession, election_id: int, page=0, page_size=0):
    offset_value = page*page_size if page_size else None
    query = select(models.Trustee).where(
        models.Trustee.election_id == election_id
    ).offset(offset_value).limit(page_size)

    result = await db_handler.execute(session, query)
    
    return result.scalars().all()

# ----- SharedPoint CRUD Utils -----


# ----- Election CRUD Utils -----


async def get_elections(session: Session | AsyncSession, page: int = 0, page_size: int = 0):
    offset_value = page*page_size if page_size else None
    query = select(models.Election).offset(offset_value).limit(page_size).options(
        *ELECTION_QUERY_OPTIONS
    )
    result = await db_handler.execute(session, query)
    return result.scalars().all()



async def get_election_by_short_name(session: Session | AsyncSession, short_name: str):
    query = select(models.Election).where(
        models.Election.short_name == short_name
    ).options(
        *ELECTION_QUERY_OPTIONS
    )

    result = await db_handler.execute(session, query)
    return result.scalars().first()
    


async def get_election_by_uuid(session: Session | AsyncSession, uuid: str):
    query = select(models.Election).where(
        models.Election.uuid == uuid
    ).options(
        *ELECTION_QUERY_OPTIONS
    )
    result = await db_handler.execute(session, query)
    return result.scalars().first()

# ----- ElectionLogs CRUD Utils -----

async def get_election_logs(session: Session | AsyncSession, election_id: int):

    query = select(models.ElectionLog).where(
        models.ElectionLog.election_id == election_id
    )
    result = await db_handler.execute(session, query)
    return result.scalars().all()

async def get_num_casted_votes(session: Session | AsyncSession, election_id: int):
    voters = await get_voters_by_election_id(session=session, election_id=election_id)
    return len([v for v in voters if v.valid_cast_votes >= 1])

async def count_cast_vote_by_date(session: Session | AsyncSession, init_date, end_date, election_id: int):
                    
    query = select(models.CastVote.cast_at).join(
        models.Voter, models.Voter.id == models.CastVote.voter_id).where(
            models.Voter.election_id == election_id,
            and_(models.CastVote.cast_at >= init_date, 
            models.CastVote.cast_at <= end_date))
    result = await db_handler.execute(session, query)
    return result.all()