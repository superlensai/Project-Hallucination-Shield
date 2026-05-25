from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional
from src.core.models import RegistryEnum

class TrustLookupRequest(BaseModel):
    name: str
    registry: RegistryEnum

class TrustLookupResponse(BaseModel):
    name: str
    registry: RegistryEnum
    trust_score: int
    trust_level: str
    is_verified: bool
    last_updated: datetime

class BulkTrustLookupRequest(BaseModel):
    packages: List[TrustLookupRequest]

class HallucinationReportRequest(BaseModel):
    package_name: str
    registry: RegistryEnum
    source: str
    source_url: Optional[str] = None

class HallucinationReportResponse(BaseModel):
    id: str
    status: str

class SnapshotResponse(BaseModel):
    snapshot_version: int
    created_at: datetime
    merkle_root: str
    snapshot_url: str
    expiry: datetime
