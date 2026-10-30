import json
import urllib.request
import os
import time

cache_dir = os.path.join(os.path.dirname(__file__), "real_trajectories_cache")
os.makedirs(cache_dir, exist_ok=True)

print("Fetching unique failed/stuck trajectories from Hugging Face...")
saved_count = 0
for offset in range(0, 300, 10):
    url = f"https://datasets-server.huggingface.co/rows?dataset=nebius%2FSWE-agent-trajectories&config=default&split=train&offset={offset}&length=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("rows", []):
                row = item["row"]
                st = row.get("exit_status")
                iid = row.get("instance_id")
                traj = row.get("trajectory", [])
                if st in ["exit_context", "early_exit", "submitted_no_patch"] and len(traj) >= 10:
                    filename = f"failed_{st}_{offset}_{saved_count}_{iid.replace('/', '_')}.json"
                    filepath = os.path.join(cache_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(row, f, indent=2)
                    saved_count += 1
                    print(f"[{saved_count}] Saved failed trajectory [{st}]: {iid} ({len(traj)} turns)")
                    if saved_count >= 10:
                        break
    except Exception as e:
        print(f"Offset {offset} fetch error: {e}")
        time.sleep(1)
        continue
    
    if saved_count >= 10:
        break

print(f"Done! Saved {saved_count} unique failed trajectories.")
