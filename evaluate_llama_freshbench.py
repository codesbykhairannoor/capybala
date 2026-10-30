"""
LiveSWE-2026: Benchmark Evaluator for Meta Llama Coding Agents
Meta Global AI Developer Hackathon 2026 Component
"""

import pandas as pd
import urllib.request
import json
import os

print("=" * 70)
print("EVALUATING LLAMA AGENT ON FRESH OCTOBER 2026 GITHUB BUGS")
print("=" * 70)

# Load dataset fresh October 2026
dataset_path = "d:/Dataset Kaggle/fresh_october_2026_bugs.csv"
df = pd.read_csv(dataset_path)

print(f"Total bugs available in benchmark: {len(df)}")
print(f"Sampling 1st bug from repository: {df.iloc[0]['repo_name']}")
sample = df.iloc[0]

print(f"\n[TASK METADATA]")
print(f"Title       : {sample['title']}")
print(f"Repo        : {sample['repo_name']} (PR #{sample['pr_number']})")
print(f"Created At  : {sample['created_at']}")
print(f"Diff URL    : {sample['diff_url']}")
print(f"\n[BUG DESCRIPTION]:\n{sample['bug_description'][:300]}...")

# Unduh kunci jawaban asli dari programmer manusia (diff)
try:
    req = urllib.request.Request(sample['diff_url'], headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        human_diff = resp.read().decode('utf-8', errors='ignore')
        print(f"\n[HUMAN GROUND-TRUTH PATCH (Kunci Jawaban Manusia)]:")
        lines = human_diff.split('\n')
        print('\n'.join(lines[:12]))
        print(f"... ({len(lines)} total lines in human patch)")
except Exception as e:
    print(f"Could not fetch diff: {e}")

print("\n" + "=" * 70)
print("[EVALUATION WORKFLOW]")
print("1. Prompt Llama-3-70B with: 'Here is the bug description, generate the patch.'")
print("2. Compare Llama's generated code against the Human Ground Truth patch.")
print("3. Quantify if Llama can solve unseen 2026 bugs or fails due to memorization drift.")
print("=" * 70)

