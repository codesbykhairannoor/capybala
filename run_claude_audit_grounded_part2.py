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

def load_pruner_and_api():
    base_dir = r"D:\Capybala\capybala\capybala"
    bundle = {}
    for fname in ["pruner.py", "api.py"]:
        fpath = os.path.join(base_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            bundle[fname] = f.read()
    return bundle

def run_grounded_part2():
    bundle = load_pruner_and_api()
    code_text = ""
    for fname, content in bundle.items():
        code_text += f"\n\n==================== REAL FILE: capybala/{fname} ====================\n{content}\n"

    system_prompt = (
        "You are an exceptionally ruthless Principal AI Infrastructure Architect and Security Auditor. "
        "Audit the REAL Python code provided below for Capybala v0.6.0 (pruner.py and api.py). "
        "DO NOT hallucinate classes or files that do not exist. Only analyze the actual code given. "
        "ZERO COMPLIMENTS. ZERO FLUFF. PURE TECHNICAL CRITIQUE."
    )

    user_prompt = f"""AUDIT THE REAL SOURCE CODE OF `capybala/pruner.py` and `capybala/api.py`:

{code_text}

FIND REAL FLAWS IN:
1. `prune_dead_searches()` (in pruner.py):
   - What if a file being viewed contains the words 'no matches found' or 'file not found' in its code or docstrings? Does it get falsely compressed?
   - What happens to Anthropic or OpenAI tool call pairing (`tool_call_id`) if the content is replaced?
   - How does boundary calculation `len(cleaned_messages) - max_age_turns` behave if `messages` has fewer turns?

2. `rollback_and_reflect()` (in pruner.py):
   - In Anthropic mode, lines 146-155: what if clean_history[-1]['content'] is a list of blocks? What if the last user turn was a tool_result block? Can appending a text block violate Anthropic schema?
   - How does it handle Gemini `parts` during rollback? Are Gemini parts preserved or lost?

3. `heal()` (in api.py):
   - Look at lines 60-146 where turns are reconstructed: What if an agent emits streaming messages or non-standard roles?
   - In Gemini handling (lines 78-100), `prev_act, _ = turns_sequence[-1]` has an `IndexError` if `turns_sequence` is empty!
   - What if `messages` is mutated while another thread is reading it? Is `heal()` thread-safe when modifying `messages` in-place?

4. TOP 3 CONCRETE RUNNABLE BREAKING TEST CASES against `pruner.py` and `api.py`.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/capybala/capybala",
        "X-Title": "Capybala Grounded Audit Part 2"
    }

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

    print(f"Connecting to OpenRouter using {model_id} for Grounded Part 2...")
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
            print("Grounded part 2 audit response received! Length:", len(content))
            out_file = os.path.join(os.path.dirname(__file__), "claude_v060_audit_grounded_part2.md")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved grounded part 2 audit report to: {out_file}")
            print("\n" + "=" * 80)
            print("PREVIEW OF GROUNDED FINDINGS:")
            print("=" * 80)
            # Use safe printing to avoid charmap codec error
            sys.stdout.buffer.write(content[:2500].encode("utf-8"))
            sys.stdout.buffer.write(b"\n")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error running audit: {e}")

if __name__ == "__main__":
    run_grounded_part2()
