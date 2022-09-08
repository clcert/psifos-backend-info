from urllib import response
from fastapi import APIRouter, Depends
from app.dependencies import get_db
from app.psifos.model import crud, schemas
from sqlalchemy.orm import Session

api_router = APIRouter()

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