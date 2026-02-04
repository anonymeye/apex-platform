"""Knowledge base and document models."""

from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apex.models.base import BaseModel


class KnowledgeBase(BaseModel):
    """Knowledge base model - container for related documents."""

    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Metadata (renamed to meta_data to avoid SQLAlchemy reserved name)
    meta_data: Mapped[Optional[dict]] = mapped_column("meta_data", JSON, nullable=True, default=dict)
    
    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
    tools: Mapped[list["Tool"]] = relationship(
        "Tool",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, name={self.name}, slug={self.slug})>"


class Document(BaseModel):
    """Document model - individual document chunks in a knowledge base."""

    __tablename__ = "documents"

    knowledge_base_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Original file name/URL
    chunk_index: Mapped[Optional[int]] = mapped_column(nullable=True)  # For chunked documents
    
    # Vector store reference
    vector_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Metadata for filtering (renamed to meta_data to avoid SQLAlchemy reserved name)
    meta_data: Mapped[Optional[dict]] = mapped_column("meta_data", JSON, nullable=True, default=dict)
    
    # Relationships
    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase",
        back_populates="documents",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, kb_id={self.knowledge_base_id}, source={self.source})>"
