from app.main import app, engine
from app.models import Trustee
from flask import Response
import json


@app.route("/elections/<election_uuid>/trustees")
def get_election_trustees(election_uuid):
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

    # 2. get trustees info
    query_2 = "select decryption_factors, decryption_proofs, email, pok, public_key, public_key_hash, uuid " \
              "from helios_trustee where election_id = %(election_id)s"
    res_2 = con.execute(query_2, election_id=election_id)
    con.close()
    trustees = []
    for row in res_2:
        trustee = Trustee(eval(str(row[0])), eval(str(row[1])), row[2], eval(str(row[3])),
                          eval(str(row[4])), row[5], row[6])
        trustees.append(trustee.__dict__)
    return Response(json.dumps(trustees), mimetype='application/json')
