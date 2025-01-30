import asyncio
import traceback
import base64
import logging

from ..telegram import send_telegram_message
from ..utils import dec_to_ip, gather_success
from ..db import BroadcastStorage
from .election import get_current_election_id
from ..config_param import get_validators_list

logger = logging.getLogger(__name__)


class Validators:
    def __init__(self, storage: BroadcastStorage, dht, election_id, nodes):
        self.storage = storage
        self.dht = dht
        self.election_id = election_id
        self.nodes = None
        self.nodes_map = None
        self.set_nodes(nodes)

    @classmethod
    async def init(cls, storage: BroadcastStorage, dht):
        election_id, nodes = await storage.get_validators()
        return cls(storage, dht, election_id, nodes)

    def set_nodes(self, nodes):
        self.nodes = nodes
        self.nodes_map = {f'{v["ip"]}:{v["port"]}': v for v in self.nodes}

    async def reload_from_db(self):
        election_id, nodes = await self.storage.get_validators()
        self.election_id = election_id
        self.set_nodes(nodes)

    async def watch(self):
        logger.info('Watching validator elections')
        while True:
            try:
                await self.check()
            except Exception as e:
                traceback.print_exc()
                await send_telegram_message(f'Critical error in election watcher: {e}')
            await asyncio.sleep(60)

    async def check(self):
        current_election_id = get_current_election_id()

        if self.election_id != current_election_id:
            logger.info(f'Updating validators for election {current_election_id}')
            vs_keys = await get_validators_list()
            vs_nodes = await self.get_validator_nodes(vs_keys)
            await self.storage.set_validators(current_election_id, vs_nodes)
            self.election_id = current_election_id
            logger.info(f'Validators for election {current_election_id} updated')

    async def get_validator_nodes(self, vs_keys):
        validators = await gather_success(*[
            asyncio.wait_for(self.find_validator_node(node), 10)
            for node in vs_keys
        ], chunk_size=10)
        return validators

    async def find_validator_node(self, node):
        dht_key = self.dht.get_dht_key_id_tl(id_=node['adnl_addr'])
        dht_value = await self.dht.find_value(key=dht_key)
        addr = dht_value['value']['value']['addrs'][0]
        return {
            'ip': dec_to_ip(addr['ip']),
            'port': addr['port'],
            'pubkey': base64.b64encode(bytes.fromhex(node['pubkey'])).decode(),
            'adnl_addr': node['adnl_addr'],
        }

    def is_validator(self, node):
        return f'{node.host}:{node.port}' in self.nodes_map
