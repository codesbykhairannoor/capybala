import os
import sys
import json
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load API Key from .env
api_key = os.environ.get("OPENROUTER_API_KEY", "")
if not api_key:
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    api_key = line.strip().split("=", 1)[1]

def load_codebase():
    base_dir = r"D:\Capybala\capybala\capybala"
    files = [
        "detector.py",
        "pruner.py",
        "healer.py",
        "api.py",
        "adapters/base.py",
        "adapters/generic.py"
    ]
    bundle = {}
    for fname in files:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                bundle[fname] = f.read()
    return bundle

def run_audit():
    code_bundle = load_codebase()
    code_text = ""
    for fname, content in code_bundle.items():
        code_text += f"\n\n==================== FILE: capybala/{fname} ====================\n{content}\n"

    system_prompt = (
        "You are an exceptionally ruthless Principal AI Infrastructure Architect and Security Auditor. "
        "Your task is to conduct an uncompromising, adversarial deep-dive audit into this Python library "
        "(Capybala v0.6.0: Runtime Deadlock Detector & Context Healer for Autonomous LLM Agents). "
        "Find EVERY SINGLE flaw, bug, vulnerability, edge case, false positive/negative risk, schema hazard, or delusion. "
        "ZERO COMPLIMENTS. ZERO FLUFF. PURE TECHNICAL CRITIQUE."
    )

    user_prompt = f"""AUDIT THE FOLLOWING CAPYBALA v0.6.0 SOURCE CODE:

{code_text}

INSPECT SPECIFICALLY AND IDENTIFY FLAWS IN:
1. EXPLORATION THRASHING GUARD & COMMAND PARSING:
   - How does `_is_mutating_or_execution` determine if an action is mutating vs read-only? Can arguments containing words like 'write' or 'create' (e.g. `grep "write" file.py` or `find . -name "*create*"`) fool it?
   - How does it handle bash tool calls or JSON function arguments?
   - Does `consecutive_exploration_turns` have boundary edge cases?

2. ADAPTIVE SYNTAX REFINEMENT & FUZZY DETECTION:
   - Does `_is_active_code_refinement` properly inspect code differences? What if an agent emits `edit 1:5 ...` vs tool calls with JSON dicts?
   - In `output_stagnation`, does checking `is_refining` have false positive/negative issues?
   - Can an adversarial agent exploit the adaptive grace period to bypass loop detection?

3. CONTEXT PRUNING & DEAD SEARCH CLEANUP:
   - In `prune_dead_searches()`, does regex pattern matching on tool outputs have false positives (e.g. what if a code file being viewed contains the words 'no matches found' or 'file not found')?
   - Could replacing message content with tombstones break Anthropic or OpenAI tool-use call_id pairing or schema invariants?
   - In `rollback_and_reflect()`, what happens if the history contains non-standard message roles or empty lists?

4. MULTI-PROVIDER & MULTI-THREAD CONCURRENCY:
   - Are there hidden race conditions across `_lock` in `DeadlockDetector` and `ContextPruner`?
   - What happens if `heal()` is called concurrently across multiple agent threads with shared global instances?
   - How does streaming generator handling in `watch()` behave if the stream raises an exception midway?

5. TOP 4 CONCRETE BREAKING TEST CASES:
   - Provide concrete, runnable Python test cases demonstrating real-world edge cases where Capybala v0.6.0 fails, throws an unhandled exception, gets bypassed, or misclassifies.

Format your output in clear Markdown with concrete technical justifications and exact line references.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/capybala/capybala",
        "X-Title": "Capybala v0.6.0 Adversarial Audit"
    }

    # Model to use: claude-haiku-4.5 gives direct technical critique without hitting reasoning limits
    model_id = "anthropic/claude-haiku-4.5"
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4096
    }

    print(f"Connecting to OpenRouter using {model_id}...")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload).encode("utf-8")
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]
            content = choice["message"]["content"]
            print("Audit response received! Length:", len(content))
            out_file = os.path.join(os.path.dirname(__file__), "claude_v060_audit_report.md")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved full audit report to: {out_file}")
            print("\n" + "=" * 80)
            print("PREVIEW OF CLAUDE'S AUDIT FINDINGS:")
            print("=" * 80)
            print(content[:2500])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error running audit: {e}")

if __name__ == "__main__":
    run_audit()

