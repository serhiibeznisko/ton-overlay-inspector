import time
from datetime import datetime

start_id = 1728925448
elected_for = 65536


def get_current_election_id():
    now = int(time.time())
    return (now - start_id) // elected_for * elected_for + start_id


def get_next_validation_start():
    ts = get_current_election_id() + elected_for
    return datetime.fromtimestamp(ts)
