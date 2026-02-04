"""File parsing utilities for document uploads."""

import logging
import io
from typing import Optional

logger = logging.getLogger(__name__)


async def parse_file(file_content: bytes, filename: str, content_type: Optional[str] = None) -> str:
    """Parse file content and extract text.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        content_type: MIME type of the file (optional)
    
    Returns:
        Extracted text content
    
    Raises:
        ValueError: If file type is not supported
    """
    # Determine file type from extension or content type
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if file_ext == 'txt' or content_type == 'text/plain':
        return parse_text_file(file_content)
    elif file_ext == 'pdf' or content_type == 'application/pdf':
        return await parse_pdf_file(file_content)
    elif file_ext in ['docx', 'doc'] or content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
        return await parse_docx_file(file_content)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Supported types: .txt, .pdf, .docx")


def parse_text_file(file_content: bytes) -> str:
    """Parse plain text file.
    
    Args:
        file_content: File content as bytes
    
    Returns:
        Text content
    """
    try:
        # Try UTF-8 first
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            # Fallback to latin-1
            return file_content.decode('latin-1')
        except UnicodeDecodeError:
            # Last resort: decode with errors='replace'
            return file_content.decode('utf-8', errors='replace')


async def parse_pdf_file(file_content: bytes) -> str:
    """Parse PDF file and extract text.
    
    Args:
        file_content: PDF file content as bytes
    
    Returns:
        Extracted text content
    
    Raises:
        ValueError: If PDF parsing fails
    """
    try:
        import pypdf
    except ImportError:
        logger.error("pypdf is not installed. Install it with: pip install pypdf")
        raise ValueError("PDF parsing requires pypdf library. Please install it: pip install pypdf")
    
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = pypdf.PdfReader(pdf_file)
        
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        raise ValueError(f"Failed to parse PDF file: {str(e)}")


async def parse_docx_file(file_content: bytes) -> str:
    """Parse DOCX file and extract text.
    
    Args:
        file_content: DOCX file content as bytes
    
    Returns:
        Extracted text content
    
    Raises:
        ValueError: If DOCX parsing fails
    """
    try:
        import docx
    except ImportError:
        logger.error("python-docx is not installed. Install it with: pip install python-docx")
        raise ValueError("DOCX parsing requires python-docx library. Please install it: pip install python-docx")
    
    try:
        docx_file = io.BytesIO(file_content)
        doc = docx.Document(docx_file)
        
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        return '\n\n'.join(text_parts)
    except Exception as e:
        logger.error(f"Failed to parse DOCX: {e}")
        raise ValueError(f"Failed to parse DOCX file: {str(e)}")
