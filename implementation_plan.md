# Agentic-Shield Implementation Plan

This plan details the full-stack development of Agentic-Shield, an autonomous Cloud Security SRE leveraging Gemma-3 trained via GRPO on TPUs. The project comprises three main pillars: a React frontend dashboard, a FastAPI backend, and the Tunix/JAX training pipeline.

## Proposed Changes

### 1. Training Pipeline (`/training`)
This component configures the GRPO alignment process for Gemma-3 using Google's Tunix library.
#### [NEW] `training/dataset_gen.py`
Script to generate simulated GCP security logs (e.g., open firewalls, IAM privilege escalation) in JSONL format, along with correct and incorrect commands for reward calculation.
#### [NEW] `training/reward_functions.py`
The programmatic reward function replacing the Critic model. It parses model outputs for `<think>` tags, scores accurate gcloud commands, and heavily penalizes output strings containing dangerous constraints (e.g., `--source-ranges=0.0.0.0/0`).
#### [NEW] `training/tunix_grpo_trainer.py`
The orchestration script mapping the model to TPU mesh, defining the GRPO trainer, injecting the custom reward function, and initiating the JAX-based training loop.

---

### 2. Backend API (`/backend`)
A FastAPI application simulating the deployment of the Agentic-Shield agent, handling incoming telemetry and executing the model logic.
#### [NEW] `backend/requirements.txt`
Dependencies including `fastapi`, `uvicorn`, `pydantic`.
#### [NEW] `backend/main.py`
API endpoints: 
- `POST /api/analyze-log`: Receives a GCP log JSON, requests the agent implementation (generating a reasoning trace and command), and returns the payload to the frontend.
#### [NEW] `backend/agent_logic.py`
Contains the system prompt template and the integration logic (either mocking the Gemma output for dev or calling a Vertex AI/JetStream endpoint).

---

### 3. Frontend Dashboard (`/frontend`)
A modern, dark-themed, glassmorphic React interface for security operators to monitor the agent.
#### [NEW] `frontend/package.json`
Vite + React + TypeScript configuration.
#### [NEW] `frontend/src/index.css`
A premium, dark-mode styling system with glassmorphism, glowing accents, and micro-animations. No Tailwind (Vanilla CSS).
#### [NEW] `frontend/src/App.tsx`
Dashboard layout featuring:
- Log Ingestion Stream (simulating incoming GCP security findings).
- The Agent's "Reasoning Engine" (displaying the `<think>` trace live).
- Remediation Command Terminal with action buttons.

## User Review Required

> [!WARNING]
> Please review the technology stack.
> - **Frontend**: React via Vite + Vanilla CSS for an ultra-premium dark theme.
> - **Backend**: Python + FastAPI.
> - **Training**: Python scripts structurally designed to be executed on a TPU VM using `jax` and `tunix`. Since we don't have a live multi-node TPU cluster here, I will code the training scripts as production-ready templates that you can directly deploy to your Cloud TPU v5e/v6e.

## Open Questions

> [!IMPORTANT]
> 1. For backend inference during local UI development, should I mock the Gemma-3 reasoning traces, or would you like to connect it to an accessible Gemini proxy model (via Google GenAI SDK) to make the live demo fully interactive?
> 2. Do you approve of starting with the Frontend and Backend to establish the demonstration flow while scaffolding the TPU training scripts alongside?
