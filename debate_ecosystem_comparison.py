"""
debate_ecosystem_comparison.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Multi-Model AI Roundtable & Ecosystem Comparison:
- DeepSeek-V3 (deepseek/deepseek-chat)
- GPT-4o-mini (openai/gpt-4o-mini)
- Claude Haiku 4.5 (anthropic/claude-haiku-4.5)

Debate Question:
"Is Capybala truly good and novel, or is it hallucinated marketing fluff (halu)
compared to existing agent frameworks (LangGraph, CrewAI, AutoGen, OpenHands, SWE-agent, NeMo Guardrails)?"
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from datetime import datetime

# Windows UTF-8 fix
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

def call_openrouter(model_id: str, messages: list, max_tokens: int = 4000, temperature: float = 0.3) -> str:
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
        "X-Title": "Capybala Ecosystem Roundtable"
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

def load_capybala_summary():
    return """
CAPYBALA v0.7.0 ARCHITECTURAL & BENCHMARK PROFILE:
- Repository: https://github.com/codesbykhairannoor/capybala
- Core Philosophy: Pure Python, zero-dependency, deterministic agent deadlock detection, context pruning, and runtime healing.
- Latency: 0.816 ms / turn (Sub-millisecond overhead; zero LLM calls, zero embeddings).
- Empirical Benchmark (50 authentic real-world dirty trajectories from Hugging Face nebius/SWE-agent-trajectories):
  * Deadlock Recall: 92.00% (23/25 real agent stuck runs caught)
  * Clean Specificity: 96.00% (24/25 clean productive runs passed without false alarms)
  * False Positive Rate: 4.00% (1/25, where agent actually repeated exact same error 3x)
  * Token & Cost Savings: 55.22% (667 burned turns saved out of 1,208)
  * Schema Compliance: 100.0% (50/50 histories healed with zero 400 Bad Request tool_call_id mismatches)

Core Features in Capybala v0.7.0:
1. Four-Tier Deadlock Detection:
   - Direct Static Repetition (SHA hashing with window=3).
   - Traceback / Error Signature Looping (regex extraction of exception types, cycle length detection up to P=4).
   - Multi-Agent Delegation Ping-Pong (Agent A -> Agent B -> Agent A, and A -> B -> C -> D -> A cycles).
   - Structural Action Normalization & Oscillation (normalizes shifting line numbers e.g. 'goto 434' -> 'goto <NUM>', 'edit 422:422' -> 'edit <RANGE>', catches trial-and-error loops when tests persistently fail).
2. Domain-Aware False Positive Guards:
   - Viewport boundary exemptions (scroll_up/down at line 1 or EOF do not trigger static repetition).
   - Active code refinement (allows edits to same file if tests change or outputs evolve).
   - Displayed code exception filtering (ignores 'raise RuntimeError' inside viewed source code).
3. Context Pruning & Rollback:
   - Atomic tool call rollback (prunes stranded tool calls along with assistant tool_calls message to prevent OpenAI/Anthropic 400 errors).
   - Fruitless search chain collapsing (compresses chains of empty grep/find commands while keeping final finding).
4. Multi-Provider In-Place Adapters:
   - OpenAI format, Anthropic format, Gemini format, LangChain tool message format.
"""

def main():
    print("=" * 75)
    print("CAPYBALA vs AGENT ECOSYSTEM ROUNDTABLE: BAGUS ATAU HALU?")
    print("Models: DeepSeek-V3, GPT-4o-mini, Claude Haiku 4.5")
    print("=" * 75)

    profile = load_capybala_summary()

    # -------------------------------------------------------------
    # ROUND 1: GPT-4o-mini (The Enterprise Ecosystem Perspective)
    # Comparing Capybala to LangGraph, CrewAI, AutoGen, and Guardrails AI
    # -------------------------------------------------------------
    print("\n[ROUND 1] Calling GPT-4o-mini (Ecosystem Comparison: LangGraph, CrewAI, AutoGen, Guardrails AI)...")
    prompt_gpt = f"""You are a Principal AI Systems Architect with deep expertise in LLM agent orchestration frameworks.
Analyze Capybala v0.7.0 against existing production tools:
1. LangChain / LangGraph (recursion_limit, interrupt_before/after, conditional edges)
2. CrewAI (max_iter, step_callback, loop detection heuristics)
3. AutoGen / AG2 (max_consecutive_auto_reply, is_termination_msg)
4. Guardrails AI / NeMo Guardrails (input/output rails, semantic self-check)
5. OpenHands / Devin / SWE-agent built-in controllers

Here is Capybala v0.7.0's technical spec and empirical benchmark:
{profile}

