from src.crawler.base import BaseCrawler
from typing import List, Dict, Any

class PyPICrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="https://pypi.org/pypi")

    async def get_package_metadata(self, name: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{name}/json"
        response = await self.client.get(url)
        if response.status_code == 200:
            return response.json()
        return {}

    async def get_recent_updates(self) -> List[str]:
        # PyPI doesn't have a simple "recent" JSON endpoint in the same way, 
        # but we can crawl the RSS feed or use the 'simple' API.
        # For this prototype, we'll return a stub or implement a simple scraper.
        return []
