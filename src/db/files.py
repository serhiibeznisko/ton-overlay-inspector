import os

from ..utils import node_to_dict


def save_peers_to_file(peers, file, get_extra_args=None):
    prepared = []
    for peer in peers:
        if not isinstance(peer, dict):
            peer = node_to_dict(peer)
        prepared.append(peer)
    prepared = sorted(prepared, key=lambda p: (p['ip'], p['port']))

    with open(get_cache_path(file), "w") as file:
        for peer in prepared:
            args = [peer["ip"], str(peer["port"]), peer["pubkey"]]
            if get_extra_args:
                args += get_extra_args(peer)
            file.write(' '.join(args) + '\n')


def read_peers_from_file(file, parse_extra_args=None):
    if not os.path.isfile(get_cache_path(file)):
        return []

    cached = []
    with open(get_cache_path(file), "r") as file:
        lines = file.read().split('\n')
        for line in lines:
            tokens = line.split()
            if len(tokens) < 3:
                continue

            peer = {
                'ip': tokens[0],
                'port': int(tokens[1]),
                'pubkey': tokens[2]
            }
            if len(tokens) > 3 and parse_extra_args:
                peer.update(parse_extra_args(tokens[3:]))

            cached.append(peer)

    return cached


def get_cache_path(file):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(root_dir, 'cache', file)
