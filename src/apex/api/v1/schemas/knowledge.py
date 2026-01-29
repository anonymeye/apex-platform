"""Knowledge request/response schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """Schema for creating a knowledge base."""

    name: str = Field(..., min_length=1, max_length=255, description="Knowledge base name")
    description: Optional[str] = Field(None, description="Optional description")
    metadata: Optional[dict] = Field(default_factory=dict, description="Optional metadata")


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Knowledge base name")
    description: Optional[str] = Field(None, description="Optional description")
    metadata: Optional[dict] = Field(None, description="Optional metadata")


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
    message: str


class ToolResponse(BaseModel):
    """Schema for tool response (generic Tool)."""

    id: UUID
    name: str
    description: str
    tool_type: str
    knowledge_base_id: Optional[UUID] = None
    config: Optional[dict] = None
    organization_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ToolUpdate(BaseModel):
    """Schema for updating a tool (generic: name, description, config)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    config: Optional[dict] = Field(None, description="Type-specific config (e.g. RAG: rag_k, rag_template)")


class KnowledgeSearchRequest(BaseModel):
    """Schema for searching a knowledge base (vector similarity)."""

    query: str = Field(..., min_length=1, description="Search query text")
    k: int = Field(5, ge=1, le=20, description="Number of results to return")


class KnowledgeSearchResult(BaseModel):
    """One retrieved chunk with similarity score."""

    content: str
    score: float
    metadata: Optional[dict] = None


class KnowledgeSearchResponse(BaseModel):
    """Response from knowledge base search (verifies embeddings + retrieval)."""

    results: list[KnowledgeSearchResult]


class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete request."""

    document_ids: list[UUID] = Field(..., min_items=1, description="List of document IDs to delete")
