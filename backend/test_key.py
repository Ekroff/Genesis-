"""Get Kie.ai results — both old and new tasks"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import httpx
import json

KIE_KEY = "a4eb1120e782c45550b9bc596453603b"
BASE = "https://api.kie.ai/api/v1"
headers = {
    "Authorization": f"Bearer {KIE_KEY}",
    "Content-Type": "application/json",
}

tasks = [
    "f56a2c3754a25e4dfb577e5b9b5d84ca",  # old task
    "ccec261c9b8395590f0e80a11c6a8ea4",  # new task
]

for tid in tasks:
    print(f"\n{'='*60}")
    print(f"Task: {tid}")
    print(f"{'='*60}")
    
    r = httpx.get(
        f"{BASE}/jobs/recordInfo",
        params={"taskId": tid},
        headers=headers,
        timeout=15,
    )
    
    if r.status_code == 200:
        data = r.json()
        
        # Print state
        task_data = data.get("data", {})
        state = task_data.get("state", "?")
        model = task_data.get("model", "?")
        print(f"  State: {state}")
        print(f"  Model: {model}")
        
        # Print ALL keys in data
        print(f"  Keys: {list(task_data.keys())}")
        
        # Check resultJson
        result_json = task_data.get("resultJson", "")
        if result_json:
            print(f"\n  resultJson (raw): {result_json[:500]}")
            try:
                parsed = json.loads(result_json)
                print(f"  resultJson (parsed): {json.dumps(parsed, indent=2)[:500]}")
                
                # Look for image URLs
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        if isinstance(v, str) and ("http" in v or "url" in k.lower()):
                            print(f"\n  >>> FOUND IMAGE: {k} = {v}")
                        if isinstance(v, list):
                            for item in v:
                                if isinstance(item, str) and "http" in item:
                                    print(f"\n  >>> FOUND IMAGE in list '{k}': {item}")
                                if isinstance(item, dict):
                                    for ik, iv in item.items():
                                        if isinstance(iv, str) and "http" in iv:
                                            print(f"\n  >>> FOUND IMAGE: {k}[].{ik} = {iv}")
            except:
                print(f"  (not valid JSON)")
        
        # Check output field
        output = task_data.get("output")
        if output:
            print(f"\n  output: {json.dumps(output, indent=2)[:500] if isinstance(output, (dict, list)) else str(output)[:500]}")
    else:
        print(f"  HTTP {r.status_code}: {r.text[:200]}")

print("\nDone!")
