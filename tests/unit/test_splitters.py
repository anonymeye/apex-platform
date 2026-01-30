"""Tests for text splitters."""

import pytest

from conduit.rag.splitters import (
    CharacterSplitter,
    Document,
    MarkdownSplitter,
    RecursiveSplitter,
    SentenceSplitter,
    TextSplitter,
)


def test_document_model():
    """Test Document model."""
    doc = Document(content="Hello world", metadata={"source": "test.txt"})
    assert doc.content == "Hello world"
    assert doc.metadata == {"source": "test.txt"}


def test_character_splitter_basic():
    """Test basic character splitting."""
    splitter = CharacterSplitter(chunk_size=10, chunk_overlap=2)
    text = "This is a test string"
    chunks = splitter.split(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Document) for chunk in chunks)
    # With overlap, we can't just join - verify chunks are reasonable size
    assert all(len(chunk.content) <= 10 for chunk in chunks)


def test_character_splitter_with_separator():
    """Test character splitter with separator."""
    splitter = CharacterSplitter(chunk_size=20, chunk_overlap=5, separator="\n\n")
    text = "First paragraph\n\nSecond paragraph\n\nThird paragraph"
    chunks = splitter.split(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Document) for chunk in chunks)


def test_character_splitter_with_document():
    """Test character splitter with Document input."""
    splitter = CharacterSplitter(chunk_size=10, chunk_overlap=2)
    doc = Document(content="This is a test", metadata={"source": "test.txt"})
    chunks = splitter.split(doc)

    assert len(chunks) > 0
    assert all(chunk.metadata == doc.metadata for chunk in chunks)


def test_character_splitter_validation():
    """Test character splitter validation."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        CharacterSplitter(chunk_size=0)

    with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
        CharacterSplitter(chunk_size=10, chunk_overlap=-1)

    with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
        CharacterSplitter(chunk_size=10, chunk_overlap=10)


def test_recursive_splitter_basic():
    """Test basic recursive splitting."""
    splitter = RecursiveSplitter(chunk_size=20, chunk_overlap=5)
    text = "First sentence. Second sentence. Third sentence."
    chunks = splitter.split(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Document) for chunk in chunks)


def test_recursive_splitter_with_separators():
    """Test recursive splitter with custom separators."""
    splitter = RecursiveSplitter(chunk_size=20, chunk_overlap=5, separators=["\n\n", "\n", ". "])
    text = "First paragraph\n\nSecond paragraph\n\nThird paragraph"
    chunks = splitter.split(text)

    assert len(chunks) > 0


def test_recursive_splitter_small_text():
    """Test recursive splitter with small text."""
    splitter = RecursiveSplitter(chunk_size=1000)
    text = "Short text"
    chunks = splitter.split(text)

    assert len(chunks) == 1
    assert chunks[0].content == text


def test_sentence_splitter_basic():
    """Test basic sentence splitting."""
    splitter = SentenceSplitter(chunk_size=2, chunk_overlap=1)
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    chunks = splitter.split(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Document) for chunk in chunks)
    assert all("." in chunk.content for chunk in chunks)


def test_sentence_splitter_validation():
    """Test sentence splitter validation."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        SentenceSplitter(chunk_size=0)

    with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
        SentenceSplitter(chunk_size=2, chunk_overlap=-1)


def test_markdown_splitter_basic():
    """Test basic markdown splitting."""
    splitter = MarkdownSplitter(chunk_size=50, chunk_overlap=10)
    text = "# Header 1\n\nContent here.\n\n## Header 2\n\nMore content."
    chunks = splitter.split(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Document) for chunk in chunks)


def test_markdown_splitter_with_headers():
    """Test markdown splitter with multiple headers."""
    splitter = MarkdownSplitter()
    text = """# First Section

Content of first section.

## Subsection

Content of subsection.

# Second Section

Content of second section."""
    chunks = splitter.split(text)

    assert len(chunks) > 0


def test_empty_text():
    """Test splitting empty text."""
    splitter = CharacterSplitter()
    chunks = splitter.split("")
    assert chunks == []

    # Document doesn't allow empty content, so test with minimal content
    doc = Document(content=" ", metadata={})
    chunks = splitter.split(doc)
    assert len(chunks) > 0


def test_text_splitter_abstract():
    """Test that TextSplitter is abstract."""
    with pytest.raises(TypeError):
        TextSplitter()  # type: ignore
