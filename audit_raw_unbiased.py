"""
audit_raw_unbiased.py
~~~~~~~~~~~~~~~~~~~~~
Strict, Unbiased, Zero-Injection Peer Review of Capybala v0.8.0 Attractor Engine.
Models: DeepSeek-V3, GPT-4o-mini, Claude Haiku 4.5
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

API_KEY = ""
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
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/codesbykhairannoor/capybala",
        "X-Title": "Unbiased Code Audit"
    }
    
    req = urllib.request.Request(BASE_URL, headers=headers, data=json.dumps(payload).encode("utf-8"))
    
    t0 = time.time()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = time.time() - t0
                content = data["choices"][0]["message"]["content"]
                return model_id, content
        except Exception as e:
            print(f"[{model_id}] Retry {attempt+1}: {e}", flush=True)
            time.sleep(2 * (attempt + 1))
            
    return model_id, f"[ERROR] Failed to obtain response from {model_id}"

def main():
    print("=" * 80, flush=True)
    print("⚖️ RAW UNBIASED CODE AUDIT (ZERO PROMPT INJECTION)", flush=True)
    print("Reviewers: DeepSeek-V3, GPT-4o-mini, Claude Haiku 4.5", flush=True)
    print("=" * 80, flush=True)

    with open("capybala/capybala/attractor.py", "r", encoding="utf-8") as f:
        attractor_code = f.read()

    neutral_system_prompt = "You are an impartial, highly rigorous code auditor and software engineer."

    # Raw, strictly neutral prompt without any praise or leading adjectives
    neutral_user_prompt = f"""Review the following Python implementation of a semantic loop detector for autonomous coding agents.

### File: `capybala/attractor.py`
```python
{attractor_code}
```

### Integration Snippet:
```python
# Invoked every agent turn in detector.py:
current_fail = self._has_failure_indicator(safe_obs) or (self.observation_signatures[-1] is not None)

# Reset attractor buffer on successful file mutation
act_clean = raw_action.strip().lower()
first_tok = act_clean.split()[0] if act_clean else ""
first_tok = first_tok.split("(")[0]
is_mutating_tool = any(m in act_clean for m in ("str_replace_editor", "modify_file", "edit_file", "write_file", "apply_diff", "apply_patch"))
if (first_tok in ("edit", "write", "create", "patch", "replace") or is_mutating_tool) and not current_fail:
    self.attractor_detector.reset()

is_attractor, confidence, details = self.attractor_detector.inspect_step(
    raw_action,
    is_failing=current_fail
)
```

Please answer objectively:
1. CODE QUALITY & ALGORITHMIC CORRECTNESS:
   - Does this code do what it claims?
   - Are the feature hashing (1024-D), semantic velocity, and Shannon entropy calculations correct and numerically stable?
2. BUGS, VULNERABILITIES, AND EDGE CASES:
   - Identify any bugs, logic errors, performance bottlenecks, or edge cases where this will fail or misbehave.
3. PRODUCTION READINESS & SCORES:
   - Rate Algorithmic Correctness (1-10) and Production Readiness (1-10).
   - Provide concrete, honest critique.
"""

    models = [
        ("deepseek/deepseek-chat", "DeepSeek-V3"),
        ("openai/gpt-4o-mini", "GPT-4o-mini"),
        ("anthropic/claude-haiku-4.5", "Claude-Haiku-4.5"),
    ]

    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(call_openrouter, model_id, neutral_system_prompt, neutral_user_prompt): label
            for model_id, label in models
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                _, content = future.result()
                results[label] = content
                print(f"✅ {label} audit received!", flush=True)
            except Exception as e:
                print(f"❌ {label} failed: {e}", flush=True)

    output_path = "ai_audit_raw_unbiased.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Capybala v0.8.0 Raw Unbiased AI Audit (Zero Prompt Injection)\n\n")
        f.write(f"**Audit Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write("**Reviewing Models:** DeepSeek-V3, GPT-4o-mini, Claude Haiku 4.5  \n\n")
        f.write("---\n\n")

        for label in ["DeepSeek-V3", "GPT-4o-mini", "Claude-Haiku-4.5"]:
            if label in results:
                f.write(f"## ⚖️ Audit by {label}\n\n")
                f.write(results[label].strip())
                f.write("\n\n---\n\n")

    print(f"Saved unbiased audit to: {output_path}", flush=True)

if __name__ == "__main__":
    main()

