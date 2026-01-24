"""Knowledge upload/management endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.api.dependencies import get_current_user_from_token
from apex.api.v1.schemas.knowledge import (
    DocumentResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
)
from apex.core.database import get_db
from apex.ml.rag.embeddings import EmbeddingService
from apex.repositories.knowledge_repository import (
    DocumentRepository,
    KnowledgeBaseRepository,
)
from apex.services.knowledge_service import KnowledgeService
from apex.storage.vector_store import ApexVectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# Global services (in production, use dependency injection)
_vector_store: ApexVectorStore | None = None
_embedding_service: EmbeddingService | None = None
_chat_model = None


def get_vector_store() -> ApexVectorStore:
    """Get or create vector store instance."""
    global _vector_store
    if _vector_store is None:
        from conduit.rag import MemoryVectorStore

        _vector_store = ApexVectorStore(MemoryVectorStore())
    return _vector_store


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_chat_model():
    """Get or create chat model instance."""
    global _chat_model
    if _chat_model is None:
        # In production, load from config
        # For now, return None and handle in service
        pass
    return _chat_model


@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Create a new knowledge base.

    Args:
        kb_data: Knowledge base creation data
        db: Database session
        user_data: Current user data from token

    Returns:
        Created knowledge base
    """
    # Get organization ID from user (simplified - in production, get from user_data)
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    knowledge_service = KnowledgeService(
        knowledge_base_repo=kb_repo,
        document_repo=DocumentRepository(db),
        vector_store=get_vector_store(),
        embedding_service=get_embedding_service(),
        chat_model=get_chat_model(),
    )

    kb = await knowledge_service.create_knowledge_base(
        name=kb_data.name,
        organization_id=organization_id,
        description=kb_data.description,
        metadata=kb_data.metadata,
    )

    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        slug=kb.slug,
        description=kb.description,
        organization_id=kb.organization_id,
        metadata=kb.meta_data,
        created_at=kb.created_at.isoformat(),
        updated_at=kb.updated_at.isoformat(),
    )


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """List all knowledge bases for the organization.

    Args:
        db: Database session
        user_data: Current user data from token

    Returns:
        List of knowledge bases
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kbs = await kb_repo.get_by_organization(organization_id)

    return [
        KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            slug=kb.slug,
            description=kb.description,
            organization_id=kb.organization_id,
            metadata=kb.meta_data,
            created_at=kb.created_at.isoformat(),
            updated_at=kb.updated_at.isoformat(),
        )
        for kb in kbs
    ]


@router.get("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Get a knowledge base by ID.

    Args:
        kb_id: Knowledge base ID
        db: Database session
        user_data: Current user data from token

    Returns:
        Knowledge base
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        slug=kb.slug,
        description=kb.description,
        organization_id=kb.organization_id,
        metadata=kb.meta_data,
        created_at=kb.created_at.isoformat(),
        updated_at=kb.updated_at.isoformat(),
    )


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    kb_id: UUID,
    request: DocumentUploadRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Upload documents to a knowledge base.

    Args:
        kb_id: Knowledge base ID
        request: Document upload request
        db: Database session
        user_data: Current user data from token

    Returns:
        Upload response with created documents and tool info
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    # Convert request to document format
    documents = [
        {
            "content": doc.content,
            "source": doc.source,
            "metadata": doc.metadata,
        }
        for doc in request.documents
    ]

    knowledge_service = KnowledgeService(
        knowledge_base_repo=kb_repo,
        document_repo=DocumentRepository(db),
        vector_store=get_vector_store(),
        embedding_service=get_embedding_service(),
        chat_model=get_chat_model(),
    )

    created_docs, created_tool = await knowledge_service.upload_documents(
        knowledge_base_id=kb_id,
        documents=documents,
        auto_create_tool=request.auto_create_tool,
        auto_add_to_agent_id=request.auto_add_to_agent_id,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
    )

    tool_info = None
    if created_tool:
        tool_info = {
            "id": str(created_tool.id),
            "name": created_tool.name,
            "description": created_tool.description,
        }

    return DocumentUploadResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                knowledge_base_id=doc.knowledge_base_id,
                content=doc.content,
                source=doc.source,
                chunk_index=doc.chunk_index,
                vector_id=doc.vector_id,
                metadata=doc.meta_data,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat(),
            )
            for doc in created_docs
        ],
        tool_created=tool_info,
        message=f"Successfully uploaded {len(created_docs)} document chunks",
    )
