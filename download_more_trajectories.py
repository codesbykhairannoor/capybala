"""
download_more_trajectories.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fetches 25 additional clean and 25 additional stuck trajectories from
nebius/SWE-agent-trajectories (Hugging Face) to expand our dataset from 50 to 100 trajectories.
"""

import urllib.request
import json
import os
import time

cache_dir = os.path.join(os.path.dirname(__file__), "hf_dataset_cache")
os.makedirs(cache_dir, exist_ok=True)

# Count existing clean and failed
existing_clean = len([f for f in os.listdir(cache_dir) if f.startswith("clean_") and f.endswith(".json")])
existing_failed = len([f for f in os.listdir(cache_dir) if f.startswith("failed_") and f.endswith(".json")])

print(f"Existing in cache: {existing_clean} clean, {existing_failed} failed.")

target_clean = 50
target_failed = 50

headers = {"User-Agent": "Mozilla/5.0"}

clean_saved = existing_clean
failed_saved = existing_failed

# Search across offsets with batch size 100
for offset in range(1600, 20000, 100):
    if clean_saved >= target_clean and failed_saved >= target_failed:
        break

    url = f"https://datasets-server.huggingface.co/rows?dataset=nebius%2FSWE-agent-trajectories&config=default&split=train&offset={offset}&length=100"
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rows = data.get("rows", [])
            print(f"[Offset {offset}] Loaded {len(rows)} candidate rows...")

            for item in rows:
                r = item["row"]
                st = r.get("exit_status", "")
                iid = r.get("instance_id", "unknown")
                traj = r.get("trajectory", [])

                if len(traj) < 5:
                    continue

                # Cohort A: Failed / Stuck / Context Exhausted
                if ("exit_context" in st or "submitted_no_patch" in st or "early_exit" in st) and failed_saved < target_failed:
                    fname = f"failed_{failed_saved:02d}_{iid.replace('/', '_')}.json"
                    fpath = os.path.join(cache_dir, fname)
                    if not os.path.exists(fpath):
                        with open(fpath, "w", encoding="utf-8") as f:
                            json.dump(r, f, indent=2)
                        failed_saved += 1
                        print(f"  -> [FAILED {failed_saved}/{target_failed}] {iid} ({len(traj)} turns) - status: {st}")

                # Cohort B: Clean Submissions
                elif st == "submitted" and len(traj) >= 8 and clean_saved < target_clean:
                    fname = f"clean_{clean_saved:02d}_{iid.replace('/', '_')}.json"
                    fpath = os.path.join(cache_dir, fname)
                    if not os.path.exists(fpath):
                        with open(fpath, "w", encoding="utf-8") as f:
                            json.dump(r, f, indent=2)
                        clean_saved += 1
                        print(f"  -> [CLEAN {clean_saved}/{target_clean}] {iid} ({len(traj)} turns) - status: {st}")

                if clean_saved >= target_clean and failed_saved >= target_failed:
                    break
    except Exception as e:
        print(f"Offset {offset} error: {e}")
        time.sleep(2)
        continue

print(f"\n[DONE] Dataset expanded! Total in cache: {clean_saved} clean, {failed_saved} failed.")
