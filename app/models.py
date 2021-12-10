class Election:
    def __init__(self, cast_url="", description="", frozen_at="", max_weight=1,
                 name="", normalization=False, openreg=False, public_key=dict, questions=list,
                 short_name="", use_voter_aliases=False, uuid="", voters_hash="",
                 voting_ends_at="", voting_starts_at=""):
        self.cast_url = cast_url
        self.description = description
        self.frozen_at = frozen_at
        self.max_weight = max_weight
        self.name = name
        self.normalization = normalization
        self.openreg = openreg
        self.public_key = public_key
        self.questions = questions
        self.short_name = short_name
        self.use_voter_aliases = use_voter_aliases
        self.uuid = uuid
        self.voters_hash = voters_hash
        self.voting_ends_at = voting_ends_at
        self.voting_starts_at = voting_starts_at


class Trustee:
    def __init__(self, decryption_factors=list, decryption_proofs=list,
                 email="", pok=dict, public_key=dict, public_key_hash="",
                 uuid=""):
        self.decryption_factors = decryption_factors
        self.decryption_proofs = decryption_proofs
        self.email = email
        self.pok = pok
        self.public_key = public_key
        self.public_key_hash = public_key_hash
        self.uuid = uuid


class Voter:
    def __init__(self, election_uuid="", name="", uuid="", voter_id_hash="", voter_type=""):
        self.election_uuid = election_uuid
        self.name = name
        self.uuid = uuid
        self.voter_id_hash = voter_id_hash
        self.voter_type = voter_type
