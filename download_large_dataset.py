import urllib.request
import json
import os
import time

cache_dir = os.path.join(os.path.dirname(__file__), "hf_dataset_cache")
os.makedirs(cache_dir, exist_ok=True)

print("Starting diverse trajectory ingestion from Hugging Face (80,036 rows available)...")

clean_saved = 0
failed_saved = 0
target_each = 25

headers = {"User-Agent": "Mozilla/5.0"}

# Step across diverse offsets to get multiple repositories
for offset in range(0, 1500, 20):
    url = f"https://datasets-server.huggingface.co/rows?dataset=nebius%2FSWE-agent-trajectories&config=default&split=train&offset={offset}&length=20"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("rows", []):
                r = item["row"]
                st = r.get("exit_status", "")
                iid = r.get("instance_id", "unknown")
                traj = r.get("trajectory", [])
                
                if len(traj) < 5:
                    continue
                    
                # Cohort A: Failed / Stuck / Context Exhausted
                if "exit_context" in st or "submitted_no_patch" in st or "early_exit" in st:
                    if failed_saved < target_each:
                        fname = f"failed_{failed_saved:02d}_{iid.replace('/', '_')}.json"
                        fpath = os.path.join(cache_dir, fname)
                        if not os.path.exists(fpath):
                            with open(fpath, "w", encoding="utf-8") as f:
                                json.dump(r, f, indent=2)
                            failed_saved += 1
                            print(f"[FAILED {failed_saved}/{target_each}] {iid} ({len(traj)} turns) - status: {st}")
                            
                # Cohort B: Clean Submissions
                elif st == "submitted" and len(traj) >= 8:
                    if clean_saved < target_each:
                        fname = f"clean_{clean_saved:02d}_{iid.replace('/', '_')}.json"
                        fpath = os.path.join(cache_dir, fname)
                        if not os.path.exists(fpath):
                            with open(fpath, "w", encoding="utf-8") as f:
                                json.dump(r, f, indent=2)
                            clean_saved += 1
                            print(f"[CLEAN {clean_saved}/{target_each}] {iid} ({len(traj)} turns) - status: {st}")
                            
                if clean_saved >= target_each and failed_saved >= target_each:
                    break
    except Exception as e:
        print(f"Offset {offset} fetch error: {e}")
        time.sleep(1)
        continue
        
    if clean_saved >= target_each and failed_saved >= target_each:
        break

print(f"\nIngestion Complete! Clean: {clean_saved}, Failed/Stuck: {failed_saved} in {cache_dir}")

