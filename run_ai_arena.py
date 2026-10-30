"""
run_ai_arena.py
~~~~~~~~~~~~~~~
Multi-Model AI Arena & Ongoing Debate for Capybala v0.6.0:
- DeepSeek-V3 (deepseek/deepseek-chat)
- GPT-4o-mini (openai/gpt-4o-mini)
- Claude Haiku 4.5 (anthropic/claude-haiku-4.5)

Format:
Round 1: Red Team Attack & Test Generation (DeepSeek vs GPT-4o-mini)
Round 2: Cross-Examination Debate ("Berantem / Saling Serang Argumen") (Claude Haiku 4.5)
Round 3: Test Extraction & Live Execution against Capybala v0.6.0
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 1. API Key resolution
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("OPENROUTER_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]

if not API_KEY:
    print("[ERROR] No OPENROUTER_API_KEY found!")
    sys.exit(1)

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openrouter(model_id: str, messages: list, max_tokens: int = 4000, temperature: float = 0.2) -> str:
    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/codesbykhairannoor/capybala",
        "X-Title": "Capybala Multi-Model Debate Arena"
    }
    
    req = urllib.request.Request(BASE_URL, headers=headers, data=json.dumps(payload).encode("utf-8"))
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            print(f"[RETRY {attempt+1}] HTTP {e.code} for {model_id}: {err_body[:200]}")
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            print(f"[RETRY {attempt+1}] Error for {model_id}: {e}")
            time.sleep(2 * (attempt + 1))
            
    raise RuntimeError(f"Failed to get response from {model_id} after 3 attempts")

def load_capybala_code():
    base_dir = r"D:\Capybala\capybala\capybala"
    files = ["detector.py", "pruner.py", "api.py"]
    bundle = {}
    for fname in files:
        fpath = os.path.join(base_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            bundle[fname] = f.read()
    return bundle

def main():
    print("=" * 70)
    print("CAPYBALA v0.6.0 MULTI-MODEL ADVERSARIAL DEBATE ARENA")
    print("Models: DeepSeek-V3 vs GPT-4o-mini vs Claude Haiku 4.5")
    print("=" * 70)
    
    code = load_capybala_code()
    code_context = ""
    for fname, content in code.items():
        code_context += f"\n\n================ FILE: capybala/{fname} ================\n{content}\n"
        
    print(f"Loaded {len(code)} core files ({len(code_context)} chars).")

    # -------------------------------------------------------------
    # ROUND 1: RED TEAM ATTACKS (DeepSeek-V3 & GPT-4o-mini)
    # -------------------------------------------------------------
    attack_prompt = f"""You are an elite adversarial red-team software security & algorithmic auditor.
You are given the exact production source code of Capybala v0.6.0 (an agent deadlock detection, cycle prevention, and context pruning library for autonomous coding agents).

The files are:
- capybala/detector.py: DeadlockDetector, cycle detection, oscillation detection, active code refinement heuristic, read-only vs mutating commands.
- capybala/pruner.py: ContextPruner, negative search pruning, deduplication, atomic tool rollback.
- capybala/api.py: monitor() and heal() wrappers, message parsing across OpenAI/Anthropic/Gemini, parallel tool calls.

Source Code:
{code_context}

YOUR MISSION:
Find genuine, concrete vulnerabilities, logical bypasses, or algorithmic edge cases where Capybala v0.6.0 will:
1. FALSE NEGATIVE (Miss a real deadlock, agent stuck loop, or infinite cycle).
2. FALSE POSITIVE (Incorrectly flag a legitimate agent behavior as deadlocked).
3. RUNTIME CRASH or DATA CORRUPTION (Crash on malformed messages, tool structures, or weird schemas).

For each issue you find:
- State the exact file, class, and method name.
- Explain the flaw step-by-step.
- Provide a concrete, executable Python test snippet (`def test_issue_name(): ...`) that proves the issue. Make the test self-contained using `from capybala.detector import DeadlockDetector` or `from capybala.pruner import ContextPruner` or `from capybala.api import heal, monitor`.

