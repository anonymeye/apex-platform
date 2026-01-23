# RAG Tool Integration Design Analysis

## Question
How should the agent access knowledge base documents after a user uploads them?

## Two Approaches

### Approach 1: Automatic Tool Creation (Auto-Inject)
**When documents are uploaded → automatically create a RAG tool and inject it into the agent**

### Approach 2: Customer-Defined Tools (Manual Link)
**Customer defines tools and explicitly links them to knowledge bases**

---

## Approach 1: Automatic Tool Creation

### How It Works
1. User uploads documents → documents are embedded and stored in vector store
2. System automatically creates a RAG tool (e.g., `search_knowledge_base`)
3. Tool is automatically added to agent's tool list
4. Agent can call the tool when it needs to retrieve information

### Implementation Example
```python
# When documents are uploaded
async def on_documents_uploaded(knowledge_base_id: str, documents: list[Document]):
    # 1. Embed and store documents
    await knowledge_service.embed_and_store(knowledge_base_id, documents)
    
    # 2. Auto-create RAG tool
    rag_tool = await create_rag_tool(
        knowledge_base_id=knowledge_base_id,
        retriever=retriever,
        tool_name=f"search_kb_{knowledge_base_id}",
        description="Search the knowledge base for relevant information"
    )
    
    # 3. Auto-inject into agent
    await agent_service.add_tool(agent_id, rag_tool)
```

### Pros ✅
1. **Zero Configuration** - Works out of the box, no user setup needed
2. **Immediate Availability** - Documents are immediately accessible to agent
3. **Simple UX** - Users just upload → agent can use it
4. **Less Cognitive Load** - Users don't need to understand tools/RAG
5. **Good for MVP** - Fast to implement, works for most use cases
6. **Consistent Behavior** - All knowledge bases work the same way

### Cons ❌
1. **Less Control** - Users can't customize tool behavior
2. **Tool Naming** - Generic names like `search_kb_123` aren't descriptive
3. **Multiple Knowledge Bases** - If user has 3 KBs, agent gets 3 similar tools (confusing)
4. **No Custom Logic** - Can't add domain-specific filtering or processing
5. **Tool Bloat** - Agent might have many auto-generated tools
6. **Less Flexible** - Hard to combine multiple KBs into one tool

---

## Approach 2: Customer-Defined Tools

### How It Works
1. User uploads documents → documents are embedded and stored
2. User goes to "Tools" tab and creates a new tool
3. User links the tool to one or more knowledge bases
4. User customizes tool name, description, and behavior
5. User explicitly adds tool to agent

### Implementation Example
```python
# User creates tool via UI/API
tool = await tool_service.create_tool(
    name="search_product_docs",
    description="Search product documentation and specifications",
    type="rag",
    knowledge_base_ids=["kb_products", "kb_specs"],
    custom_template="Use product docs to answer: {question}",
    filters={"category": "products"}
)

# User explicitly adds to agent
await agent_service.add_tool(agent_id, tool_id)
```

### Pros ✅
1. **Full Control** - Users customize tool behavior, naming, descriptions
2. **Better Organization** - Users can create domain-specific tools (e.g., "search_policies", "search_products")
3. **Flexibility** - Can combine multiple KBs, add filters, custom templates
4. **Explicit Intent** - Users understand what tools their agent has
5. **Reusability** - Same tool can be used by multiple agents
6. **Advanced Features** - Can add metadata filtering, hybrid search, etc.
7. **Better for Complex Use Cases** - Supports sophisticated workflows

### Cons ❌
1. **More Complex UX** - Users need to understand tools and RAG concepts
2. **Extra Steps** - Upload docs → create tool → link KB → add to agent
3. **Learning Curve** - Users need to learn tool creation
4. **More Code** - Requires tool builder UI and management
5. **Potential Confusion** - Users might forget to create/link tools

---

## Hybrid Approach (Recommended) 🎯

### Best of Both Worlds

**Default: Auto-Create with Smart Defaults**
- When documents are uploaded, automatically create a tool
- Use intelligent naming based on KB name/metadata
- Auto-add to agent

**Advanced: Allow Customization**
- Users can edit auto-created tools
- Users can create custom tools manually
- Users can combine multiple KBs into one tool
- Users can disable auto-creation if they prefer manual control

### Implementation Flow

