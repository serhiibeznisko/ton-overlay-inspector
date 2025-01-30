import time
import asyncio
import logging
import traceback
from datetime import datetime, timedelta

from ..telegram import send_telegram_message
from .crawler_key import CrawlerKey
from .crawler_node import CrawlerNode
from ..utils import gather_success, get_node_adnl_addr, get_node_pubkey

logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, overlay, dht, initial_peers: list[CrawlerNode], callback_peers=None):
        self.overlay = overlay
        self.dht = dht
        self.callback_peers = callback_peers
        self.peers = {
            peer.key_id: CrawlerKey(
                created_at=datetime.now(),
                node=peer,
            )
            for peer in initial_peers
        }
        self.peers_pointer = 0

        self.round_timeout = timedelta(minutes=5)
        self.lifetime_lost = timedelta(minutes=40)
        self.lifetime_disconnected = timedelta(minutes=20)
        self.max_lost_pings = 5
        self.max_lost_connects = 3

    @property
    def found_nodes(self) -> list[CrawlerNode]:
        for key_id, crawler_key in self.peers.items():
            if crawler_key.node:
                yield crawler_key.node

    @property
    def connected_nodes(self) -> list[CrawlerNode]:
        for node in self.found_nodes:
            if node.is_connected():
                yield node

    async def run(self):
        logger.info('Running crawler')
        while True:
            try:
                await self.handle()
            except Exception as e:
                traceback.print_exc()
                await send_telegram_message(f'Critical error in crawler: {e}')
            await asyncio.sleep(60)

    async def handle(self):
        count_cycle = 0

        while True:
            await self.disconnect_peers()
            await self.clean_lost_peers()
            await self.reconnect_peers()

            start_peers_count = len(self.peers)
            start_found_count = len(list(self.found_nodes))
            start_connected_count = len(list(self.connected_nodes))

            # start looking for new peers
            self.peers_pointer = 0
            count_cycle += 1
            count_round = 0
            lost_neighbours = []
            start_time = time.time()

            logger.info(f'Start cycle {count_cycle}: keys: {start_peers_count}, found: {start_found_count}, connected: {start_connected_count}')

            while True:
                selected = self.select_connected(30)

                if not selected:
                    break

                neighbours = await self.get_many_neighbours(selected)

                new_neighbours = []
                for neighbour in neighbours:
                    key_id = get_node_adnl_addr(neighbour)
                    if key_id in self.peers:
                        continue
                    self.peers[key_id] = CrawlerKey(created_at=datetime.now())
                    new_neighbours.append(neighbour)

                new_nodes = await self.get_many_overlay_nodes(new_neighbours)

                new_keys = [n.key_id for n in new_nodes]
                for n in new_neighbours:
                    if get_node_adnl_addr(n) not in new_keys:
                        lost_neighbours.append(n)

                for node in new_nodes:
                    self.peers[node.key_id].node = node

                logger.info(f'Round {count_round}: selected {len(selected)}, neighbours: {len(neighbours)}, new: {len(new_neighbours)}, found: {len(new_nodes)}, lost: {len(lost_neighbours)}')
                count_round += 1

            recovered_nodes = await self.get_many_overlay_nodes(lost_neighbours)
            logger.info(f'Recovered {len(recovered_nodes)} nodes')
            for node in recovered_nodes:
                self.peers[node.key_id].node = node

            peers_count = len(self.peers)
            found_count = len(list(self.found_nodes))
            logger.info(f'Finish cycle {count_cycle} in {int(time.time() - start_time)} seconds: new keys: {peers_count - start_peers_count}, found: {found_count - start_found_count}')

            if self.callback_peers:
                await self.callback_peers(self.connected_nodes)

            await asyncio.sleep(self.round_timeout.total_seconds())

    async def disconnect_peers(self):
        nodes = list(self.connected_nodes)
        for node in nodes:
            if node.lost_pings > self.max_lost_pings:
                if node.lost_connects >= self.max_lost_connects:
                    self.peers.pop(node.key_id, None)
                else:
                    node.disconnect()

    async def reconnect_peers(self):
        for node in self.found_nodes:
            if not node.is_connected() and datetime.now() - node.disconnected_at > self.lifetime_disconnected:
                node.reconnect()

    async def clean_lost_peers(self):
        peers = list(self.peers.items())
        for key_id, crawler_key in peers:
            if crawler_key.node is None and datetime.now() - crawler_key.created_at > self.lifetime_lost:
                self.peers.pop(key_id, None)

    def select_connected(self, count) -> list[CrawlerNode]:
        selected = []
        peers = list(self.peers.values())

        while len(selected) < count:
            if self.peers_pointer >= len(peers):
                break

            crawler_key = peers[self.peers_pointer]
            if crawler_key.node and crawler_key.node.is_connected():
                selected.append(crawler_key.node)

            self.peers_pointer += 1

        return selected

    async def get_many_overlay_nodes(self, nodes):
        return await gather_success(*[
            asyncio.wait_for(self.find_overlay_node(node), 10)
            for node in nodes
        ], chunk_size=10)

    async def find_overlay_node(self, node):
        peer = await self.dht.get_overlay_node(node, self.overlay)
        return CrawlerNode(
            peer_host=peer.host,
            peer_port=peer.port,
            peer_pub_key=get_node_pubkey(peer),
            transport=peer.transport,
        )

    async def get_many_neighbours(self, peers):
        results = await gather_success(*[
            asyncio.wait_for(peer.get_neighbours(), 3)
            for peer in peers
        ])
        ns = []
        for result in results:
            ns += result
        return ns
