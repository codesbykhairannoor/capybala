import json
import urllib.request
import sys
import os

BASE_URL = "https://raw.githubusercontent.com/SWE-agent/SWE-agent/main/"

trajs = [
    "tests/test_data/trajectories/gpt4__swe-agent-test-repo__default_from_url__t-0.00__p-0.95__c-3.00__install-1/6e44b9__sweagenttestrepo-1c2844.traj",
    "tests/test_data/trajectories/gpt4__swe-agent__test-repo__default_from_url__t-0.00__p-0.95__c-3.00__install-1/swe-agent__test-repo-i1.traj",
    "tests/test_data/trajectories/gpt4__swe-bench-dev-easy_first_only__default__t-0.00__p-0.95__c-3.00__install-1/pydicom__pydicom-1458.traj",
    "trajectories/demonstrations/ctf/crypto/BabyEncryption.traj",
    "trajectories/demonstrations/ctf/crypto/BabyTimeCapsule.traj",
    "trajectories/demonstrations/ctf/crypto/eps.traj",
    "trajectories/demonstrations/ctf/crypto/katy.traj",
    "trajectories/demonstrations/ctf/forensics/flash.traj",
    "trajectories/demonstrations/ctf/misc/networking_1.traj",
    "trajectories/demonstrations/ctf/pwn/warmup.traj",
    "trajectories/demonstrations/ctf/rev/rock.traj",
    "trajectories/demonstrations/ctf/web/i_got_id_demo.traj",
    "trajectories/demonstrations/function_calling_simple.traj",
    "trajectories/demonstrations/human_thought__swe-bench-HumanEvalFix-python__lcb__t-0.00__p-0.95__c-4.00__install-0/humanevalfix-python-0.traj",
    "trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__default__t-0.20__p-0.95__c-2.00__install-1___install_from_source/marshmallow-code__marshmallow-1867.traj",
    "trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__default_sys-env_cursors_window100__t-0.20__p-0.95__c-2.00__install-1/marshmallow-code__marshmallow-1867.traj",
    "trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__default_sys-env_window100__t-0.20__p-0.95__c-2.00__install-1/marshmallow-code__marshmallow-1867.traj",
    "trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__function_calling__install-1/marshmallow-code__marshmallow-1867.traj",
    "trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__function_calling_replace__install-1/marshmallow-code__marshmallow-1867.traj",
    "trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__function_calling_replace_from_source/marshmallow-code__marshmallow-1867.traj",
    "trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__xml_sys-env_cursors_window100__t-0.20__p-0.95__c-2.00__install-1/marshmallow-code__marshmallow-1867.traj",
    "trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__xml_sys-env_window100__t-0.20__p-0.95__c-2.00__install-1/marshmallow-code__marshmallow-1867.traj",
]

print(f"Downloading and inspecting {len(trajs)} real trajectories from SWE-agent...")
cache_dir = os.path.join(os.path.dirname(__file__), "real_trajectories_cache")
os.makedirs(cache_dir, exist_ok=True)

results = []
for idx, path in enumerate(trajs):
    filename = os.path.basename(path)
    # prepend parent folder name to prevent filename collision
    parent = path.split("/")[-2]
    local_path = os.path.join(cache_dir, f"{idx}_{parent}_{filename}")
    
    if not os.path.exists(local_path):
        url = BASE_URL + path
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
                with open(local_path, "wb") as f:
                    f.write(content)
        except Exception as e:
            print(f"Failed to download {path}: {e}")
            continue

    with open(local_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    traj_turns = data.get("trajectory", [])
    hist_turns = data.get("history", [])
    info = data.get("info", {})
    exit_status = info.get("exit_status", "unknown")
    
    results.append({
        "name": f"{parent}/{filename}",
        "exit_status": exit_status,
        "traj_len": len(traj_turns),
        "hist_len": len(hist_turns),
        "local_path": local_path
    })
    print(f"[{idx+1:2d}/{len(trajs)}] {parent[:30]:30s} | Exit: {exit_status:12s} | Steps: {len(traj_turns):2d} | Hist: {len(hist_turns):2d}")

print(f"\nCached {len(results)} trajectories in {cache_dir}")

