import json
import random
from datetime import datetime, timedelta

def generate_dataset(num_samples=1000, output_file="training_dataset.jsonl"):
    actions = [
        {"method": "v1.compute.firewalls.insert", "severity": "NOTICE", "threat": True, "resource": "allow-all-ssh", "port": "22", "ip": "0.0.0.0/0"},
        {"method": "v1.compute.instances.insert", "severity": "INFO", "threat": False, "resource": "web-server-1", "port": "443", "ip": "10.0.0.0/8"},
        {"method": "storage.buckets.update", "severity": "WARNING", "threat": True, "resource": "prod-db-backup", "acl": "allUsers"},
        {"method": "v1.compute.firewalls.delete", "severity": "NOTICE", "threat": False, "resource": "old-rule", "port": "80", "ip": "192.168.1.0/24"},
        {"method": "iam.serviceAccounts.create", "severity": "INFO", "threat": False, "resource": "new-dev-sa", "role": "roles/viewer"}
    ]
    
    principals = [
        "admin@my-gcp-project.iam.gserviceaccount.com",
        "compromised-dev@my-gcp-project.iam.gserviceaccount.com",
        "user1@company.com",
        "user2@company.com"
    ]
    
    dataset = []
    base_time = datetime.utcnow()
    
    for i in range(num_samples):
        action = random.choice(actions)
        principal = random.choice(principals)
        timestamp = (base_time - timedelta(minutes=random.randint(1, 10000))).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        log_entry = {
            "insertId": f"log-{i}-{random.randint(1000,9999)}",
            "logName": "projects/my-gcp-project/logs/cloudaudit.googleapis.com%2Factivity",
            "timestamp": timestamp,
            "severity": action["severity"],
            "protoPayload": {
                "authenticationInfo": {"principalEmail": principal},
                "methodName": action["method"],
                "request": {"name": action["resource"]}
            }
        }
        
        if action["threat"]:
            if "port" in action:
                log_entry["protoPayload"]["request"]["allowed"] = [{"IPProtocol": "tcp", "ports": [action["port"]]}]
                log_entry["protoPayload"]["request"]["sourceRanges"] = [action["ip"]]
            elif "acl" in action:
                 log_entry["protoPayload"]["request"]["binding"] = {"role": "roles/storage.objectViewer", "members": [action["acl"]]}
        
        # Determine target behavior for GRPO (just as reference for reward function)
        is_violation = False
        if action["threat"] and ("0.0.0.0/0" in str(log_entry) or "allUsers" in str(log_entry)):
            is_violation = True
            
        dataset.append({
            "prompt": f"Analyze the following Google Cloud Audit log and provide a remediation plan.\nLog: {json.dumps(log_entry)}",
            "expected_violation": is_violation
        })
        
    with open(output_file, "w") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Generated {num_samples} samples in {output_file}")

if __name__ == "__main__":
    import os
    os.makedirs("backend/data", exist_ok=True)
    generate_dataset(num_samples=2500, output_file="backend/data/training_dataset.jsonl")
