from app.psifos.utils import paginate, tz_now, from_json
from fastapi import APIRouter, Depends
from app.dependencies import get_session
from app.psifos.model import crud, schemas
from app.psifos.model import bundle_schemas
from sqlalchemy.orm import Session
from urllib.parse import unquote
from sqlalchemy.ext.asyncio import AsyncSession
from app.psifos.model.enums import ElectionPublicEventEnum
from datetime import timedelta
from app.psifos.model import models

import datetime
import json

from unidecode import unidecode

# api_router = APIRouter(prefix="/psifos/api/public")
api_router = APIRouter()

# ----- Election routes -----


@api_router.post("/elections", response_model=list[schemas.ElectionOut], status_code=200)
async def get_elections(data: dict = {}, session: Session | AsyncSession = Depends(get_session)):

    """
    POST

    This route gets all the elections that exist in the system.
    It has an optional parameter in the body to page them:

    {
      page: The page number you want to get
      page_size: Number of elements to display per page
    }

    """

    page, page_size = paginate(data)
    return await crud.get_elections(session=session, page=page, page_size=page_size)


@api_router.get("/election/{short_name}", response_model=schemas.ElectionOut, status_code=200)
async def get_election(short_name: str, session: Session | AsyncSession = Depends(get_session)):

    """
    GET

    This route delivers all public data of an election

    """

    return await crud.get_election_by_short_name(session=session, short_name=short_name)


@api_router.get("/election/{short_name}/result", status_code=200)
async def get_election_results(short_name: str, session: Session | AsyncSession = Depends(get_session)):

    """
    GET

    This route delivers the results of an election

    """
    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    return election.result


