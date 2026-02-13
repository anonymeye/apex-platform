# Apex

A platform for building, configuring, and evaluating AI chat agents over your own knowledge base and tools. Open source and **not production-ready**.

---

## Features accomplished

- **Authentication & orgs** — Register, login (JWT), switch organization; multi-tenant ready.
- **Agents** — Create, edit, delete agents; attach knowledge base, tools, and model (connection + model ref).
- **Knowledge** — Create knowledge bases; upload documents; embed and store in vector store (Qdrant/pgvector); list, search, delete documents; RAG tools linked to knowledge.
- **Tools** — CRUD for tools; RAG-aware tools; attach tools to agents.
- **Connections & model refs** — CRUD for LLM connections (provider, API key via env); model refs per connection; used by agents and evaluation judge.
- **Chat** — Chat with an agent via API; conversation state in Redis (TTL); get/clear conversation state.
- **Test Agent (portal)** — Chat with an agent in the browser; conversation ID in state.
- **Evaluation** — Judge configs (CRUD, prompt/rubric/model); saved conversations (with message snapshot in DB); create evaluation run (single turn or whole conversation); Redis-backed worker runs judge and persists scores; human review (score + comment); list runs, run detail; refetch on navigate/focus and manual Refresh.
- **Portal (Next.js)** — Dashboard, auth, agents, knowledge, tools, connections, models, evaluation, test agent; placeholder pages for monitoring, experiments, training.
- **Conduit** — LLM orchestration library (async/sync, tool calling, RAG, multiple providers) used by Apex.
- **Docker** — Compose: PostgreSQL (pgvector), Redis, Apex API, evaluation worker, portal.

---

## Not done yet (vs. end goal)

- **Fine-tuning** — No training module; training page is a stub; dataset/build pipeline and LoRA/QLoRA runs are out of scope (see `apex/docs/training/README.md`).
- **Playbooks** — Not implemented (no API or UI).
- **Schema definition** — No LLM-driven schema analysis or user-defined schema flow.
- **Experimentation / A/B testing** — Experiments page is a placeholder; no experiment tracking or model comparison.
- **Monitoring dashboard** — Monitoring page is a placeholder; no metrics, tool usage, or process tracking.
- **Guardrails** — No pre-built safety or accuracy guardrails in the agent path.
- **Background triggers** — No automated/background process execution.
- **Channel integrations** — No Slack, email, SMS, or web widgets.
- **SDK / programmatic API** — No first-class SDK or integration docs for embedding.
- **Production readiness** — Not hardened for production (auth, scaling, secrets, etc.).

---

## Repo layout

- **`apex/`** — Backend API (FastAPI), services, models, migrations, evaluation worker, docs.
- **`portal/`** — Frontend (Next.js, TypeScript, shadcn/ui, TanStack Query).
- **`conduit/`** — Python LLM orchestration library (used by Apex).
- **`docker-compose.yml`** — Run Postgres, Redis, Apex, eval worker, portal.

See `apex/README.md`, `portal/README.md`, and `conduit/README.md` for per-component setup and docs. High-level vision and design: `apex/docs/development/VISION.md`.

---

## Quick start

1. Copy `.env.example` to `.env` and set (at least) `SECRET_KEY`, DB, Redis, and any LLM API keys (e.g. `OPENAI_API_KEY`, `GROQ_API_KEY`).
2. From repo root: `docker-compose up -d` (builds and starts Postgres, Redis, Apex, eval worker, portal).
3. Run migrations: `docker-compose exec apex alembic -c apex/alembic.ini upgrade head` (or from `apex/`: `poetry run alembic upgrade head` if using local DB).
4. Open the portal (e.g. http://localhost:3000), register, create a connection and model ref, create an agent, optionally add knowledge and tools, then chat via Test Agent or API.

---

## License

To be determined. Contributing welcome for learning and demonstration.
