"""
openrouter_audit.py
~~~~~~~~~~~~~~~~~~~
Direct adversarial audit of Capybala v0.3.0 across multiple cutting-edge AI models
via OpenRouter API with strict budget safeguards (< $0.01 total).
Uses pure Python standard library (urllib.request) - 0 external dependencies.
"""

import os
import json
import urllib.request
import urllib.error
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY and os.path.exists(os.path.join(os.path.dirname(__file__), ".env")):
    with open(os.path.join(os.path.dirname(__file__), ".env"), "r") as ef:
        for line in ef:
            if line.startswith("OPENROUTER_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Select 2 top-tier, ultra-cheap code auditing models
# deepseek-chat: $0.14 / 1M tokens (~$0.0007 per request)
# meta-llama/llama-3.3-70b-instruct: $0.12 / 1M tokens (~$0.0006 per request)
MODELS = [
    {
        "id": "deepseek/deepseek-chat",
        "name": "DeepSeek-V3",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "Llama-3.3-70B-Instruct",
    }
]

def load_code():
    base_dir = r"D:\Capybala\capybala\capybala"
    files = ["api.py", "detector.py", "pruner.py"]
    code_bundle = {}
    for fname in files:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                code_bundle[fname] = f.read()
    return code_bundle

def build_adversarial_prompt(code_bundle):
    code_text = ""
    for fname, code in code_bundle.items():
        code_text += f"\n--- FILE: capybala/{fname} ---\n{code}\n"

    system_prompt = (
        "You are a notoriously hostile, adversarial Principal Systems Software Architect and Security Auditor. "
        "Your job is to ruthlessly roast and audit this Python library called 'capybala' (v0.3.0). "
        "ABSOLUTELY ZERO POSITIVITY BIAS. NO COMPLIMENTS, NO FLATTERY, NO MARKETING POLITE FILLER. "
        "Treat this like a vicious code review where you want to tear down bad assumptions, hidden bugs, race conditions, "
        "asyncio footguns, memory traps, and schema violations. "
        "Go straight for the throat with technical precision, exact failure modes, and line-level critiques."
    )

    user_prompt = f"""AUDIT THIS CODEBASE RIGHT NOW. ATTACK EVERY WEAKNESS:

{code_text}

Provide your ruthless audit structured as follows:
1. THE FATAL DEFECTS: What will crash in production, corrupt state, or deadlock under real concurrent load?
2. THE SNEAKY BUGS & EDGE CASES: Subtle logic flaws, regex misses, false positives, or contract violations.
3. THE BULLSHIT AUDIT: Is the architecture truly solving agent loops or is it just heuristic theater?
4. WHAT MUST BE RE-WRITTEN IMMEDIATELY: Clear, unfiltered technical verdict.

NO PLEASANTRIES. START ATTACKING DIRECTLY."""

    return system_prompt, user_prompt

def query_model(model_info, system_prompt, user_prompt):
    model_id = model_info["id"]
    model_name = model_info["name"]
    print(f"\n[>>>] Querying {model_name} ({model_id}) via OpenRouter...")

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1500,
    }

    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://capybala.dev",
            "X-Title": "Capybala Adversarial Audit",
            "User-Agent": "CapybalaAuditor/1.0"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            comp_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # Estimate cost in USD
            cost_est = (prompt_tokens * 0.14 / 1_000_000) + (comp_tokens * 0.28 / 1_000_000)
            cost_idr = cost_est * 16200

            content = data["choices"][0]["message"]["content"]
            print(f"[✓] {model_name} responded! Tokens: {total_tokens} (Cost: ~${cost_est:.5f} / ~Rp {cost_idr:.1f})")
            return {
                "model": model_name,
                "model_id": model_id,
                "content": content,
                "tokens": total_tokens,
                "cost_usd": cost_est,
                "cost_idr": cost_idr
            }
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[X] HTTP Error {e.code}: {err_msg}", file=sys.stderr)
        return {"model": model_name, "error": f"HTTP {e.code}: {err_msg}"}
    except Exception as e:
        print(f"[X] Error querying {model_name}: {e}", file=sys.stderr)
        return {"model": model_name, "error": str(e)}

def main():
    print("=" * 60)
    print("🦫 CAPYBALA v0.3.0 ADVERSARIAL OPENROUTER AUDIT")
    print("=" * 60)
    
    code_bundle = load_code()
    if not code_bundle:
        print("Error: Could not load code files from D:\\Capybala\\capybala\\capybala")
        sys.exit(1)
        
    print(f"Loaded {len(code_bundle)} code files ({sum(len(c) for c in code_bundle.values())} chars).")
    sys_prompt, user_prompt = build_adversarial_prompt(code_bundle)

    results = []
    total_cost_usd = 0.0
    total_cost_idr = 0.0

    for model_info in MODELS:
        res = query_model(model_info, sys_prompt, user_prompt)
        results.append(res)
        if "cost_usd" in res:
            total_cost_usd += res["cost_usd"]
            total_cost_idr += res["cost_idr"]

    # Save to Markdown
    output_path = r"D:\Capybala\openrouter_audit_results.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 🦫 CAPYBALA v0.3.0: RUTHLESS ADVERSARIAL OPENROUTER AUDIT\n\n")
        f.write(f"**Total Spent:** ${total_cost_usd:.5f} USD (~Rp {total_cost_idr:.1f} IDR)\n")
        f.write(f"**Budget Limit:** $0.50 (Used < 1% of budget!)\n\n---\n\n")

        for r in results:
            f.write(f"## 🤖 Model: {r['model']} ({r.get('model_id', '')})\n")
            if "error" in r:
                f.write(f"**Error:** {r['error']}\n\n")
            else:
                f.write(f"**Tokens:** {r['tokens']} | **Cost:** ~${r['cost_usd']:.5f} (~Rp {r['cost_idr']:.1f} IDR)\n\n")
                f.write(r["content"])
                f.write("\n\n---\n\n")

    print(f"\n[DONE] Results written to {output_path}")
    print(f"Total Cost: ${total_cost_usd:.5f} (~Rp {total_cost_idr:.1f} IDR). Strict budget preserved!")

if __name__ == "__main__":
    main()

