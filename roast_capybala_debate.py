import urllib.request
import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/capybala/capybala",
    "X-Title": "Brutal Adversarial Review of Capybala Library"
}

prompt = """
ROAST THIS AI AGENT GUARDRAIL LIBRARY MERCILESSLY.
We are building a Python library called `capybala` designed to stop and heal 'Cognitive Deadlocks' in autonomous coding agents (Llama, Claude, GPT-4o).

HERE IS OUR CURRENT IMPLEMENTATION:
1. DeadlockDetector:
   - Strips hex/timestamps. Checks if the last 3 actions are identical (`recent[-3:]`).
   - If action matches 3 times, flags Deadlock.
   - Also checks if exception names repeat 3 times.

2. ContextPruner:
   - When deadlock triggers, it slices out `messages[:-4]`, leaves the first 2 messages (system & task), and injects a string:
     `{"role": "system", "content": "[CAPYBALA PRUNING: Collapsed 4 iterations. Saved 2,000 tokens]"}`

3. AgentHealer (The Doctor):
   - Injects a system message:
     `{"role": "system", "content": "[CAPYBALA DOCTOR] STOP! Try a different approach..."}`

4. Developer API:
   ```python
   guard = CapybalaGuard(messages)
   healed = guard.step(action, observation)
   ```

YOUR TASK:
Be a brutally honest Staff AI Infrastructure Engineer at OpenAI / Anthropic.
1. WHAT ARE THE FATAL BUGS & CACAT IN THIS CODE IN PRODUCTION? (Think: OpenAI tool_call_id pairs, Claude's ban on mid-conversation system roles, false positives on 'git status').
2. WHAT IS COMPLETE HALLUCINATION / COPE? (Things we assume will work but fail in real LLM agent loops).
3. HOW SHOULD THE PYTHON API ACTUALLY LOOK SO A DEVELOPER FALLS IN LOVE WITH IT IN 1 LINE OF CODE? (Benchmark against tqdm, rich, requests).

Give it to us raw. No corporate fluff.
"""

print("Connecting to OpenRouter to query models...")

models = [
    ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B Architect"),
    ("openai/gpt-4o-mini", "OpenAI Senior Production Engineer")
]

for model_id, name in models:
    print(f"\n" + "=" * 70)
    print(f"QUERYING {name} ({model_id})...")
    print("=" * 70)
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }
    try:
        req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            print(content)
            with open(f"roast_{name.replace(' ', '_')}.md", "w", encoding="utf-8") as f:
                f.write(content)
    except Exception as e:
        print(f"Error querying {model_id}: {e}")

