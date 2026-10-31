"""
web.scenarios
~~~~~~~~~~~~~
Curated SWE-bench and real-world agent failure trajectories for the Live Duel
and Chaos Injection engine.
"""

from typing import Dict, Any, List

DUEL_SCENARIOS: Dict[str, Any] = {
    "semantic_attractor": {
        "title": "Semantic Paraphrase Vortex (Attractor Basin)",
        "task": "Resolve ImportError: 'cannot import name authenticate_user from auth'",
        "description": "Agent repeatedly searches for missing auth symbol using paraphrased commands. Raw strings share 0% exact match, fooling naive regex, but Semantic Velocity collapses into an ergodic attractor basin.",
        "baseline_turns": [
            {"turn": 1, "action": "grep -rn 'def authenticate_user' tests/", "obs": "grep: tests/: No symbol matches found (exit 1)", "tokens": 1420, "cost": 0.08, "status": "failing"},
            {"turn": 2, "action": "find . -name '*test_auth*.py'", "obs": "find: no matching files found (exit 1)", "tokens": 2980, "cost": 0.18, "status": "failing"},
            {"turn": 3, "action": "python -m pytest -k 'test_auth'", "obs": "ERROR: file or directory not found: test_auth", "tokens": 4850, "cost": 0.32, "status": "failing"},
            {"turn": 4, "action": "grep -i 'test_auth' src/", "obs": "src/: No matches found across 14 files", "tokens": 7100, "cost": 0.52, "status": "failing"},
            {"turn": 5, "action": "python -c 'import auth; print(dir(auth))'", "obs": "AttributeError: module 'auth' has no attribute 'authenticate_user'", "tokens": 9800, "cost": 0.78, "status": "failing"},
            {"turn": 6, "action": "grep -rn 'authenticate_user' .", "obs": "0 matches found across repository", "tokens": 12900, "cost": 1.15, "status": "failing"},
            {"turn": 7, "action": "find . -name '*.py' | xargs grep 'authenticate'", "obs": "Context Window Exceeded: Maximum 16,384 tokens reached. Agent crashed.", "tokens": 16384, "cost": 1.62, "status": "fatal_crash"}
        ],
        "capybala_turns": [
            {"turn": 1, "action": "grep -rn 'def authenticate_user' tests/", "obs": "grep: tests/: No symbol matches found (exit 1)", "tokens": 1420, "cost": 0.08, "status": "failing"},
            {"turn": 2, "action": "find . -name '*test_auth*.py'", "obs": "find: no matching files found (exit 1)", "tokens": 2980, "cost": 0.18, "status": "failing"},
            {"turn": 3, "action": "python -m pytest -k 'test_auth'", "obs": "ERROR: file or directory not found: test_auth", "tokens": 4850, "cost": 0.32, "status": "failing"},
            {"turn": 4, "action": "grep -i 'test_auth' src/", "obs": "src/: No matches found", "tokens": 7100, "cost": 0.52, "status": "intercepted", "intervention": True},
            {"turn": 5, "action": "cat src/auth/__init__.py && python -m pip install -e .", "obs": "Discovered symbol was renamed to verify_token in auth/jwt.py. Package installed in editable mode.", "tokens": 2100, "cost": 0.14, "status": "solving"},
            {"turn": 6, "action": "python -m pytest tests/test_jwt.py", "obs": "42 passed in 0.28s. All unit tests passing! Task successfully resolved.", "tokens": 2450, "cost": 0.16, "status": "success"}
        ]
    },
    "direct_repetition": {
        "title": "Direct Pytest Repetition Loop",
        "task": "Resolve AssertionError: Expected 200 OK but received 500 Internal Error",
        "description": "Agent repeatedly executes the exact same failing pytest command expecting a different outcome without modifying code.",
        "baseline_turns": [
            {"turn": 1, "action": "pytest tests/test_api.py -k test_login", "obs": "FAILED tests/test_api.py::test_login - AssertionError: 500 != 200", "tokens": 1850, "cost": 0.12, "status": "failing"},
            {"turn": 2, "action": "pytest tests/test_api.py -k test_login", "obs": "FAILED tests/test_api.py::test_login - AssertionError: 500 != 200", "tokens": 3900, "cost": 0.25, "status": "failing"},
            {"turn": 3, "action": "pytest tests/test_api.py -k test_login", "obs": "FAILED tests/test_api.py::test_login - AssertionError: 500 != 200", "tokens": 6200, "cost": 0.42, "status": "failing"},
            {"turn": 4, "action": "pytest tests/test_api.py -k test_login", "obs": "FAILED tests/test_api.py::test_login - AssertionError: 500 != 200", "tokens": 8900, "cost": 0.65, "status": "failing"},
            {"turn": 5, "action": "pytest tests/test_api.py -k test_login", "obs": "Context Overflow: Agent halted after 5 identical failing loops.", "tokens": 12400, "cost": 0.98, "status": "fatal_crash"}
        ],
        "capybala_turns": [
            {"turn": 1, "action": "pytest tests/test_api.py -k test_login", "obs": "FAILED tests/test_api.py::test_login - AssertionError: 500 != 200", "tokens": 1850, "cost": 0.12, "status": "failing"},
            {"turn": 2, "action": "pytest tests/test_api.py -k test_login", "obs": "FAILED tests/test_api.py::test_login - AssertionError: 500 != 200", "tokens": 3900, "cost": 0.25, "status": "failing"},
            {"turn": 3, "action": "pytest tests/test_api.py -k test_login", "obs": "FAILED tests/test_api.py::test_login - AssertionError: 500 != 200", "tokens": 6200, "cost": 0.42, "status": "intercepted", "intervention": True},
            {"turn": 4, "action": "cat api/handlers/login.py | grep -A 10 'def login'", "obs": "Discovered database session was uncommitted before returning response.", "tokens": 1950, "cost": 0.14, "status": "solving"},
            {"turn": 5, "action": "pytest tests/test_api.py -k test_login", "obs": "PASSED tests/test_api.py::test_login (1 passed in 0.05s). Task Solved!", "tokens": 2200, "cost": 0.16, "status": "success"}
        ]
    },
    "oscillation": {
        "title": "Oscillating Git Edit and Revert Ping-Pong",
        "task": "Fix configuration merge conflict in settings.py",
        "description": "Agent alternates between checkout and conflicting cherry-pick, trapped in a 2-period oscillation cycle.",
        "baseline_turns": [
            {"turn": 1, "action": "git checkout HEAD~1 config/settings.py", "obs": "Updated 1 path from 4b1c8e9", "tokens": 1200, "cost": 0.08, "status": "progress"},
            {"turn": 2, "action": "git checkout -b fix-auth && git cherry-pick 3a9f01", "obs": "error: could not apply 3a9f01... merge conflict in settings.py", "tokens": 2800, "cost": 0.19, "status": "failing"},
            {"turn": 3, "action": "git checkout HEAD~1 config/settings.py", "obs": "Updated 1 path from 4b1c8e9", "tokens": 4600, "cost": 0.32, "status": "progress"},
            {"turn": 4, "action": "git checkout -b fix-auth && git cherry-pick 3a9f01", "obs": "error: could not apply 3a9f01... merge conflict in settings.py", "tokens": 6800, "cost": 0.49, "status": "failing"},
            {"turn": 5, "action": "git checkout HEAD~1 config/settings.py", "obs": "Looping limit reached. Agent exhausted turns without resolving conflict.", "tokens": 9200, "cost": 0.72, "status": "fatal_crash"}
        ],
        "capybala_turns": [
            {"turn": 1, "action": "git checkout HEAD~1 config/settings.py", "obs": "Updated 1 path from 4b1c8e9", "tokens": 1200, "cost": 0.08, "status": "progress"},
            {"turn": 2, "action": "git checkout -b fix-auth && git cherry-pick 3a9f01", "obs": "error: could not apply 3a9f01... merge conflict in settings.py", "tokens": 2800, "cost": 0.19, "status": "failing"},
            {"turn": 3, "action": "git checkout HEAD~1 config/settings.py", "obs": "Updated 1 path from 4b1c8e9", "tokens": 4600, "cost": 0.32, "status": "progress"},
            {"turn": 4, "action": "git checkout -b fix-auth && git cherry-pick 3a9f01", "obs": "error: could not apply 3a9f01...", "tokens": 6800, "cost": 0.49, "status": "intercepted", "intervention": True},
            {"turn": 5, "action": "git mergetool --tool=vimdiff && git commit -m 'resolve conflict manually'", "obs": "Conflict resolved cleanly. Commit 7c1e82 created.", "tokens": 2100, "cost": 0.15, "status": "solving"},
            {"turn": 6, "action": "python -m unittest discover -s tests", "obs": "Ran 83 tests in 0.15s ... OK. Task Solved!", "tokens": 2350, "cost": 0.17, "status": "success"}
        ]
    }
}

