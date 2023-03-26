from app.psifos.utils import paginate
from fastapi import APIRouter, Depends
from app.dependencies import get_session
from app.psifos.model import crud, schemas
from sqlalchemy.orm import Session
from urllib.parse import unquote
from sqlalchemy.ext.asyncio import AsyncSession
from app.psifos.model.enums import ElectionPublicEventEnum

# api_router = APIRouter(prefix="/psifos/api/public")
api_router = APIRouter()

#----- Election routes -----

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

 
@api_router.get("/election/{election_uuid}", response_model=schemas.ElectionOut, status_code=200)
async def get_election(election_uuid: str, session: Session | AsyncSession = Depends(get_session)):

    """
    GET

    This route delivers all public data of an election
    
    """

    return await crud.get_election_by_uuid(session=session, uuid=election_uuid)


@api_router.get("/election/{election_uuid}/result", status_code=200)
async def get_election_results(election_uuid: str, session: Session | AsyncSession = Depends(get_session)):
    
    """
    GET

    This route delivers the results of an election
    
    """
    election = await crud.get_election_by_uuid(session=session, uuid=election_uuid)
    return election.result



#----- Voters routes -----

@api_router.post("/election/{election_uuid}/voters", response_model=list[schemas.VoterOut], status_code=200)
async def get_voters(election_uuid: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):
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

    election = await crud.get_election_by_uuid(session=session, uuid=election_uuid)
    return await crud.get_voters_by_election_id(session=session, election_id=election.id, page=page, page_size=page_size)


#----- Trustee routes -----

@api_router.post("/election/{election_uuid}/trustees", status_code=200)
async def get_trustees_election(election_uuid: str, data: dict = None, session: Session | AsyncSession = Depends(get_session)):
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

    election = await crud.get_election_by_uuid(session=session, uuid=election_uuid)
    return await crud.get_trustees_by_election_id(session=session, election_id=election.id, page=page, page_size=page_size)

@api_router.get("/trustee/{trustee_uuid}", response_model=schemas.TrusteeOut, status_code=200)
async def get_trustee(trustee_uuid: str, session: Session | AsyncSession = Depends(get_session)):

    """
    GET

    This route delivers the public information of a trustee with the corresponding uuid
    """
    return await crud.get_trustee_by_uuid(session=session, trustee_uuid=trustee_uuid)


#----- CastVote routes -----

@api_router.post("/election/{election_uuid}/cast-votes", response_model=list[schemas.CastVoteOut], status_code=200)
async def get_cast_votes(election_uuid: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):

    """
    This route delivers all the cast votes of an election
    It has an optional parameter in the body to page them:

    {
      page: The page number you want to get
      page_size: Number of elements to display per page
    }
    
    """

    page, page_size = paginate(data)

    election = await crud.get_election_by_uuid(session=session, uuid=election_uuid)
    voters = await crud.get_voters_by_election_id(session=session, election_id=election.id, page=page, page_size=page_size)
    voters_id = [v.id for v in voters]
    return await crud.get_votes_by_ids(session=session, voters_id=voters_id)

@api_router.get("/election/{election_uuid}/cast-vote/{hash_vote:path}", response_model=schemas.CastVoteOut, status_code=200)
async def get_vote_by_hash(election_uuid: str, hash_vote, session: Session | AsyncSession = Depends(get_session)):

    """
    This route return a cast vote by its hash
    
    """
    hash_vote = unquote(unquote(hash_vote))
    return await crud.get_cast_vote_by_hash(session=session, hash_vote=hash_vote)


@api_router.post("/election/{election_uuid}/votes", response_model=schemas.UrnaOut, status_code=200)
async def get_votes(election_uuid: str, data: dict = {}, session: Session | AsyncSession = Depends(get_session)):

    """
    POST

    This route delivers a list of voters according to the hash of the corresponding vote,
    it is used to display the electronic ballot box
    
    """


    page = data.get("page", 0)
    page_size = data.get("page_size", 50)
    page = page_size * page if page_size else None
    vote_hash = data.get("vote_hash", "")
    election = await crud.get_election_by_uuid(session=session, uuid=election_uuid)

    voters = await crud.get_voters_by_election_id(session=session, election_id=election.id)
    if vote_hash != "":
        voters_id = [v.id for v in voters]
        hash_votes = await crud.get_hashes_vote(session=session, voters_id=voters_id)

        if (vote_hash,) in hash_votes:
            index_hash = hash_votes.index((vote_hash,))
            page = index_hash - (index_hash % page_size)

    voters_page = await crud.get_voters_by_election_id(session=session, election_id=election.id, page=page, page_size=page_size)
    voters_next_page = await crud.get_voters_by_election_id(session=session, election_id=election.id, page=page + 1, page_size=page_size)
    voters_page = [schemas.VoterOut.from_orm(v) for v in voters_page]
    more_votes = len(voters_next_page) != 0

    return schemas.UrnaOut(voters=voters_page, position=page, more_votes=more_votes, total_votes=len(voters))

@api_router.get("/election/{election_uuid}/election-logs", response_model=list[schemas.ElectionLogOut], status_code=200)
async def election_logs(election_uuid: str, session: Session | AsyncSession = Depends(get_session)):

    election = await crud.get_election_by_uuid(session=session, uuid=election_uuid)
    election_logs = await crud.get_election_logs(session=session, election_id=election.id)
    election_logs = list(filter(lambda log: ElectionPublicEventEnum.has_member_key(log.event), election_logs))
    return election_logs
    
