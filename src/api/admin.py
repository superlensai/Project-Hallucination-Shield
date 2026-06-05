"""Admin endpoints for API key management."""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from src.auth.models import APIKey
from src.auth.dependencies import hash_key, require_auth

router = APIRouter(prefix="/internal/admin")


class CreateAPIKeyRequest(BaseModel):
    name: str
    scopes: List[str] = ["read"]
    rate_limit: int = 100
    expires_in_days: Optional[int] = None  # None = never expires


class CreateAPIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Only returned once at creation time
    key_prefix: str
    scopes: List[str]
    rate_limit: int
    expires_at: Optional[datetime]


class APIKeyInfo(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    rate_limit: int
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]


@router.post("/keys", response_model=CreateAPIKeyResponse)
async def create_api_key(
    req: CreateAPIKeyRequest,
    _: APIKey = Depends(require_auth(scopes=["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key. Requires admin scope."""
    valid_scopes = {"read", "write", "admin"}
    for scope in req.scopes:
        if scope not in valid_scopes:
            raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}")

    raw_key = APIKey.generate_key()
    key_hash_value = hash_key(raw_key)

    api_key = APIKey(
        name=req.name,
        key_hash=key_hash_value,
        key_prefix=raw_key[:8],
        scopes=req.scopes,
        rate_limit=req.rate_limit,
        expires_at=(
            datetime.utcnow() + timedelta(days=req.expires_in_days)
            if req.expires_in_days
            else None
        ),
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return CreateAPIKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        key=raw_key,  # Only time the raw key is exposed
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        rate_limit=api_key.rate_limit,
        expires_at=api_key.expires_at,
    )


@router.get("/keys", response_model=List[APIKeyInfo])
async def list_api_keys(
    _: APIKey = Depends(require_auth(scopes=["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys (without revealing the actual keys)."""
    result = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    keys = result.scalars().all()
    return [
        APIKeyInfo(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=k.scopes,
            rate_limit=k.rate_limit,
            is_active=k.is_active,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            expires_at=k.expires_at,
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    _: APIKey = Depends(require_auth(scopes=["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key (soft delete - marks as inactive)."""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalars().first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    await db.commit()

    return {"status": "revoked", "key_prefix": api_key.key_prefix}
