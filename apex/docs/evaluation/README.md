# Evaluation Module

The evaluation module provides LLM-as-judge scoring of agent responses: create evaluation runs (single turn or batch), process them via a worker, and store results by run.

- **Implementation plan**: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)

## Config & secrets (Step 1.8)

Evaluation requires **explicit judge configuration** per run — no defaults. The platform does not assume a judge model or provider.

### How judge config is specified

When creating a run (`POST /evaluation/runs`), you must provide **one** of:

- **`judge_config_id`**: Reference to a stored `EvaluationJudgeConfig` (name, prompt_template, rubric, model_ref).
- **`inline_judge_config`**: Inline config with **`model_ref_id` required** — specifies which model/connection to use for the judge. Optional `prompt_template` and `rubric` override defaults.

If neither is provided, the API returns `400` with: *"Must provide judge_config_id or inline_judge_config; evaluation requires explicit judge configuration"*.

If `inline_judge_config` is provided without `model_ref_id`, the API returns `400` with: *"inline_judge_config must include model_ref_id; evaluation requires explicit judge model"*.

### Environment variables (for ModelRef / Connection)

The judge model is determined by the `model_ref` (via `judge_config` or `inline_judge_config.model_ref_id`). Each model_ref points to a Connection, which has `provider` and `api_key_env_var`. The actual API key is read from the environment, e.g.:

- OpenAI: `OPENAI_API_KEY=sk-...`
- Anthropic: `ANTHROPIC_API_KEY=...`
- Groq: `GROQ_API_KEY=...`

There are no `JUDGE_MODEL`, `JUDGE_PROVIDER`, or `JUDGE_API_KEY_ENV_VAR` defaults in the app. Docker passes them through from `.env` if you set them, but the evaluation API does not use them — it always uses the run’s snapshot, which comes from the explicit judge config you provided.

### Docker

Both **apex** and **apex-eval-worker** receive API key env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`) so the judge can call whichever provider the selected model_ref uses. There are no judge-related defaults in `docker-compose.yml`.
