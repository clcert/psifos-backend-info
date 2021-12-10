import ast

from app import app, db
from sqlalchemy import text
from flask import Response
import json


@app.route("/elections/<election_uuid>/ballots")
def get_encrypted_ballots(election_uuid):
    # 1. get internal election_id from election_uuid
    st_1 = text('select id from helios_election where uuid = \"%s\"' % election_uuid)
    res_1 = db.engine.execute(st_1)
    election_id = [row[0] for row in res_1][0]

    # 2. get all voters of that election_id
    st_2 = text('select id, uuid from helios_voter where election_id = %s' % election_id)
    res_2 = db.engine.execute(st_2)
    voters_id = []
    voters_uuid = {}
    for row in res_2:
        voters_id.append(row[0])
        voters_uuid[row[0]] = row[1]

    # 3. get all ballots from those voters
    ballots = {}
    st_3 = text('select voter_id, vote, vote_hash, cast_at from helios_castvote where voter_id in %s' %
                str(voters_id).replace('[', '(').replace(']', ')'))
    res_3 = db.engine.execute(st_3)
    for row in res_3:
        vote_dict = {'cast_at': row[3], 'vote_hash': row[2], 'voter_uuid': voters_uuid[row[0]],
                     'last_vote': ast.literal_eval(row[1])}
        try:
            ballots[row[0]].append(vote_dict)
        except KeyError:
            ballots[row[0]] = [vote_dict]

    # 4. select, if there's the case, the last ballot cast by the voter
    encrypted_ballots = []
    for voter in ballots.keys():
        if len(ballots[voter]) == 1:
            ballots[voter][0]['cast_at'] = str(ballots[voter][0]['cast_at'])
            encrypted_ballots.append(ballots[voter][0])
        else:
            last_vote = {}
            for vote in ballots[voter]:
                if last_vote == {}:
                    last_vote = vote
                else:
                    if last_vote['cast_at'] < vote['cast_at']:
                        last_vote = vote
            last_vote['cast_at'] = str(last_vote['cast_at'])
            encrypted_ballots.append(last_vote)

    return Response(json.dumps(encrypted_ballots), mimetype='application/json')
