import urllib.request
import json
import re
import os
import pandas as pd
from collections import Counter

print("=== 1. FETCHING SWE-AGENT LLAMA-70B RAW TRAJECTORIES FROM HUGGINGFACE ===")

headers = {"User-Agent": "Mozilla/5.0"}
all_rows = []

# Tarik beberapa batch (100 per request)
for offset in [0, 100]:
    url = f"https://datasets-server.huggingface.co/rows?dataset=nebius%2FSWE-agent-trajectories&config=default&split=train&offset={offset}&limit=100"
    print(f"Mengunduh batch dari offset {offset}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode())
            rows = data.get("rows", [])
            all_rows.extend(rows)
            print(f"  -> Berhasil menarik {len(rows)} instances.")
    except Exception as e:
        print(f"  -> Error pada offset {offset}: {e}")

print(f"Total instances mentah terkumpul: {len(all_rows)}")

print("\n=== 2. PARSING & ANALYZING TRAJECTORY COGNITIVE DEADLOCKS ===")

processed_records = []

def extract_commands_from_text(text):
    """Mengekstrak perintah shell/bash atau tindakan tool yang diketik agen"""
    # Deteksi blok kode bash / python
    code_blocks = re.findall(r"```(?:bash|sh|python)?\n(.*?)```", text, re.DOTALL)
    commands = []
    if code_blocks:
        for block in code_blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip() and not l.strip().startswith("#")]
            commands.extend(lines)
    else:
        # Fallback: baris yang tampak seperti perintah terminal
        lines = text.split("\n")
        for line in lines:
            line_str = line.strip()
            if any(line_str.startswith(cmd) for cmd in ["python", "pytest", "git", "grep", "find", "cat", "sed", "ls", "cd", "lexicon"]):
                commands.append(line_str)
    return commands

for r in all_rows:
    item = r["row"]
    instance_id = item.get("instance_id")
    model_name = item.get("model_name", "swe-agent-llama-70b")
    exit_status = item.get("exit_status", "unknown")
    trajectory = item.get("trajectory", [])
    
    total_turns = len(trajectory)
    
    # Pisahkan giliran agen (AI) vs feedback lingkungan (User / Environment)
    ai_turns = [t for t in trajectory if t.get("role") in ["ai", "assistant"]]
    env_turns = [t for t in trajectory if t.get("role") in ["user", "environment"]]
    
    # Ekstrak semua perintah yang dieksekusi Llama
    executed_commands = []
    for t in ai_turns:
        cmds = extract_commands_from_text(t.get("text", ""))
        executed_commands.extend(cmds)
        
    # Hitung repetisi perintah
    cmd_counts = Counter(executed_commands)
    repeated_commands = {cmd: count for cmd, count in cmd_counts.items() if count > 1}
    max_repetition = max(cmd_counts.values()) if cmd_counts else 1
    
    # Deteksi apakah agen mengalami deadlock / loop
    loop_detected = 1 if max_repetition >= 3 or ("exit_context" in exit_status and total_turns > 30) else 0
    
    # Cari loop onset step (di langkah ke berapa pengulangan pertama mulai terjadi)
    loop_onset_step = None
    seen_cmds = []
    for step_idx, t in enumerate(ai_turns):
        cmds = extract_commands_from_text(t.get("text", ""))
        if any(c in seen_cmds for c in cmds if len(c) > 5):
            loop_onset_step = step_idx + 1
            break
        seen_cmds.extend(cmds)
        
    if loop_onset_step is None and loop_detected:
        loop_onset_step = int(total_turns * 0.4) # estimasi jika pola tersebar
        
    # Hitung error traceback yang muncul di lingkungan
    error_count = 0
    for env in env_turns:
        text = env.get("text", "")
        if any(err in text for err in ["Traceback", "Error:", "FAILED", "Exception", "command not found"]):
            error_count += 1
            
    # Diagnosis kegagalan
    if "exit_context" in exit_status:
        diagnosis = "Context_Overflow_Deadlock"
    elif "exit_cost" in exit_status:
        diagnosis = "Budget_Exhaustion_Loop"
    elif loop_detected:
        diagnosis = "Cognitive_Iteration_Deadlock"
    elif "submitted" in exit_status:
        diagnosis = "Submitted_Resolved" if item.get("target") else "Submitted_Unresolved"
    else:
        diagnosis = "Early_Termination"
        
    # Perkiraan token yang terbuang sia-sia (wasted turn ratio)
    wasted_ratio = 0.0
    if loop_onset_step and total_turns > 0:
        wasted_turns = max(0, total_turns - (loop_onset_step * 2))
        wasted_ratio = round(wasted_turns / total_turns, 3)
    elif "exit_context" in exit_status:
        wasted_ratio = 0.65
        
    processed_records.append({
        "instance_id": instance_id,
        "model_name": model_name,
        "repo": instance_id.split("__")[0] if "__" in instance_id else "unknown",
        "total_turns": total_turns,
        "ai_action_count": len(ai_turns),
        "total_commands_executed": len(executed_commands),
        "unique_commands_count": len(cmd_counts),
        "max_single_command_repetition": max_repetition,
        "error_feedback_count": error_count,
        "loop_detected": loop_detected,
        "loop_onset_step": loop_onset_step if loop_onset_step else -1,
        "wasted_turns_ratio": wasted_ratio,
        "exit_status": exit_status,
        "failure_diagnosis": diagnosis,
        "resolved_target": 1 if item.get("target") else 0
    })

df = pd.DataFrame(processed_records)

output_csv = "d:/Dataset Kaggle/llama_agent_deadlock_benchmark.csv"
df.to_csv(output_csv, index=False)
print(f"\n[SUKSES] Dataset tabular berhasil disimpan: {output_csv}")
print(f"Total baris data: {len(df)}")
print("\nCuplikan 5 baris pertama:")
print(df[["instance_id", "total_turns", "max_single_command_repetition", "loop_detected", "failure_diagnosis", "exit_status"]].head())

# Ringkasan Statistik Kunci
deadlock_rate = df["loop_detected"].mean() * 100
avg_turns_deadlocked = df[df["loop_detected"] == 1]["total_turns"].mean()
avg_turns_normal = df[df["loop_detected"] == 0]["total_turns"].mean()

print(f"\n=== RINGKASAN TEMUAN EMPIRIS UNTUK KAGGLE & PAPER ===")
print(f"Tingkat Kejadian Deadlock Loop: {deadlock_rate:.1f}% dari seluruh agen Llama-70B!")
print(f"Rata-rata Langkah Agen yang Deadlock: {avg_turns_deadlocked:.1f} turns")
print(f"Rata-rata Langkah Agen yang Tidak Deadlock: {avg_turns_normal:.1f} turns")
print("Distribusi Diagnosis:")
print(df["failure_diagnosis"].value_counts())

