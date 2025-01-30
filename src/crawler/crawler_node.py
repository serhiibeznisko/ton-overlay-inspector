import time
from datetime import datetime

from pytoniq_core.crypto.ciphers import get_random

from ..adnl import OverlayNode


class CrawlerNode(OverlayNode):
    def __init__(
            self,
            peer_host: str,  # ipv4 host
            peer_port: int,  # port
            peer_pub_key: str,
            transport,
            lost_pings=0,
            lost_connects=0,
            disconnected_at=None
    ):
        self.crawl_lost_pings = lost_pings
        self.lost_connects = lost_connects
        self.disconnected_at = disconnected_at
        super().__init__(peer_host, peer_port, peer_pub_key, transport)

    def disconnect(self):
        self.disconnected_at = datetime.now()
        self.lost_connects += 1

    def is_connected(self):
        return self.disconnected_at is None

    def reconnect(self):
        self.disconnected_at = None
        self.crawl_lost_pings = 0

    async def get_neighbours(self):
        self.crawl_lost_pings += 1
        ns = await self.get_neighbours_fast()
        self.crawl_lost_pings = 0
        self.lost_connects = 0
        return ns

    async def get_neighbours_fast(self, known_peers=None):
        default_message = {
            '@type': 'adnl.message.query',
            'query_id': get_random(32),
            'query': self.transport.get_message_with_overlay_prefix(
                {'@type': 'overlay.getRandomPeers', 'peers': {'nodes': known_peers or []}},
                True
            )
        }
        response = await self.send_peer_message(default_message)
        return response[0]['nodes']

    async def send_peer_message(self, message):
        ts = int(time.time())
        from_ = self.transport.schemas.serialize(self.transport.schemas.get_by_name('pub.ed25519'), data={
            'key': self.transport.client.ed25519_public.encode().hex()})
        data = {
            'from': from_,
            'messages': [message],
            'address': {
                'addrs': [],
                'version': ts,
                'reinit_date': ts,
                'priority': 0,
                'expire_at': 0,
            },
            'recv_addr_list_version': ts,
            'reinit_date': ts,
            'dst_reinit_date': 0,
        }
        return await self.transport.send_message_outside_channel(data, self)
