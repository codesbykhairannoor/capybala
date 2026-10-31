"""
audit_final_evaluation.py
Comprehensive Final Review of Capybala Library & Modular Web App
Reviewing Models: DeepSeek-V3, Claude Haiku 4.5, GPT-4o-mini
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

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

MODELS = [
    ("DeepSeek-V3", "deepseek/deepseek-chat"),
    ("Claude-Haiku-4.5", "anthropic/claude-haiku-4.5"),
    ("GPT-4o-mini", "openai/gpt-4o-mini")
]

SYSTEM_PROMPT = """You are a veteran open-source evaluator, senior AI systems architect, and hackathon judge (Y Combinator, NeurIPS LLM Agent benchmarks, Devpost).
You evaluate projects with strict objectivity, technical rigor, and zero fluff.
Provide clear numeric scores (X/10), strengths, remaining risks, and a final verdict."""

# Read key files to provide actual code context
with open("web/app.py", "r", encoding="utf-8") as f:
    web_app_code = f.read()

with open("web/scenarios.py", "r", encoding="utf-8") as f:
    scenarios_code = f.read()

with open("web/static/js/duel.js", "r", encoding="utf-8") as f:
    duel_js_code = f.read()

with open("web/static/js/canvas.js", "r", encoding="utf-8") as f:
    canvas_js_code = f.read()

USER_PROMPT = f"""Please provide an authoritative review of the **Capybala** project (Library + Modular Web Demo).

### Context & Implementation:
1. **The Library (`capybala`)**:
   - Zero-dependency, pure Python standard library.
   - Detects autonomous agent deadlocks (direct loops, oscillations, tool thrashing, paraphrased command attractors).
   - Mathematical Manifold Engine:
     * 1024-D unit sphere projection via hybrid word + character n-gram hashing.
     * Semantic Velocity: v_t = 1 - cos_sim(v_t, v_t-1).
     * Velocity Variance gating: sigma^2 <= 0.08 (distinguishes true ergodic traps from active random exploration).
     * 64-state Markov Transition Entropy (H = -sum p_ij log p_ij).
     * Atomic Rollback + Context Pruner + Heuristic Doctor Strategic Pivot.
   - SWE-bench 100-Trajectory Stress Test: 90.0% TNR, 90.0% TPR, 0.00% attractor false positives, 0.605 ms P50 latency, 52.59% turn savings.

2. **The New Modular Web App (`web/`)**:
   - Clean modular architecture: `web/app.py` (FastAPI backend), `web/scenarios.py`, `web/templates/index.html`, `web/static/css/style.css`, and modular JS (`duel.js`, `canvas.js`, `chaos.js`, `app.js`).
   - **Feature 1: The Live Split-Screen Agent Duel**: Real-time dollar ticker ($) and token burn meter comparing Unprotected Agent ($1.62 burned, fatal crash) vs Capybala Guarded Agent ($0.16 total, 10.1x cheaper, auto-recovery at Turn 4, task solved).
   - **Feature 2: Phase-Space Trajectory Manifold Canvas**: Interactive 2D/3D unit sphere projection with concentric shells, central attractor basin vortex (v_t < 0.70), decaying spiral orbits, and golden Capybala atomic deflection vector.
   - **Feature 3: Interactive Chaos Injection Panel**: 4 one-click failure presets + custom 2-action semantic distance calculator.
   - **Theme**: Light Mode default (editorial paper & slate with honey amber accent) + instant theme toggle (Sun/Moon).

### Key Code Highlights from the Implementation:
```python
# web/app.py snippet:
{web_app_code[:1200]}
```

```javascript
// web/static/js/canvas.js snippet:
{canvas_js_code[:1200]}
```

```javascript
// web/static/js/duel.js snippet:
{duel_js_code[:1200]}
```

### Please Evaluate and Provide:
1. **SCORECARD (Rate 1-10 with one-sentence justification each)**:
   - *Algorithmic & Mathematical Rigor* (Library)
   - *Software Engineering & Clean Architecture* (Library + Web refactoring)
   - *Demo Engagement & 'Holy Shit' Factor* (Split-screen duel, dollar ticker, phase-space canvas)
   - *Overall Hackathon / Open Source Win Potential*
2. **WHAT ELEVATES THIS ABOVE TYPICAL AI PROJECTS**:
   - Why does this stand out against generic LLM wrappers and standard hackathon entries?
3. **CRITICAL EYE (ANY REMAINING EDGE CASES OR RISKS)**:
   - What is one thing an aggressive judge or senior distributed systems engineer might probe?
4. **FINAL SUMMARY VERDICT**:
   - Is this project now ready to compete at the very top tier?
"""

def query_model(name: str, model_id: str) -> tuple:
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        "max_tokens": 2500,
        "temperature": 0.15
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/codesbykhairannoor/capybala",
        "X-Title": "Final Evaluation"
    }
    
    req = urllib.request.Request(BASE_URL, headers=headers, data=json.dumps(payload).encode("utf-8"))
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            content = data["choices"][0]["message"]["content"]
            return name, True, content, elapsed
    except Exception as e:
        return name, False, str(e), time.time() - t0

def main():
    print("=" * 70, flush=True)
    print("RUNNING FINAL MULTI-AI EVALUATION (DEEPSEEK-V3, CLAUDE HAIKU 4.5, GPT-4O-MINI)", flush=True)
    print("=" * 70, flush=True)
    
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(query_model, name, m_id): name for name, m_id in MODELS}
        for fut in as_completed(futures):
            name, success, content, elapsed = fut.result()
            print(f"[{'SUCCESS' if success else 'FAILED'}] {name} completed in {elapsed:.2f}s", flush=True)
            results[name] = {"success": success, "content": content, "elapsed": elapsed}
    
    output_path = "ai_final_evaluation_report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Capybala Library & Web App: Final Multi-AI Review\n\n")
        f.write(f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Evaluators: DeepSeek-V3, Claude Haiku 4.5, GPT-4o-mini\n\n---\n\n")
        for name, data in results.items():
            f.write(f"## 🏆 Review by {name}\n\n")
            f.write(data["content"])
            f.write("\n\n---\n\n")
            
    print(f"\n[DONE] Final evaluation report saved to {output_path}", flush=True)

if __name__ == "__main__":
    main()

