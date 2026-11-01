---
name: capybala-runtime-guard
description: >-
  Autonomous Agent Self-Healing, Anti-Loop Supervisor & Deadlock Resolution Runtime for AI coding assistants.
  Monitors tool execution, calculates Semantic Velocity (v_t), prevents polling loops (e.g. repeated task checking),
  detects ergodic attractor traps, and enforces Atomic Rollback & Doctor Pivots to ensure agents make forward progress.
---

# Capybala Runtime Guard: Anti-Loop & Self-Healing Protocol for AI Agents

This skill equips Antigravity with its own **Capybala Runtime Supervisor (`capybala`)**, preventing cognitive deadlocks, repeated polling loops, and analysis paralysis.

---

## 1. The Core Golden Laws (Zero-Loop Mandate)

### Law 1: Anti-Polling Guard (Zero Polling Loops)
- **NEVER poll `manage_task` or shell commands in a loop** while waiting for asynchronous background tasks.
- The Antigravity environment features **Reactive Wakeup**: background tasks automatically deliver high-priority system messages when completed.
- When an asynchronous task or command is triggered:
  1. Either proceed to independent, useful work in parallel, OR
  2. Stop invoking tools and yield control to await the reactive wakeup notification.
  3. **Strictly Forbidden**: Calling `manage_task(Action='status')` consecutively every few seconds.

### Law 2: Semantic Velocity Monitoring ($v_t$)
- Before executing any command, compare the proposed action $a_t$ with previous action $a_{t-1}$.
- Calculate the semantic distance:
  $$\Delta s = 1 - \cos(\vec{u}(a_t), \vec{u}(a_{t-1}))$$
- If the agent repeats the same command (e.g. re-running `pytest` with slightly different verbosity flags `-v`, `-vv`, `--tb=long`), semantic velocity collapses ($v_t < 0.15$).
- **Action**: Halt the loop immediately. Do not execute the redundant command.

### Law 3: Three-Read Limit (Anti-Paralysis Rule)
- An agent must NOT execute more than 2 consecutive read-only actions (`cat`, `grep`, `find`, `sed -n`, `wc`) on a failing codebase without performing a write/mutation action.
- If a test or runtime fails, inspect the failing trace ONCE, pinpoint the root cause, and apply the surgical code modification.

### Law 4: Atomic Rollback & Doctor Pivot
- When a loop or failure cascade occurs, do NOT keep appending failed attempts to the conversation memory.
- Redundant error messages create attention inertia, causing the model to second-guess and repeat inspections.
- **Rollback**: Purge the redundant failed turns from memory.
- **Doctor Pivot**: Formulate an assertive, deterministic fix directive and apply it directly.

---

## 2. Using Python Capybala Directly in Workspace

The `capybala` package is installed in the Python runtime (`import capybala`).

```python
import capybala

# 1. In-place context healing for multi-turn messages:
healed_messages = capybala.heal(messages)

# 2. Sub-millisecond Deadlock & Attractor Detection:
from capybala.detector import DeadlockDetector
from capybala.attractor import SemanticAttractorDetector

detector = DeadlockDetector(repetition_threshold=2)
attractor = SemanticAttractorDetector(velocity_threshold=0.7, stagnation_steps=2)

is_attractor, v_t, msg = attractor.inspect_step(action_string, is_failing=True)
if is_attractor:
    # Trigger Atomic Rollback and Doctor Pivot
    pass
```

---

## 3. Self-Diagnostic Checklist for the Agent

Before calling any tool:
- [ ] Did I just call this exact tool with identical or similar arguments in the previous turn?
- [ ] Am I polling a background task that will notify me automatically when done?
- [ ] Have I read the same file more than once without modifying it?
- [ ] If tests are failing, am I actively mutating the code or just running more diagnostic checks?
