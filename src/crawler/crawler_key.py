from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from .crawler_node import CrawlerNode


@dataclass
class CrawlerKey:
    created_at: datetime
    node: Optional[CrawlerNode] = None