```
1. User uploads documents to "Product Docs" knowledge base
   ↓
2. System auto-creates tool:
   - Name: "search_product_docs" (from KB name)
   - Description: "Search Product Docs knowledge base"
   - Linked to: kb_product_docs
   - Auto-added to agent
   ↓
3. User can optionally:
   - Rename tool to "get_product_info"
   - Add custom description
   - Link additional KBs
   - Add metadata filters
   - Remove from agent if not needed
```

### Code Structure
```python
# Auto-create with smart defaults
async def auto_create_rag_tool(knowledge_base: KnowledgeBase) -> Tool:
    """Auto-create RAG tool when KB is created."""
    tool_name = f"search_{knowledge_base.slug}"  # e.g., "search_product_docs"
    
    return Tool(
        name=tool_name,
        description=f"Search {knowledge_base.name} knowledge base",
        type="rag",
        knowledge_base_ids=[knowledge_base.id],
        auto_created=True,  # Flag for UI
    )

# Allow customization
async def update_tool(tool_id: str, updates: ToolUpdate):
    """User can customize auto-created tool."""
    # Allow renaming, adding KBs, custom templates, etc.
    pass
```

---

## Comparison Matrix

| Feature | Auto-Create | Customer-Defined | Hybrid |
|---------|-------------|-------------------|--------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Flexibility** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Control** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Implementation Complexity** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Good for MVP** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Good for Advanced Users** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Recommendation

### For MVP: Start with Auto-Create (Approach 1)
- Fastest to implement
- Works for 80% of use cases
- Can always add customization later

### For Production: Move to Hybrid (Approach 3)
- Best user experience
- Supports both simple and complex use cases
- Progressive disclosure (simple by default, advanced when needed)

---

## Implementation Details

### Auto-Create Tool Structure
```python
class RAGTool:
    name: str  # Auto-generated from KB name
    description: str  # Auto-generated
    knowledge_base_ids: list[str]  # Linked KBs
    retriever_config: dict  # k, filters, etc.
    template: str  # RAG prompt template
    auto_created: bool = True
    editable: bool = True  # Users can modify
```

### Tool-to-KB Relationship
- **One-to-Many**: One tool can search multiple KBs
- **Many-to-One**: Multiple tools can search same KB (with different configs)
- **Default**: One tool per KB (auto-created)

### Agent Tool Management
```python
# Agent has list of tools
agent.tools = [
    "search_product_docs",  # Auto-created
    "search_policies",      # Auto-created
    "custom_calculator",    # User-defined
    "api_lookup"            # User-defined
]
```

---

## Implementation Example

### Auto-Create RAG Tool Service

```python
# apex/src/apex/services/rag_tool_service.py

from conduit.rag import RAGChain, VectorRetriever
from conduit.tools import Tool
from pydantic import BaseModel, Field
from typing import Optional

class KnowledgeBaseSearchParams(BaseModel):
    """Parameters for knowledge base search tool."""
    query: str = Field(description="The question or query to search the knowledge base")

class RAGToolService:
    """Service for creating and managing RAG tools."""
    
    async def auto_create_rag_tool(
        self,
        knowledge_base_id: str,
        knowledge_base_name: str,
        retriever: VectorRetriever,
        model: ChatModel,
        agent_id: Optional[str] = None,
    ) -> Tool:
        """Auto-create a RAG tool when knowledge base is created.
        
        Args:
            knowledge_base_id: ID of the knowledge base
            knowledge_base_name: Name of the knowledge base (for tool naming)
            retriever: VectorRetriever instance for the KB
            model: ChatModel for RAG chain
            agent_id: Optional agent to auto-add tool to
            
        Returns:
            Created Tool instance
        """
        # Generate tool name from KB name
        tool_name = self._generate_tool_name(knowledge_base_name)
        
        # Default RAG template
        default_template = (
            "Use the following information from the knowledge base to answer "
            "the question accurately. If the information is not available, "
            "say so clearly.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )
        
        # Create RAG chain
        rag_chain = RAGChain(
            model=model,
            retriever=retriever,
            template=default_template,
            k=5,  # Retrieve top 5 chunks
        )
        
        # Create tool function
        async def search_knowledge_base(params: KnowledgeBaseSearchParams) -> str:
            """Search knowledge base and return answer."""
            result = await rag_chain(params.query)
            
            answer = result["answer"]
            sources = [doc.metadata.get("source", "unknown") for doc in result["sources"]]
            unique_sources = list(set(sources))
            
            return (
                f"{answer}\n\n"
                f"[Sources: {', '.join(unique_sources[:3])}]"  # Show top 3 sources
            )
        
        # Create tool
        tool = Tool(
            name=tool_name,
            description=f"Search the {knowledge_base_name} knowledge base for information",
            parameters=KnowledgeBaseSearchParams,
            fn=search_knowledge_base,
        )
        
        # Auto-add to agent if specified
        if agent_id:
            await self._add_tool_to_agent(agent_id, tool)
        
        return tool
    
    def _generate_tool_name(self, kb_name: str) -> str:
        """Generate tool name from knowledge base name.
        
        Examples:
            "Product Docs" -> "search_product_docs"
            "Company Policies" -> "search_company_policies"
        """
        # Convert to slug
        slug = kb_name.lower().replace(" ", "_").replace("-", "_")
        # Remove special chars
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        return f"search_{slug}"
    
    async def _add_tool_to_agent(self, agent_id: str, tool: Tool):
        """Add tool to agent's tool list."""
        # Implementation would update agent.tools in database
        pass
```

