# Training module – thinking and options (reference only)

**Nothing is finalized.** This doc is a reference of options, pros/cons, and open questions. No commitment to a specific approach.

---

## 1. What “training” means in this context

- **Fine-tuning:** User has a base model (e.g. open-source LLM). They provide a dataset (prompt/completion or text). A process (e.g. LoRA) updates a small adapter so the model behaves better on that data. Output = adapter weights (and tokenizer).
- **Trained model in use:** Base model + adapter (and tokenizer) are loaded by an inference server. The agent calls that server via an API (e.g. OpenAI-compatible). Apex does not run inference; it only calls the API (connection + model ref).

---

## 2. Who runs training / where does it run?

| Option | Who runs it | Where | Apex’s role |
|--------|-------------|--------|-------------|
| **User runs Colab (or similar)** | User | Colab, Kaggle, etc. | None or minimal (e.g. “here’s a notebook link”, or dataset ref only). |
| **Apex triggers a worker** | Apex calls cloud API to start a container/worker | RunPod, Vast.ai, Lambda, etc. | Create job → call vendor API to start worker with job payload → worker runs training (same codebase) → worker reports back. |
| **Apex runs worker pool** | We run long-lived workers | Our infra / our cloud | Workers poll Apex for jobs, run training, report back. We own the worker infra. |

**Takeaway:** Training needs a GPU and real compute. Apex (control plane) does not run that compute; either the user runs it (Colab) or we trigger/run workers elsewhere. We don’t host GPUs.

---

## 3. Who runs deployment (serving the trained model)?

After training, the user has an adapter (and tokenizer). To use it in an agent, something must **serve** base model + adapter behind an API.

| Option | Who deploys / serves | Experience |
|--------|----------------------|------------|
| **User owns server/API** | User runs vLLM, Ollama, or custom API on their machine or cloud. | User does the work; Apex only needs connection URL + model ref. |
| **Vendor “deploy as API”** | e.g. Hugging Face Inference Endpoints: user uploads model/adapter, vendor serves it and gives a URL. | User configures deployment; Apex connects to that URL. No server/API code for user to write. |
| **RunPod / Vast.ai (typical)** | User rents a GPU instance and runs their own serving stack (vLLM, etc.) on it. | User still “owns” the API (container/code); vendor just hosts the box. |

**Takeaway:** If we don’t want to run or build the inference API ourselves, the user must use a vendor that offers “deploy model → get API” (e.g. HF Inference Endpoints) or run their own server. RunPod/Vast.ai reduce infra burden but don’t remove the need to run the serving layer.

---

## 4. Datasets: storage and size

- **Datasets can be huge (e.g. terabytes).** We should not store the raw data in Apex.
- **Apex can store references only:** e.g. dataset = name, format (jsonl/etc.), **URI** (s3://…, gs://…, https://…), optional schema/version. The actual bytes live in the user’s bucket or at a URL they control.
- **How the training pipeline uses it:** The job payload (or UI) contains the dataset URI. The training run (Colab, worker, etc.) loads data **from that URI** (e.g. S3, GCS). Apex never streams or stores the TB; it only passes the reference.
- **Optional:** “Managed upload” for **small** datasets (e.g. cap at 100 MB); for large data, only references.

---

## 5. Is a training module in Apex worth it?

**Ways Apex could add value (without running GPUs or inference):**

- **Datasets:** Catalog of dataset references (URI + metadata). Export or “use in job” so the user’s pipeline gets the URI. We don’t store the data.
- **Job tracking:** Record jobs (base model, dataset ref, method, status, output model/adapter ref). Execution happens elsewhere (Colab, worker). Apex is the log/dashboard.
- **Link to agents:** When the user deploys the trained model somewhere, they add a connection + model ref in Apex. Training adds lineage: “this model ref came from job X / dataset Y.”

**Ways it might not be worth it:**

- If users are fine managing files, Colab, and deployment (e.g. HF) themselves, a thin “dataset list + link to notebook” adds little.
- If we don’t trigger training (no “create job → start worker”), the module is mostly catalog/audit. Whether that’s enough depends on product goals.

**Alternative:** Pause training features; focus on RAG, evaluation, tools, agents. Users train and deploy entirely outside Apex; Apex only connects to whatever endpoint they end up with (connection + model ref).

---

## 6. Options summary (for later decision)

| Approach | What we’d build | Pros | Cons |
|----------|-----------------|------|-----|
| **Light control plane** | Datasets (refs only), optional job records, docs/links (e.g. “train in Colab, deploy on HF”). | One place for data refs and lineage; no GPU/inference to run. | Value is organizational; users still run training/deployment elsewhere. |
| **Trigger execution** | Same as above + launcher: Apex calls RunPod/HF/etc. to start a worker with job payload. | “Start training” from portal; execution is automated. | More integration and vendor coupling; worker image/code to maintain. |
| **No training module** | No datasets/jobs in Apex. Training is out of scope. | Simpler product; focus on RAG, evals, agents. | No single place for “what was trained” or dataset refs. |

---

## 7. What we tried (and reverted)

- Implemented a minimal LoRA trainer (Hugging Face + PEFT) in `apex.ml.fine_tuning`, a CLI entrypoint, and Colab notebooks.
- Reverted that code and removed training notebooks so the codebase stays clean while we decide. This doc is the only remaining reference for the thinking above.

---

*Last updated as a reference; no decision on which approach to pick.*
