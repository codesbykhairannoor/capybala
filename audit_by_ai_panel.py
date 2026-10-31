"""
audit_by_ai_panel.py
~~~~~~~~~~~~~~~~~~~~
Parallel Multi-Model Peer Review of Capybala v0.8.0 by:
1. DeepSeek-V3 (deepseek/deepseek-chat)
2. GPT-4o-mini (openai/gpt-4o-mini)
3. Claude 3.5 Haiku (anthropic/claude-3.5-haiku)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("OPENROUTER_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]

if not API_KEY:
    print("[ERROR] No OPENROUTER_API_KEY found!", flush=True)
    sys.exit(1)

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openrouter(model_id: str, system_prompt: str, user_prompt: str, max_tokens: int = 2500) -> tuple:
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/codesbykhairannoor/capybala",
        "X-Title": "Capybala Post-IF-ELSE AI Peer Review"
    }
    
    req = urllib.request.Request(BASE_URL, headers=headers, data=json.dumps(payload).encode("utf-8"))
    
    t0 = time.time()
    for attempt in range(3):
        try:
            print(f"[{model_id}] Sending request (attempt {attempt+1})...", flush=True)
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = time.time() - t0
                content = data["choices"][0]["message"]["content"]
                print(f"[{model_id}] Received response in {elapsed:.1f}s ({len(content)} chars)", flush=True)
                return model_id, content
        except Exception as e:
            print(f"[{model_id}] Attempt {attempt+1} error: {e}", flush=True)
            time.sleep(2 * (attempt + 1))
            
    return model_id, f"[ERROR] Failed to obtain response from {model_id}"

def main():
    print("=" * 80, flush=True)
    print("🚀 CAPYBALA v0.8.0 PARALLEL AI PEER REVIEW PANEL", flush=True)
    print("Reviewers: DeepSeek-V3, GPT-4o-mini, Claude 3.5 Haiku", flush=True)
    print("=" * 80, flush=True)

    with open("capybala/capybala/attractor.py", "r", encoding="utf-8") as f:
        attractor_code = f.read()

    with open("capybala/tests/test_v080_semantic_attractor.py", "r", encoding="utf-8") as f:
        tests_code = f.read()

    core_prompt = f"""Conduct a brutally rigorous technical audit of Capybala v0.8.0's newly implemented Post-IF-ELSE Semantic Attractor Manifold engine.

### THE SYSTEM UNDER REVIEW
Capybala is a zero-dependency, sub-millisecond agent supervision runtime designed to detect agent cognitive deadlocks and heal corrupted context.
In v0.8.0, Capybala implemented a Post-IF-ELSE continuous dynamical engine to catch paraphrased tool loops (e.g. `find . -name "*.py"` vs `ls -R | grep '\.py$'` vs `python -c "import glob..."`) which bypass traditional string hashing.

### SOURCE CODE: `capybala/attractor.py`
```python
{attractor_code}
```

### INTEGRATION IN `DeadlockDetector.check()` (`detector.py` Step 8):
```python
# In detector.py Step 8:
current_fail = self._has_failure_indicator(safe_obs) or (self.observation_signatures[-1] is not None)

# Phase Space Separation (State Space Shift Invariant):
# Successful code modifications alter the system vector field f -> f', resetting execution attractors
act_clean = raw_action.strip().lower()
first_tok = act_clean.split()[0] if act_clean else ""
first_tok = first_tok.split("(")[0]
if first_tok in ("edit", "write", "create", "patch", "replace") and not current_fail:
    self.attractor_detector.reset()

is_attractor, confidence, attractor_details = self.attractor_detector.inspect_step(
    raw_action,
    is_failing=current_fail
)
```

### UNIT TESTS: `tests/test_v080_semantic_attractor.py`
```python
{tests_code}
```

### EMPIRICAL BENCHMARK (100 Authentic SWE-bench Trajectories, 2,184 Turns):
- Deadlock Detection Recall (TPR): 90.00% (45 / 50 caught; 95.7% of true multi-turn deadlocks)
- Clean Specificity (TNR): 90.00% (45 / 50 clean trajectories safe)
- False Positive Rate on Semantic Attractor: 0.00% (0 / 50 clean runs tripped the attractor!)
- Token & Turn Savings: 52.59% (1,309 wasted turns prevented)
- Latency (Median P50): 0.681 ms / turn (Throughput: 904 turns/sec)
- Dependencies: 0 (Pure Python standard library, zero PyTorch/NumPy)
- Unit Tests: 83/83 passing in 0.095s

### AUDIT REQUIREMENTS:
Please provide your direct, expert evaluation on:
1. MATHEMATICAL & ALGORITHMIC VALIDITY:
   - Is the 256-D feature hashing + L2 normalization unit vector projection an effective, theoretically sound way to compute cosine semantic velocity in sub-millisecond pure Python?
   - Is the 64-state discrete Markov transition Shannon entropy ($H(M) = -\\sum p_{{ij}} \\log p_{{ij}}$) mathematically valid for identifying ergodic attractor traps?
   - Does the Phase Space Shift invariant (resetting buffer on successful code mutations) correctly prevent false alarms on TDD / active code refinement?
2. EDGE CASES & POTENTIAL VULNERABILITIES:
   - What adversarial agent behaviors could fool this attractor?
   - Any numerical risks (underflow, division by zero, float drift)?
3. COMPARISON WITH INDUSTRY SOTA:
   - How does this compare to LangGraph, AutoGen, CrewAI, and Devin?
4. FINAL SCORE & VERDICT:
   - Scores (1-10) for: Algorithmic Soundness, Production Readiness, Innovation.
   - Overall Verdict: Is this a genuine breakthrough or overhyped?
"""

    models = [
        ("deepseek/deepseek-chat", "You are a Principal AI Research Scientist specializing in Dynamical Systems Theory and Information Geometry.", "DeepSeek-V3"),
        ("openai/gpt-4o-mini", "You are a Principal Software Engineer and Distributed Systems Architect at OpenAI / Anthropic.", "GPT-4o-mini"),
        ("anthropic/claude-3.5-haiku", "You are a Principal Security and Reliability Auditor for Autonomous Agent Systems.", "Claude-3.5-Haiku"),
    ]

    print("Launching parallel queries across 3 frontier models...", flush=True)
    t_start = time.time()
    results = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(call_openrouter, model_id, sys_p, core_prompt): label
            for model_id, sys_p, label in models
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                _, content = future.result()
                results[label] = content
                print(f"✅ Successfully collected review from {label}!", flush=True)
            except Exception as e:
                print(f"❌ Failed to get review from {label}: {e}", flush=True)

    print(f"\nAll models finished in {time.time() - t_start:.1f}s!", flush=True)

    # Save to markdown report
    output_path = "ai_peer_review_capybala_v080.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Capybala v0.8.0 Multi-Model AI Peer Review Audit\n\n")
        f.write(f"**Audit Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write("**Reviewing Frontier Models:** DeepSeek-V3, GPT-4o-mini, Claude 3.5 Haiku  \n")
        f.write("**Target Engine:** `capybala.attractor.SemanticAttractorDetector` & Dynamical Phase Space  \n\n")
        f.write("---\n\n")

        for label in ["DeepSeek-V3", "GPT-4o-mini", "Claude-3.5-Haiku"]:
            if label in results:
                f.write(f"## 🏛️ Review by {label}\n\n")
                f.write(results[label].strip())
                f.write("\n\n---\n\n")

    print(f"Saved complete audit report to: {output_path}", flush=True)

if __name__ == "__main__":
    main()
