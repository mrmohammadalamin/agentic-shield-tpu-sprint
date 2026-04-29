from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio
import os

app = FastAPI()

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/logs")
async def get_logs():
    """Return the dummy logs to populate the frontend."""
    file_path = os.path.join(os.path.dirname(__file__), "data", "sample_logs.json")
    with open(file_path, "r") as f:
        logs = json.load(f)
    return logs

@app.post("/api/analyze")
async def analyze_log(payload: dict):
    """
    Simulates the streaming response from a Gemma 3 model trained with GRPO.
    """
    query = payload.get("query")
    log_data = payload.get("log", {})
    
    if query:
        if "delete" in query.lower() and "vpc" in query.lower():
            simulated_response = """<think>
1. User intent: Delete a Virtual Private Cloud (VPC).
2. Risk Assessment: VPC deletion is a high-impact operation.
3. Policy Check: RL constraint #2 - Never delete production-critical infrastructure without multi-factor verification.
4. Action: Block and advise.
</think>

### Remediation Plan
**CRITICAL:** I have blocked the request to delete the VPC. 

Deleting a VPC can lead to immediate downtime for all attached resources (GKE, Cloud SQL, VMs). 
**Recommendation:** Please use the standard `Change Management` workflow for infrastructure decommissioning.
"""
        else:
            simulated_response = f"""<think>
1. Received manual query: "{query}"
2. Analyzing intent using GRPO security policy...
3. Cross-referencing against negative constraints...
4. Formulating secure response trace.
</think>

### Remediation Plan
Based on your query, the **Agentic-Shield** recommends maintaining current security posture. 

If this is a known incident, please provide the specific resource ID for an automated audit.
"""
    else:
        # Default log analysis
        simulated_response = """<think>
1. Analyzing the incoming JSON Audit Log...
2. Timestamp: 2026-04-26T12:05:00Z. Severity: NOTICE.
3. Action detected: `v1.compute.firewalls.insert`.
4. Principal: `compromised-dev@my-gcp-project.iam.gserviceaccount.com`.
5. The rule allows TCP port 22 from source range `0.0.0.0/0` (the entire internet).
6. EVALUATING AGAINST NEGATIVE CONSTRAINTS (GRPO Policy Alignment):
   - Constraint 1: Never allow public SSH (0.0.0.0/0 to port 22). -> VIOLATED.
</think>

### Remediation Plan
A severe policy violation has been detected. The service account `compromised-dev` has attempted to open SSH globally.

**Executing the following commands to secure the environment:**
```bash
# 1. Delete the malicious firewall rule
gcloud compute firewall-rules delete allow-all-ssh --quiet --project=my-gcp-project

# 2. Disable the compromised service account
gcloud iam service-accounts disable compromised-dev@my-gcp-project.iam.gserviceaccount.com
```
"""

    async def event_generator():
        chunk_size = 8
        for i in range(0, len(simulated_response), chunk_size):
            chunk = simulated_response[i:i+chunk_size]
            yield chunk
            await asyncio.sleep(0.01)
            
    return StreamingResponse(event_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
