# RAG Tool Auto-Creation Implementation

## Overview

This implementation provides automatic RAG tool creation when documents are uploaded to a knowledge base. The system follows the **hybrid approach** from the design document - auto-creating tools by default while allowing customization later.

## What Was Implemented

### 1. Database Models

**Knowledge Models** (`apex/models/knowledge.py`):
- `KnowledgeBase`: Container for related documents
- `Document`: Individual document chunks with vector store references

**Tool Models** (`apex/models/tool.py`):
- `Tool`: Represents a tool (RAG, API, function, etc.)
- `AgentTool`: Many-to-many relationship between agents and tools

**Agent Models** (`apex/models/agent.py`):
- `Agent`: Agent configuration with model settings

### 2. Repositories

- `KnowledgeBaseRepository`: CRUD for knowledge bases
- `DocumentRepository`: CRUD for documents with batch operations
- `ToolRepository`: CRUD for tools
- `AgentToolRepository`: Manage agent-tool relationships
- `AgentRepository`: CRUD for agents

### 3. Services

**RAGToolService** (`apex/services/rag_tool_service.py`):
- Auto-creates RAG tools from knowledge bases
- Generates tool names from KB names (e.g., "Product Docs" → `search_product_docs`)
- Creates Conduit Tool instances for runtime use
- Supports custom RAG templates and configuration

**KnowledgeService** (`apex/services/knowledge_service.py`):
- Manages knowledge bases and documents
- Handles document upload, chunking, and embedding
- Integrates with RAG tool service for auto-creation
- Supports auto-adding tools to agents

### 4. RAG Pipeline Components

**EmbeddingService** (`apex/ml/rag/embeddings.py`):
- Wraps HuggingFace embedding provider
- Handles batch embedding operations

**KnowledgeBaseRetriever** (`apex/ml/rag/retriever.py`):
- Custom retriever that filters by knowledge base ID
- Integrates with vector store for semantic search

**RAGPipeline** (`apex/ml/rag/pipeline.py`):
- Orchestrates RAG chain creation
- Manages templates and retrieval parameters

**ApexVectorStore** (`apex/storage/vector_store.py`):
- Wrapper around vector store with KB filtering
- Adds knowledge_base_id to document metadata

### 5. API Routes

**Knowledge Management** (`apex/api/v1/routes/knowledge.py`):
- `POST /api/v1/knowledge/knowledge-bases`: Create knowledge base
- `GET /api/v1/knowledge/knowledge-bases`: List knowledge bases
- `GET /api/v1/knowledge/knowledge-bases/{kb_id}`: Get knowledge base
- `POST /api/v1/knowledge/knowledge-bases/{kb_id}/documents`: Upload documents

## How It Works

### Flow: Document Upload → Auto-Create Tool

```
1. User uploads documents to knowledge base
   ↓
2. Documents are chunked and embedded
   ↓
3. Documents stored in vector store with KB metadata
   ↓
4. Documents saved to database
   ↓
5. System checks if tool already exists for KB
   ↓
6. If not, auto-creates RAG tool:
   - Generates tool name from KB name
   - Creates retriever for this KB
   - Creates RAG chain with default template
   - Saves tool to database
   ↓
7. Optionally auto-adds tool to specified agent
   ↓
8. Returns created documents and tool info
```

### Example API Usage

#### 1. Create Knowledge Base

```bash
POST /api/v1/knowledge/knowledge-bases
{
  "name": "Product Documentation",
  "description": "Product specs and user guides",
  "metadata": {}
}
```

#### 2. Upload Documents (Auto-Creates Tool)

```bash
POST /api/v1/knowledge/knowledge-bases/{kb_id}/documents
{
  "documents": [
    {
      "content": "Product X is a high-performance widget...",
      "source": "product_x_guide.pdf",
      "metadata": {"category": "guides"}
    }
  ],
  "auto_create_tool": true,
  "auto_add_to_agent_id": "agent-uuid-here",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

**Response:**
```json
{
  "documents": [...],
  "tool_created": {
    "id": "tool-uuid",
    "name": "search_product_documentation",
    "description": "Search the Product Documentation knowledge base..."
  },
  "message": "Successfully uploaded 15 document chunks"
}
```

## Key Features

### ✅ Auto-Creation
- Tools automatically created when documents are uploaded
- Smart naming from knowledge base names
- No manual configuration required

### ✅ Knowledge Base Filtering
- Each tool only searches its associated knowledge base
- Vector store filtering by `knowledge_base_id`
- Prevents cross-contamination between KBs

### ✅ Agent Integration
- Tools can be auto-added to agents
- Supports multiple tools per agent
- Tool-specific configuration per agent

### ✅ Extensibility
- Custom RAG templates per tool
- Configurable chunk size and overlap
- Metadata filtering support

## Next Steps / TODO

1. **Database Migrations**: Create Alembic migrations for new models
2. **Chat Model Integration**: Properly wire up chat model from config
3. **Agent Service**: Complete agent service to load tools at runtime
4. **Tool Customization**: Add endpoints for editing auto-created tools
5. **Multiple KB Support**: Allow tools to search multiple knowledge bases
6. **Testing**: Add unit and integration tests
7. **Error Handling**: Improve error handling and validation
8. **Vector Store Persistence**: Move from MemoryVectorStore to persistent store (Qdrant)

## Configuration Needed

### Environment Variables
```env
# Embedding model (optional, has defaults)
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32

# Chat model provider (needs to be configured)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=...
```

### Database Setup
Run migrations to create tables:
```bash
alembic upgrade head
```

## Architecture Notes

- **Separation of Concerns**: Models, repositories, services, and API layers are separated
- **Async-First**: All operations are async for better performance
- **Type Safety**: Uses Pydantic for validation and SQLAlchemy for ORM
- **Extensible**: Easy to add new tool types beyond RAG
- **Multi-Tenant**: All resources are scoped by organization_id
