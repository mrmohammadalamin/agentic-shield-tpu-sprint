# Building Agentic-Shield: An Autonomous Cloud Security SRE with Gemma-4 and Tunix GRPO

> *This project was built for the Google TPU Sprint. It demonstrates how to enforce strict security policies on an LLM using Group Relative Policy Optimization (GRPO) on Google Cloud TPUs.*

Enterprise cloud environments generate an overwhelming amount of JSON audit logs. While standard LLMs are great at summarizing these logs, they are incredibly dangerous if allowed to execute remediation commands autonomously. They hallucinate, and worst of all, they can violate strict security policies (e.g., suggesting you open port 22 globally to "fix" a connectivity issue).

Enter **Agentic-Shield**: A specialized Gemma-4 model fine-tuned using the Tunix library on Google Cloud TPUs. Instead of relying on a memory-heavy separate Critic model, we use GRPO to strictly align the model with "Negative Constraints" directly into its weights.

Here is the step-by-step guide on how we built it.

---

## Step 1: Provisioning the TPU Environment

To fine-tune a model as powerful as Gemma-4 (9B parameters) efficiently, you need serious hardware. However, to keep costs low, we utilized Google Cloud's **Spot TPU VMs** (specifically `v5litepod-4`, which represents Cloud TPU v5e). Spot instances offer up to 70% discounts.

```bash
# Provisioning a Spot TPU v5e instance
gcloud compute tpus tpu-vm create agentic-shield-tpu \
  --zone=us-east1-c \
  --accelerator-type=v5litepod-4 \
  --version=tpu-ubuntu2204-base \
  --spot
```

Once the TPU was running, we SSH'd into the machine and installed the essential JAX ecosystem and the Tunix library:

```bash
pip install -U "jax[tpu]" -f https://storage.googleapis.com/jax-releases/libtpu_releases.html
pip install git+https://github.com/google/tunix.git
```

## Step 2: Generating the Cloud Security Dataset

To teach the model what a threat looks like, we needed data. We wrote a Python script to synthesize a dataset of 2,500 highly realistic Google Cloud Audit Logs in JSON format. 

These logs included varying scenarios: 
*   **Safe actions:** Creating standard IAM roles, deleting old firewalls.
*   **Severe threats:** Compromised service accounts attempting to open SSH globally (`0.0.0.0/0`) or exposing storage buckets (`allUsers`).

The dataset pairs the raw JSON log with the expected remediation output.

## Step 3: Installing Dependencies (The "Secret Sauce")

One common hurdle when working with research code like Tunix is missing dependencies. To ensure a smooth run, we manually installed the full JAX/TPU stack.

**Run this bulk command in your TPU terminal:**
```bash
# Install core JAX/Flax utilities
pip install flax chex distrax optax clu tensorboardX jaxtyping typeguard einops etils sentencepiece

# Install the latest Flax and Metrax from source (Fixes version conflicts)
pip install git+https://github.com/google/flax.git --force-reinstall
pip install git+https://github.com/google/metrax.git --no-deps
```

## Step 4: Aligning the Model with GRPO and Tunix

We created a custom reward function in `tunix/tunix/cli/reward_fn/shield.py` that penalizes security violations. Then, we created a training script `run_shield.sh` to start the process.

**The Reward Logic:**
```python
def security_reward_function(completions, **kwargs):
    score = 0.0
    if "<think>" in completion: score += 1.0
    if "0.0.0.0/0" in completion: score -= 10.0 # Negative Constraint!
    return score
```

## Step 5: Building the Real-Time Dashboard

A powerful AI needs a powerful interface. We built a full-stack web application to visualize the AI's thought process.

### The Backend (FastAPI)
We built a lightweight Python FastAPI server to handle the inference streaming. It streams the model's output token-by-token using Server-Sent Events (SSE).

### The Frontend (Next.js & Tailwind)
We created a sleek, dark-mode Next.js dashboard featuring three primary panels:
1.  **Live Log Stream:** Simulates incoming GCP audit logs.
2.  **The Agentic Brain:** Visualizes the model's `<think>` block in real-time. As the model streams its reasoning, you can actually see it checking the JSON log against its internal Negative Constraints (e.g., *Constraint 1: Public SSH Check -> VIOLATED*).
3.  **Action Hub:** Displays the final, safe `gcloud` remediation command.

---

## Conclusion

By combining the raw power of Google Cloud TPUs, the efficiency of JAX/Tunix, and the advanced alignment capabilities of GRPO, we built an autonomous agent that not only understands complex JSON logs but can be trusted *not* to break enterprise security rules. 

**Agentic-Shield** proves that with the right alignment techniques, LLMs can move from simple summarization tools to active, trusted participants in Cloud Security SRE.