Be ruthless, technical, and precise. Do not give generic advice. Show real bugs.
"""

    print("\n[ROUND 1A] Sending attack prompt to DeepSeek-V3...")
    t0 = time.time()
    deepseek_resp = call_openrouter(
        "deepseek/deepseek-chat",
        [
            {"role": "system", "content": "You are a ruthlessly rigorous adversarial code auditor."},
            {"role": "user", "content": attack_prompt}
        ],
        max_tokens=3500,
        temperature=0.2
    )
    print(f"DeepSeek-V3 answered in {time.time()-t0:.2f}s ({len(deepseek_resp)} chars).")

    print("\n[ROUND 1B] Sending attack prompt to OpenAI GPT-4o-mini...")
    t0 = time.time()
    gpt_resp = call_openrouter(
        "openai/gpt-4o-mini",
        [
            {"role": "system", "content": "You are a ruthlessly rigorous adversarial code auditor."},
            {"role": "user", "content": attack_prompt}
        ],
        max_tokens=3500,
        temperature=0.2
    )
    print(f"GPT-4o-mini answered in {time.time()-t0:.2f}s ({len(gpt_resp)} chars).")

    # -------------------------------------------------------------
    # ROUND 2: THE CLASH / CROSS-EXAMINATION (Claude Haiku 4.5)
    # -------------------------------------------------------------
    print("\n[ROUND 2] Pitting them against each other in debate with Claude Haiku 4.5...")
    debate_prompt = f"""You are the Chief Judge and Adversarial Referee in an AI Code Audit Arena.
Two frontier models (DeepSeek-V3 and GPT-4o-mini) were tasked with breaking Capybala v0.6.0.
Here are their respective attack reports and proposed test cases:

=== DEEPSEEK-V3 AUDIT REPORT & ATTACKS ===
{deepseek_resp}

=== GPT-4O-MINI AUDIT REPORT & ATTACKS ===
{gpt_resp}

=== REFERENCE SOURCE CODE OF CAPYBALA v0.6.0 ===
{code_context}

YOUR JUDICIAL / DEBATE MISSION:
Critique and adjudicate their findings ruthlessly ("Ajakin mereka berantem"):
1. HALLUCINATION & FALSE CLAIM CHECK:
   - Did DeepSeek or GPT-4o-mini make claims that are contradicted by the actual source code?
   - Point out exactly where either model misunderstood Capybala's logic or hallucinated non-existent bugs.
2. VALID STRIKES & REAL VULNERABILITIES:
   - Which attacks are genuinely VALID and demonstrate a real bug, bypass, or false positive/negative in Capybala v0.6.0?
   - Rank the valid vulnerabilities by severity (High / Medium / Low).
3. EXECUTABLE TEST SUITE SYNTHESIS:
   - Provide a clean, unified Python test suite containing ONLY the genuine, verified tests from both models that will run against Capybala v0.6.0.
   - Enclose the test code in ```python ... ``` so we can execute it directly against the codebase.
"""

    t0 = time.time()
    claude_debate_resp = call_openrouter(
        "anthropic/claude-haiku-4.5",
        [
            {"role": "system", "content": "You are a master software adjudicator and red-team referee. You ruthlessly dismantle hallucinations and validate genuine software vulnerabilities."},
            {"role": "user", "content": debate_prompt}
        ],
        max_tokens=4000,
        temperature=0.2
    )
    print(f"Claude Haiku 4.5 adjudicated in {time.time()-t0:.2f}s ({len(claude_debate_resp)} chars).")

    # -------------------------------------------------------------
    # SAVE FULL DEBATE REPORT
    # -------------------------------------------------------------
    report_path = "ai_arena_debate_v060.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Capybala v0.6.0 Multi-Model AI Arena Debate & Audit\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 1. DeepSeek-V3 Red Team Attacks\n\n")
        f.write(deepseek_resp + "\n\n")
        f.write("## 2. GPT-4o-mini Red Team Attacks\n\n")
        f.write(gpt_resp + "\n\n")
        f.write("## 3. Claude Haiku 4.5 Adjudication & Cross-Examination ('Adu Argumen')\n\n")
        f.write(claude_debate_resp + "\n\n")
        
    print(f"\nSaved full multi-model debate report to {report_path}!")

if __name__ == "__main__":
    main()

