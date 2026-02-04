"""Knowledge upload/management endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from apex.api.dependencies import get_current_user_from_token
from apex.api.v1.schemas.knowledge import (
    BulkDeleteRequest,
    DocumentResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
)
from apex.api.v1.schemas.tools import ToolResponse, ToolUpdate
from fastapi import Request
from apex.core.database import get_db
from apex.core.config import settings
from apex.ml.rag.embeddings import EmbeddingService
from apex.repositories.knowledge_repository import (
    DocumentRepository,
    KnowledgeBaseRepository,
)
from apex.repositories.tool_repository import ToolRepository
from apex.utils.file_parser import parse_file
from apex.services.knowledge_service import KnowledgeService
from apex.storage.vector_store import ApexVectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# Fallback global services (used if app state not available)
_vector_store: ApexVectorStore | None = None
_embedding_service: EmbeddingService | None = None


def get_vector_store(request: Request) -> ApexVectorStore:
    """Get vector store instance from app state or create fallback."""
    # Try to get from app state (preloaded)
    if hasattr(request.app.state, "vector_store") and request.app.state.vector_store:
        return request.app.state.vector_store

    # Fallback to global singleton (uses same config: pgvector or memory)
    global _vector_store
    if _vector_store is None:
        from apex.storage.vector_store import create_vector_store
        _vector_store = create_vector_store()
    return _vector_store


def get_embedding_service(request: Request) -> EmbeddingService:
    """Get embedding service instance from app state or create fallback."""
    # Try to get from app state (preloaded)
    if hasattr(request.app.state, "embedding_service") and request.app.state.embedding_service:
        return request.app.state.embedding_service
    
    # Fallback to lazy loading
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(
            model_name=settings.embedding_model,
            batch_size=settings.embedding_batch_size,
        )
    return _embedding_service


@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    request: Request,
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
        vector_store=get_vector_store(request),
        embedding_service=get_embedding_service(request),
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


@router.put("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: UUID,
    kb_data: KnowledgeBaseUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Update a knowledge base.

    Args:
        kb_id: Knowledge base ID
        kb_data: Knowledge base update data
        db: Database session
        user_data: Current user data from token

    Returns:
        Updated knowledge base
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    knowledge_service = KnowledgeService(
        knowledge_base_repo=kb_repo,
        document_repo=DocumentRepository(db),
        vector_store=get_vector_store(request),
        embedding_service=get_embedding_service(request),
    )

    updated_kb = await knowledge_service.update_knowledge_base(
        knowledge_base_id=kb_id,
        name=kb_data.name,
        description=kb_data.description,
        metadata=kb_data.metadata,
    )

    return KnowledgeBaseResponse(
        id=updated_kb.id,
        name=updated_kb.name,
        slug=updated_kb.slug,
        description=updated_kb.description,
        organization_id=updated_kb.organization_id,
        metadata=updated_kb.meta_data,
        created_at=updated_kb.created_at.isoformat(),
        updated_at=updated_kb.updated_at.isoformat(),
    )


@router.delete("/knowledge-bases/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Delete a knowledge base and all its documents.

    Args:
        kb_id: Knowledge base ID
        db: Database session
        user_data: Current user data from token
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    knowledge_service = KnowledgeService(
        knowledge_base_repo=kb_repo,
        document_repo=DocumentRepository(db),
        vector_store=get_vector_store(request),
        embedding_service=get_embedding_service(request),
    )

    await knowledge_service.delete_knowledge_base(knowledge_base_id=kb_id)


@router.get("/knowledge-bases/{kb_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """List all documents for a knowledge base.

    Args:
        kb_id: Knowledge base ID
        db: Database session
        user_data: Current user data from token

    Returns:
        List of documents
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    doc_repo = DocumentRepository(db)
    documents = await doc_repo.get_by_knowledge_base(kb_id)

    return [
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
        for doc in documents
    ]


