/**
 * duel.js - Split-Screen Agent Duel & Real-Time Dollar Ticker Engine
 * Controls step-by-step playback, dollar cost accumulation, and self-healing state transitions.
 * Fully resilient with embedded fallback scenarios and zero reliance on async blocking.
 */

const DUEL_FALLBACK_SCENARIOS = {
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
            {"turn": 4, "action": "grep -i 'test_auth' src/", "obs": "src/: No matches found", "tokens": 7100, "cost": 0.52, "status": "intercepted", "intervention": true},
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
            {"turn": 3, "action": "pytest tests/test_api.py -k test_login", "obs": "FAILED tests/test_api.py::test_login - AssertionError: 500 != 200", "tokens": 6200, "cost": 0.42, "status": "intercepted", "intervention": true},
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
            {"turn": 4, "action": "git checkout -b fix-auth && git cherry-pick 3a9f01", "obs": "error: could not apply 3a9f01...", "tokens": 6800, "cost": 0.49, "status": "intercepted", "intervention": true},
            {"turn": 5, "action": "git mergetool --tool=vimdiff && git commit -m 'resolve conflict manually'", "obs": "Conflict resolved cleanly. Commit 7c1e82 created.", "tokens": 2100, "cost": 0.15, "status": "solving"},
            {"turn": 6, "action": "python -m unittest discover -s tests", "obs": "Ran 83 tests in 0.15s ... OK. Task Solved!", "tokens": 2350, "cost": 0.17, "status": "success"}
        ]
    }
};

