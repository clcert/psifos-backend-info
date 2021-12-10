from app import app, db
from app.models import Trustee
from sqlalchemy import text
from flask import Response
import json


@app.route("/elections/<election_uuid>/trustees")
def get_election_trustees(election_uuid):
    # 1. get internal election id from election uuid
    st_1 = text('select id from helios_election where uuid = \"%s\"' % election_uuid)
    res_1 = db.engine.execute(st_1)
    election_id = int([row[0] for row in res_1][0])

    # 2. get trustees info
    st_2 = text('select decryption_factors, decryption_proofs, email, pok, public_key, public_key_hash, uuid '
                'from helios_trustee where election_id = %d' % election_id)
    res_2 = db.engine.execute(st_2)
    trustees = []
    for row in res_2:
        trustee = Trustee(eval(str(row[0])), eval(str(row[1])), row[2], eval(str(row[3])),
                          eval(str(row[4])), row[5], row[6])
        trustees.append(trustee.__dict__)
    return Response(json.dumps(trustees), mimetype='application/json')
