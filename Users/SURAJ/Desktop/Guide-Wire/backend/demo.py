import json
import urllib.request

def req(url, data=None):
    if data:
        data = json.dumps(data).encode('utf-8')
        request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    else:
        request = urllib.request.Request(url)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())

print(">> 1. Onboarding new worker in PRISM central zone...")
worker = req("http://localhost:8001/api/v1/workers", {
    "name": "Fast Demo Worker", 
    "platform": "Swiggy", 
    "zone": "central", 
    "working_hours": "08:00-18:00"
})
print(f"    Worker ID Data: {worker}")

print(f">> 2. Generating PRISM parametric policy for Worker ID: {worker['id']}...")
from datetime import datetime
import datetime as dt

week_start = datetime.now().strftime("%Y-%m-%d")
week_end = (datetime.now() + dt.timedelta(days=7)).strftime("%Y-%m-%d")

policy = req("http://localhost:8001/api/v1/policies", {
    "worker_id": worker['id'], 
    "week_start": week_start, 
    "week_end": week_end
})
print(f"    Policy ID Data: {policy}")
print(">> 3. Triggering claim block (Disruption: Rain) with simulated GPS + ML scoring...")

claim = req("http://localhost:8001/api/v1/claims/trigger", {
    "worker_id": worker['id'], 
    "policy_id": policy['id'], 
    "expected_income": 500.0, 
    "actual_income": 100.0, 
    "trigger_source": "Rain (Heavy Rain)", 
    "lat": 12.97, "lon": 77.59, 
    "activity_score": 0.85
})

print("\n========= PRISM PIPELINE DECISION =========")
print(json.dumps(claim, indent=2))
print("===========================================")

print("\n>> 4. Pipeline Component Health Status...")
status = req("http://localhost:8001/api/v1/fraud/pipeline-status")
for comp in status.get("pipeline", []):
    print(f"    - [{comp['layer']}] {comp['component']} : {comp['status'].upper()}")

print("\n>> Flow Complete. Output captured successfully!")
