# Evaluation Module — Implementation Plan

This document outlines the implementation plan for the Apex evaluation module: LLM- and human-judge evaluation of agent responses, run-based storage, and async execution via a separate worker. It distinguishes **MVP** scope from **future enhancements**.

---

## 1. Design Decisions (Accepted)

- **Judge model**: A different LLM than the agent (e.g. GPT-4o-mini) for cost, bias, and role separation.
- **Storage**: Reuse the same PostgreSQL database; add evaluation-specific tables (e.g. `evaluation_runs`, `evaluation_scores`).
- **Idempotency**: Run-based model. Each evaluation run creates new records; no global deduplication by (conversation, config). Optional per-batch idempotency for batch retries (same batch_id → skip or overwrite only within that batch).
- **Worker**: Evaluation runs in a separate process/container (same image as API, different command). API enqueues jobs to Redis; worker consumes and writes results to DB.
- **Scope of evaluation**: Single-turn (one user message → one agent response, optional tool calls) first; multi-turn and tool correctness can follow.

---

## 2. Implementation Phases

### Phase 1 — Foundation (MVP)

**Goal**: Store evaluation runs and scores, run LLM judge on demand or in a batch via a worker, and expose minimal API and visibility.

| Step | Description | Deliverables |
|------|-------------|--------------|
| **1.1** | **Schema & migrations** ✅ | Tables: `evaluation_runs` (id, scope_type, scope_payload, judge_config_snapshot, status, created_at, etc.), `evaluation_scores` (run_id, conversation_id/turn or test_case_id, dimensions/scores JSON, raw_judge_output, created_at). Optional: `evaluation_judge_configs` (id, name, prompt_template, rubric, model_ref) for reusable judge configs. |
| **1.2** | **Models & repositories** ✅ | SQLAlchemy models for the above; repository layer for create/read/list runs and scores (by run_id, by conversation, by time range). |
| **1.3** | **Judge service (LLM)** ✅  | Module that takes (conversation turn or messages + optional rubric) and judge config (model, prompt template, user-defined metrics), calls the judge LLM, parses structured output (e.g. scores per dimension + optional free text), returns a result object. No storage inside this module; caller persists. |
| **1.4** | **Evaluation service** ✅ | Orchestrates: create run, for each item in scope load conversation/turn (from Redis or DB), call judge service, persist score to DB. Handles “single run” (one conversation/turn) and “batch run” (list of conversations or a query). Returns run_id; actual work can be sync (MVP) or async via queue. |
| **1.5** | **Queue + worker** ✅ | Redis as job queue. API: enqueue job (payload: run_id, scope, judge_config_ref). Worker process: same image as API, command runs a loop that BLPOPs (or similar), loads run, calls evaluation service for that run’s scope, updates run status and writes scores. Worker has same env (DB, Redis, judge API keys). |
| **1.6** | **Docker** ✅ | Add `apex-eval-worker` service in `docker-compose.yml`: same build as `apex`, same env, same network/volumes, no ports; `command` runs the worker entrypoint (e.g. `python -m apex.worker`). |
| **1.7** | **API (MVP)** ✅ | Endpoints: (a) `POST /v1/evaluation/runs` — create run (body: scope type + payload, judge_config_id or inline config), enqueue job, return run_id; (b) `GET /v1/evaluation/runs/{run_id}` — run status + summary (e.g. score count); (c) `GET /v1/evaluation/runs/{run_id}/scores` — list scores for run (paginated). Optional: `GET /v1/evaluation/runs` — list runs (filter by time, status). |
| **1.8** | **Config & secrets** ✅ | Judge model and API key (e.g. OpenAI for GPT-4o-mini) in config/env; evaluation service and worker read the same. See [README.md](README.md#config--secrets-step-18).. |

**MVP outcome**: User can trigger an evaluation run (single or batch) via API; run is processed by the worker; results are stored and retrievable by run_id. No portal UI required for MVP; API-only is acceptable.

---

### Phase 2 — Portal & Human Judge (MVP or Early Enhancement)

**Goal**: Visibility in the portal and optional human scoring.

| Step | Description | Deliverables |
|------|-------------|--------------|
| **2.1** | **Runs list & detail in portal** ✅ | UI: list evaluation runs (filter by date, status), drill into a run to see scores (e.g. conversation snippet, turn, LLM score, dimensions). Reuse existing API from Phase 1. |
| **2.2** | **Human judge flow** ✅ | API: endpoint to record a human score for a given (run_id, conversation_id, turn) — e.g. `POST /v1/evaluation/runs/{run_id}/scores/{score_id}/human` with body `{ score, optional_comment }`. Store in DB (e.g. `human_score`, `human_comment`, `human_reviewed_at` on scores table or a small `human_reviews` table). |
| **2.3** | **Side panel for human review** | In portal: show a conversation (or a single turn) and the agent response; side panel to submit human score and comment. Calls the human-score API. Optionally show LLM score alongside for comparison. |

**Scope note**: Phase 2 can be split so that 2.1 is MVP (basic visibility) and 2.2–2.3 are “early enhancement” if you want to ship MVP with API-only first.

---

### Phase 3 — Batch Idempotency & Schedules (Enhancement)

**Goal**: Safe retries and scheduled evaluation jobs.

| Step | Description | Deliverables |
|------|-------------|--------------|
| **3.1** | **Batch idempotency** | For batch runs, accept optional `batch_id`. When processing a job, for each (batch_id, conversation_id, turn) either skip if a score already exists for that batch or overwrite. Ensures re-running the same batch doesn’t double-count; new batch_id always creates new scores. |
| **3.2** | **Scheduled runs** | Optional scheduler (e.g. cron in container or external) that creates a run (e.g. “all conversations from yesterday”) and enqueues it. No need to build a full scheduler in MVP; can be a simple script or cron job that calls the API. |

---

### Phase 4 — Comparison Runs & Analytics (Enhancement)

**Goal**: Compare agents/models and aggregate scores for decisions.

| Step | Description | Deliverables |
|------|-------------|--------------|
| **4.1** | **Comparison runs** | Scope type “comparison”: same prompt(s) sent to multiple agents/models; one run stores multiple scores per turn (one per agent/model). API and schema support run-level comparison flag and score rows keyed by agent_id or model ref. |
| **4.2** | **Analytics & dashboards** | Aggregate views: average score by agent, by time window, by dimension. “Latest run per conversation” or “by run_id” when querying. Optional: export to CSV/JSON for external analysis. |

---

### Phase 5 — Export & Training Integration (Enhancement)

**Goal**: Use evaluation data for training and prompt tuning.

| Step | Description | Deliverables |
|------|-------------|--------------|
| **5.1** | **Export for training** | Endpoint or job: export (conversation, response, LLM score, human score) filtered by run, date, or score threshold (e.g. “only scores ≥ 4”) in a format suitable for fine-tuning or filtering datasets. |
| **5.2** | **Integration with playbooks/prompts** | Link runs to playbook or prompt version; show which playbook/prompt produced which scores. Enables “tweak prompt → re-run eval → compare” without new schema in MVP. |

---

### Phase 6 — Live Iteration (Enhancement)

**Goal**: Optional in-chat re-evaluation and retry when score is low.

| Step | Description | Deliverables |
|------|-------------|--------------|
| **6.1** | **Sync evaluate-after-response** | After agent responds, optionally call judge (same process or quick async); if score below threshold, trigger retry (e.g. different strategy, more context) or flag for human. High latency/cost; make it opt-in and configurable per agent or experiment. |
| **6.2** | **Configurable threshold** | Per-agent or per-run config: threshold and max retries for live iteration. |

---

## 3. MVP vs Future — Summary

| Area | MVP | Future enhancement |
|------|-----|--------------------|
| **Storage** | Same DB; `evaluation_runs` + `evaluation_scores`; run-based (no global dedupe) | Per-batch idempotency; optional `evaluation_judge_configs` if not in MVP |
| **Judge** | LLM judge only; user-defined metrics in prompt; different model (e.g. GPT-4o-mini) | Rubric templates; multiple judge models A/B |
| **Human** | — | Human score API + side-panel review UI |
| **Execution** | Async via Redis queue + separate worker (same image as API) | Parallelism (multiple workers); scheduled runs |
| **API** | Create run (enqueue), get run, get scores for run | List runs with filters; comparison runs; export |
| **Portal** | Optional: minimal runs list + run detail | Human review panel; dashboards; export UI |
| **Idempotency** | Run-based only; each run creates new records | Batch idempotency for retries |
| **Live iteration** | — | Optional evaluate-after-response + retry |

---

## 4. Suggested Implementation Order

1. **Phase 1** (Foundation) — Do fully for MVP: schema, models, repositories, judge service, evaluation service, queue + worker, Docker service, minimal API.
2. **Phase 2.1** — Add runs list/detail in portal if you want any UI in MVP; otherwise defer.
3. **Phase 2.2–2.3** — Human judge API + side panel when you need human-in-the-loop.
4. **Phase 3** — Batch idempotency and schedules when you run large or recurring batches.
5. **Phases 4–6** — As product needs arise (comparison, analytics, export, live iteration).

---

## 5. Dependencies

- **Existing**: Conversation state (Redis) and/or persisted conversations (DB) so that the worker can load messages for a given conversation/turn. If conversations are only in Redis with TTL, ensure either persistence or that evaluation runs are triggered before TTL (e.g. “evaluate last 24h” with a run within that window).
- **Judge LLM**: API key and model ref (e.g. OpenAI GPT-4o-mini) in env; conduit or existing provider for calling the judge.
- **Worker**: Redis available at same URL as API; worker process has DB and Redis connectivity and judge API key.

---

## 6. Docs to Add or Update

- **`apex/docs/evaluation/README.md`** ✅: Overview of the evaluation module, link to this plan, and **Config & secrets** (judge env vars, Docker, where they are used).
- **`apex/docs/development/PROJECT_STRUCTURE.md`**: Add `evaluation` under routes/schemas and mention `apex.worker` when the worker exists.
- **`docker-compose`**: Document the `apex-eval-worker` service in deployment docs (e.g. `apex/docs/deployment/DOCKER_MIGRATIONS.md` or a dedicated deployment section).

This plan is the single source of truth for evaluation module implementation; update it as phases are completed or scope changes.
