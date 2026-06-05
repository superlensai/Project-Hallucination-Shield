import hashlib
from datetime import datetime
from typing import Optional, List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from src.auth.models import APIKey

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_key(raw_key: str) -> str:
    """Hash an API key using SHA-256 for storage/lookup."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def get_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Optional[APIKey]:
    """Resolve and validate an API key. Returns None if no key provided."""
    if not api_key:
        return None

    key_hash = hash_key(api_key)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    )
    db_key = result.scalars().first()

    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    # Check expiry
    if db_key.expires_at and db_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last_used_at
    db_key.last_used_at = datetime.utcnow()
    await db.commit()

    return db_key


def require_auth(scopes: Optional[List[str]] = None):
    """Dependency that requires a valid API key with optional scope check."""

    async def _require(
        api_key: Optional[APIKey] = Depends(get_api_key),
    ) -> APIKey:
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Pass it via the X-API-Key header.",
            )

        if scopes:
            # Admin scope grants access to everything
            if "admin" in api_key.scopes:
                return api_key
            for scope in scopes:
                if scope not in api_key.scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"API key lacks required scope: {scope}",
                    )

        return api_key

    return _require
