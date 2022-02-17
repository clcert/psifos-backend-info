from ast import Num
from asyncio.windows_events import NULL
import re
from app import app, db
from app.models import Election
from sqlalchemy import null, text
from flask import Response, request, jsonify
from flask_cors import cross_origin
import json


@app.route("/elections/<election_uuid>")
def get_election(election_uuid):
    st = text('select cast_url, description, frozen_at, max_weight, name, normalization, openreg, public_key,'
              'questions, short_name, use_voter_aliases, uuid, voters_hash, voting_ends_at, voting_starts_at, '
              'voting_stopped from helios_election where uuid = \"%s\"' % election_uuid)
    res = db.engine.execute(st)
    election = Election
    for row in res:
        print(row)
        election = Election(row[0], row[1], str(row[2]), row[3],
                            row[4], bool(row[5]), bool(row[6]), eval(str(row[7])),
                            eval(str(row[8])), row[9], bool(row[10]), row[11], row[12], str(row[13]),
                            str(row[14]))
    return Response(json.dumps(election.__dict__), mimetype='application/json')


@app.route("/elections/<election_uuid>/result")
def get_election_result(election_uuid):
    st = text('select result, questions from helios_election where uuid = \"%s\"' % election_uuid)
    res = db.engine.execute(st)
    election_result = {}
    for row in res:
        election_result["result"] = row[0]
        election_result["questions"] = row[1]
    return Response(json.dumps(election_result), mimetype='application/json')



@app.route("/elections/<election_uuid>/resume")
@cross_origin()
def get_election_resume(election_uuid):

    st_election = text('SELECT name, id, max_weight FROM helios_election WHERE uuid = \"%s\"' % election_uuid)
    res_election = db.engine.execute(st_election)
    info_election = {}
    for row in res_election:
        info_election["name"] = row[0]
        info_election["id"] = int(row[1])
        info_election["max_weight"] = row[2]


    st_voter_file = text('SELECT election_id, COUNT(*) FROM helios_voter WHERE election_id = \"%s\" GROUP BY election_id' % info_election["id"])
    res_voter_file = db.engine.execute(st_voter_file)
    total_voters = 0
    for row in res_voter_file:
        total_voters = row[1]

    #st_voters = text('SELECT voter_weight, COUNT(*) FROM helios_voter WHERE election_id = \"%s\" GROUP BY voter_weight' % info_election["id"])
    st_voters = text('SELECT voter_weight, SUM(CASE WHEN vote_hash IS NOT NULL THEN 1 ELSE 0 END) FROM helios_voter WHERE election_id = \"%s\" GROUP BY voter_weight' % info_election["id"])
    res_voters = db.engine.execute(st_voters)
    voter_info = {}
    num_voters = 0
    for row in res_voters:
        voter_info[row[0]] = int(row[1])
        num_voters += int(row[1])

    result = {"name": info_election["name"], "num_voters": num_voters, "total_voters": total_voters, "max_weight": info_election["max_weight"], "info": voter_info}
    return Response(json.dumps(result), mimetype='application/json')


@app.route("/elections/<election_uuid>/openreg", methods=['GET', 'POST'])
def update_election_openreg(election_uuid):
    data = request.get_json()
    reg = data["openreg"]
    print(reg)
    value_reg = 1 if reg else 0
    print(value_reg)
    st = text('update helios_election set openreg = \"%s\" where uuid = \"%s\"' % (value_reg, election_uuid))
    print(st)
    res = db.engine.execute(st)
    return {"status": "ok"}
        