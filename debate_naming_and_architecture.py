import urllib.request
import json
import os
import sys

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/composable-models/llm_multiagent_debate",
    "X-Title": "MIT MultiAgent Debate - Naming & Architecture"
}

def call_model(messages, model="openai/gpt-4o-mini", temperature=0.6):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    req = urllib.request.Request(URL, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data['choices'][0]['message']['content']

def construct_debate_msg(other_responses, round_num, max_rounds):
    prefix = f"=== ROUND {round_num}/{max_rounds} ADVERSARIAL DEBATE ===\n"
    prefix += "You are participating in an adversarial debate based on the MIT `llm_multiagent_debate` framework.\n"
    prefix += "TASK:\n"
    prefix += "1. DEBATE THE PROJECT NAME: Must be unforgettable, authoritative, developer-loved, and fit the Meta Llama ecosystem ($1M Cerebral Valley Hackathon).\n"
    prefix += "2. DEBATE THE PYTHON LIBRARY ARCHITECTURE: Exactly how the core Python logic should be implemented (Classes, Methods, Context Pruning algorithm, Llama Stack integration, Hook mechanism).\n\n"
    prefix += "Here are the positions argued by the other agents:\n"
    for agent_name, response in other_responses.items():
        prefix += f"\n>>> [Argument from {agent_name}]:\n{response}\n"
    
    if round_num == max_rounds:
        prefix += "\nThis is the FINAL ROUND. Attack the weak points of others, reconcile the trade-offs, and reach a definitive consensus on: (1) The Winning Project Name, and (2) The Exact Python Library Core Logic & API Specification."
    else:
        prefix += "\nTear down the other proposals. Call out cringe names, architectural bottlenecks, or over-engineering. Defend your proposal with technical precision."
    return prefix

print("=" * 70)
print("INITIALIZING MULTI-AGENT DEBATE: PROJECT NAME & LIBRARY LOGIC")
print("Framework: MIT llm_multiagent_debate (Du et al., ICML 2024)")
print("=" * 70)

personas = {
    "Agent_MetaHacker": """You are Agent 1: Lead Llama Stack Developer & Open-Source Hacker.
Focus: You love developer ergonomics (`pip install ...`), clean decorator/middleware syntax, and names that feel like official Meta tools (like `llama-guard`, `llama-stack`, `llama-index`).
Reject over-complicated, academic names. Demand simple, punchy, production-ready Python APIs.""",

    "Agent_SystemsArchitect": """You are Agent 2: Principal Systems & Formal Verification Architect.
Focus: You care about mathematical rigor, state machine invariants, zero runtime latency, and exact memory pruning.
You despise buzzwords and medical cliches. You demand an algorithmic state-space loop detector with sliding-window hashing and provable token reduction.""",

    "Agent_HackathonJudge": """You are Agent 3: Head of Judging at Cerebral Valley & Silicon Valley AI Founder.
Focus: You want to win the $1,000,000 prize. You evaluate viral appeal, pitch clarity, market category creation ('Self-Healing Autonomous Agents'), and a demo that makes judges' jaws drop in 2 minutes."""
}

initial_task = """
We are building a Python library based on our newly crawled October 2026 Kaggle dataset (1,000 fresh bug fixes, 14.7% AI bot PRs, showing 70% of autonomous agents die from Cognitive Deadlocks and repeated error loops).
The library monitors autonomous AI agents (especially Meta Llama-powered coding agents), intercepts infinite error loops, prunes toxic error context, and injects corrective healing prompts.

Debate and propose:
1. 3 Candidate Names for the library + rationale.
2. The core Python library architecture: What are the exact classes, methods, and step-by-step logic to implement first?
"""

# Round 1: Individual Proposals
round_1 = {}
for name, role in personas.items():
    print(f"\n>> Calling {name} for Round 1 proposal...")
    msgs = [
        {"role": "system", "content": role},
        {"role": "user", "content": initial_task}
    ]
    resp = call_model(msgs, model="openai/gpt-4o-mini", temperature=0.7)
    round_1[name] = resp
    print(f"[{name}] Round 1 proposal complete ({len(resp)} chars)")

# Round 2: Adversarial Debate & Consensus
print("\n" + "=" * 70)
print("STARTING ROUND 2: ADVERSARIAL CROSS-EXAMINATION & FINAL CONSENSUS")
print("=" * 70)

round_2 = {}
for name, role in personas.items():
    print(f"\n>> Calling {name} for Round 2 cross-examination...")
    others = {k: v for k, v in round_1.items() if k != name}
    debate_prompt = construct_debate_msg(others, 2, 2)
    msgs = [
        {"role": "system", "content": role},
        {"role": "user", "content": debate_prompt}
    ]
    resp = call_model(msgs, model="openai/gpt-4o-mini", temperature=0.4)
    round_2[name] = resp
    print(f"[{name}] Round 2 debate complete ({len(resp)} chars)")

# Save full transcript
output_file = "d:/Dataset Kaggle/naming_and_architecture_debate.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# MIT MULTI-AGENT DEBATE: PROJECT NAMING & PYTHON LIBRARY ARCHITECTURE\n\n")
    f.write("## ROUND 1: INITIAL PROPOSALS\n\n")
    for k, v in round_1.items():
        f.write(f"### {k}\n{v}\n\n")
    f.write("## ROUND 2: ADVERSARIAL CROSS-EXAMINATION & CONSENSUS\n\n")
    for k, v in round_2.items():
        f.write(f"### {k} (Consensus Vote)\n{v}\n\n")

print("\n" + "=" * 70)
print(f"[DEBATE COMPLETE] Full transcript saved to: {output_file}")
print("=" * 70)