BE BRUTALLY HONEST. Answer these questions with concrete technical precision:
1. APAKAH INI BAGUS ATAU HALU? (Is this a genuine, valuable innovation or redundant fluff/marketing hype?)
2. COMPARISON TABLE / HEAD-TO-HEAD: Compare Capybala against LangGraph recursion limits, CrewAI max_iter, and AutoGen termination. Why isn't a simple counter (e.g. max_iter=15) enough?
3. WHERE DOES CAPYBALA GENUINELY WIN? (Unique moats, performance, cost).
4. WHERE DOES CAPYBALA LOSE OR HAVE LIMITATIONS? (What can other tools do that Capybala cannot?).
Format your response in structured markdown with clear headings.
"""
    resp_gpt = call_openrouter("openai/gpt-4o-mini", [{"role": "user", "content": prompt_gpt}], max_tokens=3500)
    print("✓ GPT-4o-mini response received.")

    # -------------------------------------------------------------
    # ROUND 2: DeepSeek-V3 (The Open-Source Infrastructure & Benchmark Critic)
    # Cross-examining GPT-4o-mini's claims and looking at SWE-bench / real-world agent trajectories
    # -------------------------------------------------------------
    print("\n[ROUND 2] Calling DeepSeek-V3 (Benchmark & Algorithmic Reality Check)...")
    prompt_deepseek = f"""You are a Lead Autonomous Agent Researcher specializing in SWE-bench, OpenHands, and agent failure modes.
Review GPT-4o-mini's analysis and Capybala v0.7.0's technical specification.

Capybala Specification:
{profile}

GPT-4o-mini's Assessment:
{resp_gpt}

YOUR ROLE:
Challenge both Capybala and GPT-4o-mini. Saring mana yang nyata (real engineering) dan mana yang cuma "gimmick/halu".
Focus on:
1. Why do real SWE-bench agents actually fail? (Reference real behaviors: shifting line-number oscillation, fruitless grep storms, tool-schema 400 corruption).
2. Does Capybala's zero-dependency, sub-millisecond (0.8ms), deterministic approach actually beat "LLM-as-a-judge" supervisors (like LangSmith or NeMo)? Why or why not?
3. Is Capybala's 92% Recall and 96% Specificity on 50 real SWE-bench trajectories believable and meaningful, or can it be gamed?
4. What is the single biggest architectural flaw or missing capability that would make a senior engineer hesitate to adopt Capybala?
Be technical, sharp, and uncompromising.
"""
    resp_deepseek = call_openrouter("deepseek/deepseek-chat", [{"role": "user", "content": prompt_deepseek}], max_tokens=3500)
    print("✓ DeepSeek-V3 response received.")

    # -------------------------------------------------------------
    # ROUND 3: Claude Haiku 4.5 (The Supreme Adjudicator & Verdict)
    # Bringing it all together: Bagus vs Halu final verdict, positioning, and action plan
    # -------------------------------------------------------------
    print("\n[ROUND 3] Calling Claude Haiku 4.5 (Adjudicator: Final Verdict & Real Positioning)...")
    prompt_claude = f"""You are the Chief AI Systems Adjudicator and Senior Fellow at an open-source evaluation council.
You have read the technical profile of Capybala v0.7.0, along with the detailed assessments from GPT-4o-mini and DeepSeek-V3.

Capybala Profile:
{profile}

GPT-4o-mini's Assessment:
{resp_gpt}

DeepSeek-V3's Critique:
{resp_deepseek}

YOUR MISSION:
Deliver the definitive, unbiased verdict for the user:
1. VERDICT: "BAGUS" atau "HALU"? (Grade from F to A+, with exact justification).
2. WHY EXISTING TOOLS ARE FAILING: Explain in simple, vivid terms why LangGraph `recursion_limit` or CrewAI `max_iter` are crude blunt instruments compared to Capybala's structural oscillation and atomic rollback.
3. THE "SWEET SPOT" POSITIONING: Should Capybala compete as a full agent framework (competing with LangGraph/CrewAI), or should it be the universal, drop-in "ABS (Anti-lock Braking System)" that plugs into ANY agent framework?
4. THREE CONCRETE MISSING PIECES needed before Capybala can be crowned the undisputed industry standard for agent supervision.
Summarize clearly in Indonesian and English so the engineering user gets maximum clarity.
"""
    resp_claude = call_openrouter("anthropic/claude-haiku-4.5", [{"role": "user", "content": prompt_claude}], max_tokens=3500)
    print("✓ Claude Haiku 4.5 response received.")

    # -------------------------------------------------------------
    # SAVE FULL DEBATE REPORT
    # -------------------------------------------------------------
    report_path = r"d:\Capybala\ai_roundtable_bagus_atau_halu.md"
    content = f"""# Capybala v0.7.0 Ecosystem Roundtable: "Bagus atau Halu?"
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Models:** OpenAI GPT-4o-mini, DeepSeek-V3, Anthropic Claude Haiku 4.5  

---

## 1. GPT-4o-mini: Enterprise Ecosystem Comparison
{resp_gpt}

---

## 2. DeepSeek-V3: SWE-bench & Algorithmic Reality Check
{resp_deepseek}

---

## 3. Claude Haiku 4.5: Final Verdict & Strategic Positioning
{resp_claude}
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n[DONE] Full Roundtable Report saved to: {report_path}")

if __name__ == "__main__":
    main()

