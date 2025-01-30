from .database import BroadcastDatabase
from ..crawler import CrawlerNode
from ..utils import get_node_pubkey


class BroadcastStorage:
    def __init__(self, db: BroadcastDatabase, overlay):
        self.db = db
        self.overlay = overlay

    @classmethod
    async def init(cls, overlay):
        db = await BroadcastDatabase.init()
        return cls(db, overlay)

    # CRAWLER NODES

    async def get_crawler_nodes(self, wc=0):
        raw = await self.db.get_setting(self.crawler_nodes_key(wc), [])
        return [
            self.to_crawler_node(item)
            for item in raw
        ]

    async def get_active_crawler_nodes(self, wc=0):
        nodes = await self.get_crawler_nodes(wc=wc)
        return [
            node for node in nodes
            if node.disconnected_at is None and node.lost_pings == 0
        ]

    async def set_crawler_nodes(self, nodes, wc=0):
        await self.db.set_setting(self.crawler_nodes_key(wc), [
            self.from_crawler_node(node)
            for node in nodes
        ])

    def crawler_nodes_key(self, wc):
        return f'crawler_nodes_{wc}'

    def to_crawler_node(self, item):
        return CrawlerNode(
            peer_host=item['ip'],
            peer_port=item['port'],
            peer_pub_key=item['pubkey'],
            transport=self.overlay,
            lost_pings=item['lost_pings'],
            lost_connects=item['lost_connects'],
            disconnected_at=item['disconnected_at'],
        )

    def from_crawler_node(self, node):
        return {
            'ip': node.host,
            'port': node.port,
            'pubkey': get_node_pubkey(node),
            'lost_pings': node.lost_pings,
            'lost_connects': node.lost_connects,
            'disconnected_at': node.disconnected_at,
        }

    # VALIDATOR NODES

    async def get_validators(self):
        raw = await self.db.get_setting('validators')
        return raw['election_id'], raw['nodes']

    async def set_validators(self, election_id, nodes):
        await self.db.set_setting('validators', {
            'election_id': election_id,
            'nodes': nodes
        })
