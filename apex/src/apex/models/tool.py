"""Tool definition models."""

from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apex.models.base import BaseModel


class Tool(BaseModel):
    """Tool model - represents a tool that can be used by agents."""

    __tablename__ = "tools"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tool_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "rag", "api", "function", etc.
    
    # For RAG tools - link to knowledge base
    knowledge_base_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Tool configuration (type-specific: RAG k/template, API URL, etc.)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    knowledge_base: Mapped[Optional["KnowledgeBase"]] = relationship(
        "KnowledgeBase",
        back_populates="tools",
    )
    agent_tools: Mapped[list["AgentTool"]] = relationship(
        "AgentTool",
        back_populates="tool",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tool(id={self.id}, name={self.name}, type={self.tool_type})>"


class AgentTool(BaseModel):
    """Many-to-many relationship between Agents and Tools."""

    __tablename__ = "agent_tools"

    agent_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Optional tool-specific config for this agent
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="agent_tools")
    tool: Mapped["Tool"] = relationship("Tool", back_populates="agent_tools")

    def __repr__(self) -> str:
        return f"<AgentTool(agent_id={self.agent_id}, tool_id={self.tool_id})>"
