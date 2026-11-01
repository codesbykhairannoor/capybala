# Capybala Workspace Rules

## 1. Zero Polling Mandate
- Never poll `manage_task(Action='status')` or shell commands in a loop when waiting for asynchronous tasks.
- Yield execution immediately and rely on reactive wakeups.

## 2. Anti-Loop & Ergodic Attractor Prevention
- Monitor action semantic velocity ($v_t$). Never repeat identical failing commands (e.g. `pytest`, `cat`, `grep`).
- If a test fails, inspect once, synthesize the root cause, and apply the code fix directly. Maximum 2 read-only actions before code mutation.

## 3. Git Synchronization
- Always ensure changes are verified with unit tests (`python -m unittest discover -s capybala/tests`) and pushed to `origin/main`.
