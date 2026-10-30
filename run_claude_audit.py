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
        "(Capybala v0.5.0: Runtime Deadlock Detector & Healer for Autonomous LLM Agents). "
        "Find EVERY SINGLE flaw, vulnerability, edge case, schema hazard, or delusion. "
        "ZERO COMPLIMENTS. ZERO FLUFF. PURE TECHNICAL CRITIQUE."
    )

    user_prompt = f"""AUDIT THE FOLLOWING CAPYBALA v0.5.0 SOURCE CODE:

{code_text}

INSPECT SPECIFICALLY:
1. FUZZY POLYMORPHIC DETECTION:
   - Does `_calculate_fuzzy_similarity` have ReDoS or division-by-zero risks?
   - How does it behave on very short strings (1-3 chars) or multi-megabyte payloads?
   - Can an agent maliciously or inadvertently bypass it?
   - Are there false positive risks on sequential parameter tuning (e.g., hyperparameter search or chunked indexing)?

2. MULTI-AGENT DELEGATION PING-PONG:
   - Can complex JSON structures, nested tool calls, or unusual agent naming schemas bypass `_extract_delegation_target`?
   - What happens if an agent talks to 3 agents in parallel?

3. CONCURRENCY & THREAD SAFETY:
   - Is `DeadlockDetector` thread-safe if an agent framework calls `check()` concurrently from multiple threads or async tasks?
   - Does `ContextPruner` or `AgentHealer` have race conditions?

4. PROTOCOL SCHEMA COMPLIANCE:
   - Does `validate()` or `rollback_and_reflect()` strictly respect Anthropic Claude's turn alternation rule?
   - Could an injected reflection message cause a 400 Bad Request error on OpenAI, Anthropic, or Gemini?

5. MEMORY LEAKS & GC PINNING:
   - Are ring buffers truly bounded under long runs (100,000 turns)?
   - Does `self.raw_actions` pin memory?

6. TOP 3 CONCRETE BREAKING TEST CASES:
   - Provide concrete python test code snippets demonstrating realistic edge cases where Capybala fails, raises an unhandled exception, or misclassifies.

Format your output in clear Markdown with concrete technical justifications.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/capybala/capybala",
        "X-Title": "Capybala Adversarial Audit"
    }

    # Model to use: claude-haiku-4.5 gives direct technical critique without hitting reasoning limits
    model_id = "anthropic/claude-haiku-4.5"
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4096
    }

    print(f"Sending codebase to {model_id} via OpenRouter...")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]
            msg = choice.get("message", {})
            audit_report = msg.get("content") or ""
            
            output_path = r"D:\Capybala\claude_haiku_audit_report.md"
            with open(output_path, "w", encoding="utf-8") as out_f:
                out_f.write(audit_report)
            
            print(f"\nAudit completed successfully! Saved to: {output_path}\n")
            print("=" * 60)
            print(audit_report[:1500])
            print("...\n[Full report saved]")
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.read().decode("utf-8"))

if __name__ == "__main__":
    run_audit()
