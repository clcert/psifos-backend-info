from app.psifos.utils import paginate
from fastapi import APIRouter, Depends
from app.dependencies import get_db
from app.psifos.model import crud, schemas
from sqlalchemy.orm import Session

# api_router = APIRouter(prefix="/psifos/api/public")
api_router = APIRouter()

#----- Election routes -----

@api_router.post("/elections", response_model=list[schemas.ElectionOut], status_code=200)
def get_elections(data: dict = {}, db: Session = Depends(get_db)):

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

    return crud.get_elections(db=db, page=page, page_size=page_size)

 
@api_router.get("/election/{election_uuid}", response_model=schemas.ElectionOut, status_code=200)
def get_election(election_uuid: str, db: Session = Depends(get_db)):

    """
    GET

    This route delivers all public data of an election
    
    """

    return crud.get_election_by_uuid(db, election_uuid)


@api_router.get("/election/{election_uuid}/result", status_code=200)
def get_election_results(election_uuid: str, db: Session = Depends(get_db)):
    
    """
    GET

    This route delivers the results of an election
    
    """

    return crud.get_election_by_uuid(db, election_uuid).result



#----- Voters routes -----

@api_router.post("/election/{election_uuid}/voters", response_model=list[schemas.VoterOut], status_code=200)
def get_voters(election_uuid: str, data: dict = {}, db: Session = Depends(get_db)):
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

    election = crud.get_election_by_uuid(db, election_uuid)
    return crud.get_voters_by_election_id(db=db, election_id=election.id, page=page, page_size=page_size)


#----- Trustee routes -----

@api_router.post("/election/{election_uuid}/trustees", status_code=200)
def get_trustees_election(election_uuid: str, data: dict = None, db: Session = Depends(get_db)):
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

    election = crud.get_election_by_uuid(db=db, uuid=election_uuid)
    return crud.get_trustees_by_election_id(db=db, election_id=election.id, page=page, page_size=page_size)

@api_router.get("/trustee/{trustee_uuid}", response_model=schemas.TrusteeOut, status_code=200)
def get_trustee(trustee_uuid: str, db: Session = Depends(get_db)):

    """
    GET

    This route delivers the public information of a trustee with the corresponding uuid
    """
    return crud.get_trustee_by_uuid(db=db, trustee_uuid=trustee_uuid)


#----- CastVote routes -----

@api_router.post("/election/{election_uuid}/cast-votes", response_model=list[schemas.CastVoteOut], status_code=200)
def get_cast_votes(election_uuid: str, data: dict = {}, db: Session = Depends(get_db)):

    """
    This route delivers all the cast votes of an election
    It has an optional parameter in the body to page them:

    {
      page: The page number you want to get
      page_size: Number of elements to display per page
    }
    
    """

    page, page_size = paginate(data)

    election = crud.get_election_by_uuid(db=db, uuid=election_uuid)
    voters = crud.get_voters_by_election_id(db=db, election_id=election.id, page=page, page_size=page_size)
    voters_id = [v.id for v in voters]
    return crud.get_votes_by_ids(db=db, voters_id=voters_id)

@api_router.post("/election/{election_uuid}/cast-vote", response_model=schemas.CastVoteOut, status_code=200)
def get_vote_by_hash(election_uuid: str, data: dict = {}, db: Session = Depends(get_db)):

    """
    This route return a cast vote by its hash
    
    """
    hash_vote = data.get("hash_vote", None)
    return crud.get_cast_vote_by_hash(db=db, election_uuid=election_uuid, hash_vote=hash_vote)


@api_router.post("/election/{election_uuid}/votes", response_model=schemas.UrnaOut, status_code=200)
def get_votes(election_uuid: str, data: dict = {}, db: Session = Depends(get_db)):

    """
    POST

    This route delivers a list of voters according to the hash of the corresponding vote,
    it is used to display the electronic ballot box
    
    """


    page = data.get("page", 0)
    page_size = data.get("page_size", None)
    page = page_size * page if page_size else None
    vote_hash = data.get("vote_hash", "")
    election = crud.get_election_by_uuid(db=db, uuid=election_uuid)

    if vote_hash != "":
        voters = crud.get_voters_by_election_id(db=db, election_id=election.id)
        voters_id = [v.id for v in voters]
        hash_votes = crud.get_hashes_vote(db=db, election_uuid=election_uuid, voters_id=voters_id)

        if (vote_hash,) in hash_votes:
            index_hash = hash_votes.index((vote_hash,))
            page = index_hash - (index_hash % page_size)

    voters_page = crud.get_voters_by_election_id(db=db, election_id=election.id, page=page, page_size=page_size)
    voters_id = [v.id for v in voters_page]
    cast_votes = crud.get_votes_by_ids(db=db, voters_id=voters_id)

    voters = [schemas.VoterOut.from_orm(v) for v in voters_page]
    cast_votes = [schemas.CastVoteOut.from_orm(c) for c in cast_votes]

    return schemas.UrnaOut(voters=voters, cast_vote=cast_votes, position=page)
