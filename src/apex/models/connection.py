"""Connection models (inference/training endpoints)."""

from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apex.models.base import BaseModel


class Connection(BaseModel):
    """Connection to an external model runtime (vendor API or self-hosted endpoint)."""

    __tablename__ = "connections"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # vendor_api | openai_compatible
    connection_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # openai | anthropic | groq | openai_compatible
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Only relevant for self-hosted or custom endpoints (and some vendors via proxies)
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # env | bearer | none
    auth_type: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key_env_var: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    model_refs: Mapped[list["ModelRef"]] = relationship(
        "ModelRef",
        back_populates="connection",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Connection(id={self.id}, name={self.name}, type={self.connection_type}, provider={self.provider})>"

