"""Chat endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apex.api.dependencies import get_current_user_from_token
from apex.api.v1.schemas.chat import ChatRequest, ChatResponse
from apex.core.config import settings
from apex.core.database import get_db
from apex.repositories.agent_repository import AgentRepository
from apex.repositories.tool_repository import AgentToolRepository, ToolRepository
from apex.services.chat_service import ChatService
from apex.services.rag_tool_service import RAGToolService
from apex.ml.rag.embeddings import EmbeddingService
from apex.storage.vector_store import ApexVectorStore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

# Fallback global services (used if app state not available)
_vector_store: ApexVectorStore | None = None
_embedding_service: EmbeddingService | None = None


def get_vector_store(request: Request) -> ApexVectorStore:
    """Get vector store instance from app state or create fallback."""
    # Try to get from app state (preloaded)
    if hasattr(request.app.state, "vector_store") and request.app.state.vector_store:
        return request.app.state.vector_store
    
    # Fallback to global singleton
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


def get_chat_service(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ChatService:
    """Get chat service instance."""
    vector_store = get_vector_store(request)
    embedding_service = get_embedding_service(request)

    rag_tool_service = RAGToolService(
        tool_repository=ToolRepository(db),
        vector_retriever=vector_store,
        embedding_service=embedding_service,
        chat_model=None,
    )
    
    return ChatService(
        agent_repo=AgentRepository(db),
        tool_repo=ToolRepository(db),
        agent_tool_repo=AgentToolRepository(db),
        rag_tool_service=rag_tool_service,
    )


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: UUID,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Chat with an agent.

    Args:
        agent_id: Agent ID
        chat_request: Chat request with user message
        db: Database session
        user_data: Current user data from token
        chat_service: Chat service instance

    Returns:
        Chat response with assistant message and metadata

    Raises:
        HTTPException: If agent not found, unauthorized, or execution fails
    """
    organization_id = UUID(user_data.get("org_id"))

    try:
        response = await chat_service.chat(
            agent_id=agent_id,
            user_message=chat_request.message,
            organization_id=organization_id,
            conversation_id=chat_request.conversation_id,
        )
        return ChatResponse(**response)
    except ValueError as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat execution failed: {str(e)}",
        )
