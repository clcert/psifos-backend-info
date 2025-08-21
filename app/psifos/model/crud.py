"""
CRUD utils for Psifos
(Create - Read - Update - delete)

01/08/2022
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.psifos.model import models
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload
from app.database import db_handler
from sqlalchemy import and_


ELECTION_QUERY_OPTIONS = [
    selectinload(models.Election.public_key),
]

COMPLETE_ELECTION_QUERY_OPTIONS = [
    selectinload(models.Election.trustees),
    selectinload(models.Election.sharedpoints),
    selectinload(models.Election.audited_ballots),
    selectinload(models.Election.voters),
    selectinload(models.Election.public_key),
    selectinload(models.Election.questions),
    selectinload(models.Election.result),
]

VOTER_QUERY_OPTIONS = [selectinload(
    models.Voter.cast_vote
)]

# ----- Voter CRUD Utils -----


async def get_voters_by_election_id(session: Session | AsyncSession, election_id: int, page=0, page_size=None, simple: bool = False):

    query_options = [] if simple else VOTER_QUERY_OPTIONS
    offset_value = page*page_size if page_size else None
    query = select(models.Voter).where(
        models.Voter.election_id == election_id
    ).offset(offset_value).limit(page_size).options(
        *query_options
    )

    result = await db_handler.execute(session, query)
    return result.scalars().all()

async def get_voters_by_group_and_weight_initial(session: Session | AsyncSession, election_id: int):
    query = select(
        models.Voter.group,
        models.Voter.weight_init,
        func.count(models.Voter.id).label('voter_count')
    ).where(
        models.Voter.election_id == election_id
    ).group_by(
        models.Voter.group,
        models.Voter.weight_init
    )

    result = await db_handler.execute(session, query)
    return result.all()


async def get_voters_by_group_and_weight_valid(session: Session | AsyncSession, election_id: int):
    query = (
        select(
            models.Voter.group,
            models.Voter.weight_init,
            models.Voter.weight_end,
            func.count(models.Voter.id).label("voter_count"),
        )
        .outerjoin(models.CastVote)
        .where(models.Voter.election_id == election_id, and_(models.CastVote.is_valid))
        .group_by(models.Voter.group, models.Voter.weight_init, models.Voter.weight_end)
    )

    result = await db_handler.execute(session, query)
    return result.all()


async def get_voters_group_by_election_id(session: Session | AsyncSession, election_id: int, group: str, page=0, page_size=None, simple: bool = False):

    query_options = [] if simple else VOTER_QUERY_OPTIONS
    offset_value = page*page_size if page_size else None
    query = select(models.Voter).outerjoin(models.CastVote).where(
        models.Voter.election_id == election_id, models.Voter.group == group
    ).offset(offset_value).limit(page_size).options(
        *query_options
    )

    result = await db_handler.execute(session, query)
    return result.scalars().all()


async def get_voters_with_valid_vote(session: Session | AsyncSession, election_id: int, page=0, page_size=None):
    offset_value = page*page_size if page_size else None
    query = select(models.Voter).outerjoin(models.CastVote).where(
        models.Voter.election_id == election_id, and_(
            models.CastVote.is_valid)
    ).offset(offset_value).limit(page_size).options(
        *VOTER_QUERY_OPTIONS
    )

    result = await db_handler.execute(session, query)
    return result.scalars().all()


async def get_votes_by_ids(session: Session | AsyncSession, voters_id: list):
    query = select(models.CastVote).where(
        models.CastVote.voter_id.in_(voters_id))
    result = await db_handler.execute(session, query)
    return result.scalars().all()


# ----- CastVote CRUD Utils -----

async def get_cast_vote_by_hash(session: Session | AsyncSession, hash_vote: str):
    query = select(models.CastVote).where(
        models.CastVote.encrypted_ballot_hash == hash_vote
    )
    result = await db_handler.execute(session, query)
    return result.scalars().first()

async def get_public_vote_by_hash(session: Session | AsyncSession, hash_vote: str):
    query = select(models.Vote).where(
        models.Vote.vote_hash == hash_vote
    )
    result = await db_handler.execute(session, query)
    return result.scalars().first()

async def get_hashes_vote(session: Session | AsyncSession, voters_id: list):
    query = select(models.CastVote.encrypted_ballot_hash).where(
        models.CastVote.voter_id.in_(voters_id)
    )
    result = await db_handler.execute(session, query)
    return result.scalars().all()

async def has_valid_vote(session: Session | AsyncSession, voter_id: int):
    query = select(models.CastVote).where(
        models.CastVote.voter_id == voter_id, models.CastVote.is_valid == True
    )
    result = await db_handler.execute(session, query)
    return result.scalars().first()


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


async def get_election_by_short_name(session: Session | AsyncSession, short_name: str, simple: bool = False):
    query_options = ELECTION_QUERY_OPTIONS if simple else COMPLETE_ELECTION_QUERY_OPTIONS
    query = select(models.Election).where(
        models.Election.short_name == short_name
    ).options(
        *query_options
    )

    result = await db_handler.execute(session, query)
    return result.scalars().first()

async def get_election_options_by_name(session: Session | AsyncSession, short_name: str, options: list):
    query = select(*options).where(
        models.Election.short_name == short_name
    )

    result = await db_handler.execute(session, query)
    return result.first()

async def get_election_status_by_short_name(session: Session | AsyncSession, short_name: str):
    query = select(models.Election.status).where(
        models.Election.short_name == short_name
    )
    result = await db_handler.execute(session, query)
    return result.scalars().first()

async def get_election_id_by_short_name(session: Session | AsyncSession, short_name: str):
    query = select(models.Election.id).where(
        models.Election.short_name == short_name
    )
    result = await db_handler.execute(session, query)
    return result.scalars().first()

async def get_total_voters_by_election_id(session: Session | AsyncSession, election_id: int):
    query = select(func.count(models.Voter.id)).where(
        models.Voter.election_id == election_id
    )
    result = await db_handler.execute(session, query)
    return result.scalar()

async def get_total_trustees_by_election_id(session: Session | AsyncSession, election_id: int):
    query = select(func.count(models.TrusteeCrypto.trustee_id)).where(
        models.TrusteeCrypto.election_id == election_id
    )
    result = await db_handler.execute(session, query)
    return result.scalar()

# ----- ElectionLogs CRUD Utils -----


async def get_election_logs(session: Session | AsyncSession, election_id: int):

    query = select(models.ElectionLog).where(
        models.ElectionLog.election_id == election_id
    )
    result = await db_handler.execute(session, query)
    return result.scalars().all()

async def get_election_logs_by_event(session: Session | AsyncSession, election_id: int, event: str):    
    query = select(models.ElectionLog).where(
        models.ElectionLog.election_id == election_id,
        models.ElectionLog.event == event
    )
    result = await db_handler.execute(session, query)
    return result.scalars().all()

async def get_num_casted_votes(session: Session | AsyncSession, election_id: int):
    query = (
        select(func.count(distinct(models.CastVote.voter_id)))
        .join(models.Voter, models.Voter.id == models.CastVote.voter_id)
        .where(models.Voter.election_id == election_id)
        .where(models.CastVote.is_valid == True)
    )
    
    result = await session.scalar(query)    
    return result or 0

async def get_num_public_casted_votes(session: Session | AsyncSession, election_id: int):
    query = (
        select(func.count(distinct(models.Vote.voter_id)))
        .join(models.Voter, models.Voter.id == models.Vote.voter_id)
        .where(models.Voter.election_id == election_id)
        .where(models.Vote.is_valid == True)
    )
    
    result = await session.scalar(query)    
    return result or 0

async def get_num_casted_votes_group(session: Session | AsyncSession, election_id: int, group: str):
    voters = await get_voters_group_by_election_id(session=session, election_id=election_id, group=group)
    return len([v for v in voters if await has_valid_vote(session=session, voter_id=v.id)])

async def count_cast_vote_by_date(session: Session | AsyncSession, init_date, end_date, election_id: int):

    query = select(models.CastVote.cast_at).join(
        models.Voter, models.Voter.id == models.CastVote.voter_id).where(
            models.Voter.election_id == election_id,
            and_(models.CastVote.cast_at >= init_date,
                 models.CastVote.cast_at <= end_date))
    result = await db_handler.execute(session, query)
    return result.all()

# === Public Key ===
async def get_public_key_by_id(session: Session | AsyncSession, public_key_id: int):
    query = select(models.PublicKey).where(models.PublicKey.id == public_key_id)
    result = await db_handler.execute(session, query)
    return result.scalars().first()

async def get_decryption_by_trustee_id(session: Session | AsyncSession, trustee_crypto_id: int):
    query = select(models.HomomorphicDecryption).where(models.HomomorphicDecryption.trustee_crypto_id == trustee_crypto_id)
    result = await db_handler.execute(session, query)
    result = result.scalars().all()
    if not result:
        query = select(models.MixnetDecryption).where(models.MixnetDecryption.trustee_crypto_id == trustee_crypto_id)
        result = await db_handler.execute(session, query)
        result = result.scalars().all()
    return result

# === Trustee Crypto ===
async def get_trustee_crypto_by_id(session: Session | AsyncSession, trustee_crypto_id: int):
    query = select(models.TrusteeCrypto).where(models.TrusteeCrypto.id == trustee_crypto_id)
    result = await db_handler.execute(session, query)
    return result.scalars().first()

async def get_trustee_crypto_params_by_election_id(session: Session | AsyncSession, election_id: int, params: list):
    query = select(*params).where(
        models.TrusteeCrypto.election_id == election_id
    )
    result = await db_handler.execute(session, query)
    return result.all()

# === Questions ===

async def get_questions_by_election_id(session: Session | AsyncSession, election_id: int):
    query = select(models.AbstractQuestion).where(
        models.AbstractQuestion.election_id == election_id
    )
    result = await db_handler.execute(session, query)
    return result.scalars().all()

async def get_questions_params_by_election_id(session: Session | AsyncSession, election_id: int, params: list):
    query = select(*params).where(
        models.AbstractQuestion.election_id == election_id
    )
    result = await db_handler.execute(session, query)
    return result.all()
