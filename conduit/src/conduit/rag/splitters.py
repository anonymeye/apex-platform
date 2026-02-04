"""Text splitting strategies for RAG."""

import re
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Document with content and optional metadata.

    Examples:
        >>> doc = Document(content="Hello world", metadata={"source": "test.txt"})
        >>> print(doc.content)
    """

    content: str = Field(..., min_length=1, description="Document content")
    metadata: dict[str, str] = Field(default_factory=dict, description="Document metadata")


class TextSplitter(ABC):
    """Abstract base class for text splitters."""

    @abstractmethod
    def split(self, text: str | Document) -> list[Document]:
        """Split text into chunks.

        Args:
            text: Text string or Document to split

        Returns:
            List of Document chunks
        """
        ...


class CharacterSplitter(TextSplitter):
    """Split text by character count.

    Examples:
        >>> splitter = CharacterSplitter(chunk_size=100, chunk_overlap=20)
        >>> chunks = splitter.split("Long text here...")
    """

    def __init__(
        self,
        *,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
    ):
        """Initialize character splitter.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            separator: Separator to prefer when splitting
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split(self, text: str | Document) -> list[Document]:
        """Split text by character count with overlap.

        Args:
            text: Text string or Document to split

        Returns:
            List of Document chunks
        """
        if isinstance(text, Document):
            content = text.content
            metadata = text.metadata
        else:
            content = text
            metadata = {}

        if not content:
            return []

        # First try splitting by separator
        if self.separator in content:
            splits = content.split(self.separator)
            chunks = []
            current_chunk = ""

            for split in splits:
                # If adding this split would exceed chunk_size, save current and start new
                chunk_with_split = len(current_chunk) + len(self.separator) + len(split)
                if current_chunk and chunk_with_split > self.chunk_size:
                    chunks.append(Document(content=current_chunk, metadata=metadata.copy()))
                    # Start new chunk with overlap
                    if self.chunk_overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-self.chunk_overlap :]
                        current_chunk = overlap_text + self.separator + split
                    else:
                        current_chunk = split
                else:
                    if current_chunk:
                        current_chunk += self.separator + split
                    else:
                        current_chunk = split

            if current_chunk:
                chunks.append(Document(content=current_chunk, metadata=metadata.copy()))

            return chunks

        # Fallback to simple character splitting
        chunks = []
        start = 0
        while start < len(content):
            end = start + self.chunk_size
            chunk_content = content[start:end]

            if end < len(content) and self.chunk_overlap > 0:
                # Include overlap for next chunk
                start = end - self.chunk_overlap
            else:
                start = end

            chunks.append(Document(content=chunk_content, metadata=metadata.copy()))

        return chunks


