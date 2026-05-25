import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseCrawler(ABC):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)

    @abstractmethod
    async def get_package_metadata(self, name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_recent_updates(self) -> List[str]:
        pass

    async def close(self):
        await self.client.aclose()
