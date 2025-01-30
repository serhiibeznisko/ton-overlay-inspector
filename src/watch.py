import asyncio

from .db import BroadcastStorage
from .clients import get_clients
from .validators import Validators
from .crawler import Crawler


async def main():
    workchain = 0
    adnl, overlay, dht = await get_clients()
    storage = await BroadcastStorage.init(overlay)
    validators = await Validators.init(storage, dht)
    initial_nodes = await storage.get_crawler_nodes(workchain)
    crawler = Crawler(
        overlay,
        dht,
        initial_nodes,
        callback_peers=lambda nodes: storage.set_crawler_nodes(nodes, workchain)
    )

    try:
        await asyncio.gather(
            validators.watch(),
            crawler.run()
        )
    except asyncio.CancelledError:
        print('Cancelling...')

    await storage.db.close()


if __name__ == '__main__':
    asyncio.run(main())
