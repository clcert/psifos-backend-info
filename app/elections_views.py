from app import app, db
from app.models import Election
from sqlalchemy import text
from flask import Response
import json


@app.route("/elections/<election_uuid>")
def get_election(election_uuid):
    st = text('select cast_url, description, frozen_at, max_weight, name, normalization, openreg, public_key,'
              'questions, short_name, use_voter_aliases, uuid, voters_hash, voting_ends_at, voting_starts_at '
              'from helios_election where uuid = \"%s\"' % election_uuid)
    res = db.engine.execute(st)
    election = Election
    for row in res:
        election = Election(row[0], row[1], str(row[2]), row[3],
                            row[4], bool(row[5]), bool(row[6]), eval(str(row[7])),
                            eval(str(row[8])), row[9], bool(row[10]), row[11], row[12], row[13],
                            row[14])
    return Response(json.dumps(election.__dict__), mimetype='application/json')


@app.route("/elections/<election_uuid>/result")
def get_election_result(election_uuid):
    st = text('select result from helios_election where uuid = \"%s\"' % election_uuid)
    res = db.engine.execute(st)
    election_result = eval([row[0] for row in res][0])
    return Response(json.dumps(election_result), mimetype='application/json')
