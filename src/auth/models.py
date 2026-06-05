import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from src.core.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)  # Human-readable label, e.g. "CI pipeline"
    key_hash = Column(String(128), unique=True, nullable=False, index=True)
    key_prefix = Column(String(8), nullable=False)  # First 8 chars for identification
    scopes = Column(ARRAY(String), default=["read"])  # read, write, admin
    rate_limit = Column(Integer, default=100)  # requests per minute
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    @staticmethod
    def generate_key() -> str:
        """Generate a secure API key with a recognizable prefix."""
        return f"hw_{secrets.token_urlsafe(32)}"