### Knowledge Service Integration

```python
# apex/src/apex/services/knowledge_service.py

class KnowledgeService:
    """Service for managing knowledge bases."""
    
    async def upload_documents(
        self,
        knowledge_base_id: str,
        documents: list[Document],
        agent_id: Optional[str] = None,
    ):
        """Upload documents to knowledge base and auto-create tool.
        
        Flow:
        1. Embed documents
        2. Store in vector store
        3. Auto-create RAG tool
        4. Auto-add to agent (if agent_id provided)
        """
        # 1. Embed and store documents
        embeddings = await self.embed_model.embed_documents(
            [doc.content for doc in documents]
        )
        await self.vector_store.add_documents(documents, embeddings)
        
        # 2. Get knowledge base info
        kb = await self.get_knowledge_base(knowledge_base_id)
        
        # 3. Create retriever for this KB
        retriever = VectorRetriever(
            store=self.vector_store,
            embedding_model=self.embed_model,
            filter={"knowledge_base_id": knowledge_base_id}  # Filter by KB
        )
        
        # 4. Auto-create RAG tool
        rag_tool_service = RAGToolService()
        tool = await rag_tool_service.auto_create_rag_tool(
            knowledge_base_id=knowledge_base_id,
            knowledge_base_name=kb.name,
            retriever=retriever,
            model=self.chat_model,
            agent_id=agent_id,  # Auto-add to agent
        )
        
        # 5. Save tool to database
        await self.tool_repository.create(tool)
        
        return tool
```

### Agent Service Integration

```python
# apex/src/apex/services/agent_service.py

class AgentService:
    """Service for managing agents."""
    
    async def create_agent_for_chat(
        self,
        agent_id: str,
        user_message: str,
    ) -> Agent:
        """Create agent instance with all tools for chat.
        
        This loads:
        - Agent configuration
        - All linked tools (including auto-created RAG tools)
        - Model configuration
        """
        # Get agent config from database
        agent_config = await self.agent_repository.get(agent_id)
        
        # Get all tools for this agent
        tools = await self.tool_repository.get_by_agent(agent_id)
        
        # Convert database tools to Conduit Tool objects
        conduit_tools = []
        for tool_db in tools:
            if tool_db.type == "rag":
                # Recreate RAG tool from config
                tool = await self._create_rag_tool_from_db(tool_db)
            else:
                # Other tool types
                tool = await self._create_tool_from_db(tool_db)
            conduit_tools.append(tool)
        
        # Create agent
        agent = make_agent(
            model=self._get_model(agent_config.model_id),
            tools=conduit_tools,
            system_message=agent_config.system_message,
            max_iterations=agent_config.max_iterations,
        )
        
        return agent
```

---

## Next Steps

1. **Phase 1 (MVP)**: Implement auto-create approach
   - Auto-generate tool when KB is created
   - Simple naming: `search_{kb_slug}`
   - Auto-add to agent

2. **Phase 2**: Add customization
   - Allow tool editing (rename, description)
   - Allow linking multiple KBs to one tool
   - Allow removing auto-created tools

3. **Phase 3**: Advanced features
   - Custom RAG templates per tool
   - Metadata filtering
   - Hybrid search options
   - Tool versioning
