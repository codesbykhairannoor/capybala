"""
debate_beyond_if_else.py
~~~~~~~~~~~~~~~~~~~~~~~~
Multi-Model AI Roundtable: Moving Beyond IF-ELSE in Agent Deadlock Detection
- DeepSeek-V3 (deepseek/deepseek-chat)
- GPT-4o-mini (openai/gpt-4o-mini)
- Claude Haiku 4.5 (anthropic/claude-haiku-4.5)

Debate Topic:
"Is relying purely on IF-ELSE / regex heuristics a dead end for autonomous agent supervision?
How can Capybala implement a true post-IF-ELSE mathematical paradigm (Semantic Velocity,
Attractor Manifolds, Markov Ergodic Traps, or Pure-Python LSH/Random Projection)
WITHOUT bloating into a 500MB PyTorch/Transformers dependency and keeping latency < 2ms?"
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

def call_openrouter(model_id: str, messages: list, max_tokens: int = 3500, temperature: float = 0.3) -> str:
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
        "X-Title": "Beyond IF-ELSE AI Debate"
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

def main():
    print("=" * 80)
    print("ROUNDTABLE: BEYOND IF-ELSE IN AGENT DEADLOCK DETECTION")
    print("Models: DeepSeek-V3, GPT-4o-mini, Claude Haiku 4.5")
    print("=" * 80)

    # -------------------------------------------------------------
    # ROUND 1: DeepSeek-V3 (The Mathematical / Algorithmic Theorist)
    # -------------------------------------------------------------
    print("\n[ROUND 1] Calling DeepSeek-V3 (Mathematical & Dynamical Systems Formulation)...")
    prompt_deepseek = """You are a Principal AI Research Scientist specializing in Dynamical Systems Theory, Information Geometry, and Autonomous Agent Trajectories.

CONTEXT:
Capybala is a zero-dependency, sub-millisecond agent supervision runtime that detects agent deadlocks and heals context. Currently, like 95% of the agent industry (LangGraph, CrewAI, AutoGen, Devin), it relies heavily on IF-ELSE logic, bounded regex, and sliding-window hashes.
While it achieves 86-92% recall on SWE-bench, IF-ELSE has a fatal theoretical blind spot:
LLM agents can paraphrase their actions or oscillate across semantically equivalent operations:
- Turn 1: `find . -name "*.py"`
- Turn 2: `python -c "import glob; print(glob.glob('**/*.py'))"`
- Turn 3: `ls -R | grep '\.py$'`
Syntactically, these commands have 0% hash/regex overlap. Semantically, the agent is stuck in an identical attractor basin!

QUESTION:
1. How do we mathematically formalize this beyond IF-ELSE? (e.g. Semantic Velocity v = ||e_t - e_{t-1}||, Latent Attractor Manifolds, or Markov Ergodic Traps).
2. HARD CONSTRAINT: Capybala CANNOT pull in a 500MB PyTorch/Transformers dependency. It must remain pure Python or zero heavy dependencies, and latency MUST stay under 2ms.
3. What mathematical technique in pure Python (e.g., Sparse Random Projections, SimHash / MinHash LSH, Fast Subword N-Gram TF-IDF Vector Spaces, or Discrete State Transition Entropy) can detect these semantic attractor loops in < 2ms?
Provide exact mathematical formulations and pseudo-code.
"""
    resp_deepseek = call_openrouter("deepseek/deepseek-chat", [{"role": "user", "content": prompt_deepseek}], max_tokens=3000)
    print("✓ DeepSeek-V3 response received.")

    # -------------------------------------------------------------
    # ROUND 2: GPT-4o-mini (The Systems Architect & Pragmatic Implementer)
    # -------------------------------------------------------------
    print("\n[ROUND 2] Calling GPT-4o-mini (Engineering Viability & Hybrid Architecture)...")
    prompt_gpt = f"""You are a Distinguished AI Systems Architect.
Review DeepSeek-V3's mathematical proposal for moving Capybala beyond IF-ELSE:

DeepSeek-V3's Proposal:
{resp_deepseek}

YOUR CHALLENGE:
1. Is DeepSeek-V3's proposal actually implementable in real production Python without crashing on weird agent outputs or blowing up CPU latency?
2. Critique the trade-offs:
   - Why not an ONNX quantized micro-model (e.g. 5MB) vs Pure-Python Sparse Random Projection / MinHash?
   - What happens when an agent legitimately explores diverse tools (how do we prevent false positives in a vector manifold)?
3. Propose the EXACT HYBRID ARCHITECTURE for Capybala:
   - Tier 1: Reflex (deterministic IF-ELSE / exact hash - 0.05ms)
   - Tier 2: Manifold / Semantic Attractor (post-IF-ELSE mathematical engine - < 1.5ms)
How should Tier 1 and Tier 2 collaborate?
"""
    resp_gpt = call_openrouter("openai/gpt-4o-mini", [{"role": "user", "content": prompt_gpt}], max_tokens=3000)
    print("✓ GPT-4o-mini response received.")

    # -------------------------------------------------------------
    # ROUND 3: Claude Haiku 4.5 (The Supreme Adjudicator & Concrete Blueprint)
    # -------------------------------------------------------------
    print("\n[ROUND 3] Calling Claude Haiku 4.5 (Final Consensus & Execution Blueprint)...")
    prompt_claude = f"""You are the Chief AI Systems Adjudicator.
Synthesize the debate between DeepSeek-V3 and GPT-4o-mini.

DeepSeek-V3:
{resp_deepseek}

GPT-4o-mini:
{resp_gpt}

DELIVER THE FINAL BLUEPRINT FOR CAPYBALA:
1. THE WINNING POST-IF-ELSE PARADIGM: What is the exact algorithm we should implement in Capybala RIGHT NOW? (Name the algorithm, the metric, and the threshold).
2. ZERO-DEPENDENCY FORMULA: Give the exact pure-Python mathematical formulation (e.g. N-gram feature hashing + Cosine Velocity / Spectral Graph / Markov Transition Matrix).
3. CONCRETE STEP-BY-STEP IMPLEMENTATION PLAN:
   - What new class to write (`SemanticAttractorDetector` or `ManifoldDeadlockEngine`)?
   - What mathematical formulas to use?
   - How to integrate it into `DeadlockDetector.check()` so existing tests and SWE-bench replays stay 100% green while unlocking semantic loop detection?
Summarize clearly in Indonesian and English with production-grade engineering precision.
"""
    resp_claude = call_openrouter("anthropic/claude-haiku-4.5", [{"role": "user", "content": prompt_claude}], max_tokens=3500)
    print("✓ Claude Haiku 4.5 response received.")

    # -------------------------------------------------------------
    # SAVE FULL DEBATE REPORT
    # -------------------------------------------------------------
    report_path = r"d:\Capybala\ai_roundtable_beyond_if_else.md"
    content = f"""# Capybala: Moving Beyond IF-ELSE Roundtable Debate
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Models:** DeepSeek-V3, OpenAI GPT-4o-mini, Anthropic Claude Haiku 4.5  

---

## 1. DeepSeek-V3: Mathematical Formulation & Dynamical Systems
{resp_deepseek}

---

## 2. GPT-4o-mini: Systems Architecture & Hybrid Dual-Engine
{resp_gpt}

---

## 3. Claude Haiku 4.5: Definitive Post-IF-ELSE Blueprint & Algorithm
{resp_claude}
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n[DONE] Full Roundtable Report saved to: {report_path}")

if __name__ == "__main__":
    main()

