# Apex - Project Vision & Design Document

## Project Overview

**Apex** is a SaaS platform that enables businesses to build, train, and deploy AI chat agents tailored to their specific knowledge base, processes, and use cases. The platform is industry-agnostic, allowing customers to define their own data schemas, tools, and workflows.

## Vision

**Value Proposition**: Empower businesses to create intelligent assistants that understand their unique context—whether for customer support, internal operations, or process automation—without requiring deep ML expertise.

**Project Goals**:

- Open source the codebase (not production-ready)
- Demonstrate ability to build semi-production systems
- Showcase learnings from LLM engineering best practices
- **Showcase fine-tuning techniques and experimentation capabilities**
- Keep it simple and focused (not feature-complete like commercial solutions)

---

## Target Users

- **Primary**: Businesses across industries (agnostic approach)
- **Use Cases**: 
  - Customer-facing support and assistance
  - Internal knowledge management and operations
  - Process automation and background workflows

---

## Core Features (MVP)

### 1. Agent Builder & Configuration

- **Knowledge Loading**: Upload documents, policies, rules, documentation, product data, company information
- **Schema Definition**: Users manually upload their data schema; LLM analyzes and understands the structure
- **Persona & Tone**: Configure agent personality, greetings, and communication style
- **Guardrails**: Pre-built safety measures for accuracy, toxicity, context boundaries, security

### 2. Training & Fine-tuning

- **Q&A Training**: Provide example questions and answers to guide agent behavior
- **Answer Scoring**: Rate agent responses to improve quality
- **Fine-tuning Workflow**: 
  - Collect training data from playbooks, Q&A pairs, and user interactions
  - Experiment with different fine-tuning approaches (LoRA, QLoRA)
  - Model selection and comparison (7B-13B models: LLaMA, Mistral, Qwen-based)
  - Track fine-tuning experiments and results
- **Response Evaluators**: Automatic evaluation system that prompts agent for iteration when needed
- **Experimentation Platform**: A/B test different models, fine-tuning strategies, and configurations

### 3. Tools & Playbooks

- **Custom Tools**: Users define their own tools with schemas (industry-agnostic)
- **Playbooks**: Primarily used for fine-tuning the model - define training scenarios, expected behaviors, and process workflows
- **Fine-tuning Pipeline**: Convert playbooks and Q&A examples into fine-tuning datasets
- **Background Triggers**: Set up automated processes that run in the background

### 4. Testing & Deployment

- **Portal Testing**: Test agents directly within the SaaS portal (no SDK required for MVP)
- **Pre-deployment Validation**: Ensure agent is ready before going live

### 5. Monitoring & Experimentation Dashboard

- **Performance Metrics**: Track agent performance, response quality, scores
- **Tool Usage**: Monitor which tools are being used and how
- **Process Tracking**: View triggered background processes
- **Response Logging**: Review agent interactions and responses
- **Fine-tuning Experiments**: Track and compare different fine-tuning runs, model versions, and configurations
- **A/B Testing**: Compare performance across different model variants and strategies

---

## Architecture Overview

### System Components

```
┌─────────────────┐
│  Frontend Portal │  (SaaS Interface)
│  - Agent Builder │
│  - Testing       │
│  - Monitoring    │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│   Backend API   │  (REST API)
│   - Chat API    │
│   - Agent Mgmt  │
│   - Data Ingestion│
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│  ML/Agent Layer │  (Built on Conduit)
│  - RAG Pipeline │
│  - Agent Loop   │
│  - Tools Exec   │
│  - Evaluators   │
│  - Fine-tuning  │
│  - Experimentation│
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│  Data Layer     │
│  - Vector Store │
│  - Knowledge DB │
│  - Config Store │
└─────────────────┘
```

### Key Design Decisions

1. **Industry-Agnostic Approach**

   - Users define their own data schemas
   - LLM analyzes and understands custom schemas (Option 3)
   - Flexible tool definition system

2. **Portal-First MVP**

   - No SDK/integration layer for MVP
   - All interaction through web portal
   - Future: Channel integrations (Slack, email, SMS)

3. **Built on Conduit**

   - Leverages existing LLM orchestration library
   - RAG, agents, tools, providers already implemented
   - Focus on application layer, not infrastructure

4. **Data Processing Pipeline**

   - Cleaning, filtering, and chunking before embedding
   - Text-based embeddings for MVP (documents with graphs/images handled later)
   - Schema-aware RAG extraction

5. **Fine-tuning & Experimentation Focus**

   - Playbooks serve as primary fine-tuning data source
   - Support for LoRA/QLoRA fine-tuning techniques
   - Experimentation platform to compare models and strategies
   - Showcase best practices in fine-tuning workflows

---

## Data Flow

### Agent Training Flow

```
User Uploads Data → Schema Definition → LLM Analysis → 
Data Processing → Embedding → Vector Store → Agent Configuration

Playbooks + Q&A → Fine-tuning Dataset → Experimentation → 
Model Training (LoRA/QLoRA) → Evaluation → Model Selection
```

### Chat Interaction Flow

```
User Message → Backend API → Agent Loop → 
RAG Retrieval → Tool Selection → Response Generation → 
Evaluation → (Iteration if needed) → Response to User
```

### Background Process Flow

```
Trigger Event → Process Playbook → Agent Execution → 
Tool Calls → Result Logging → Monitoring Dashboard
```

---

## Future Enhancements (Post-MVP)

- **Channel Integrations**: Slack, email, SMS, web widgets
- **Advanced Analytics**: Customer interaction analytics, usage patterns
- **Advanced Fine-tuning**: Additional techniques, hyperparameter optimization, automated fine-tuning pipelines
- **Multi-modal**: Support for documents with graphs, images, tables
- **SDK/API**: Programmatic access for integrations
- **Advanced Monitoring**: Third-party tool integrations (e.g., Datadog, Sentry)

---

## Technical Stack (High-Level)

- **Frontend**: Web portal (framework TBD)
- **Backend**: Python API (FastAPI/Flask)
- **ML Layer**: Conduit library (LLM orchestration)
- **Embeddings**: Local HuggingFace service (sentence-transformers)
- **Fine-tuning**: LoRA/QLoRA libraries (e.g., PEFT, transformers)
- **Models**: 7B-13B range (LLaMA-based, Mistral-based, Qwen-based)
- **Vector Store**: TBD (e.g., Pinecone, Weaviate, local)
- **Database**: TBD (for config, schemas, metadata, experiment tracking)

---

## Open Questions / Decisions Needed

1. Vector store choice (managed vs self-hosted)
2. Database choice for metadata/config
3. Frontend framework selection
4. Deployment infrastructure approach
5. Authentication/authorization strategy
6. Multi-tenancy architecture
7. Pricing/billing model (if applicable)

---

## Success Criteria

- Users can successfully build and deploy an agent
- Agent accurately retrieves and uses customer knowledge
- Fine-tuning workflow is clear and demonstrates best practices
- Experimentation platform allows comparison of different approaches
- Monitoring provides actionable insights
- System handles custom schemas and tools effectively
- Codebase demonstrates production-quality patterns and showcases fine-tuning techniques
