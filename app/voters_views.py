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
