import urllib.request
import json
import time

def req(url, data=None, headers=None, method='GET'):
    h = headers or {}
    b = json.dumps(data).encode('utf-8') if data else None
    if b:
        h['Content-Type'] = 'application/json'
    r = urllib.request.Request(url, data=b, headers=h, method=method)
    with urllib.request.urlopen(r) as resp:
        return resp.getcode(), json.loads(resp.read().decode('utf-8'))

print("1. Checking Express Health Endpoint...")
code, health = req("http://localhost:5000/api/health")
print("Health Response:", code, health)
assert health["status"] == "ONLINE"
assert health["storage"]["uploads"] == "/uploads"  # Verify safe path
assert health["storage"]["evidence"] == "/evidence" # Verify safe path

print("\n2. Logging in as Chief Inspector Manthan...")
code, login = req(
    "http://localhost:5000/api/auth/login",
    {"email": "admin@traffic-sentinel.gov", "password": "Admin@1234"},
    method="POST"
)
token = login["data"]["token"]
print("Login OK, Token acquired:", token[:25] + "...")
headers = {"Authorization": f"Bearer {token}"}

print("\n3. Triggering Video AI Inference Queue...")
code, proc = req(
    "http://localhost:5000/api/ai/process-sample",
    {"speedLimit": 50.0},
    headers=headers,
    method="POST"
)
print("Process Queued:", code, proc)
job_id = proc["jobId"]

print("\n4. Polling AI Inference Progress...")
for i in range(15):
    time.sleep(1.5)
    code, status = req(f"http://localhost:5000/api/ai/jobs/{job_id}", headers=headers)
    d = status["data"]
    prog = d.get("progress", 0)
    proc_frames = d.get("processed_frames", 0)
    tot_frames = d.get("total_frames", 0)
    viols_count = d.get("violations_detected", 0)
    state = d.get("status")
    print(f"   [Poll {i+1}] State: {state} | Progress: {prog}% | Frames: {proc_frames}/{tot_frames} | Violations: {viols_count}")
    if state in ["COMPLETED", "FAILED"]:
        break

print("\n5. Querying Live Violation Records...")
code, viols = req("http://localhost:5000/api/violations?limit=5", headers=headers)
print(f"Total fetched records: {viols['count']}")
for v in viols["data"][:3]:
    v_id = v.get("id")
    plate = v.get("plate_number")
    v_type = v.get("violation_type")
    fine = v.get("total_fine")
    sec = v.get("secondary_fine")
    rev = v.get("review_status")
    snap = v.get("snapshot_path")
    print(f"   > #{v_id} | Plate: {plate} | Type: {v_type} | Total: Rs.{fine} (Sec: Rs.{sec}) | Review: {rev} | Evidence: {snap}")

if viols["data"]:
    target_id = viols["data"][0]["id"]
    print(f"\n6. Testing Review Action on Violation #{target_id}...")
    code, rev = req(
        f"http://localhost:5000/api/violations/{target_id}/review",
        {"review_status": "CONFIRMED"},
        headers=headers,
        method="PATCH"
    )
    print("Review Update Response:", rev["message"])

print("\n[SUCCESS] Full-Stack AI pipeline verification completed successfully!")
