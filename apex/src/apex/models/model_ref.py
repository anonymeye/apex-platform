"""Model reference models."""

from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apex.models.base import BaseModel


class ModelRef(BaseModel):
    """A stable reference to a deployable model on a Connection."""

    __tablename__ = "model_refs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Model identifier expected by the target runtime (e.g., "gpt-4o-mini" or "llama3:70b-instruct")
    runtime_id: Mapped[str] = mapped_column(String(255), nullable=False)

    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    connection_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    connection: Mapped["Connection"] = relationship("Connection", back_populates="model_refs")
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="model_ref")

    def __repr__(self) -> str:
        return f"<ModelRef(id={self.id}, name={self.name}, runtime_id={self.runtime_id}, connection_id={self.connection_id})>"

