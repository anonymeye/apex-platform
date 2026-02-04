"""RAG chain implementation."""

from collections.abc import Callable
from typing import Any

from conduit.core.protocols import ChatModel
from conduit.rag.retriever import RetrievalResult, Retriever
from conduit.schema.messages import Message

DEFAULT_TEMPLATE = (
    "Use the following context to answer the question. "
    "If you cannot answer based on the context, say so.\n\n"
    "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
)


class RAGChain:
    """RAG chain for question answering.

    Examples:
        >>> chain = RAGChain(
        ...     model=model,
        ...     retriever=retriever,
        ...     k=5
        ... )
        >>> result = await chain("What is machine learning?")
        >>> print(result["answer"])
    """

    def __init__(
        self,
        *,
        model: ChatModel,
        retriever: Retriever,
        template: str = DEFAULT_TEMPLATE,
        k: int = 5,
        format_context: Callable[[list[RetrievalResult]], str] | None = None,
    ):
        """Initialize RAG chain.

        Args:
            model: ChatModel instance
            retriever: Retriever instance
            template: Prompt template with {context} and {question} placeholders
            k: Number of documents to retrieve
            format_context: Optional function to format context from retrieval results
        """
        self.model = model
        self.retriever = retriever
        self.template = template
        self.k = k
        self.format_context = format_context or self._default_format_context

    async def __call__(self, question: str) -> dict[str, Any]:
        """Execute RAG chain.

        Args:
            question: User question

        Returns:
            Dict with:
                - answer: Generated answer text
                - sources: List of source documents
                - usage: Token usage information
                - scores: List of similarity scores
        """
        # Retrieve relevant documents
        results = await self.retriever.retrieve(question, k=self.k)

        # Format context
        context = self.format_context(results)

        # Build prompt
        prompt = self.template.format(context=context, question=question)

        # Call model
        response = await self.model.chat([Message(role="user", content=prompt)])

        return {
            "answer": response.extract_content(),
            "sources": [r.document for r in results],
            "usage": response.usage,
            "scores": [r.score for r in results],
        }

    def _default_format_context(self, results: list[RetrievalResult]) -> str:
        """Default context formatting.

        Args:
            results: List of retrieval results

        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant context found."

        formatted_parts = []
        for i, result in enumerate(results, 1):
            content = result.document.content
            formatted_parts.append(f"[{i}] {content}")

        return "\n\n---\n\n".join(formatted_parts)
