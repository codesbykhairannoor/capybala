import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/capybala/capybala",
    "X-Title": "Capybala Step 1 Engine Architecture Consultation"
}

prompt = """
We are building the Step 1 Core Engine for `capybala`: a zero-dependency, ultra-fast Python library that prevents and heals Cognitive Deadlocks in autonomous coding agents (Llama, Claude, GPT).

We need your expert review on the exact algorithms for:
1. `detector.py`: DeadlockDetector
   - Must detect:
     a) Direct repetition: Action A -> A -> A (exact or normalized command match).
     b) Oscillations: Cycle A -> B -> A -> B (e.g., patch file -> run test fails -> revert file -> run test fails).
     c) Semantic traceback loop: When tool output contains repeated Exception/Traceback signatures even if file line numbers slightly drift.
   - Zero external dependencies (Pure Python: re, hashlib, difflib/Levenshtein).
   - High speed (< 1ms execution time).

2. `pruner.py`: ContextPruner
   - When a deadlock is confirmed, how should the conversation history list of messages `[{role, content}]` be pruned?
   - Rule: NEVER delete system instructions, user task prompt, or the very first observation.
   - Strategy: Cycle Collapsing. How do we collapse the repetitive cycle into a concise tombstone/summary while keeping the agent grounded?

Provide concise, battle-tested Python class structures and algorithms. Be direct and technical.
"""

def query_expert(model, role_name):
    print(f"Consulting {role_name} ({model})...")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"You are a World-Class {role_name} specializing in autonomous LLM agent execution, graph theory, and context window optimization."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }
    req = urllib.request.Request(URL, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data['choices'][0]['message']['content']

response = query_expert("openai/gpt-4o-mini", "Principal Distributed Systems & AI Agent Architect")
print("\n=== CONSULTATION RESULT ===")
print(response)

with open("consultation_step1_verdict.md", "w", encoding="utf-8") as f:
    f.write("# Consultation: Step 1 Core Engine Algorithms for Capybala\n\n")
    f.write(response)