class RecursiveSplitter(TextSplitter):
    """Recursively split text by trying different separators.

    Examples:
        >>> splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=50)
        >>> chunks = splitter.split("Long text with paragraphs...")
    """

    def __init__(
        self,
        *,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ):
        """Initialize recursive splitter.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to try (in order of preference)
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split(self, text: str | Document) -> list[Document]:
        """Recursively split text using multiple separators.

        Args:
            text: Text string or Document to split

        Returns:
            List of Document chunks
        """
        if isinstance(text, Document):
            content = text.content
            metadata = text.metadata
        else:
            content = text
            metadata = {}

        if not content:
            return []

        return self._split_recursive(content, metadata)

    def _split_recursive(self, text: str, metadata: dict[str, str]) -> list[Document]:
        """Recursively split text."""
        # If text is small enough, return as single chunk
        if len(text) <= self.chunk_size:
            return [Document(content=text, metadata=metadata.copy())]

        # Try each separator in order
        for separator in self.separators:
            if separator and separator in text:
                splits = text.split(separator)
                # Filter out empty splits
                splits = [s for s in splits if s.strip()]

                if len(splits) > 1:
                    chunks = []
                    for split in splits:
                        # Recursively split if still too large
                        if len(split) > self.chunk_size:
                            sub_chunks = self._split_recursive(split, metadata)
                            chunks.extend(sub_chunks)
                        else:
                            chunks.append(Document(content=split, metadata=metadata.copy()))

                    # Merge small chunks with overlap
                    merged_chunks = self._merge_chunks(chunks)
                    return merged_chunks

        # No separator worked, split by character
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_content = text[start:end]

            if end < len(text) and self.chunk_overlap > 0:
                start = end - self.chunk_overlap
            else:
                start = end

            chunks.append(Document(content=chunk_content, metadata=metadata.copy()))

        return chunks

    def _merge_chunks(self, chunks: list[Document]) -> list[Document]:
        """Merge small chunks together with overlap."""
        if not chunks:
            return []

        merged = []
        current = chunks[0].content

        for i in range(1, len(chunks)):
            chunk = chunks[i].content

            # If merging would exceed chunk_size, save current and start new
            if len(current) + len(chunk) > self.chunk_size:
                merged.append(Document(content=current, metadata=chunks[i - 1].metadata.copy()))
                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current:
                    overlap_text = current[-self.chunk_overlap :]
                    current = overlap_text + chunk
                else:
                    current = chunk
            else:
                current += chunk

        if current:
            merged.append(Document(content=current, metadata=chunks[-1].metadata.copy()))

        return merged


class SentenceSplitter(TextSplitter):
    """Split text by sentences.

    Examples:
        >>> splitter = SentenceSplitter(chunk_size=3)
        >>> chunks = splitter.split("First sentence. Second sentence. Third sentence.")
    """

    def __init__(self, *, chunk_size: int = 3, chunk_overlap: int = 1):
        """Initialize sentence splitter.

        Args:
            chunk_size: Number of sentences per chunk
            chunk_overlap: Number of sentences to overlap between chunks
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str | Document) -> list[Document]:
        """Split text by sentences.

        Args:
            text: Text string or Document to split

        Returns:
            List of Document chunks
        """
        if isinstance(text, Document):
            content = text.content
            metadata = text.metadata
        else:
            content = text
            metadata = {}

        if not content:
            return []

        # Split by sentence endings
        sentence_pattern = r"[.!?]+\s+"
        sentences = re.split(sentence_pattern, content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return [Document(content=content, metadata=metadata.copy())]

        chunks = []
        start = 0

        while start < len(sentences):
            end = start + self.chunk_size
            chunk_sentences = sentences[start:end]
            chunk_content = ". ".join(chunk_sentences) + "."

            chunks.append(Document(content=chunk_content, metadata=metadata.copy()))

            if end >= len(sentences):
                break

            # Move start with overlap
            start = end - self.chunk_overlap

        return chunks


class MarkdownSplitter(TextSplitter):
    """Split markdown text by headers.

    Examples:
        >>> splitter = MarkdownSplitter()
        >>> chunks = splitter.split("# Header\\n\\nContent here...")
    """

    def __init__(self, *, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize markdown splitter.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str | Document) -> list[Document]:
        """Split markdown by headers.

        Args:
            text: Text string or Document to split

        Returns:
            List of Document chunks
        """
        if isinstance(text, Document):
            content = text.content
            metadata = text.metadata
        else:
            content = text
            metadata = {}

        if not content:
            return []

        # Split by markdown headers (# ## ### etc.)
        header_pattern = r"^#{1,6}\s+.+$"
        lines = content.split("\n")
        chunks = []
        current_chunk_lines: list[str] = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            # If this is a header and we have content, save current chunk
            if re.match(header_pattern, line) and current_chunk_lines:
                chunk_content = "\n".join(current_chunk_lines)
                chunks.append(Document(content=chunk_content, metadata=metadata.copy()))

                # Start new chunk with overlap if needed
                if self.chunk_overlap > 0 and current_chunk_lines:
                    overlap_lines: list[str] = []
                    overlap_size = 0
                    for overlap_line in reversed(current_chunk_lines):
                        if overlap_size + len(overlap_line) + 1 <= self.chunk_overlap:
                            overlap_lines.insert(0, overlap_line)
                            overlap_size += len(overlap_line) + 1
                        else:
                            break
                    current_chunk_lines = overlap_lines
                    current_size = overlap_size
                else:
                    current_chunk_lines = []
                    current_size = 0

            # Add line to current chunk
            current_chunk_lines.append(line)
            current_size += line_size

            # If chunk is too large, split it
            if current_size > self.chunk_size:
                # Save what fits
                chunk_to_save = []
                saved_size = 0
                for chunk_line in current_chunk_lines:
                    if saved_size + len(chunk_line) + 1 <= self.chunk_size:
                        chunk_to_save.append(chunk_line)
                        saved_size += len(chunk_line) + 1
                    else:
                        break

                if chunk_to_save:
                    chunk_content = "\n".join(chunk_to_save)
                    chunks.append(Document(content=chunk_content, metadata=metadata.copy()))

                    # Keep remaining with overlap
                    remaining_lines = current_chunk_lines[len(chunk_to_save) :]
                    if self.chunk_overlap > 0:
                        overlap_lines = []
                        overlap_size = 0
                        for overlap_line in reversed(chunk_to_save):
                            if overlap_size + len(overlap_line) + 1 <= self.chunk_overlap:
                                overlap_lines.insert(0, overlap_line)
                                overlap_size += len(overlap_line) + 1
                            else:
                                break
                        remaining_lines = overlap_lines + remaining_lines

                    current_chunk_lines = remaining_lines
                    current_size = sum(len(line) + 1 for line in current_chunk_lines)

        # Save final chunk
        if current_chunk_lines:
            chunk_content = "\n".join(current_chunk_lines)
            chunks.append(Document(content=chunk_content, metadata=metadata.copy()))

        return chunks if chunks else [Document(content=content, metadata=metadata.copy())]
