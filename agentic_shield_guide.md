# Agentic-Shield: Architecture Analysis & Building Guide

## 1. Use Case Analysis

**Agentic-Shield** represents a state-of-the-art approach to autonomous security operations. By acting as an internal Cloud Security SRE, the agent digests complex telemetry (GCP JSON logs) and provides safe, actionable remediations.

### Core Architecture Components

- **Base Model:** Gemma-3 (4B or 12B). The 4B model is incredibly efficient and easily fits on a single Cloud TPU v5e for fast inference, while the 12B offers deeper reasoning for complex log correlations.
- **Hardware:** Google Cloud TPUs (v5e or v6e). TPUs provide massive parallelism, which is critical for GRPO since the algorithm requires generating multiple completions simultaneously to calculate relative advantages.
- **Framework:** Tunix (Tune-in-JAX). Google's JAX-native library engineered specifically for efficient LLM post-training on TPUs. It provides out-of-the-box support for GRPO.
- **Algorithm:** GRPO (Group Relative Policy Optimization). 
- **The "Negative Constraint" Mechanism:** GRPO removes the heavily parameterized Critic model. Instead of training a Critic, GRPO generates a group of responses (e.g., Group Size = 8) for a single prompt, scores them via a programmatic **Reward Function**, and normalizes the scores to compute the advantage. Negative constraints (e.g., "never open port 22 to 0.0.0.0/0") are strictly enforced by applying massive negative reward penalties to violations.

---

## 2. Step-by-Step Implementation Guide

### Step 1: Infrastructure setup on Google Cloud
1. **Provision TPU Resources:**
   - Create a TPU VM (e.g., `v5litepod-8` for v5e or `v6e` instance) in Google Cloud.
   - Ensure the VM has sufficient disk space for the Gemma-3 12B weights and dataset.
2. **Environment Configuration:**
   - Install JAX with TPU support: `pip install jax[tpu] -f https://storage.googleapis.com/jax-releases/libtpu_releases.html`
   - Install the **Tunix** library and its dependencies (Flax, Optax).
   - Authenticate with Hugging Face (or Kaggle) to download the basic Gemma-3 weights.

### Step 2: Dataset & Prompt Engineering
1. **Log Ingestion:** Export sample logs from GCP (Cloud Audit Logs, VPC Flow Logs, Security Command Center findings) into JSONL format.
2. **Prompt Template:** Structure your training prompt to forcefully elicit a Chain-of-Thought (Reasoning Trace).
   ```xml
   <system>You are Agentic-Shield, an expert GCP Security SRE.</system>
   <log_input>{json_log_payload}</log_input>
   <instructions>
   Analyze the logs. Provide your reasoning inside <think>...</think> tags.
   Then, provide the exact gcloud remediation command.
   </instructions>
   ```

### Step 3: Designing the Rule-Based Reward Function
Since Tunix's GRPO implementation relies on external rewards rather than a Critic model, construct a deterministic Python reward function:

1. **Format Reward (+0.2):** Did the model use `<think>` and `</think>` tags properly?
2. **Correctness Reward (+0.8):** Did the remediation command solve the core vulnerability described in the log? (This can be evaluated via exact pattern matching or regex against known good commands for that log scenario).
3. **Negative Constraint Penalty (-2.0):** (CRITICAL) Use regex to search the output string for forbidden patterns:
   - Contains `--source-ranges=0.0.0.0/0`
   - Modifies IAM policies to grant `roles/owner` or `roles/editor`.
   - Modifies destructive resources without conditions.
   - Any violation immediately results in a severe negative score, teaching the model that this behavior is highly dangerous.

### Step 4: GRPO Training via Tunix
1. **Configure the Tunix Trainer:**
   Initiate the Tunix GRPO training loop. Specify the base model as `google/gemma-3-12b` or `4b`.
2. **Group Size Tuning:**
   Set the group size to 4, 8, or 16 depending on your TPU memory limits. The TPU will parallelize the generation of these completions for each log prompt.
3. **Execution:**
   Execute the training script. Tunix, backed by JAX's `pjit`, will automatically shard the model and the generated completions across the TPU cores. The policy model updates its weights by comparing which of the completions scored highest against the baseline average of the group.

### Step 5: Evaluation & "Red Teaming"
1. **Validation Set:** Run the aligned model against a holdout set of highly ambiguous or malicious logs (e.g., a scenario designed to trick the agent into opening an SSH port).
2. **Safety Check:** Ensure that zero outputs trigger the Negative Constraint conditions. Because GRPO heavily penalizes these, the model's reasoning trace should explicitly identify and block the requested dangerous action.

### Step 6: Agentic Deployment
1. **Serving:** Export the Tunix-trained JAX checkpoint. Convert it for serving (e.g., using Google's JetStream, vLLM, or Vertex AI Endpoints).
2. **Execution Loop:** Wrap the model in an Agentic logic framework (like LangChain or a lightweight Python loop) that:
   - Polls GCP Pub/Sub for new log anomalies.
   - Injects the log into the system template.
   - Extracts the final command output, validates it syntactically, and securely executes it via the GCP SDK.
