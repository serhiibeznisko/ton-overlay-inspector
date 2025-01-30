import time
import socket
import struct
import base64
import asyncio
from pytoniq_core.crypto.ciphers import Server


def dec_to_ip(dec):
    return socket.inet_ntoa(struct.pack('>i', dec))


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def gather_success(*coros_or_futures, chunk_size=None):
    if not chunk_size:
        chunk_size = len(coros_or_futures)

    success = []

    for chunk in chunks(coros_or_futures, chunk_size):
        results = await asyncio.gather(*chunk, return_exceptions=True)

        for result in results:
            if isinstance(result, (Exception, BaseException)):
                continue
            if result is not None:
                success.append(result)

    return success


def node_to_dict(node):
    return {
        'ip': node.host,
        'port': node.port,
        'pubkey': get_node_pubkey(node)
    }

def get_node_pubkey(node):
    return base64.b64encode(node.ed25519_public.encode()).decode()


def get_node_adnl_addr(node):
    pub_k = bytes.fromhex(node['id']['key'])
    return Server('', 0, pub_key=pub_k).get_key_id()


def add_major_lt(lt, n):
    return int(lt + (n * 1e6))


def get_now_ts():
    return int(round(time.time()))
