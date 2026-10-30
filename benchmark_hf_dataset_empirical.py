"""
benchmark_hf_dataset_empirical.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Large-Scale Empirical Benchmark of Capybala v0.6.1 against
50 Authentic Hugging Face SWE-bench Trajectories (nebius/SWE-agent-trajectories).
"""

import os
import sys
import json
import time
import glob
import re
from collections import defaultdict

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath("capybala"))
from capybala.detector import DeadlockDetector
from capybala.pruner import ContextPruner
from capybala.api import heal, validate

CACHE_DIR = os.path.join(os.path.dirname(__file__), "hf_dataset_cache")

def extract_command(text: str) -> str:
    """Extracts actual shell/editor command from agent markdown response."""
    if not text:
        return ""
    # Look for code fences: ```bash\ncmd\n``` or ```\ncmd\n```
    blocks = re.findall(r"```(?:bash|sh|python)?\s*\n(.*?)\n```", text, re.DOTALL)
    if blocks:
        return blocks[-1].strip()
    return text.strip()

def extract_agent_turns(traj):
    """
    Extracts chronological (action, observation) pairs from an agent transcript.
    Compatible with SWE-agent / Hugging Face multi-turn conversation format.
    """
    turns = []
    current_action = None
    
    for item in traj:
        if not isinstance(item, dict):
            continue
            
        # Case 1: direct action/observation dictionary
        if "action" in item or "observation" in item:
            act = item.get("action")
            obs = item.get("observation")
            if act is not None or obs is not None:
                turns.append((extract_command(str(act or "")), str(obs or "")))
            continue
            
        # Case 2: role/text transcript (SWE-agent Hugging Face format)
        role = item.get("role", "")
        text = str(item.get("text") or item.get("content") or "")
        
        if role in ("ai", "assistant", "model"):
            if current_action is not None:
                turns.append((extract_command(current_action), ""))
            current_action = text
        elif role in ("user", "tool", "environment"):
            if current_action is not None:
                turns.append((extract_command(current_action), text))
                current_action = None
                
    if current_action is not None:
        turns.append((extract_command(current_action), ""))
        
    return turns