const DuelEngine = {
    scenarios: DUEL_FALLBACK_SCENARIOS,
    currentKey: 'semantic_attractor',
    isRunning: false,

    async init() {
        // Sync with dropdown if user already selected something
        const sel = document.getElementById("duelScenarioSelect");
        if (sel && sel.value) {
            this.currentKey = sel.value;
        }

        this.resetDisplay();

        // Asynchronously supplement with backend scenarios if available
        try {
            const res = await fetch('/api/duel/scenarios');
            if (res.ok) {
                const data = await res.json();
                if (data && Object.keys(data).length > 0) {
                    this.scenarios = data;
                }
            }
        } catch (err) {
            console.log("Using embedded duel scenarios (offline/resilient fallback).");
        }
    },

    selectScenario(key) {
        if (this.isRunning) return;
        this.currentKey = key;
        this.resetDisplay();
    },

    getActiveScenario() {
        const sel = document.getElementById("duelScenarioSelect");
        if (sel && sel.value) {
            this.currentKey = sel.value;
        }
        return (this.scenarios && this.scenarios[this.currentKey]) || DUEL_FALLBACK_SCENARIOS[this.currentKey] || DUEL_FALLBACK_SCENARIOS['semantic_attractor'];
    },

    resetDisplay() {
        const sc = this.getActiveScenario();
        if (!sc) return;

        const leftStream = document.getElementById("leftStream");
        const rightStream = document.getElementById("rightStream");

        if (leftStream) {
            leftStream.innerHTML = `<div class='text-slate-400 dark:text-slate-500 text-xs italic py-2'>Ready to simulate. Selected scenario: <b>${this.escapeHtml(sc.title)}</b>.<br>Press <b>'Run Live Duel'</b> to start head-to-head execution.</div>`;
        }
        if (rightStream) {
            rightStream.innerHTML = `<div class='text-slate-400 dark:text-slate-500 text-xs italic py-2'>Capybala Armed (0.6ms sub-millisecond monitor active).<br>Watching for ergodic attractor collapse and tool oscillations.</div>`;
        }

        const elLeftCost = document.getElementById("duelCostLeft");
        const elRightCost = document.getElementById("duelCostRight");
        const elBadge = document.getElementById("duelOutcomeBadge");
        const elLeftTicker = document.getElementById("leftCostTicker");
        const elRightTicker = document.getElementById("rightCostTicker");
        const elLeftStep = document.getElementById("leftStepIndicator");
        const elRightStep = document.getElementById("rightStepIndicator");
        const elMultiplier = document.getElementById("duelSavingsMultiplier");

        if (elLeftCost) elLeftCost.innerText = "$0.00";
        if (elRightCost) elRightCost.innerText = "$0.00";
        if (elBadge) {
            elBadge.innerText = "Ready to execute";
            elBadge.className = "text-base font-bold font-mono text-slate-800 dark:text-white mt-1";
        }
        if (elLeftTicker) elLeftTicker.innerText = "$0.00 Wasted";
        if (elRightTicker) elRightTicker.innerText = "$0.00 Total";
        if (elLeftStep) elLeftStep.innerText = "Step 0";
        if (elRightStep) elRightStep.innerText = "Step 0";
        if (elMultiplier) elMultiplier.innerText = "10.1x";
    },

    async runDuel() {
        if (this.isRunning) return;

        const sc = this.getActiveScenario();
        if (!sc) {
            console.error("No valid duel scenario available");
            return;
        }

        this.isRunning = true;
        const btn = document.getElementById("duelBtn");
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-slate-950 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg><span>Simulating Duel...</span>`;
        }

        const leftStream = document.getElementById("leftStream");
        const rightStream = document.getElementById("rightStream");
        if (leftStream) leftStream.innerHTML = "";
        if (rightStream) rightStream.innerHTML = "";

        const bTurns = sc.baseline_turns || [];
        const cTurns = sc.capybala_turns || [];
        const maxSteps = Math.max(bTurns.length, cTurns.length);

        try {
            for (let i = 0; i < maxSteps; i++) {
                const elLeftStep = document.getElementById("leftStepIndicator");
                const elRightStep = document.getElementById("rightStepIndicator");
                if (elLeftStep) elLeftStep.innerText = `Step ${Math.min(i + 1, bTurns.length)} / ${bTurns.length}`;
                if (elRightStep) elRightStep.innerText = `Step ${Math.min(i + 1, cTurns.length)} / ${cTurns.length}`;

                // Left: Unprotected Baseline Execution
                if (i < bTurns.length && leftStream) {
                    const t = bTurns[i];
                    const d = document.createElement("div");
                    d.className = "stream-item transition-all duration-300";

                    if (t.status === 'fatal_crash') {
                        d.className += " p-3 rounded-lg bg-rose-200 dark:bg-rose-950/80 border-2 border-rose-500 text-rose-950 dark:text-rose-200 font-bold shadow-md";
                        d.innerHTML = `💥 <b>[FATAL CONTEXT OVERFLOW]</b><br><span class='text-xs font-normal'>${this.escapeHtml(t.obs)}</span>`;
                    } else {
                        d.className += " p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-300 shadow-sm";
                        d.innerHTML = `<span class='text-rose-600 dark:text-rose-400 font-bold'>[Turn ${t.turn}] ${this.escapeHtml(t.action)}</span><br><span class='text-slate-500 text-[11px] font-mono'>${this.escapeHtml(t.obs)}</span>`;
                    }
                    leftStream.appendChild(d);
                    leftStream.scrollTop = leftStream.scrollHeight;

                    const elLeftCost = document.getElementById("duelCostLeft");
                    const elLeftTicker = document.getElementById("leftCostTicker");
                    if (elLeftCost) elLeftCost.innerText = `$${t.cost.toFixed(2)}`;
                    if (elLeftTicker) elLeftTicker.innerText = `$${t.cost.toFixed(2)} Wasted`;
                }

                // Right: Capybala Protected Execution
                if (i < cTurns.length && rightStream) {
                    const t = cTurns[i];
                    const d = document.createElement("div");
                    d.className = "stream-item transition-all duration-300";

                    if (t.status === 'intercepted') {
                        d.className += " p-3 rounded-lg bg-amber-100 dark:bg-amber-950/70 border-2 border-amber-400 dark:border-amber-500 text-amber-950 dark:text-amber-200 font-bold shadow-md animate-pulse";
                        d.innerHTML = `🦫 <b>[CAPYBALA INTERCEPTED DEADLOCK]</b><br><span class='text-[11px] font-normal'>Phase transition caught in 0.6ms. Semantic velocity collapsed. Atomic Rollback performed &amp; Doctor Pivot injected!</span>`;
                    } else if (t.status === 'success') {
                        d.className += " p-3 rounded-lg bg-emerald-100 dark:bg-emerald-950/70 border-2 border-emerald-500 text-emerald-950 dark:text-emerald-200 font-bold shadow-md";
                        d.innerHTML = `🎉 <b>[TASK SOLVED!]</b><br><span class='text-[11px] font-normal'>${this.escapeHtml(t.obs)}</span>`;
                    } else {
                        d.className += " p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-300 shadow-sm";
                        d.innerHTML = `<span class='text-emerald-700 dark:text-emerald-400 font-bold'>[Turn ${t.turn}] ${this.escapeHtml(t.action)}</span><br><span class='text-slate-500 text-[11px] font-mono'>${this.escapeHtml(t.obs)}</span>`;
                    }
                    rightStream.appendChild(d);
                    rightStream.scrollTop = rightStream.scrollHeight;

                    const elRightCost = document.getElementById("duelCostRight");
                    const elRightTicker = document.getElementById("rightCostTicker");
                    if (elRightCost) elRightCost.innerText = `$${t.cost.toFixed(2)}`;
                    if (elRightTicker) elRightTicker.innerText = `$${t.cost.toFixed(2)} Total`;
                }

                // Smooth realistic step delay
                await new Promise(r => setTimeout(r, 650));
            }

            // Final Calculations & Scoreboard
            const finalLeft = bTurns.length > 0 ? bTurns[bTurns.length - 1].cost : 1.62;
            const finalRight = cTurns.length > 0 ? cTurns[cTurns.length - 1].cost : 0.16;
            const multiplier = (finalLeft / Math.max(0.01, finalRight)).toFixed(1);

            const elMultiplier = document.getElementById("duelSavingsMultiplier");
            const elBadge = document.getElementById("duelOutcomeBadge");

            if (elMultiplier) elMultiplier.innerText = `${multiplier}x`;
            if (elBadge) {
                elBadge.innerText = `Capybala Solved (${multiplier}x cheaper)`;
                elBadge.className = "text-base font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1";
            }
        } catch (err) {
            console.error("Error during live duel execution:", err);
        } finally {
            this.isRunning = false;
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `<svg class="w-4 h-4 fill-current mr-1.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg><span>Run Live Duel</span>`;
            }
        }
    },

    escapeHtml(str) {
        return str ? String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;") : "";
    }
};

// Immediate synchronous ready state
if (typeof window !== 'undefined') {
    window.DuelEngine = DuelEngine;
}
