from typing import Optional
import aiohttp
from aiohttp.client_exceptions import ContentTypeError


_session: Optional[aiohttp.ClientSession] = None


async def http_request(method, url, **kwargs):
    global _session

    if not _session:
        _session = aiohttp.ClientSession()

    response = await _session.request(method, url, **kwargs)
    response.raise_for_status()

    try:
        return await response.json()
    except ContentTypeError:
        return await response.text()


async def close_session():
    if _session:
        await _session.close()
