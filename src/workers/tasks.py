import os
import asyncio
from celery import Celery
from src.crawler.pypi import PyPICrawler
from src.verifier.trust import TrustCalculator
from src.core.database import AsyncSessionLocal
from src.core.models import Package, RegistryEnum, Version
from sqlalchemy.future import select
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

app = Celery("halwall", broker=REDIS_URL, backend=REDIS_URL)

async def _crawl_package(name: str):
    crawler = PyPICrawler()
    metadata = await crawler.get_package_metadata(name)
    await crawler.close()
    
    if not metadata:
        return
    
    score = TrustCalculator.calculate_score(metadata)
    info = metadata.get("info", {})
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Package).where(Package.name == name, Package.registry == RegistryEnum.PYPI)
        )
        package = result.scalars().first()
        
        if not package:
            package = Package(
                name=name,
                registry=RegistryEnum.PYPI,
                trust_score=score
            )
            db.add(package)
        else:
            package.trust_score = score
            package.updated_at = datetime.utcnow()
            
        await db.commit()

@app.task
def crawl_pypi(package_name: str = "requests"):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_crawl_package(package_name))
    return f"Crawled {package_name}"
