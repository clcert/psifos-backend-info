import ast

from app import app, db
from sqlalchemy import text
from flask import Response
import json
import hashlib
import base64


@app.route("/elections/<election_uuid>/ballots")
def get_last_short_ballots(election_uuid):
    # 1. get internal election_id from election_uuid
    st_1 = text('select id from helios_election where uuid = \"%s\"' % election_uuid)
    res_1 = db.engine.execute(st_1)
    election_id = [row[0] for row in res_1][0]

    # 2. get all voters of that election_id
    st_2 = text('select id, uuid, voter_name, uuid, voter_login_id from helios_voter where election_id = %s' % election_id)
    res_2 = db.engine.execute(st_2)
    voters_id = []
    voters_uuid = {}
    voters_hash = {}
    for row in res_2:
        name = row[2]
        voter_uuid = row[3]
        voter_id_hash = base64.b64encode(hashlib.sha256(str(row[4]).encode('utf-8')).digest())[:-1].decode('ascii')
        voters_id.append(row[0])
        voters_uuid[row[0]] = row[1]
        serialized_voter = '{\"election_uuid\": \"%s\", ' \
                           '\"name\": \"%s\", ' \
                           '\"uuid\": \"%s\", ' \
                           '\"voter_id_hash\": \"%s\", ' \
                           '\"voter_type\": \"%s\"}' % (election_uuid, name, voter_uuid, voter_id_hash, 'cas')
        voter_hash = base64.b64encode(hashlib.sha256(serialized_voter.encode('utf-8')).digest())[:-1].decode('ascii')
        voters_hash[row[0]] = voter_hash

    # 3. get all ballots from those voters
    ballots = {}
    st_3 = text('select voter_id, vote_hash, cast_at from helios_castvote where verified_at is not null and '
                'voter_id in %s' %
                str(voters_id).replace('[', '(').replace(']', ')'))
    res_3 = db.engine.execute(st_3)
    for row in res_3:
        vote_dict = {'cast_at': str(row[2]), 'vote_hash': row[1], 'voter_hash': voters_hash[row[0]],
                     'voter_uuid': voters_uuid[row[0]]}
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


@app.route("/elections/<election_uuid>/complete_ballots")
def get_last_complete_ballots(election_uuid):
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
    st_3 = text('select voter_id, vote, vote_hash, cast_at from helios_castvote where verified_at is not null and '
                'voter_id in %s' %
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


@app.route("/elections/<election_uuid>/ballots/<voter_uuid>/all")
def get_all_ballots_by_user(election_uuid, voter_uuid):
    # 1. get voter id from voter uuid
    st_1 = text('select id, voter_name, voter_login_id from helios_voter where uuid = \"%s\"' % voter_uuid)
    res_1 = db.engine.execute(st_1)
    voter_id = name = voter_id_hash = ''
    for row in res_1:
        voter_id = row[0]
        name = row[1]
        voter_id_hash = base64.b64encode(hashlib.sha256(str(row[2]).encode('utf-8')).digest())[:-1].decode('ascii')

    # 2. create serialized voter and voter hash values
    serialized_voter = '{\"election_uuid\": \"%s\", ' \
                       '\"name\": \"%s\", ' \
                       '\"uuid\": \"%s\", ' \
                       '\"voter_id_hash\": \"%s\", ' \
                       '\"voter_type\": \"%s\"}' % (election_uuid, name, voter_uuid, voter_id_hash, 'cas')
    voter_hash = base64.b64encode(hashlib.sha256(serialized_voter.encode('utf-8')).digest())[:-1].decode('ascii')

    # 3. get all ballots from voter id and complete data
    ballots = []
    st_2 = text('select cast_at, vote, vote_hash from helios_castvote where voter_id = %s' % voter_id)
    res_2 = db.engine.execute(st_2)
    for row in res_2:
        ballot = {'cast_at': str(row[0]), 'vote': ast.literal_eval(row[1]), 'vote_hash': row[2],
                  'voter_hash': voter_hash, 'voter_uuid': voter_uuid}
        ballots.append(ballot)

    return Response(json.dumps(ballots), mimetype='application/json')


@app.route("/elections/<election_uuid>/ballots/<voter_uuid>/last")
def get_last_ballot_by_user(election_uuid, voter_uuid):
    # 1. get voter id from voter uuid
    st_1 = text('select id, voter_name, voter_login_id from helios_voter where uuid = \"%s\"' % voter_uuid)
    res_1 = db.engine.execute(st_1)
    voter_id = name = voter_id_hash = ''
    for row in res_1:
        voter_id = row[0]
        name = row[1]
        voter_id_hash = base64.b64encode(hashlib.sha256(str(row[2]).encode('utf-8')).digest())[:-1].decode('ascii')

    # 2. create serialized voter and voter hash values
    serialized_voter = '{\"election_uuid\": \"%s\", ' \
                       '\"name\": \"%s\", ' \
                       '\"uuid\": \"%s\", ' \
                       '\"voter_id_hash\": \"%s\", ' \
                       '\"voter_type\": \"%s\"}' % (election_uuid, name, voter_uuid, voter_id_hash, 'cas')
    voter_hash = base64.b64encode(hashlib.sha256(serialized_voter.encode('utf-8')).digest())[:-1].decode('ascii')

    # 3. get only last ballot from voter id and complete data
    st_2 = text('select cast_at, vote, vote_hash from helios_castvote where voter_id = %s and verified_at is not null '
                'order by cast_at desc limit 1' % voter_id)
    res_2 = db.engine.execute(st_2)
    ballot = {}
    for row in res_2:
        ballot = {'cast_at': str(row[0]), 'vote': ast.literal_eval(row[1]), 'vote_hash': row[2],
                  'voter_hash': voter_hash, 'voter_uuid': voter_uuid}

    return Response(json.dumps(ballot), mimetype='application/json')
