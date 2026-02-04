"""Agent configuration models."""

from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apex.models.base import BaseModel


class Agent(BaseModel):
    """Agent configuration model."""

    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Model selection
    model_ref_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("model_refs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # Agent configuration
    system_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_iterations: Mapped[int] = mapped_column(default=10, nullable=False)
    
    # Model parameters
    temperature: Mapped[Optional[float]] = mapped_column(nullable=True)
    max_tokens: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Additional config
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    model_ref: Mapped["ModelRef"] = relationship("ModelRef", back_populates="agents")
    agent_tools: Mapped[list["AgentTool"]] = relationship(
        "AgentTool",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, model_ref_id={self.model_ref_id})>"