def load_trajectory_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def main():
    print("=" * 80)
    print(" CAPYBALA v0.6.1 LARGE-SCALE REAL-WORLD DATASET BENCHMARK")
    print(" Dataset: Hugging Face nebius/SWE-agent-trajectories (80,036 Authentic SWE-bench Runs)")
    print("=" * 80)
    
    clean_files = sorted(glob.glob(os.path.join(CACHE_DIR, "clean_*.json")))
    failed_files = sorted(glob.glob(os.path.join(CACHE_DIR, "failed_*.json")))
    
    print(f"Loaded {len(clean_files)} Clean / Productive Trajectories.")
    print(f"Loaded {len(failed_files)} Failed / Context-Exhausted Stuck Trajectories.")
    print("-" * 80)
    
    if not clean_files and not failed_files:
        print("[ERROR] No files found in hf_dataset_cache!")
        return

    # --------------------------------------------------------------------------
    # PART 1: SPECIFICITY / FALSE POSITIVE TEST ON CLEAN AGENT TRAJECTORIES
    # --------------------------------------------------------------------------
    print("\n[PART 1: SPECIFICITY / FALSE POSITIVE IMMUNITY ON CLEAN TRAJECTORIES]")
    clean_total = len(clean_files)
    clean_passed = 0
    clean_false_alarms = 0
    clean_total_turns = 0
    total_time_clean_ms = 0.0
    
    for cfile in clean_files:
        data = load_trajectory_file(cfile)
        if not data:
            continue
        iid = data.get("instance_id", "unknown")
        traj = data.get("trajectory", [])
        turns = extract_agent_turns(traj)
        clean_total_turns += len(turns)
        
        detector = DeadlockDetector(
            repetition_threshold=3,
            oscillation_threshold=2,
            fuzzy_threshold=0.65,
            max_exploration_depth=15,
            enable_exploration_guard=True,
            enable_delegation=True
        )
        
        flagged = False
        first_flag_turn = -1
        first_flag_pattern = ""
        
        t0 = time.perf_counter()
        for idx, (act, obs) in enumerate(turns):
            ev = detector.check(act, obs)
            if ev.is_deadlock and not flagged:
                flagged = True
                first_flag_turn = idx + 1
                first_flag_pattern = ev.pattern_type
        total_time_clean_ms += (time.perf_counter() - t0) * 1000.0
        
        fname_short = os.path.basename(cfile)[:38]
        if flagged:
            clean_false_alarms += 1
            print(f"  [FALSE ALARM] {fname_short:<38} -> Turn {first_flag_turn:2d}/{len(turns):2d} ({first_flag_pattern})")
        else:
            clean_passed += 1
            print(f"  [CLEAN OK]    {fname_short:<38} -> {len(turns):2d} turns (0 false alarms)")
            
    clean_specificity = (clean_passed / clean_total * 100.0) if clean_total > 0 else 0.0
    clean_fpr = (clean_false_alarms / clean_total * 100.0) if clean_total > 0 else 0.0
    avg_latency_clean = (total_time_clean_ms / clean_total_turns) if clean_total_turns > 0 else 0.0
    
    print("\nClean Trajectory Results:")
    print(f"  Total Clean Trajectories Tested: {clean_total}")
    print(f"  Total Clean Agent Turns Executed: {clean_total_turns}")
    print(f"  False Alarms Triggered: {clean_false_alarms}")
    print(f"  False Positive Rate (FPR): {clean_fpr:.2f}%")
    print(f"  Clean Specificity: {clean_specificity:.2f}%")
    print(f"  Average Processing Latency: {avg_latency_clean:.3f} ms / turn")

    # --------------------------------------------------------------------------
    # PART 2: SENSITIVITY / RECALL & TOKEN SAVINGS ON STUCK TRAJECTORIES
    # --------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[PART 2: SENSITIVITY / RECALL & TURN SAVINGS ON STUCK TRAJECTORIES]")
    failed_total = len(failed_files)
    intercepted_count = 0
    total_unprotected_turns = 0
    total_turns_saved = 0
    pattern_breakdown = defaultdict(int)
    total_time_failed_ms = 0.0
    
    for ffile in failed_files:
        data = load_trajectory_file(ffile)
        if not data:
            continue
        iid = data.get("instance_id", "unknown")
        traj = data.get("trajectory", [])
        turns = extract_agent_turns(traj)
        n_turns = len(turns)
        total_unprotected_turns += n_turns
        
        detector = DeadlockDetector(
            repetition_threshold=3,
            oscillation_threshold=2,
            fuzzy_threshold=0.65,
            max_exploration_depth=15,
            enable_exploration_guard=True,
            enable_delegation=True
        )
        
        detected = False
        first_detect_turn = -1
        detect_pattern = ""
        circuit_break_turn = -1
        consecutive_deadlocks = 0
        
        t0 = time.perf_counter()
        for idx, (act, obs) in enumerate(turns):
            ev = detector.check(act, obs)
            if ev.is_deadlock:
                if not detected:
                    detected = True
                    first_detect_turn = idx + 1
                    detect_pattern = ev.pattern_type
                    pattern_breakdown[ev.pattern_type] += 1
                consecutive_deadlocks += 1
                if consecutive_deadlocks >= 3 and circuit_break_turn == -1:
                    circuit_break_turn = idx + 1
            else:
                consecutive_deadlocks = 0
        total_time_failed_ms += (time.perf_counter() - t0) * 1000.0
        
        fname_short = os.path.basename(ffile)[:38]
        if detected:
            intercepted_count += 1
            trip_turn = circuit_break_turn if circuit_break_turn != -1 else min(n_turns, first_detect_turn + 3)
            saved = max(0, n_turns - trip_turn)
            total_turns_saved += saved
            pct = (saved / n_turns * 100.0) if n_turns > 0 else 0.0
            print(f"  [CAUGHT] {fname_short:<38} | Turns: {n_turns:3d} | Caught @ Turn {first_detect_turn:2d} ({detect_pattern}) | Tripped @ {trip_turn:2d} | Saved {saved:3d} turns ({pct:.1f}%)")
        else:
            print(f"  [MISSED] {fname_short:<38} | Turns: {n_turns:3d} | No deadlock pattern identified")
            
    recall_rate = (intercepted_count / failed_total * 100.0) if failed_total > 0 else 0.0
    savings_pct = (total_turns_saved / total_unprotected_turns * 100.0) if total_unprotected_turns > 0 else 0.0
    avg_latency_failed = (total_time_failed_ms / total_unprotected_turns) if total_unprotected_turns > 0 else 0.0
    
    print("\nStuck Trajectory Results:")
    print(f"  Total Stuck Trajectories Tested: {failed_total}")
    print(f"  Total Turns Burned by Unprotected Agents: {total_unprotected_turns}")
    print(f"  Successfully Intercepted: {intercepted_count}/{failed_total} ({recall_rate:.1f}%)")
    print(f"  Total Wasted Turns Prevented: {total_turns_saved}/{total_unprotected_turns} ({savings_pct:.1f}% Turn/Token Savings)")
    print("  Deadlock Patterns Caught:")
    for pat, cnt in pattern_breakdown.items():
        print(f"    • {pat}: {cnt} runs")

    # --------------------------------------------------------------------------
    # PART 3: CONTEXT HEALING & SCHEMA INTEGRITY ON REAL HISTORIES
    # --------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[PART 3: CONTEXT HEALING & SCHEMA INTEGRITY ON REAL HISTORIES]")
    all_files = clean_files + failed_files
    tested_histories = 0
    schema_compliant = 0
    
    for f in all_files:
        data = load_trajectory_file(f)
        if not data:
            continue
        traj = data.get("trajectory", [])
        if not traj or not isinstance(traj, list) or len(traj) < 6:
            continue
            
        tested_histories += 1
        messages = []
        for m in traj:
            role = "assistant" if m.get("role") == "ai" else m.get("role", "user")
            content = m.get("text") or m.get("system_prompt") or ""
            messages.append({"role": role, "content": content})
            
        initial_len = len(messages)
        healed_messages = heal(messages, raise_on_circuit_break=False)
        is_valid = validate(healed_messages)
        if is_valid:
            schema_compliant += 1
            
    schema_compliance_pct = (schema_compliant / tested_histories * 100.0) if tested_histories > 0 else 100.0
    print(f"  Real Conversation Histories Evaluated: {tested_histories}")
    print(f"  Schema Invariants & Prompt Integrity Maintained: {schema_compliant}/{tested_histories} ({schema_compliance_pct:.1f}%)")

    # --------------------------------------------------------------------------
    # FINAL BENCHMARK SCORECARD
    # --------------------------------------------------------------------------
    total_turns_all = clean_total_turns + total_unprotected_turns
    overall_latency = (total_time_clean_ms + total_time_failed_ms) / total_turns_all if total_turns_all > 0 else 0.0
    print("\n" + "=" * 80)
    print(" FINAL EMPIRICAL DATASET SCORECARD (Capybala v0.6.1)")
    print("=" * 80)
    print(f"  Clean Specificity          : {clean_specificity:.2f}% ({clean_passed}/{clean_total})")
    print(f"  False Positive Rate (FPR)  : {clean_fpr:.2f}%")
    print(f"  Deadlock Detection Recall  : {recall_rate:.2f}% ({intercepted_count}/{failed_total})")
    print(f"  Turn / Cost Savings        : {savings_pct:.2f}% ({total_turns_saved} wasted turns prevented)")
    print(f"  Schema Compliance Rate     : {schema_compliance_pct:.1f}% ({schema_compliant}/{tested_histories})")
    print(f"  Average Capybala Latency   : {overall_latency:.3f} ms / turn")
    print("=" * 80)

if __name__ == "__main__":
    main()
