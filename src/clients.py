import asyncio
from pyraptorq.raptorq_cpp_engine import RaptorQCppEngine

from .adnl import (
    AdnlTransport,
    DhtClient,
    DhtNode,
    OverlayTransport,
)
from .db import read_peers_from_file


async def get_dht_client(adnl):
    cached = read_peers_from_file('dht_nodes.txt')
    if cached:
        nodes = [
            DhtNode(data['ip'], data['port'], data['pubkey'], adnl)
            for data in cached
        ]
        return DhtClient(nodes, adnl)
    return DhtClient.from_mainnet_config(adnl)


def get_overlay_client(overlay_id=None, allow_fec=False):
    if overlay_id is None:
        overlay_id = OverlayTransport.get_mainnet_overlay_id()

    raptorq_engine = None
    if allow_fec:
        raptorq_engine = RaptorQCppEngine.default()

    return OverlayTransport(
        timeout=10,
        overlay_id=overlay_id,
        allow_fec=allow_fec,
        raptorq_engine=raptorq_engine
    )


async def get_clients(overlay_id=None, allow_fec=False):
    adnl = AdnlTransport(timeout=10)
    overlay = get_overlay_client(overlay_id, allow_fec)

    await asyncio.gather(
        adnl.start(),
        overlay.start()
    )
    dht = await get_dht_client(adnl)
    return adnl, overlay, dht
