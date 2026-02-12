# Plan: Judge Configuration & Saved Conversations for Evaluation

This document breaks down the work to deliver:

1. **Judge configuration in the Evaluation flow** — A dedicated section where users define and save judges (prompt, rubric, connection/model). Run creation then picks a saved judge instead of re-entering config each time.
2. **Save conversation from Test Agent** — A "Save" action that prompts for a label and persists the conversation so it can be selected when creating a single evaluation run.
3. **Run creation from the Portal** — A form to create a single evaluation run by choosing a saved conversation and a saved judge (no batch in this phase).

---

## Current state (brief)

- **Apex**
  - `evaluation_judge_configs` table and `EvaluationJudgeConfig` model exist (name, prompt_template, rubric, model_ref_id, organization_id). Repository has `get_by_id_and_organization` and `get_by_organization`. **No public API** for listing or creating judge configs; create-run accepts `judge_config_id` only.
  - Create-run payload supports `scope_type: "single"` with `scope_payload: { conversation_id, user_id?, turn_index? }`. Worker loads conversation from Redis via `ConversationStateStore.get(user_id, conversation_id)`. So **user_id is required** for ref-based single runs.
  - Conversations live only in Redis (ConversationStateStore) with TTL; no DB table for conversations or "saved" conversations yet.
- **Portal**
  - Evaluation: runs list + run detail + human review side panel. No "Create run" or "Judge configs" UI. No API client for judge configs or saved conversations.
  - Test Agent: chat with agent, conversationId in state. No Save button or persistence.
  - Connections and model refs are available via existing APIs; these can be reused for judge config (connection/model picker).

---

## Part A — Judge configuration (Apex API + Portal UI)

### A.1 Backend: Judge config API (Apex)

| # | Task | Details |
|---|------|--------|
| A.1.1 | **Schemas** | Add request/response Pydantic schemas for judge config: e.g. `JudgeConfigCreate` (name, prompt_template, rubric optional, model_ref_id), `JudgeConfigUpdate` (optional fields), `JudgeConfigResponse` (id, name, prompt_template, rubric, model_ref_id, organization_id, created_at, updated_at). |
| A.1.2 | **List & get** | `GET /v1/evaluation/judge-configs` — list by organization (paginated), scoped by auth. `GET /v1/evaluation/judge-configs/{id}` — get one by id and org. |
| A.1.3 | **Create** | `POST /v1/evaluation/judge-configs` — body: name, prompt_template, rubric (optional), model_ref_id. Resolve model_ref in org, create `EvaluationJudgeConfig`, return response. |
| A.1.4 | **Update & delete** | `PATCH /v1/evaluation/judge-configs/{id}` (optional fields). `DELETE /v1/evaluation/judge-configs/{id}`. Both scoped by organization. |

**Dependencies:** Existing `EvaluationJudgeConfigRepository`, `ModelRefRepository` (to validate model_ref_id for org). No new migrations (table exists).

---

### A.2 Portal: Judge config section (Evaluation page)

| # | Task | Details |
|---|------|--------|
| A.2.1 | **API client & types** | Add `evaluationJudgeConfigsApi` (or extend `evaluationApi`): list, get, create, update, delete. Add types: `JudgeConfig`, `JudgeConfigCreate`, `JudgeConfigUpdate`. |
| A.2.2 | **Judge config list** | On Evaluation page (or a sub-view), a section "Judge configs": list saved configs (name, model ref summary, created). Buttons: Add judge, Edit, Delete. |
| A.2.3 | **Judge config form** | Form (modal or inline): Name (required), Prompt template (textarea, with hint for placeholders e.g. `{{ user_message }}`, `{{ agent_response }}`, `{{ rubric }}`), Rubric (e.g. key-value list: dimension name + scale, or JSON textarea), Connection/Model (dropdown: reuse connections + model refs from existing APIs). Submit → create or update. |
| A.2.4 | **Reuse connections/models** | Use existing `connectionsApi` and `modelRefsApi` (or equivalent) to populate model ref dropdown; filter by org is implicit from auth. No new backend for connections/model refs. |

**Dependencies:** Part A.1 (backend API) done so the portal can list and create judge configs.

---

## Part B — Saved conversations (Apex persistence + API, Portal Test Agent + Evaluation)

### B.1 Backend: Persist saved conversations (Apex)

