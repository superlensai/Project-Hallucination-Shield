import os
import asyncio
import logging
from celery import Celery
from src.crawler.pypi import PyPICrawler
from src.verifier.trust import TrustCalculator
from src.core.db_gate import db_gate
from src.core.models import Package, RegistryEnum, Version
from sqlalchemy.future import select
from datetime import datetime

logger = logging.getLogger("halwall.worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

app = Celery("halwall", broker=REDIS_URL, backend=REDIS_URL)


async def _crawl_package(name: str):
    crawler = PyPICrawler()
    try:
        metadata = await crawler.get_package_metadata(name)
    except Exception as e:
        logger.error(f"Failed to crawl package '{name}': {e}")
        return
    finally:
        await crawler.close()

    if not metadata:
        logger.warning(f"No metadata returned for package '{name}'")
        return

    score = TrustCalculator.calculate_score(metadata)

    await db_gate.initialize()
    async with db_gate.session() as db:
        result = await db.execute(
            select(Package).where(Package.name == name, Package.registry == RegistryEnum.PYPI)
        )
        package = result.scalars().first()

        if not package:
            package = Package(
                name=name,
                registry=RegistryEnum.PYPI,
                trust_score=score,
            )
            db.add(package)
        else:
            package.trust_score = score
            package.updated_at = datetime.utcnow()

        await db.commit()

    logger.info(f"Crawled '{name}' — trust_score={score}")


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_pypi(self, package_name: str = "requests"):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_crawl_package(package_name))
        return f"Crawled {package_name}"
    except Exception as e:
        logger.error(f"Task crawl_pypi failed for '{package_name}': {e}")
        raise self.retry(exc=e)
    finally:
        loop.close()
