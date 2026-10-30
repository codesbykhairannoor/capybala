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

# Load API Key from .env
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY:
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    API_KEY = line.strip().split("=", 1)[1]

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    {"id": "deepseek/deepseek-chat", "name": "DeepSeek-V3"},
    {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama-3.3-70B-Instruct"}
]

def load_code():
    base_dir = r"D:\Capybala\capybala\capybala"
    files = ["api.py", "detector.py", "pruner.py", "healer.py"]
    code_bundle = {}
    for fname in files:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                code_bundle[fname] = f.read()
    return code_bundle

def build_prompt(code_bundle):
    code_text = ""
    for fname, code in code_bundle.items():
        code_text += f"\n--- FILE: capybala/{fname} ---\n{code}\n"

    system_prompt = (
        "You are a cynical, battle-hardened Principal AI Infrastructure Engineer and Research Scientist. "
        "Your task is to identify every single 'HALLUCINATION' and 'WISHFUL THINKING' in this library design. "
        "A 'hallucination' in library design is when the developer assumes something will work in production "
        "with real LLM agents (Claude 3.7, GPT-4o, Llama 3.3, DeepSeek-V3), but in reality it fails, breaks contracts, "
        "or creates worse failure modes. "
        "ZERO MARKETING TALK. ZERO COMPLIMENTS. BRUTALLY HONEST TECHNICAL DRILL-DOWN."
    )

    user_prompt = f"""Here is the Capybala v0.3.0 implementation:

{code_text}

Analyze and expose:
1. WHAT ARE THE DEVELOPER'S DELUSIONS / HALLUCINATIONS?
   - What does the code assume the LLM will do that LLMs NEVER actually do in production?
   - (e.g. Does injecting a reflection prompt actually prevent autoregressive repetition, or does it trigger an infinite heal loop?)
2. THE INFINITE HEAL TRAP (META-DEADLOCK):
   - What happens if the agent fails -> gets healed -> fails another way -> gets healed -> ad infinitum? Is there a circuit breaker?
3. THE TOOL ARGUMENT & SERIALIZATION BLIND SPOTS:
   - What happens with complex JSON, streaming completions, parallel tool calls with kwargs dicts, or dynamic timestamps?
4. REAL-WORLD PRODUCTION EDGE CASES:
   - What will break in LangGraph, CrewAI, AutoGen, or multi-threaded FastAPI servers?
5. THE CONCRETE FIXES:
   - Exactly what code changes are needed to eliminate these delusions?

Be direct, technical, and ruthless."""

    return system_prompt, user_prompt

def query_model(model_info, system_prompt, user_prompt):
    model_id = model_info["id"]
    model_name = model_info["name"]
    print(f"\n[>>>] Consulting {model_name} on architecture delusions/hallucinations...")

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
            "X-Title": "Capybala Delusion & Hallucination Audit",
            "User-Agent": "CapybalaAuditor/2.0"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            content = data["choices"][0]["message"]["content"]
            print(f"[✓] {model_name} delivered ruthless verdict! ({total_tokens} tokens)")
            return {
                "model": model_name,
                "model_id": model_id,
                "content": content,
                "tokens": total_tokens
            }
    except Exception as e:
        print(f"[X] Error querying {model_name}: {e}", file=sys.stderr)
        return {"model": model_name, "error": str(e)}

def main():
    code_bundle = load_code()
    sys_prompt, user_prompt = build_prompt(code_bundle)
    results = []

    for model_info in MODELS:
        res = query_model(model_info, sys_prompt, user_prompt)
        results.append(res)

    out_file = r"D:\Capybala\consultation_hallucinations_round2.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# 🦫 CAPYBALA ROUND 2: EXPOSING ARCHITECTURAL DELUSIONS & HALLUCINATIONS\n\n")
        for r in results:
            f.write(f"## 🤖 Verdict by {r['model']} ({r.get('model_id', '')})\n\n")
            if "error" in r:
                f.write(f"**Error:** {r['error']}\n\n")
            else:
                f.write(r["content"] + "\n\n---\n\n")

    print(f"\n[DONE] Saved to {out_file}")

if __name__ == "__main__":
    main()