| # | Task | Details |
|---|------|--------|
| B.1.1 | **Schema & migration** | New table e.g. `saved_conversations` (or `evaluation_conversations`): id (UUID), organization_id, conversation_id (UUID), user_id (UUID), label (string, required), agent_id (UUID nullable), created_at. Optional: message_count, or a JSON/related table to snapshot messages for TTL independence (can be Phase 2). Indexes: org_id, conversation_id (if you need lookup by conv), created_at. |
| B.1.2 | **Model & repository** | SQLAlchemy model `SavedConversation` (or equivalent). Repository: create, get_by_id, list_by_organization (with optional filters, pagination), delete. |
| B.1.3 | **API** | `POST /v1/evaluation/saved-conversations` — body: conversation_id, label. Infer user_id and organization_id from auth; optionally agent_id from request body if Test Agent sends it. Load current conversation from Redis (optional: snapshot messages into DB here for durability); create row. Return created record. `GET /v1/evaluation/saved-conversations` — list by org (paginated), return id, conversation_id, user_id, label, agent_id, created_at. Optional: `GET /v1/evaluation/saved-conversations/{id}`, `DELETE /v1/evaluation/saved-conversations/{id}`. |
| B.1.4 | **Evaluation worker** | No change required: single-run scope_payload already supports conversation_id + user_id + turn_index. When creating a run from the portal, send user_id from the saved conversation record so the worker can load state from Redis. |

**Note:** If you do not snapshot messages to DB, saved conversations are "bookmarks"; evaluation must run before Redis TTL expires (or ensure TTL is long enough / extended on save). Snapshotting messages is optional and can be a follow-up.

---

### B.2 Portal: Save conversation (Test Agent page)

| # | Task | Details |
|---|------|--------|
| B.2.1 | **API client & types** | Add saved-conversations API: create(body), list(). Types: SavedConversation (id, conversation_id, user_id, label, agent_id, created_at), SavedConversationCreate (conversation_id, label, agent_id?). |
| B.2.2 | **Save button** | On Test Agent page, add a "Save for evaluation" (or "Save") button. Enabled when there is an active conversation (conversationId and at least one message). |
| B.2.3 | **Label modal** | On Save click: open modal (or inline form) — "Label this conversation" (required text input), optional note. Submit → call POST saved-conversations with conversation_id, label, and agent_id if available. On success: toast or message "Saved"; optionally close modal. |

**Dependencies:** B.1 (backend API for saved conversations). Test Agent page already has conversationId and agent context.

---

### B.3 Portal: Pick saved conversation when creating a run (Evaluation)

| # | Task | Details |
|---|------|--------|
| B.3.1 | **List in run form** | In the "Create run" form (Part C), add a "Conversation" selector: call GET saved-conversations, show dropdown or list (label + conversation_id snippet + date). User picks one. Store selected saved_conversation (so you have conversation_id and user_id for the API). |
| B.3.2 | **Payload** | When submitting create run, scope_payload must include conversation_id, user_id (from selected saved conversation), and turn_index (default 0 or from a small form field). |

**Dependencies:** B.1 API and B.2 (so there are saved conversations to list). Part C defines the full Create run form.

---

## Part C — Run creation from Portal (Evaluation)

| # | Task | Details |
|---|------|--------|
| C.1 | **Create run form** | On Evaluation page: "Create run" button → form (new page or modal). Fields: (1) Conversation — dropdown/list from saved conversations (Part B.3). (2) Turn index — number, default 0. (3) Judge — dropdown of saved judge configs (Part A.2). (4) Optional: Agent (for association). Submit → POST /v1/evaluation/runs with scope_type: "single", scope_payload: { conversation_id, user_id, turn_index }, judge_config_id: selected judge id. The existing create-run API already accepts this payload; no backend change. |
| C.2 | **Success behavior** | On success: show "Run created" and link to run detail page, or redirect to run detail. User can see status (pending/running) and scores when the worker completes. |

**Dependencies:** Part A (judge configs list so user can pick one), Part B (saved conversations list and payload shape).

---

## Suggested implementation order

1. **A.1** — Judge config API (Apex). Enables portal to manage judges.
2. **A.2** — Judge config section in Portal (list + form, reuse connections/model refs).
3. **B.1** — Saved conversations table, model, repository, API (Apex). Enables save and list.
4. **B.2** — Save button + label modal on Test Agent page.
5. **B.3** — Conversation selector in Create run form (can be done together with C.1).
6. **C.1–C.2** — Create run form and success handling.

Optional: Message snapshot when saving a conversation (B.1) can be added later for TTL independence; scope is still "single" and worker can be extended to load from DB when Redis key is missing.

---

## Out of scope in this plan

- **Batch runs** from the portal (UI and any batch-specific API).
- **Listing "all" conversations** from Redis by org (no such API today); only "saved" conversations are listable.
- **Editing judge config** from run detail; only from the Judge config section.
- **Permissions** beyond org scoping (assume same as rest of evaluation).

---

## Summary table

| Part | Backend (Apex) | Portal |
|------|----------------|--------|
| **A. Judge config** | Judge config CRUD API (list, get, create, update, delete) | Judge config section: list, add/edit form (name, prompt, rubric, connection/model) |
| **B. Saved conversations** | Table + API (create, list); run creation already accepts user_id + conversation_id | Test Agent: Save + label modal; Evaluation: pick conversation in Create run form |
| **C. Run creation** | No change (existing POST /evaluation/runs) | Create run form: pick saved conversation, turn index, pick judge, submit |

This plan keeps judge configuration and saved conversations modular so they can be implemented and tested in order above.
