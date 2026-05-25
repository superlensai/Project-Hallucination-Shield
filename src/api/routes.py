from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from src.core.models import Package, HallucinationCandidate, TrustSnapshot
from src.api.schemas import (
    TrustLookupRequest, TrustLookupResponse, 
    BulkTrustLookupRequest, HallucinationReportRequest, 
    HallucinationReportResponse, SnapshotResponse
)
from datetime import datetime

router = APIRouter(prefix="/internal")

def get_trust_level(score: int) -> str:
    if score >= 90: return "PROTOTYPE_TRUSTED"
    if score >= 70: return "VERIFIED"
    if score >= 40: return "NEUTRAL"
    if score >= 20: return "SUSPICIOUS"
    return "UNTRUSTED"

@router.post("/trust/lookup", response_model=TrustLookupResponse)
async def lookup_trust(req: TrustLookupRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Package).where(Package.name == req.name, Package.registry == req.registry)
    )
    package = result.scalars().first()
    
    if not package:
        raise HTTPException(status_code=404, detail="Package not found in trusted database")
    
    return TrustLookupResponse(
        name=package.name,
        registry=package.registry,
        trust_score=package.trust_score,
        trust_level=get_trust_level(package.trust_score),
        is_verified=package.is_verified,
        last_updated=package.updated_at
    )

@router.post("/trust/bulk", response_model=List[TrustLookupResponse])
async def bulk_lookup_trust(req: BulkTrustLookupRequest, db: AsyncSession = Depends(get_db)):
    responses = []
    for pkg_req in req.packages:
        result = await db.execute(
            select(Package).where(Package.name == pkg_req.name, Package.registry == pkg_req.registry)
        )
        package = result.scalars().first()
        if package:
            responses.append(TrustLookupResponse(
                name=package.name,
                registry=package.registry,
                trust_score=package.trust_score,
                trust_level=get_trust_level(package.trust_score),
                is_verified=package.is_verified,
                last_updated=package.updated_at
            ))
    return responses

@router.post("/hallucination/report", response_model=HallucinationReportResponse)
async def report_hallucination(req: HallucinationReportRequest, db: AsyncSession = Depends(get_db)):
    # Check if already exists
    result = await db.execute(
        select(HallucinationCandidate).where(
            HallucinationCandidate.package_name == req.package_name,
            HallucinationCandidate.registry == req.registry
        )
    )
    candidate = result.scalars().first()
    
    if candidate:
        candidate.suggestion_count += 1
    else:
        candidate = HallucinationCandidate(
            package_name=req.package_name,
            registry=req.registry,
            source=req.source,
            source_url=req.source_url
        )
        db.add(candidate)
    
    await db.commit()
    await db.refresh(candidate)
    
    return HallucinationReportResponse(id=str(candidate.id), status="reported")

@router.get("/snapshot/latest", response_model=SnapshotResponse)
async def get_latest_snapshot(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrustSnapshot).order_by(TrustSnapshot.snapshot_version.desc())
    )
    snapshot = result.scalars().first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshots available")
    
    return SnapshotResponse(
        snapshot_version=snapshot.snapshot_version,
        created_at=snapshot.created_at,
        merkle_root=snapshot.merkle_root,
        snapshot_url=f"/snapshots/{snapshot.snapshot_version}.json.gz",
        expiry=snapshot.expiry
    )
