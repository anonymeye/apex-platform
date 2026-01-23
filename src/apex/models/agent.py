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
    
    # Model configuration
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False)  # "openai", "anthropic", "groq", etc.
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)  # "gpt-4", "claude-3-opus", etc.
    
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
    agent_tools: Mapped[list["AgentTool"]] = relationship(
        "AgentTool",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, model={self.model_provider}/{self.model_name})>"
