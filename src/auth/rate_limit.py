import time
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from src.auth.models import APIKey
from src.auth.dependencies import get_api_key
from src.core.config import settings
import redis.asyncio as aioredis

# Lazy-initialized Redis connection
_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get or create the Redis client for rate limiting."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def check_rate_limit(
    request: Request,
    api_key: Optional[APIKey] = Depends(get_api_key),
):
    """
    Sliding window rate limiter backed by Redis.
    
    - Authenticated requests: limited per API key at key-specific rate.
    - Unauthenticated requests: limited per IP at a global default (30/min).
    """
    redis_client = await get_redis()

    if api_key:
        identifier = f"ratelimit:key:{api_key.key_prefix}"
        max_requests = api_key.rate_limit
    else:
        # Unauthenticated — rate limit by IP
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ratelimit:ip:{client_ip}"
        max_requests = settings.DEFAULT_RATE_LIMIT

    window_seconds = 60
    now = time.time()
    window_start = now - window_seconds

    pipe = redis_client.pipeline()
    # Remove expired entries
    pipe.zremrangebyscore(identifier, 0, window_start)
    # Count current window
    pipe.zcard(identifier)
    # Add current request
    pipe.zadd(identifier, {f"{now}": now})
    # Set expiry on the key so it doesn't live forever
    pipe.expire(identifier, window_seconds + 1)
    results = await pipe.execute()

    current_count = results[1]

    if current_count >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {max_requests} requests per minute.",
            headers={"Retry-After": "60"},
        )
