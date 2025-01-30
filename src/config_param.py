import re
from bs4 import BeautifulSoup
from pytoniq_core.proof.check_proof import calculate_node_id_short

from .http_request import http_request


async def get_config_param(id_):
    response = await http_request('GET', 'https://explorer.toncoin.org/config')
    soup = BeautifulSoup(response, 'html.parser')
    el = soup.find('div', attrs={'id': f'configparam{id_}'})
    return el.text


async def get_validators_list(past=False):
    lines = await get_config_param(32 if past else 34)
    vs = []
    for line in lines.split('\n'):
        if 'public_key:' in line:
            pubkey = re.findall(r'pubkey:x([A-Z0-9]*)\)', line)[0]
            adnl_addr = re.findall(r'adnl_addr:x([A-Z0-9]*)\)', line)[0]
            vs.append({
                'pubkey': pubkey,
                'adnl_addr': adnl_addr,
            })

    return vs


async def get_validators_short_ids(past=False):
    vs_keys = await get_validators_list(past=past)
    return {
        calculate_node_id_short(bytes.fromhex(vs['pubkey'])).hex(): vs['adnl_addr']
        for vs in vs_keys
    }
