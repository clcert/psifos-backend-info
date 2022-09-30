from fastapi import APIRouter, Depends
from app.dependencies import get_db
from app.psifos.model import crud, schemas
from sqlalchemy.orm import Session

api_router = APIRouter(prefix="/psifos/api/public")

#----- Election routes -----

@api_router.get("/elections", response_model=list[schemas.ElectionOut], status_code=200)
def get_elections(db: Session = Depends(get_db)):

    return crud.get_elections(db=db)

 
@api_router.get("/election/{election_uuid}", response_model=schemas.ElectionOut, status_code=200)
def get_election(election_uuid: str, db: Session = Depends(get_db)):

    return crud.get_election_by_uuid(db, election_uuid)


@api_router.get("/election/{election_uuid}/result", status_code=200)
def get_election_results(election_uuid: str, db: Session = Depends(get_db)):

    return crud.get_election_by_uuid(db, election_uuid).result



#----- Voters routes -----

@api_router.get("/election/{election_uuid}/voters", response_model=list[schemas.VoterOut], status_code=200)
def get_voters(election_uuid: str, db: Session = Depends(get_db)):
    """
    Route for get voters
    """
    election = crud.get_election_by_uuid(db, election_uuid)
    return crud.get_voters_by_election_id(db=db, election_id=election.id)


#----- Trustee routes -----

@api_router.get("/election/{election_uuid}/trustees", status_code=200)
def get_trustees_election(election_uuid: str, db: Session = Depends(get_db)):

    election = crud.get_election_by_uuid(db=db, uuid=election_uuid)
    return crud.get_trustees_by_election_id(db=db, election_id=election.id)

@api_router.get("/trustee/{trustee_uuid}", response_model=schemas.TrusteeOut, status_code=200)
def get_trustee(trustee_uuid: str, db: Session = Depends(get_db)):

    return crud.get_trustee_by_uuid(db=db, trustee_uuid=trustee_uuid)


#----- CastVote routes -----

@api_router.get("/election/{election_uuid}/cast-votes", response_model=list[schemas.CastVoteOut], status_code=200)
def get_cast_votes(election_uuid: str, db: Session = Depends(get_db)):

    election = crud.get_election_by_uuid(db=db, uuid=election_uuid)
    voters = crud.get_voters_by_election_id(db=db, election_id=election.id)
    voters_id = [v.id for v in voters]
    return crud.get_votes_by_ids(db=db, voters_id=voters_id)


@api_router.post("/election/{election_uuid}/votes", response_model=schemas.UrnaOut, status_code=200)
def get_votes(election_uuid: str, data: dict, db: Session = Depends(get_db)):


    init = data["init"]
    end = data["end"]
    vote_hash = data["vote_hash"]
    election = crud.get_election_by_uuid(db=db, uuid=election_uuid)

    if vote_hash != "":
        voters = crud.get_voters_by_election_id(db=db, election_id=election.id)
        voters_id = [v.id for v in voters]
        hash_votes = crud.get_hashes_vote(db=db, election_uuid=election_uuid, voters_id=voters_id)

        if (vote_hash,) in hash_votes:
            index_hash = hash_votes.index((vote_hash,))
            init = index_hash - (index_hash % end)

    voters_page = crud.get_voters_page(db=db, election_id=election.id, init=init, end=end)
    voters_id = [v.id for v in voters_page]
    cast_votes = crud.get_votes_by_ids(db=db, voters_id=voters_id)

    voters = [schemas.VoterOut.from_orm(v) for v in voters_page]
    cast_votes = [schemas.CastVoteOut.from_orm(c) for c in cast_votes]

    return schemas.UrnaOut(voters=voters, cast_vote=cast_votes, position=init)
