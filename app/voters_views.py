from app import app, engine
from app.models import Voter
from flask import Response
import json
import hashlib
import base64


@app.route("/elections/<election_uuid>/voters")
def get_election_voters(election_uuid):
    con = engine.connect()

    # 1. get internal election id from election uuid
    query_1 = "select id from helios_election where uuid = %(uuid)s"
    res_1 = con.execute(query_1, uuid=election_uuid)
    election_id = None
    for row in res_1:
        if row is not None:
            election_id = int(row[0])
    if election_id is None:
        return Response("Election not found", status=404)

    # 2. get all voters
    query_2 = "select voter_name, uuid, voter_login_id, user_id from helios_voter where election_id = %(election_id)s"
    res_2 = con.execute(query_2, election_id=election_id)
    con.close()
    voters = []
    for row in res_2:
        voter_id_hash = base64.b64encode(hashlib.sha256(str(row[2]).encode('utf-8')).digest())[:-1].decode('ascii')
        voter_type = 'cas'  # TODO: review this
        voter = Voter(election_uuid, row[0], row[1], voter_id_hash, voter_type)
        voters.append(voter.__dict__)
    return Response(json.dumps(voters), mimetype='application/json')
