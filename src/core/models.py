import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, BigInteger, Table
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from src.core.database import Base

class RegistryEnum(str, Enum):
    PYPI = "pypi"
    NPM = "npm"
    CRATES = "crates"
    GO = "go"

# Association table for Package-Maintainer many-to-many relationship
package_maintainers = Table(
    "package_maintainers",
    Base.metadata,
    Column("package_id", UUID(as_uuid=True), ForeignKey("packages.id"), primary_key=True),
    Column("maintainer_id", UUID(as_uuid=True), ForeignKey("maintainers.id"), primary_key=True),
    Column("role", String, default="maintainer") # owner, maintainer
)

class Package(Base):
    __tablename__ = "packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    registry = Column(SQLEnum(RegistryEnum), nullable=False)
    trust_score = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    merkle_proof = Column(String, nullable=True)
    sigstore_bundle = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("Version", back_populates="package", cascade="all, delete-orphan")
    maintainers = relationship("Maintainer", secondary=package_maintainers, back_populates="packages")
    vulnerabilities = relationship("Vulnerability", back_populates="package")

class Version(Base):
    __tablename__ = "versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("packages.id"), nullable=False)
    version = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    download_count = Column(BigInteger, default=0)
    is_malicious = Column(Boolean, default=False)
    malware_score = Column(Float, default=0.0)
    cve_ids = Column(ARRAY(String), default=[])

    package = relationship("Package", back_populates="versions")

class Maintainer(Base):
    __tablename__ = "maintainers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False)
    registry = Column(SQLEnum(RegistryEnum), nullable=False)
    github_username = Column(String, nullable=True)
    github_verified = Column(Boolean, default=False)
    trust_score = Column(Integer, default=0)
    is_suspicious = Column(Boolean, default=False)

    packages = relationship("Package", secondary=package_maintainers, back_populates="maintainers")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("packages.id"), nullable=False)
    cve_id = Column(String, index=True, nullable=False)
    cvss_score = Column(Float, nullable=False)
    published_at = Column(DateTime, nullable=False)

    package = relationship("Package", back_populates="vulnerabilities")

class HallucinationCandidate(Base):
    __tablename__ = "hallucination_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_name = Column(String, index=True, nullable=False)
    registry = Column(SQLEnum(RegistryEnum), nullable=False)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String, nullable=False) # stackoverflow, reddit, etc.
    source_url = Column(String, nullable=True)
    suggestion_count = Column(Integer, default=1)
    is_verified_hallucination = Column(Boolean, default=False)
    registered_malicious = Column(Boolean, default=False)
    action_taken = Column(String, default="monitored") # blocked, monitored, ignored

class TrustSnapshot(Base):
    __tablename__ = "trust_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_version = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    merkle_root = Column(String(64), nullable=False)
    snapshot_data = Column(JSONB, nullable=False) # Could be compressed path instead
    signature = Column(String, nullable=False)
    expiry = Column(DateTime, nullable=False)
