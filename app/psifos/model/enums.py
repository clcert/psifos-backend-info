"""
Enums for Psifos model.

25-04-2022
"""

import enum

class ElectionTypeEnum(str, enum.Enum):
    query = "Query"
    election = "Election"

class ElectionStatusEnum(str, enum.Enum):
    setting_up = "Setting up"
    ready_key_generation = "Ready for key generation"
    ready_opening = "Ready for opening"
    started = "Started"
    ended = "Ended"
    computing_tally = "Computing Tally"
    tally_computed = "Tally computed"
    decryptions_uploaded = "Decryptions uploaded"
    decryptions_combined = "Decryptions combined"
    results_released = "Results released"


class ElectionEvenEnum(str, enum.Enum):

    @classmethod
    def has_member_key(cls, key):
        return key in cls.__members__.values()

class ElectionPublicEventEnum(ElectionEvenEnum):

    VOTER_FILE_UPLOADED = "voter_file_uploaded"
    ELECTORAL_ROLL_MODIFIED = "electoral_roll_modified"
    TRUSTEE_CREATED = "trustee_created"
    PUBLIC_KEY_UPLOADED = "public_key_uploaded"
    VOTING_STARTED = "voting_started"
    VOTING_STOPPED = "voting_stopped"
    TALLY_COMPUTED = "tally_computed"
    DECRYPTION_RECIEVED = "decryption_recieved"
    DECRYPTIONS_COMBINED = "decryptions_combined"
    RESULTS_RELEASED = "results_released"

class ElectionAdminEventEnum(ElectionEvenEnum):
    VOTER_LOGIN = "voter_login"

class ElectionLoginTypeEnum(str, enum.Enum):
    close_p = "Close"
    open_p = "Open"
    semi_close_p = "Semi Public"

class TrusteeStepEnum(int, enum.Enum):
    config_step = 0
    secret_key_step = 1
    certificates_step = 2
    coefficients_step = 3
    points_step = 4
    waiting_decryptions = 5
    decryptions_sent = 6
