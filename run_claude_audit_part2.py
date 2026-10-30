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
    ]
    bundle = {}
    for fname in files:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                bundle[fname] = f.read()
    return bundle

code_bundle = load_codebase()
code_text = ""
for fname, content in code_bundle.items():
    code_text += f"\n\n==================== FILE: capybala/{fname} ====================\n{content}\n"

system_prompt = (
    "You are an exceptionally ruthless Principal AI Infrastructure Architect and Security Auditor. "
    "Continue the adversarial audit of Capybala v0.5.0. "
    "Focus specifically on SECTIONS 3, 4, 5, and 6. "
    "Be concise, technical, and concrete. Give executable Python test code for breaking cases. "
    "ZERO MARKETING TALK. ZERO COMPLIMENTS."
)

user_prompt = f"""CONTINUE THE AUDIT OF CAPYBALA v0.5.0:
{code_text}

FOCUS ON:
SECTION 3: CONCURRENCY & THREAD SAFETY CATASTROPHES (DeadlockDetector, ContextPruner, watch wrapper)
SECTION 4: PROTOCOL SCHEMA VIOLATIONS (Anthropic turn-alternation, OpenAI tool call/response pairing, Gemini)
SECTION 5: MEMORY MANAGEMENT & GC LEAKS (Deque retention, raw_actions, token caching)
SECTION 6: TOP 3 BREAKING PYTHON TEST CASES (Exact runnable code snippets that cause crashes or misclassifications)
"""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/capybala/capybala",
    "X-Title": "Capybala Adversarial Audit Part 2"
}

payload = {
    "model": "anthropic/claude-haiku-4.5",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": 0.2,
    "max_tokens": 4096
}

print("Running Part 2 Audit via anthropic/claude-haiku-4.5...")
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers=headers
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        part2_text = data["choices"][0]["message"]["content"]
        
        output_path = r"D:\Capybala\claude_haiku_audit_part2.md"
        with open(output_path, "w", encoding="utf-8") as out_f:
            out_f.write(part2_text)
        print(f"Saved Part 2 Audit to: {output_path}")
        print("=" * 60)
        print(part2_text[:1200])
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.read().decode("utf-8"))