@router.post(
    "/knowledge-bases/{kb_id}/search",
    response_model=KnowledgeSearchResponse,
)
async def search_documents(
    kb_id: UUID,
    search_request: KnowledgeSearchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Search a knowledge base by semantic similarity (verifies embeddings in vector store).

    Embeds the query and returns the top-k chunks with similarity scores.
    Use this to confirm that uploaded documents have embeddings and retrieval works.
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    embedding_service = get_embedding_service(request)
    vector_store = get_vector_store(request)

    query_embedding = (await embedding_service.embed(search_request.query))["embeddings"][0]
    results_with_scores = await vector_store.search_with_score(
        query_embedding,
        k=search_request.k,
        knowledge_base_id=kb_id,
    )

    return KnowledgeSearchResponse(
        results=[
            KnowledgeSearchResult(
                content=doc.content,
                score=score,
                metadata=doc.metadata or {},
            )
            for doc, score in results_with_scores
        ]
    )


@router.delete(
    "/knowledge-bases/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_document(
    kb_id: UUID,
    doc_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Delete a document from a knowledge base.

    Args:
        kb_id: Knowledge base ID
        doc_id: Document ID
        db: Database session
        user_data: Current user data from token
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    doc_repo = DocumentRepository(db)
    doc = await doc_repo.get(doc_id)

    if not doc or doc.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    knowledge_service = KnowledgeService(
        knowledge_base_repo=kb_repo,
        document_repo=doc_repo,
        vector_store=get_vector_store(request),
        embedding_service=get_embedding_service(request),
    )

    await knowledge_service.delete_document(document_id=doc_id)


@router.post(
    "/knowledge-bases/{kb_id}/documents/bulk-delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def bulk_delete_documents(
    kb_id: UUID,
    request: Request,
    delete_request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Bulk delete documents from a knowledge base.

    Args:
        kb_id: Knowledge base ID
        document_ids: List of document IDs to delete
        db: Database session
        user_data: Current user data from token
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    doc_repo = DocumentRepository(db)
    document_ids = delete_request.document_ids
    
    # Verify all documents belong to this KB
    for doc_id in document_ids:
        doc = await doc_repo.get(doc_id)
        if not doc or doc.knowledge_base_id != kb_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found or doesn't belong to this knowledge base"
            )

    knowledge_service = KnowledgeService(
        knowledge_base_repo=kb_repo,
        document_repo=doc_repo,
        vector_store=get_vector_store(request),
        embedding_service=get_embedding_service(request),
    )

    # Delete all documents
    for doc_id in document_ids:
        await knowledge_service.delete_document(document_id=doc_id)


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    kb_id: UUID,
    request: Request,
    upload_request: DocumentUploadRequest,
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

    # Convert upload_request to document format
    documents = [
        {
            "content": doc.content,
            "source": doc.source,
            "metadata": doc.metadata,
        }
        for doc in upload_request.documents
    ]

    knowledge_service = KnowledgeService(
        knowledge_base_repo=kb_repo,
        document_repo=DocumentRepository(db),
        vector_store=get_vector_store(request),
        embedding_service=get_embedding_service(request),
    )

    created_docs = await knowledge_service.upload_documents(
        knowledge_base_id=kb_id,
        documents=documents,
        chunk_size=upload_request.chunk_size,
        chunk_overlap=upload_request.chunk_overlap,
    )

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
        message=f"Successfully uploaded {len(created_docs)} document chunks",
    )


@router.post(
    "/knowledge-bases/{kb_id}/documents/upload-files",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_files(
    kb_id: UUID,
    request: Request,
    files: list[UploadFile] = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Upload files to a knowledge base.
    
    Supports: .txt, .pdf, .docx files
    
    Args:
        kb_id: Knowledge base ID
        files: List of files to upload
        chunk_size: Chunk size for text splitting
        chunk_overlap: Chunk overlap for text splitting
        db: Database session
        user_data: Current user data from token
    
    Returns:
        Upload response with created documents
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    # Parse files and extract text content
    documents = []
    for file in files:
        try:
            file_content = await file.read()
            content = await parse_file(file_content, file.filename or "unknown", file.content_type)
            
            documents.append({
                "content": content,
                "source": file.filename or "unknown",
                "metadata": {"filename": file.filename or "unknown", "content_type": file.content_type},
            })
        except ValueError as e:
            logger.warning(f"Failed to parse file {file.filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse file {file.filename}: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing file {file.filename}: {str(e)}"
            )

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid files were uploaded"
        )

    knowledge_service = KnowledgeService(
        knowledge_base_repo=kb_repo,
        document_repo=DocumentRepository(db),
        vector_store=get_vector_store(request),
        embedding_service=get_embedding_service(request),
    )

    created_docs = await knowledge_service.upload_documents(
        knowledge_base_id=kb_id,
        documents=documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

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
        message=f"Successfully uploaded {len(files)} file(s) ({len(created_docs)} chunks)",
    )


@router.get("/knowledge-bases/{kb_id}/tools", response_model=list[ToolResponse])
async def list_tools(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """List all tools for a knowledge base.

    Args:
        kb_id: Knowledge base ID
        db: Database session
        user_data: Current user data from token

    Returns:
        List of tools
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    tool_repo = ToolRepository(db)
    tools = await tool_repo.get_by_knowledge_base(kb_id)

    return [
        ToolResponse(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            tool_type=tool.tool_type,
            knowledge_base_id=tool.knowledge_base_id,
            config=tool.config,
            organization_id=tool.organization_id,
            created_at=tool.created_at.isoformat(),
            updated_at=tool.updated_at.isoformat(),
        )
        for tool in tools
    ]


@router.put("/knowledge-bases/{kb_id}/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    kb_id: UUID,
    tool_id: UUID,
    tool_data: ToolUpdate,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Update a tool for a knowledge base.

    Args:
        kb_id: Knowledge base ID
        tool_id: Tool ID
        tool_data: Tool update data
        db: Database session
        user_data: Current user data from token

    Returns:
        Updated tool
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    tool_repo = ToolRepository(db)
    tool = await tool_repo.get(tool_id)

    if not tool or tool.knowledge_base_id != kb_id or tool.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found"
        )

    update_data = {}
    if tool_data.name is not None:
        update_data["name"] = tool_data.name
    if tool_data.description is not None:
        update_data["description"] = tool_data.description
    if tool_data.config is not None:
        # Merge config: existing config updated with provided keys
        existing = tool.config or {}
        update_data["config"] = {**existing, **tool_data.config}

    if update_data:
        updated_tool = await tool_repo.update(tool_id, update_data)
    else:
        updated_tool = tool

    return ToolResponse(
        id=updated_tool.id,
        name=updated_tool.name,
        description=updated_tool.description,
        tool_type=updated_tool.tool_type,
        knowledge_base_id=updated_tool.knowledge_base_id,
        config=updated_tool.config,
        organization_id=updated_tool.organization_id,
        created_at=updated_tool.created_at.isoformat(),
        updated_at=updated_tool.updated_at.isoformat(),
    )


@router.delete(
    "/knowledge-bases/{kb_id}/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_tool(
    kb_id: UUID,
    tool_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
):
    """Delete a tool from a knowledge base.

    Args:
        kb_id: Knowledge base ID
        tool_id: Tool ID
        db: Database session
        user_data: Current user data from token
    """
    organization_id = UUID(user_data.get("org_id"))

    kb_repo = KnowledgeBaseRepository(db)
    kb = await kb_repo.get(kb_id)

    if not kb or kb.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found"
        )

    tool_repo = ToolRepository(db)
    tool = await tool_repo.get(tool_id)

    if not tool or tool.knowledge_base_id != kb_id or tool.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found"
        )

    await tool_repo.delete(tool_id)
