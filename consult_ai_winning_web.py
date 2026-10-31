"""
consult_ai_winning_web.py
Consulting Frontier AI Models (DeepSeek-V3, Claude Haiku 4.5, GPT-4o-mini)
Topic: How to transform Capybala's web demo into an indisputable 1st-Place WINNER.
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

SYSTEM_PROMPT = """You are a senior hackathon judge, principal AI systems architect, and open-source evaluator who has judged hundreds of top-tier AI hackathons (NeurIPS LLM Agent benchmarks, Devpost, Y Combinator demo days).
You give brutally honest, high-signal, tactical advice. You hate generic marketing fluff and cookie-cutter demo toys.
You evaluate projects strictly on technical credibility, interactive visual drama, and undeniable proof of value."""

USER_PROMPT = """We are building **Capybala**, a pure-Python, zero-dependency library for autonomous AI agent deadlock detection and self-healing.
Instead of brittle regex string-matching or burning $0.10 and 2 seconds on an LLM supervisor judge, Capybala uses a 1024-D unit sphere semantic velocity manifold (v_t = 1 - cos_sim) and Markov transition entropy to catch loops, tool thrashing, and paraphrased command attractors in 0.605 ms.

Currently, we built a standard developer web dashboard:
- It has scenario dropdowns, an action turn editor, a 2-command velocity calculator, an active hash bucket bar chart, a context pruner preview, and benchmark numbers.

Our team asked:
"Is this really enough to WIN? What does a truly WINNING, 1st-place hackathon / top-tier OSS demo web app actually look like in 2026?"

Please answer with brutal honesty:
1. **CRITIQUE OF THE CURRENT APPROACH**: Why do standard form-and-table dashboards usually LOSE or fail to excite senior judges? What is missing?
2. **THE 'KILLER DEMO' HOOKS (WHAT MAKES JUDGES SAY 'HOLY SHIT')**:
   - What specific interactive features create an unforgettable 'Aha!' moment? (e.g. Side-by-side agent duel/showdown? Live dollar ticker burning cash? Dynamic phase-space trajectory canvas/graph? Live trajectory upload? Live LLM API execution?)
3. **VISUAL STORYTELLING & UX STRUCTURE**:
   - What should the user see in the first 5 seconds?
   - How should the demo be structured to prove both 'extreme technical depth' AND 'instant visceral clarity'?
4. **TACTICAL TOP-PRIORITY ROADMAP**:
   - If we have 24 hours to turn this into an uncontested 1st-place submission, what are the exact top 3 things we must build right now?

Be specific, practical, and uncompromisingly direct.
"""

def query_model(name: str, model_id: str) -> tuple:
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        "max_tokens": 2500,
        "temperature": 0.2
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/codesbykhairannoor/capybala",
        "X-Title": "Winning Web App Consultation"
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
    print("CONSULTING FRONTIER AI JUDGES: HOW TO MAKE CAPYBALA A 1ST-PLACE WINNER", flush=True)
    print("=" * 70, flush=True)
    
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(query_model, name, m_id): name for name, m_id in MODELS}
        for fut in as_completed(futures):
            name, success, content, elapsed = fut.result()
            print(f"[{'SUCCESS' if success else 'FAILED'}] {name} responded in {elapsed:.2f}s", flush=True)
            results[name] = {"success": success, "content": content, "elapsed": elapsed}
    
    # Save to markdown report
    output_path = "ai_winning_web_consultation.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Capybala Winning Demo Consultation: Multi-AI Panel\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Evaluators: DeepSeek-V3, Claude Haiku 4.5, GPT-4o-mini\n\n---\n\n")
        for name, data in results.items():
            f.write(f"## 🏆 Verdict by {name}\n\n")
            f.write(data["content"])
            f.write("\n\n---\n\n")
            
    print(f"\n[DONE] Consultation saved to {output_path}", flush=True)

if __name__ == "__main__":
    main()

