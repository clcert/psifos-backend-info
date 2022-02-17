from app import app, db
from app.models import Voter
from sqlalchemy import text
from flask import Response
import json
import hashlib
import base64


@app.route("/elections/<election_uuid>/voters")
def get_election_voters(election_uuid):
    # 1. get internal election id from election uuid
    st_1 = text('select id from helios_election where uuid = \"%s\"' % election_uuid)
    res_1 = db.engine.execute(st_1)
    election_id = int([row[0] for row in res_1][0])

    # 2. get all voters
    st_2 = text('select voter_name, uuid, voter_login_id, user_id from helios_voter '
                'where election_id = %d' % election_id)
    res_2 = db.engine.execute(st_2)
    voters = []
    for row in res_2:
        voter_id_hash = base64.b64encode(hashlib.sha256(str(row[2]).encode('utf-8')).digest())[:-1].decode('ascii')
        voter_type = 'cas'  # TODO: review this
        voter = Voter(election_uuid, row[0], row[1], voter_id_hash, voter_type)
        voters.append(voter.__dict__)
    return Response(json.dumps(voters), mimetype='application/json')


@app.route("/elections/<election_uuid>/voters/info")
def get_voters_info(election_uuid):

    st_1 = text('select id from helios_election where uuid = \"%s\"' % election_uuid)
    res_1 = db.engine.execute(st_1)
    election_id = int([row[0] for row in res_1][0])

    st_2 = text('select voter_login_id, voter_name, voter_email, vote_hash, voter_weight, uuid from helios_voter where election_id = \"%s\"' % election_id)
    res_2 = db.engine.execute(st_2)
    voters = []
    votes_cast = 0
    total_voters = 0
    data = {}

    for row in res_2:
        voter = {'voter_login_id': row[0], 'name': row[1], 'voter_email': row[2], 'vote_hash': row[3], 'voter_weight': row[4], 'uuid': row[5]}
        voters.append(voter)
        if row[3]:
            votes_cast += 1
        total_voters += 1
    
    data["info_votes"] = {"votes_cast": votes_cast, "total_voters": total_voters}
    data["info_voters"] = voters


    return Response(json.dumps(data), mimetype='application/json')