@api_router.get("/get-election-stats/{short_name}", status_code=200)
async def get_election_stats(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    Route for getting the stats of a specific election.
    """

    query_options = [
        models.Election.id,
        models.Election.total_voters,
        models.Election.election_status,
        models.Election.short_name
    ]

    election = await crud.get_election_options_by_name(session=session, short_name=short_name, options=query_options)
    return {
        "num_casted_votes": await crud.get_num_casted_votes(
            session=session,
            election_id=election.id
        ),
        "total_voters": election.total_voters,
        "status": election.election_status,
        "name": election.short_name
    }


@api_router.post("/get-election-group-stats/{short_name}", status_code=200)
async def get_election_group_stats(short_name: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):
    """
    Route for getting the stats of a specific election.
    """
    group = data.get("group")
    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    group_voters = await crud.get_voters_group_by_election_id(session=session, election_id=election.id, group=group)
    return {
        "num_casted_votes": await crud.get_num_casted_votes_group(
            session=session,
            election_id=election.id,
            group=group
        ),
        "total_voters": len(group_voters),
        "status": election.election_status,
        "name": election.short_name
    }


@api_router.post("/{short_name}/count-dates", status_code=200)
async def get_count_votes_by_date(short_name: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):
    """
    Return the number of votes per deltaTime from the start of the election until it ends

    """

    election = await crud.get_election_by_short_name(session=session, short_name=short_name)

    if election.election_status == "Setting up":
        return {}

    date_init = election.voting_started_at
    date_end = election.voting_ended_at if election.voting_ended_at else tz_now()
    date_end = datetime.datetime(year=date_end.year, month=date_end.month, day=date_end.day,
                                 hour=date_end.hour, minute=date_end.minute, second=date_end.second)

    delta_minutes = data.get("minutes", 60)
    count_cast_votes = {}

    while date_init <= date_end:

        date_delta = date_init + timedelta(minutes=delta_minutes)
        dates = await crud.count_cast_vote_by_date(session=session, election_id=election.id, init_date=date_init, end_date=date_delta)
        count_cast_votes[str(date_init)] = len(dates)
        date_init = date_delta

    return count_cast_votes


@api_router.get("/{short_name}/resume", status_code=200)
async def resume(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    Route for get a resume election
    """
    election = await crud.get_election_by_short_name(session=session, short_name=short_name, simple=True)
    voters = await crud.get_voters_by_election_id(session=session, election_id=election.id, simple=True)

    valid_voters = [v for v in voters if v.valid_cast_votes >= 1]
    voters_group = {}
    votes_election = {}

    for v in valid_voters:
        normalized_weight = v.voter_weight / election.max_weight
        voters_group.setdefault(v.group, []).append(normalized_weight)
        votes_election[normalized_weight] = votes_election.get(
            normalized_weight, 0) + 1

    votes_by_weight = [{"group": group, "weights": {str(w): value.count(
        w) for w in value}} for group, value in voters_group.items()]

    votes_by_weight = json.dumps({
        "voters_by_weight": votes_election,
        "voters_by_weight_grouped": votes_by_weight
    })

    return {
        "weights_init": election.voters_by_weight_init,
        "weights_election": votes_by_weight,
        "weights_end": election.voters_by_weight_end
    }


@api_router.get("/election/{short_name}/election-logs", response_model=list[schemas.ElectionLogOut], status_code=200)
async def election_logs(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    GET

    Is used to obtain the different logs of an election

    """

    election_id = await crud.get_election_id_by_short_name(session=session, short_name=short_name)
    election_logs = await crud.get_election_logs(session=session, election_id=election_id)
    election_logs = list(filter(
        lambda log: ElectionPublicEventEnum.has_member_key(log.event), election_logs))
    return election_logs


@api_router.get("/election/{short_name}/bundle-file", response_model=bundle_schemas.Bundle, status_code=200)
async def election_bundle_file(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    GET

    It is used to get all the necessary values ​​for the bundle file.

    """

    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    election.public_key = from_json(election.public_key)
    election.questions = from_json(election.questions)
    voters = [bundle_schemas.VoterBundle.from_orm(v) for v in election.voters]
    voters_id = [v.id for v in election.voters]

    # Get votes by uuid and voter uuid
    votes = await crud.get_votes_by_ids(session=session, voters_id=voters_id)
    votes = [bundle_schemas.VoteBundle.from_orm(v) for v in votes]
    votes = list(map(lambda v: {"vote": from_json(v.vote), "vote_hash": v.vote_hash,
                 "cast_at": v.cast_at, "voter_login_id": v.psifos_voter.voter_login_id}, votes))

    # Lets decode string to json
    trustee_out = []
    for t in election.trustees:
        t.public_key = await crud.get_public_key_by_id(session=session, public_key_id=t.public_key_id)
        t.decryptions = await crud.get_decryption_by_trustee_id(session=session, trustee_id=t.id)
        t.certificate = from_json(t.certificate)
        t.coefficients = from_json(t.coefficients)
        t.acknowledgements = from_json(t.acknowledgements)
        trustee_out.append(t)

    return bundle_schemas.Bundle(election=bundle_schemas.ElectionBundle.from_orm(election),
                                 voters=voters,
                                 votes=votes,
                                 result=from_json(election.result),
                                 trustees=trustee_out)


@api_router.get("/election/{short_name}/get_status", status_code=200)
async def get_election_status(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    GET

    Returns the status of an election
    """
    election_status = await crud.get_election_status_by_short_name(session=session, short_name=short_name)
    return {
        "election_short_name": short_name,
        "status": election_status
    }


# ----- Voters routes -----


@api_router.post("/election/{short_name}/voters", response_model=list[schemas.VoterOut], status_code=200)
async def get_voters(short_name: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):
    """
    POST

    This route delivers all voters in an election with their public data
    It has an optional parameter in the body to page them:

    {
      page: The page number you want to get
      page_size: Number of elements to display per page
    }
    """
    page, page_size = paginate(data)

    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    return await crud.get_voters_by_election_id(session=session, election_id=election.id, page=page, page_size=page_size)


# ----- Trustee routes -----

@api_router.post("/election/{short_name}/trustees", status_code=200)
async def get_trustees_election(short_name: str, data: dict = None, session: Session | AsyncSession = Depends(get_session)):
    """
    POST

    This route delivers all trustees in an election with their public data
    It has an optional parameter in the body to page them:

    {
      page: The page number you want to get
      page_size: Number of elements to display per page
    }
    """

    page, page_size = paginate(data)

    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    return await crud.get_trustees_by_election_id(session=session, election_id=election.id, page=page, page_size=page_size)


@api_router.get("/trustee/{trustee_uuid}", response_model=schemas.TrusteeOut, status_code=200)
async def get_trustee(trustee_uuid: str, session: Session | AsyncSession = Depends(get_session)):

    """
    GET

    This route delivers the public information of a trustee with the corresponding uuid
    """
    return await crud.get_trustee_by_uuid(session=session, trustee_uuid=trustee_uuid)


# ----- CastVote routes -----

@api_router.post("/election/{short_name}/cast-votes", response_model=list[schemas.CastVoteOut], status_code=200)
async def get_cast_votes(short_name: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):

    """
    This route delivers all the cast votes of an election
    It has an optional parameter in the body to page them:

    {
      page: The page number you want to get
      page_size: Number of elements to display per page
    }

    """

    page, page_size = paginate(data)

    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    voters = await crud.get_voters_by_election_id(session=session, election_id=election.id, page=page, page_size=page_size)
    voters_id = [v.id for v in voters]
    return await crud.get_votes_by_ids(session=session, voters_id=voters_id)


@api_router.get("/election/{short_name}/cast-vote/{hash_vote:path}", response_model=schemas.CastVoteOut, status_code=200)
async def get_vote_by_hash(short_name: str, hash_vote, session: Session | AsyncSession = Depends(get_session)):

    """
    This route return a cast vote by its hash

    """
    hash_vote = unquote(unquote(hash_vote))
    return await crud.get_cast_vote_by_hash(session=session, hash_vote=hash_vote)


@api_router.post("/election/{short_name}/votes", response_model=schemas.UrnaOut, status_code=200)
async def get_votes(short_name: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):

    """
    POST

    This route delivers a list of voters according to the hash of the corresponding vote,
    it is used to display the electronic ballot box

    """

    page = data.get("page", 0)
    page_size = data.get("page_size", 50)
    vote_hash = data.get("vote_hash", "")
    voter_name = data.get("voter_name", "")
    only_with_valid_vote = data.get("only_with_valid_vote")
    election = await crud.get_election_by_short_name(session=session, short_name=short_name)

    if only_with_valid_vote:
        voters = await crud.get_voters_with_valid_vote(session=session, election_id=election.id)
    else:
        voters = await crud.get_voters_by_election_id(session=session, election_id=election.id)

    if voter_name != "":
        voters = list(
            filter(lambda v: (unidecode(voter_name.lower()) in unidecode(v.voter_name.lower())) or (unidecode(voter_name.lower()) in unidecode(v.voter_login_id.lower())), voters))
            # filter(lambda v: voter_name.lower() in v.voter_name.lower(), voters))
        return schemas.UrnaOut(voters=voters, position=0, more_votes=False, total_votes=len(voters))

    elif vote_hash != "":
        voters_id = [v.id for v in voters]
        hash_votes = await crud.get_hashes_vote(session=session, voters_id=voters_id)

        if (vote_hash,) in hash_votes:
            index_hash = hash_votes.index((vote_hash,))
            page = index_hash - (index_hash % page_size)

    if only_with_valid_vote:
        voters_page = await crud.get_voters_with_valid_vote(session=session, election_id=election.id, page=page, page_size=page_size)
        voters_next_page = await crud.get_voters_with_valid_vote(session=session, election_id=election.id, page=page + 1, page_size=page_size)

    else:
        voters_page = await crud.get_voters_by_election_id(session=session, election_id=election.id, page=page, page_size=page_size)
        voters_next_page = await crud.get_voters_by_election_id(session=session, election_id=election.id, page=page + 1, page_size=page_size)

    voters_page = [schemas.VoterCastVote.from_orm(v) for v in voters_page]
    more_votes = len(voters_next_page) != 0

    return schemas.UrnaOut(voters=voters_page, position=page, more_votes=more_votes, total_votes=len(voters))
