from app.psifos.utils import paginate, tz_now, from_json
from fastapi import APIRouter, Depends
from app.dependencies import get_session
from app.psifos.model import crud, schemas
from app.psifos.model import bundle_schemas
from sqlalchemy.orm import Session
from urllib.parse import unquote
from sqlalchemy.ext.asyncio import AsyncSession
from app.psifos.model.enums import ElectionPublicEventEnum, TrusteeStepEnum, ElectionStatusEnum, ElectionLoginTypeEnum
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
        models.Election.status,
        models.Election.short_name
    ]

    election = await crud.get_election_options_by_name(session=session, short_name=short_name, options=query_options)
    total_voters = await crud.get_total_voters_by_election_id(session=session, election_id=election.id)
    return {
        "num_casted_votes": await crud.get_num_casted_votes(
            session=session,
            election_id=election.id
        ),
        "total_voters": total_voters,
        "status": election.status,
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
        "status": election.status,
        "name": election.short_name
    }

@api_router.get("/{short_name}/get-questions", status_code=200)
async def get_questions(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    Route for get the questions of an election
    """
    election_params = [models.Election.id]
    election = await crud.get_election_options_by_name(session=session, short_name=short_name, options=election_params)
    questions = await crud.get_questions_by_election_id(session=session, election_id=election.id)
    return {
        "questions": [schemas.QuestionBase.from_orm(q) for q in questions]
    }

@api_router.post("/{short_name}/count-dates", status_code=200)
async def get_count_votes_by_date(short_name: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):
    """
    Return the number of votes per deltaTime from the start of the election until it ends

    """

    election = await crud.get_election_by_short_name(session=session, short_name=short_name)

    states_without_data = ["Setting up", "Ready for key generation", "Ready for opening"]
    if election.status in states_without_data:
        return {}
    
    logs_init = await crud.get_election_logs_by_event(session=session, election_id=election.id, event="voting_started")
    logs_end = await crud.get_election_logs_by_event(session=session, election_id=election.id, event="voting_stopped")

    date_init = logs_init[0].created_at if logs_init else None
    date_end = logs_init[0].created_at if logs_end else tz_now()
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

@api_router.get("/{short_name}/total-voters", status_code=200)
async def get_total_voters(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    Route for get the total voters of an election
    """
    election = await crud.get_election_by_short_name(session=session, short_name=short_name, simple=True)
    total_voters = await crud.get_total_voters_by_election_id(session=session, election_id=election.id)
    return {
        "total_voters": total_voters
    }

@api_router.get("/{short_name}/total-trustees", status_code=200)
async def get_total_trustees(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    Route for get the total trustees of an election
    """
    election = await crud.get_election_by_short_name(session=session, short_name=short_name, simple=True)
    return {
        "total_trustees": await crud.get_total_trustees_by_election_id(session=session, election_id=election.id)
    }

@api_router.get("/{short_name}/election-has-questions", status_code=200)
async def election_has_questions(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    return {"result": bool(election.questions)}

@api_router.get("/{short_name}/election-has-trustees", status_code=200)
async def election_has_trustees(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    return {"result": bool(election.trustees)}

@api_router.get("/{short_name}/election-has-voters", status_code=200)
async def election_has_voters(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    election = await crud.get_election_by_short_name(session=session, short_name=short_name)
    return {"result": bool(election.voters)}

@api_router.get("/{short_name}/voters-by-weight-init", status_code=200)
async def get_voters_by_weight_init(short_name: str, session: Session | AsyncSession = Depends(get_session)):

    election_params = [
        models.Election.id,
        models.Election.max_weight
    ]

    election = await crud.get_election_options_by_name(session=session, short_name=short_name, options=election_params)
    voters = await crud.get_voters_by_group_and_weight_initial(session=session, election_id=election.id)

    normalized_weights = {}
    voters_by_weight_init = {}
    for v in voters:
        v_group, v_weight_init, total_voters = v
        v_w = v_weight_init / election.max_weight
        normalized_weights.setdefault(v_group, []).extend([v_w] * total_voters)
        voters_by_weight_init[v_w] = voters_by_weight_init.get(v_w, 0) + total_voters

    voters_by_weight_init_grouped = [
        {"group": group, "weights": {
            str(w): weights_group.count(w) for w in weights_group}}
        for group, weights_group in normalized_weights.items()
    ]

    return {
        "voters_by_weight_init": voters_by_weight_init,
        "voters_by_weight_init_grouped": voters_by_weight_init_grouped
    }

@api_router.get("/{short_name}/votes-by-weight-init", status_code=200)
async def get_votes_by_weight_init(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    Route for get a resume election
    """

    election_params = [
        models.Election.id,
        models.Election.max_weight
    ]

    election = await crud.get_election_options_by_name(session=session, short_name=short_name, options=election_params)
    voters = await crud.get_voters_by_group_and_weight_valid(session=session, election_id=election.id)

    voters_group = {}
    votes_election = {}

    for v in voters:
        v_group, v_weight_init, _, total_voters = v
        normalized_weight = v_weight_init / election.max_weight
        voters_group.setdefault(v_group, []).extend([normalized_weight] * total_voters)
        votes_election[normalized_weight] = votes_election.get(
            normalized_weight, 0) + total_voters

    votes_by_weight = [{"group": group, "weights": {str(w): value.count(
        w) for w in value}} for group, value in voters_group.items()]

    return {
        "votes_by_weight": votes_election,
        "votes_by_weight_grouped": votes_by_weight
    }


@api_router.get("/{short_name}/votes-by-weight-end", status_code=200)
async def get_votes_by_weight_end(short_name: str, session: Session | AsyncSession = Depends(get_session)):

    election_params = [
        models.Election.id,
        models.Election.max_weight
    ]
    election = await crud.get_election_options_by_name(session=session, short_name=short_name, options=election_params)
    voters = await crud.get_voters_by_group_and_weight_valid(session=session, election_id=election.id)

    votes_by_weight_end = {}
    normalized_weights = {}
    for v in voters:
        v_group, _, v_weight_end, total_voters = v
        v_w = v_weight_end / election.max_weight
        normalized_weights.setdefault(v_group, []).extend([v_w] * total_voters)
        votes_by_weight_end[v_w] = votes_by_weight_end.get(v_w, 0) + total_voters

    votes_by_weight_end_grouped = [
        {"group": group, "weights": {
            str(w): weights_group.count(w) for w in weights_group}}
        for group, weights_group in normalized_weights.items()
    ]

    return {
        "votes_by_weight_end": votes_by_weight_end,
        "votes_by_weight_end_grouped": votes_by_weight_end_grouped
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
    votes = list(map(lambda v: {"vote": from_json(v.encrypted_ballot), "vote_hash": v.encrypted_ballot_hash,
                 "cast_at": v.cast_at, "voter_login_id": v.psifos_voter.username}, votes))

    # Lets decode string to json
    trustee_out = []
    for t in election.trustees:
        t.public_key = await crud.get_public_key_by_id(session=session, public_key_id=t.public_key_id)
        t.decryptions = await crud.get_decryption_by_trustee_id(session=session, trustee_crypto_id=t.id)
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
    election = await crud.get_election_by_short_name(session=session, short_name=short_name, simple=True)

    if only_with_valid_vote:
        voters = await crud.get_voters_with_valid_vote(session=session, election_id=election.id)
    else:
        voters = await crud.get_voters_by_election_id(session=session, election_id=election.id)

    if voter_name:
        voters = [
            v for v in voters
            if unidecode(voter_name.lower()) in unidecode(v.name.lower()) or
               unidecode(voter_name.lower()) in unidecode(v.username.lower())
        ]
        return schemas.UrnaOut(voters=voters, position=0, more_votes=False, total_votes=len(voters))

    if vote_hash:
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

@api_router.get("/{short_name}/check-status", status_code=200)
async def check_election_status(short_name: str, session: Session | AsyncSession = Depends(get_session)):
    """
    GET

    Returns the status of an election
    """
    election = await crud.get_election_by_short_name(session=session, short_name=short_name, simple=True)
    voters = await crud.get_voters_by_election_id(session=session, election_id=election.id)

    trustee_params = [models.TrusteeCrypto.id, models.TrusteeCrypto.current_step]
    trustees = await crud.get_trustee_crypto_params_by_election_id(session=session, election_id=election.id, params=trustee_params)

    questions_params = [models.AbstractQuestion.id]
    questions = await crud.get_questions_params_by_election_id(session=session, election_id=election.id, params=questions_params)

    waiting_decryptions = filter(lambda t: t.current_step == TrusteeStepEnum.waiting_decryptions, trustees)
    decryptions_uploaded = filter(lambda t: t.current_step == TrusteeStepEnum.decryptions_sent, trustees)

    can_combine_decryptions = election.status == ElectionStatusEnum.decryptions_uploaded or (election.status == ElectionStatusEnum.tally_computed and len(list(decryptions_uploaded)) >= len(trustees) // 2 + 1)
    opening_ready = len(list(waiting_decryptions)) == len(trustees) and election.status == ElectionStatusEnum.ready_key_generation

    total_trustees = len(trustees)
    total_voters = len(voters)
    add_questions = len(questions) == 0 and election.status == ElectionStatusEnum.setting_up
    add_voters = len(voters) == 0 and election.voters_login_type == ElectionLoginTypeEnum.close_p and election.status == ElectionStatusEnum.setting_up
    add_trustees = len(trustees) == 0 and election.status == ElectionStatusEnum.setting_up and not election.has_psifos_trustees

    key_generation_ready = election.status == ElectionStatusEnum.setting_up and (total_voters > 0 or election.voters_login_type != ElectionLoginTypeEnum.close_p) and (total_trustees > 0 or election.has_psifos_trustees) and not add_questions

    return {
        "add_voters": add_voters,
        "add_trustees": add_trustees,
        "add_questions": add_questions,
        "opening_ready": opening_ready,
        "can_combine_decryptions": can_combine_decryptions,
        "key_generation_ready": key_generation_ready,
    }
