"""Knowledge request/response schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """Schema for creating a knowledge base."""

    name: str = Field(..., min_length=1, max_length=255, description="Knowledge base name")
    description: Optional[str] = Field(None, description="Optional description")
    metadata: Optional[dict] = Field(default_factory=dict, description="Optional metadata")


class KnowledgeBaseResponse(BaseModel):
    """Schema for knowledge base response."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    organization_id: UUID
    metadata: Optional[dict] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    """Schema for uploading a document."""

    content: str = Field(..., min_length=1, description="Document content")
    source: Optional[str] = Field(None, description="Source file name or URL")
    metadata: dict = Field(default_factory=dict, description="Document metadata")


class DocumentUploadRequest(BaseModel):
    """Schema for document upload request."""

    documents: list[DocumentUpload] = Field(..., min_items=1, description="List of documents to upload")
    auto_create_tool: bool = Field(True, description="Whether to auto-create RAG tool")
    auto_add_to_agent_id: Optional[UUID] = Field(
        None, description="Optional agent ID to auto-add tool to"
    )
    chunk_size: int = Field(1000, ge=100, le=5000, description="Chunk size for text splitting")
    chunk_overlap: int = Field(200, ge=0, le=500, description="Chunk overlap for text splitting")


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: UUID
    knowledge_base_id: UUID
    content: str
    source: Optional[str] = None
    chunk_index: Optional[int] = None
    vector_id: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    documents: list[DocumentResponse]
    tool_created: Optional[dict] = Field(None, description="Created tool info if auto_create_tool=True")
    message: str
