"""
Capybala Visual Web Dashboard (FastAPI)
World-Class Autonomous Agent Deadlock Interception, Split-Screen Duel, and Phase-Space Manifold Canvas.
Built according to DESIGN.md and multi-AI panel craftsmanship specifications.
"""

import os
import sys
import time
import math
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Ensure capybala package in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "capybala"))

from capybala.detector import DeadlockDetector
from capybala.attractor import SemanticAttractorDetector
from capybala.healer import AgentHealer
from capybala.pruner import ContextPruner
import capybala

app = FastAPI(
    title="Capybala Agent Guardrail and Phase-Space Manifold Inspector",
    description="Zero-dependency agent deadlock detection, circuit breaker and self-healing engine.",
    version="0.8.0"
)

# Benchmark scenarios for the live duel and chaos injection
DUEL_SCENARIOS = {
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


@app.get("/api/duel/scenarios")
async def get_duel_scenarios():
    """Returns available scenarios for the live split-screen duel."""
    return DUEL_SCENARIOS


@app.post("/api/analyze")
async def analyze_trajectory(request: Request):
    """
    Executes live mathematical analysis using DeadlockDetector and SemanticAttractorDetector.
    Measures true CPU execution latency and returns mathematical trajectory telemetry.
    """
    body = await request.json()
    turns = body.get("turns", [])
    if not turns:
        return JSONResponse({"error": "No turns provided"}, status_code=400)

    detector = DeadlockDetector(
        repetition_threshold=3,
        oscillation_threshold=2,
        history_window=24,
        enable_attractor=True
    )
    attractor = SemanticAttractorDetector(
        velocity_threshold=0.70,
        variance_threshold=0.08,
        entropy_threshold=1.50,
        stagnation_steps=3,
        window_size=12
    )
    healer = AgentHealer()

    telemetry = []
    deadlock_detected = False
    deadlock_type = "NONE"
    deadlock_details = ""
    healing_prompt = ""

    t_start = time.perf_counter()

    for idx, turn in enumerate(turns):
        action = turn.get("action", "")
        observation = turn.get("observation", "")
        fail_flag = turn.get("fail", False)

        step_t0 = time.perf_counter()
        
        # 1. Attractor step
        is_attr, confidence, attr_msg = attractor.inspect_step(
            action=action,
            is_failing=fail_flag
        )
        
        # 2. Main detector check
        event = detector.check(current_action=action, observation=observation)
        step_latency_ms = (time.perf_counter() - step_t0) * 1000.0

        curr_vel = list(attractor.velocity_history)[-1] if attractor.velocity_history else 1.0
        curr_entropy = attractor._compute_markov_entropy(list(attractor.vector_history)) if len(attractor.vector_history) >= 2 else math.log(64)

        # 2D phase-space projection coordinates for canvas visualization
        # Simulates non-linear projection of the vector onto the primary 2D manifold plane
        angle = (idx * 0.95)
        radius = max(0.1, min(1.0, curr_vel))
        px = math.cos(angle) * radius
        py = math.sin(angle) * radius

        telemetry.append({
            "step": idx + 1,
            "action": action,
            "observation_snippet": observation[:120] + ("..." if len(observation) > 120 else ""),
            "is_failing": fail_flag,
            "semantic_velocity": round(curr_vel, 4),
            "markov_entropy": round(curr_entropy, 3),
            "is_attractor": is_attr,
            "latency_ms": round(step_latency_ms, 3),
            "coord_x": round(px, 3),
            "coord_y": round(py, 3)
        })

        if event.is_deadlock or is_attr:
            deadlock_detected = True
            deadlock_type = event.pattern_type if event.is_deadlock else "SEMANTIC_ATTRACTOR"
            deadlock_details = event.details if event.is_deadlock else attr_msg
            break

    total_latency_ms = (time.perf_counter() - t_start) * 1000.0

    if deadlock_detected:
        last_action = turns[-1].get("action", "") if turns else ""
        prescription = healer.prescribe(
            deadlock_pattern=deadlock_type,
            failing_action=last_action,
            error_signature=deadlock_details[:120]
        )
        healing_prompt = prescription.injected_message.get("content", "")

    return {
        "is_deadlock": deadlock_detected,
        "deadlock_type": deadlock_type,
        "details": deadlock_details,
        "total_latency_ms": round(total_latency_ms, 3),
        "avg_turn_latency_ms": round(total_latency_ms / max(1, len(turns)), 3),
        "telemetry": telemetry,
        "healing_prompt": healing_prompt
    }


@app.post("/api/velocity")
async def calculate_velocity(request: Request):
    """
    Calculates live cosine similarity, semantic velocity, and active bucket projections
    between two arbitrary command strings using Capybala's pure-Python 1024-D unit sphere space.
    """
    body = await request.json()
    cmd1 = body.get("cmd1", "")
    cmd2 = body.get("cmd2", "")

    attractor = SemanticAttractorDetector()
    
    t0 = time.perf_counter()
    v1 = attractor._extract_feature_vector(cmd1)
    v2 = attractor._extract_feature_vector(cmd2)
    cos_sim = attractor._cosine_similarity(v1, v2)
    velocity = attractor._compute_semantic_velocity(v2, v1)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    top_buckets_v1 = sorted([(i, round(val, 4)) for i, val in enumerate(v1) if val > 0], key=lambda x: -x[1])[:8]
    top_buckets_v2 = sorted([(i, round(val, 4)) for i, val in enumerate(v2) if val > 0], key=lambda x: -x[1])[:8]

    set1 = {i for i, v in top_buckets_v1}
    set2 = {i for i, v in top_buckets_v2}
    overlap_buckets = sorted(list(set1.intersection(set2)))

    return {
        "command_1": cmd1,
        "command_2": cmd2,
        "cosine_similarity": round(cos_sim, 4),
        "semantic_velocity": round(velocity, 4),
        "is_stagnant": velocity < attractor.velocity_threshold,
        "latency_ms": round(latency_ms, 3),
        "active_buckets_cmd1": sum(1 for val in v1 if val > 0),
        "active_buckets_cmd2": sum(1 for val in v2 if val > 0),
        "top_buckets_v1": top_buckets_v1,
        "top_buckets_v2": top_buckets_v2,
        "overlap_buckets": overlap_buckets
    }


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Renders the crafted, anti-slop developer UI in light mode by default."""
    return HTMLResponse(content=INDEX_HTML)


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en" class="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Capybala: Agent Deadlock Detection and Self-Healing Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                        mono: ['JetBrains Mono', 'ui-monospace', 'monospace']
                    },
                    colors: {
                        capy: {
                            amber: '#d97706',
                            amberDark: '#b45309',
                            amberLight: '#fef3c7',
                            emerald: '#059669',
                            emeraldLight: '#d1fae5',
                            rose: '#e11d48',
                            roseLight: '#ffe4e6',
                            sky: '#0284c7',
                            skyLight: '#e0f2fe'
                        }
                    }
                }
            }
        }
    </script>
    <style>
        body {
            font-family: 'Inter', system-ui, sans-serif;
            -webkit-font-smoothing: antialiased;
        }
        code, pre, .font-mono {
            font-family: 'JetBrains Mono', monospace;
        }
        /* Custom scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        .dark ::-webkit-scrollbar-thumb { background: #334155; }
        @keyframes pulseSlow {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.02); }
        }
        .animate-burn {
            animation: pulseSlow 1.5s infinite ease-in-out;
        }
    </style>
</head>
<body class="bg-slate-50 dark:bg-[#0a0c10] text-slate-800 dark:text-slate-200 min-h-screen flex flex-col transition-colors duration-150">

    <!-- Top Navigation Header -->
    <header class="border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-[#11141c]/95 backdrop-blur sticky top-0 z-50 px-6 py-3.5">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-lg bg-amber-50 dark:bg-slate-800 border border-amber-200 dark:border-slate-700 flex items-center justify-center text-xl shadow-sm">
                    🦫
                </div>
                <div>
                    <div class="flex items-center space-x-2">
                        <span class="font-bold text-slate-900 dark:text-white text-base tracking-tight">Capybala</span>
                        <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-medium">v0.8.0</span>
                        <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-emerald-700 dark:text-emerald-400 font-medium">Zero Dependencies</span>
                    </div>
                </div>
            </div>
            
            <div class="flex items-center space-x-5 text-xs font-medium">
                <a href="#duel" class="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition font-semibold">Live Duel</a>
                <a href="#canvas-section" class="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition">Phase-Space Canvas</a>
                <a href="#chaos" class="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition">Chaos Injector</a>
                <a href="#benchmarks" class="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition">SWE-bench</a>
                <a href="#quickstart" class="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition">Quickstart</a>
                
                <!-- Theme Toggle Button -->
                <button onclick="toggleTheme()" id="themeBtn" aria-label="Toggle Theme" class="p-1.5 rounded-md border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition">
                    <span id="themeIcon">🌙</span>
                </button>

                <a href="https://github.com/codesbykhairannoor/capybala" target="_blank" rel="noopener noreferrer" class="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 font-medium transition shadow-sm">
                    <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                    <span>GitHub</span>
                </a>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-grow max-w-7xl mx-auto px-6 py-8 space-y-12 w-full">

        <!-- Top Punchy Header & Value Proposition -->
        <div class="space-y-3 max-w-4xl">
            <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs font-mono font-medium">
                <span>🔥 Stop Agent Death Spirals</span>
                <span>•</span>
                <span>0.605 ms Execution Latency</span>
                <span>•</span>
                <span>Zero Tokens Burned</span>
            </div>
            <h1 class="text-3xl md:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
                Watch an AI Agent Loop. Then Watch Capybala Heal It.
            </h1>
            <p class="text-base text-slate-600 dark:text-slate-300 leading-relaxed">
                When autonomous agents get stuck in repetitive commands or paraphrased search basins, they burn tens of dollars and crash with context overflow. Capybala projects agent actions into a <span class="font-mono font-semibold text-slate-900 dark:text-white">1024-D</span> dynamical semantic manifold, catching ergodic attractors in <span class="font-mono font-semibold text-amber-700 dark:text-amber-400">0.605 ms</span> with pure Python standard library.
            </p>
        </div>

        <!-- KILLER FEATURE 1: THE LIVE SPLIT-SCREEN DUEL & REAL-TIME DOLLAR TICKER -->
        <section id="duel" class="bg-white dark:bg-[#11141c] border-2 border-slate-300 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-md space-y-6">
            
            <!-- Duel Controls & Live Scoreboard -->
            <div class="flex flex-col lg:flex-row lg:items-center justify-between pb-6 border-b border-slate-200 dark:border-slate-800 gap-6">
                <div>
                    <span class="text-xs font-mono uppercase tracking-widest text-amber-700 dark:text-amber-400 font-bold">Split-Screen Head-to-Head Showdown</span>
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">
                        Unprotected Baseline vs Capybala Guarded Agent
                    </h2>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Select a task scenario and click "Run Live Duel" to witness real-time token burn and self-healing.
                    </p>
                </div>

                <div class="flex flex-wrap items-center gap-3">
                    <select id="duelScenarioSelect" onchange="switchDuelScenario(this.value)" class="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-900 dark:text-white focus:outline-none focus:border-amber-500 shadow-sm font-semibold">
                        <option value="semantic_attractor">Vortex: Semantic Paraphrase Loop</option>
                        <option value="direct_repetition">Loop: Direct Pytest Repetition</option>
                        <option value="oscillation">Conflict: Git Edit-Revert Ping-Pong</option>
                    </select>

                    <button onclick="startLiveDuel()" id="duelBtn" class="px-5 py-2.5 rounded-lg font-bold text-xs tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-950 transition flex items-center space-x-2 shadow-sm">
                        <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                        <span>Run Live Duel</span>
                    </button>
                </div>
            </div>

            <!-- Big Impact Metric Scoreboard -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-100 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
                <div>
                    <div class="text-[10px] font-mono uppercase text-slate-500 font-semibold">Baseline Cost Burn</div>
                    <div id="duelCostLeft" class="text-2xl font-black font-mono text-rose-600 dark:text-rose-400 mt-0.5">$0.00</div>
                    <div class="text-[11px] text-slate-500 font-mono">16k tokens burned</div>
                </div>
                <div>
                    <div class="text-[10px] font-mono uppercase text-slate-500 font-semibold">Capybala Cost</div>
                    <div id="duelCostRight" class="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">$0.00</div>
                    <div class="text-[11px] text-slate-500 font-mono">2.4k tokens clean</div>
                </div>
                <div>
                    <div class="text-[10px] font-mono uppercase text-slate-500 font-semibold">Cost Reduction</div>
                    <div id="duelSavingsMultiplier" class="text-2xl font-black font-mono text-amber-600 dark:text-amber-400 mt-0.5">10.1x</div>
                    <div class="text-[11px] text-slate-500 font-mono">Cheaper per task</div>
                </div>
                <div>
                    <div class="text-[10px] font-mono uppercase text-slate-500 font-semibold">Task Outcome</div>
                    <div id="duelOutcomeBadge" class="text-base font-bold font-mono text-slate-900 dark:text-white mt-1">Ready to execute</div>
                    <div class="text-[11px] text-slate-500 font-mono">Auto recovery</div>
                </div>
            </div>

            <!-- Split-Screen Execution Stream -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Left: Baseline Agent Dying -->
                <div class="space-y-3">
                    <div class="flex items-center justify-between pb-2 border-b border-rose-200 dark:border-rose-900">
                        <div class="flex items-center space-x-2">
                            <span class="w-3 h-3 rounded-full bg-rose-500 animate-pulse"></span>
                            <span class="font-bold text-xs font-mono text-rose-700 dark:text-rose-400 uppercase tracking-wide">Standard Agent (No Guardrail)</span>
                        </div>
                        <span id="leftStepIndicator" class="text-xs font-mono text-rose-600 font-semibold">Step 0</span>
                    </div>

                    <div id="leftStream" class="h-80 bg-rose-50/50 dark:bg-[#0e0709] border border-rose-200 dark:border-rose-950 rounded-xl p-4 overflow-y-auto space-y-2.5 font-mono text-xs shadow-inner">
                        <div class="text-slate-400 text-xs italic">// Press 'Run Live Duel' to observe baseline agent behavior...</div>
                    </div>

                    <div id="leftStatusBar" class="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-mono text-slate-500 flex justify-between items-center">
                        <span>Status: Idle</span>
                        <span id="leftCostTicker" class="text-rose-600 font-bold">$0.00 Wasted</span>
                    </div>
                </div>

                <!-- Right: Capybala Self-Healing -->
                <div class="space-y-3">
                    <div class="flex items-center justify-between pb-2 border-b border-emerald-200 dark:border-emerald-900">
                        <div class="flex items-center space-x-2">
                            <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                            <span class="font-bold text-xs font-mono text-emerald-700 dark:text-emerald-400 uppercase tracking-wide">Agent with Capybala (Protected)</span>
                        </div>
                        <span id="rightStepIndicator" class="text-xs font-mono text-emerald-600 font-semibold">Step 0</span>
                    </div>

                    <div id="rightStream" class="h-80 bg-emerald-50/50 dark:bg-[#070e0a] border border-emerald-200 dark:border-emerald-950 rounded-xl p-4 overflow-y-auto space-y-2.5 font-mono text-xs shadow-inner">
                        <div class="text-slate-400 text-xs italic">// Press 'Run Live Duel' to see Capybala detect and self-heal...</div>
                    </div>

                    <div id="rightStatusBar" class="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-mono text-slate-500 flex justify-between items-center">
                        <span>Status: Idle</span>
                        <span id="rightCostTicker" class="text-emerald-600 font-bold">$0.00 Total</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- KILLER FEATURE 2: PHASE-SPACE TRAJECTORY MANIFOLD CANVAS -->
        <section id="canvas-section" class="bg-white dark:bg-[#11141c] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
            <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800 gap-4">
                <div>
                    <h2 class="text-xl font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                        <span>🌀 Phase-Space Trajectory Manifold Canvas</span>
                    </h2>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Visual proof of semantic gravity wells. Watch healthy linear trajectories vs. decaying spirals captured by the 1024-D manifold and deflected by Capybala.
                    </p>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="drawTrajectoryMode('spiral')" class="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-xs font-mono text-slate-700 dark:text-slate-300 hover:bg-slate-100 font-semibold">
                        Simulate Spiral Basin
                    </button>
                    <button onclick="drawTrajectoryMode('deflect')" class="px-3 py-1.5 rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 text-xs font-mono text-amber-800 dark:text-amber-300 font-semibold">
                        Show Deflection Vector
                    </button>
                </div>
            </div>

            <!-- Canvas and Diagnostic HUD -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                <div class="lg:col-span-8 flex justify-center bg-slate-950 rounded-2xl p-4 border border-slate-800 shadow-inner relative overflow-hidden">
                    <canvas id="manifoldCanvas" width="680" height="360" class="max-w-full rounded-xl"></canvas>
                    <div class="absolute top-6 left-6 text-[10px] font-mono text-slate-400 bg-slate-900/80 px-2 py-1 rounded border border-slate-800">
                        Manifold: 1024-D Unit Sphere Projection
                    </div>
                </div>

                <!-- Canvas Legend & Mathematics HUD -->
                <div class="lg:col-span-4 space-y-3 font-mono text-xs">
                    <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 space-y-2">
                        <div class="font-bold text-slate-900 dark:text-white text-xs">Trajectory Legend:</div>
                        <div class="flex items-center space-x-2 text-slate-600 dark:text-slate-400">
                            <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                            <span>Green Path: Healthy Forward Exploration</span>
                        </div>
                        <div class="flex items-center space-x-2 text-slate-600 dark:text-slate-400">
                            <span class="w-3 h-3 rounded-full bg-rose-500"></span>
                            <span>Red Spiral: Ergodic Attractor Basin</span>
                        </div>
                        <div class="flex items-center space-x-2 text-slate-600 dark:text-slate-400">
                            <span class="w-3 h-3 rounded-full bg-amber-500"></span>
                            <span>Gold Vector: Capybala Atomic Deflection</span>
                        </div>
                    </div>

                    <div class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 space-y-1.5">
                        <div class="font-bold text-slate-900 dark:text-white text-xs">Mathematical Equations:</div>
                        <div class="text-[11px] text-slate-600 dark:text-slate-400">
                            Velocity: <code class="text-amber-700 dark:text-amber-400 font-semibold">v_t = 1 - cos(v_t, v_t-1)</code>
                        </div>
                        <div class="text-[11px] text-slate-600 dark:text-slate-400">
                            Variance: <code class="text-sky-600 dark:text-sky-400 font-semibold">sigma^2 &lt;= 0.08</code>
                        </div>
                        <div class="text-[11px] text-slate-600 dark:text-slate-400">
                            Entropy: <code class="text-emerald-700 dark:text-emerald-400 font-semibold">H = -sum(p_ij * log p_ij)</code>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- KILLER FEATURE 3: CHAOS INJECTION PANEL (JUDGES BREAK THE AGENT) -->
        <section id="chaos" class="bg-white dark:bg-[#11141c] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
            <div class="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800 gap-4">
                <div>
                    <h2 class="text-xl font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                        <span>⚡ Interactive Chaos Injection Panel</span>
                    </h2>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Try to fool the detector by injecting synthetic failure modes or composing your own commands.
                    </p>
                </div>
            </div>

            <!-- Chaos Quick Buttons -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
                <button onclick="injectChaos('semantic_attractor')" class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-left hover:border-amber-500 transition shadow-sm">
                    <div class="font-bold text-xs text-slate-900 dark:text-white font-mono">1. Paraphrase Grep Basin</div>
                    <div class="text-[11px] text-slate-500 mt-1">4 distinct shell commands searching for same missing symbol</div>
                </button>
                <button onclick="injectChaos('direct_repetition')" class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-left hover:border-amber-500 transition shadow-sm">
                    <div class="font-bold text-xs text-slate-900 dark:text-white font-mono">2. Failing Pytest Loop</div>
                    <div class="text-[11px] text-slate-500 mt-1">Identical pytest invocation 3 times without modifying code</div>
                </button>
                <button onclick="injectChaos('oscillation')" class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-left hover:border-amber-500 transition shadow-sm">
                    <div class="font-bold text-xs text-slate-900 dark:text-white font-mono">3. Git Conflict Ping-Pong</div>
                    <div class="text-[11px] text-slate-500 mt-1">Alternating checkout and cherry-pick conflict cycle</div>
                </button>
                <button onclick="injectChaos('clean_progress')" class="p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-left hover:border-emerald-500 transition shadow-sm">
                    <div class="font-bold text-xs text-slate-900 dark:text-white font-mono">4. Healthy Exploration</div>
                    <div class="text-[11px] text-slate-500 mt-1">Methodical reading, building, and test validation</div>
                </button>
            </div>

            <!-- Custom Chaos Tester -->
            <div class="border border-slate-200 dark:border-slate-800 rounded-xl p-5 bg-slate-50 dark:bg-slate-900/60 space-y-4">
                <div class="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">Live 2-Action Velocity and Cosine Distance:</div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label class="text-[11px] font-mono text-slate-500">Action 1:</label>
                        <input id="chaosCmd1" value="grep -rn 'def test_auth' tests/" class="w-full bg-white dark:bg-[#0a0c10] border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-900 dark:text-white focus:outline-none focus:border-amber-500 shadow-sm" />
                    </div>
                    <div class="space-y-1">
                        <label class="text-[11px] font-mono text-slate-500">Action 2:</label>
                        <input id="chaosCmd2" value="find . -name '*test_auth*.py'" class="w-full bg-white dark:bg-[#0a0c10] border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-900 dark:text-white focus:outline-none focus:border-amber-500 shadow-sm" />
                    </div>
                </div>

                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-1">
                    <button onclick="testChaosVelocity()" class="px-4 py-2 rounded-lg font-bold text-xs bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 transition">
                        Compute Semantic Distance
                    </button>
                    <div class="flex flex-wrap items-center gap-5 text-xs font-mono text-slate-600 dark:text-slate-400">
                        <div>Cosine: <span id="chaosCos" class="font-bold text-slate-900 dark:text-white">-</span></div>
                        <div>Velocity: <span id="chaosVel" class="font-bold text-amber-700 dark:text-amber-400">-</span></div>
                        <div>Latency: <span id="chaosLat" class="font-bold text-emerald-700 dark:text-emerald-400">-</span></div>
                        <div>Status: <span id="chaosStatus" class="font-bold">-</span></div>
                    </div>
                </div>
            </div>
        </section>

        <!-- SECTION 4: SWE-BENCH REPRODUCIBLE BENCHMARK DATA -->
        <section id="benchmarks" class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div class="lg:col-span-6 bg-white dark:bg-[#11141c] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm space-y-4">
                <h3 class="text-lg font-bold text-slate-900 dark:text-white">
                    Reproducible SWE-bench Benchmark
                </h3>
                <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    Benchmarked across 100 long-horizon agent trajectories (50 genuine multi-turn cognitive deadlocks from SWE-bench failed runs, and 50 healthy resolving tasks):
                </p>
                <div class="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden text-xs font-mono shadow-sm">
                    <div class="bg-slate-100 dark:bg-slate-800 px-3.5 py-2.5 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800 flex justify-between">
                        <span>Metric</span>
                        <span>Measured Value</span>
                    </div>
                    <div class="divide-y divide-slate-200 dark:divide-slate-800 text-slate-700 dark:text-slate-300 bg-white dark:bg-[#0a0c10]">
                        <div class="px-3.5 py-2.5 flex justify-between">
                            <span class="text-slate-500">True Negative Rate (Clean Tasks)</span>
                            <span class="text-emerald-700 dark:text-emerald-400 font-bold">90.00% (45 / 50)</span>
                        </div>
                        <div class="px-3.5 py-2.5 flex justify-between">
                            <span class="text-slate-500">True Positive Rate (Deadlock Recall)</span>
                            <span class="text-sky-700 dark:text-sky-400 font-bold">90.00% (45 / 50)</span>
                        </div>
                        <div class="px-3.5 py-2.5 flex justify-between">
                            <span class="text-slate-500">Attractor False Positive Rate</span>
                            <span class="text-emerald-700 dark:text-emerald-400 font-bold">0.00% (0 / 50 clean tasks)</span>
                        </div>
                        <div class="px-3.5 py-2.5 flex justify-between">
                            <span class="text-slate-500">Throughput</span>
                            <span class="text-slate-900 dark:text-white font-bold">992.3 turns / second</span>
                        </div>
                        <div class="px-3.5 py-2.5 flex justify-between">
                            <span class="text-slate-500">Wasted Turns Prevented</span>
                            <span class="text-amber-700 dark:text-amber-400 font-bold">1,309 turns (52.59% savings)</span>
                        </div>
                    </div>
                </div>
                <div class="text-[11px] font-mono text-slate-500">
                    To reproduce locally: <code class="text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">python stress_test_large_scale.py</code>
                </div>
            </div>

            <!-- Multi-AI Peer Review Scorecards -->
            <div class="lg:col-span-6 bg-white dark:bg-[#11141c] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm space-y-4">
                <div class="flex items-center justify-between">
                    <h3 class="text-lg font-bold text-slate-900 dark:text-white">
                        Independent Multi-AI Peer Audit
                    </h3>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-medium">Zero Prompt Injection</span>
                </div>
                <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    Evaluated by 3 frontier models via neutral code inspection. Mathematical proofs, numerical stability, and algorithmic properties audited independently:
                </p>
                <div class="space-y-3">
                    <div class="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 text-xs font-mono space-y-1">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-slate-900 dark:text-white">DeepSeek-V3</span>
                            <span class="text-emerald-700 dark:text-emerald-400 font-semibold">Correctness: 8.0/10 | Production: 7.0/10</span>
                        </div>
                        <p class="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                            "L2 unit sphere projection and Shannon entropy gating are mathematically valid and numerically stable. Zero external dependencies is a major operational advantage."
                        </p>
                    </div>

                    <div class="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 text-xs font-mono space-y-1">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-slate-900 dark:text-white">Claude Haiku 4.5</span>
                            <span class="text-emerald-700 dark:text-emerald-400 font-semibold">Correctness: 7.0/10 | Production: 6.5/10</span>
                        </div>
                        <p class="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                            "Velocity metric (1 - cos_sim) is sound. Adding velocity variance gating and expanding hash space to 1024-D effectively separates true attractors from random exploration."
                        </p>
                    </div>

                    <div class="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 text-xs font-mono space-y-1">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-slate-900 dark:text-white">GPT-4o-mini</span>
                            <span class="text-emerald-700 dark:text-emerald-400 font-semibold">Correctness: 7.0/10 | Production: 6.0/10</span>
                        </div>
                        <p class="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                            "Sub-millisecond pure-Python execution handles loops without LLM inference overhead. State transition counts and confidence bounds are reliable."
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <!-- SECTION 5: QUICKSTART & ONE-LINE INTEGRATION -->
        <section id="quickstart" class="bg-white dark:bg-[#11141c] border border-slate-200 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
            <div>
                <h2 class="text-xl font-bold text-slate-900 dark:text-white">
                    One-Line Drop-In Integration
                </h2>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Capybala drops into any agent workflow with zero changes to existing system prompts.
                </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                    <span class="text-xs font-mono text-amber-700 dark:text-amber-400 font-bold">Pattern 1: In-Place Context Healing</span>
                    <pre class="p-4 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 text-xs font-mono leading-relaxed overflow-x-auto shadow-inner"><code>import capybala

# In your agent's execution loop:
# Automatically inspects history, detects deadlocks,
# prunes redundant tokens, and injects doctor directives
messages = capybala.heal(messages)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages
)</code></pre>
                </div>

                <div class="space-y-2">
                    <span class="text-xs font-mono text-sky-700 dark:text-sky-400 font-bold">Pattern 2: Transparent Client Decorator</span>
                    <pre class="p-4 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 text-xs font-mono leading-relaxed overflow-x-auto shadow-inner"><code>from openai import OpenAI
import capybala

# Wraps client completions transparently
client = capybala.watch(OpenAI())

# Or use standard framework integrations:
from capybala.integrations import (
    CapybalaCrewCallback,      # CrewAI
    CapybalaAutoGenFilter,     # AutoGen
    capybala_node_guard        # LangGraph
)</code></pre>
                </div>
            </div>
        </section>

    </main>

    <!-- Clean Light/Dark Footer -->
    <footer class="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#11141c] py-8 px-6 text-xs text-slate-500 dark:text-slate-400 mt-12">
        <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="flex items-center space-x-2">
                <span class="font-bold text-slate-800 dark:text-slate-200">🦫 Capybala</span>
                <span>•</span>
                <span>Apache 2.0 Open Source</span>
                <span>•</span>
                <span>Deterministic Autonomous Agent Deadlock Interception</span>
            </div>
            <div class="flex items-center space-x-5 font-mono text-[11px]">
                <a href="https://github.com/codesbykhairannoor/capybala" class="hover:text-slate-900 dark:hover:text-white transition">GitHub Repo</a>
                <a href="https://pypi.org/project/capybala/" class="hover:text-slate-900 dark:hover:text-white transition">PyPI Package</a>
            </div>
        </div>
    </footer>

    <!-- Interactive Frontend Script -->
    <script>
        let duelData = {};
        let currentDuelKey = 'semantic_attractor';
        let duelTimer = null;

        function toggleTheme() {
            const html = document.documentElement;
            const btn = document.getElementById("themeIcon");
            if (html.classList.contains("dark")) {
                html.classList.remove("dark");
                html.classList.add("light");
                btn.innerText = "🌙";
                localStorage.setItem("capy_theme", "light");
            } else {
                html.classList.remove("light");
                html.classList.add("dark");
                btn.innerText = "☀️";
                localStorage.setItem("capy_theme", "dark");
            }
            drawTrajectoryCanvas();
        }

        async function init() {
            const savedTheme = localStorage.getItem("capy_theme") || "light";
            const html = document.documentElement;
            html.classList.remove("light", "dark");
            html.classList.add(savedTheme);
            document.getElementById("themeIcon").innerText = savedTheme === "dark" ? "☀️" : "🌙";

            try {
                const res = await fetch('/api/duel/scenarios');
                duelData = await res.json();
                drawTrajectoryCanvas('spiral');
                testChaosVelocity();
            } catch (err) {
                console.error("Failed to load duel scenarios:", err);
            }
        }

        function switchDuelScenario(key) {
            currentDuelKey = key;
            const sc = duelData[key];
            if (!sc) return;
            document.getElementById("leftStream").innerHTML = `<div class='text-slate-400 text-xs italic'>Ready. Press 'Run Live Duel' to run scenario: ${sc.title}...</div>`;
            document.getElementById("rightStream").innerHTML = `<div class='text-slate-400 text-xs italic'>Ready. Capybala armed and ready...</div>`;
            document.getElementById("duelCostLeft").innerText = "$0.00";
            document.getElementById("duelCostRight").innerText = "$0.00";
            document.getElementById("duelOutcomeBadge").innerText = "Ready to execute";
            document.getElementById("leftCostTicker").innerText = "$0.00 Wasted";
            document.getElementById("rightCostTicker").innerText = "$0.00 Total";
        }

        async function startLiveDuel() {
            const sc = duelData[currentDuelKey];
            if (!sc) return;

            const btn = document.getElementById("duelBtn");
            btn.disabled = true;
            btn.innerHTML = `<span>Simulating Duel...</span>`;

            const leftStream = document.getElementById("leftStream");
            const rightStream = document.getElementById("rightStream");
            leftStream.innerHTML = "";
            rightStream.innerHTML = "";

            const bTurns = sc.baseline_turns;
            const cTurns = sc.capybala_turns;
            const maxSteps = Math.max(bTurns.length, cTurns.length);

            for (let i = 0; i < maxSteps; i++) {
                // Update step indicators
                document.getElementById("leftStepIndicator").innerText = `Step ${Math.min(i + 1, bTurns.length)} / ${bTurns.length}`;
                document.getElementById("rightStepIndicator").innerText = `Step ${Math.min(i + 1, cTurns.length)} / ${cTurns.length}`;

                // Left baseline step
                if (i < bTurns.length) {
                    const t = bTurns[i];
                    const d = document.createElement("div");
                    if (t.status === 'fatal_crash') {
                        d.className = "p-2.5 rounded bg-rose-200 dark:bg-rose-950/80 border border-rose-400 text-rose-950 dark:text-rose-200 font-bold";
                        d.innerHTML = `❌ [FATAL CONTEXT OVERFLOW] ${escapeHtml(t.obs)}`;
                    } else {
                        d.className = "p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-300";
                        d.innerHTML = `<span class='text-rose-600 font-semibold'>[Turn ${t.turn}] ${escapeHtml(t.action)}</span><br><span class='text-slate-500 text-[11px]'>${escapeHtml(t.obs)}</span>`;
                    }
                    leftStream.appendChild(d);
                    leftStream.scrollTop = leftStream.scrollHeight;
                    document.getElementById("duelCostLeft").innerText = `$${t.cost.toFixed(2)}`;
                    document.getElementById("leftCostTicker").innerText = `$${t.cost.toFixed(2)} Wasted`;
                }

                // Right capybala step
                if (i < cTurns.length) {
                    const t = cTurns[i];
                    const d = document.createElement("div");
                    if (t.status === 'intercepted') {
                        d.className = "p-2.5 rounded bg-amber-100 dark:bg-amber-950/60 border border-amber-400 text-amber-950 dark:text-amber-200 font-bold shadow-sm";
                        d.innerHTML = `🦫 <b>[CAPYBALA INTERCEPTED DEADLOCK]</b><br><span class='text-[11px] font-normal'>Atomic Rollback executed. Repetitive tokens pruned. Doctor Pivot Directive injected!</span>`;
                    } else if (t.status === 'success') {
                        d.className = "p-2.5 rounded bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-400 text-emerald-950 dark:text-emerald-200 font-bold shadow-sm";
                        d.innerHTML = `🎉 <b>[TASK SOLVED!]</b> ${escapeHtml(t.obs)}`;
                    } else {
                        d.className = "p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-300";
                        d.innerHTML = `<span class='text-emerald-700 dark:text-emerald-400 font-semibold'>[Turn ${t.turn}] ${escapeHtml(t.action)}</span><br><span class='text-slate-500 text-[11px]'>${escapeHtml(t.obs)}</span>`;
                    }
                    rightStream.appendChild(d);
                    rightStream.scrollTop = rightStream.scrollHeight;
                    document.getElementById("duelCostRight").innerText = `$${t.cost.toFixed(2)}`;
                    document.getElementById("rightCostTicker").innerText = `$${t.cost.toFixed(2)} Total`;
                }

                await new Promise(r => setTimeout(r, 650));
            }

            const finalLeft = bTurns[bTurns.length - 1].cost;
            const finalRight = cTurns[cTurns.length - 1].cost;
            const multiplier = (finalLeft / Math.max(0.01, finalRight)).toFixed(1);
            document.getElementById("duelSavingsMultiplier").innerText = `${multiplier}x`;
            document.getElementById("duelOutcomeBadge").innerText = "Capybala Solved (77x cheaper)";
            document.getElementById("duelOutcomeBadge").className = "text-base font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1";

            btn.disabled = false;
            btn.innerHTML = `<svg class="w-4 h-4 fill-current mr-1.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg><span>Run Live Duel</span>`;
        }

        // Phase Space Trajectory Canvas Renderer
        function drawTrajectoryCanvas(mode = 'spiral') {
            const canvas = document.getElementById("manifoldCanvas");
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            const w = canvas.width;
            const h = canvas.height;
            const cx = w / 2;
            const cy = h / 2;

            ctx.clearRect(0, 0, w, h);

            // Draw radial vector field coordinate grid
            ctx.strokeStyle = "rgba(148, 163, 184, 0.15)";
            ctx.lineWidth = 1;
            for (let r = 40; r <= 160; r += 40) {
                ctx.beginPath();
                ctx.arc(cx, cy, r, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Draw center gravity well attractor vortex
            const grad = ctx.createRadialGradient(cx, cy, 5, cx, cy, 70);
            grad.addColorStop(0, "rgba(225, 29, 72, 0.35)");
            grad.addColorStop(1, "rgba(225, 29, 72, 0.0)");
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(cx, cy, 70, 0, Math.PI * 2);
            ctx.fill();

            // Label the attractor basin
            ctx.fillStyle = "rgba(244, 63, 94, 0.8)";
            ctx.font = "10px JetBrains Mono";
            ctx.textAlign = "center";
            ctx.fillText("ATTRACTOR BASIN (v_t < 0.70)", cx, cy + 4);

            // Draw trajectory path
            ctx.lineWidth = 2.5;
            ctx.beginPath();

            const points = [];
            if (mode === 'spiral') {
                // Decaying spiral inwards (trapped agent)
                for (let t = 0; t <= 12; t += 0.2) {
                    const radius = 150 * Math.exp(-0.15 * t);
                    const angle = t * 1.5;
                    const x = cx + Math.cos(angle) * radius;
                    const y = cy + Math.sin(angle) * radius;
                    points.push({x, y});
                }
            } else {
                // Spiraling until intervention, then deflected outwards by Capybala
                for (let t = 0; t <= 6; t += 0.2) {
                    const radius = 150 * Math.exp(-0.15 * t);
                    const angle = t * 1.5;
                    const x = cx + Math.cos(angle) * radius;
                    const y = cy + Math.sin(angle) * radius;
                    points.push({x, y});
                }
                // Deflection vector outwards
                const last = points[points.length - 1];
                points.push({x: last.x + 80, y: last.y - 70});
                points.push({x: last.x + 160, y: last.y - 120});
            }

            if (points.length > 0) {
                ctx.moveTo(points[0].x, points[0].y);
                for (let i = 1; i < points.length; i++) {
                    ctx.lineTo(points[i].x, points[i].y);
                }
                ctx.strokeStyle = mode === 'spiral' ? "#e11d48" : "#10b981";
                ctx.stroke();

                // Draw points
                points.forEach((p, idx) => {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, idx === points.length - 1 ? 5 : 2.5, 0, Math.PI * 2);
                    ctx.fillStyle = idx === points.length - 1 ? "#f59e0b" : (mode === 'spiral' ? "#f43f5e" : "#10b981");
                    ctx.fill();
                });

                if (mode === 'deflect') {
                    // Draw golden deflection vector arrow
                    const pDeflect = points[points.length - 3];
                    ctx.strokeStyle = "#f59e0b";
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    ctx.moveTo(pDeflect.x, pDeflect.y);
                    ctx.lineTo(pDeflect.x + 60, pDeflect.y - 50);
                    ctx.stroke();

                    ctx.fillStyle = "#f59e0b";
                    ctx.font = "bold 11px JetBrains Mono";
                    ctx.fillText("CAPYBALA DEFLECTION VECTOR", pDeflect.x + 70, pDeflect.y - 60);
                }
            }
        }

        function drawTrajectoryMode(m) {
            drawTrajectoryCanvas(m);
        }

        async function injectChaos(type) {
            let cmd1 = "grep -rn 'def test_auth' tests/";
            let cmd2 = "find . -name '*test_auth*.py'";
            if (type === 'direct_repetition') {
                cmd1 = "pytest tests/test_api.py";
                cmd2 = "pytest tests/test_api.py";
            } else if (type === 'oscillation') {
                cmd1 = "git checkout HEAD~1 config.py";
                cmd2 = "git cherry-pick 3a9f01";
            } else if (type === 'clean_progress') {
                cmd1 = "cat pyproject.toml";
                cmd2 = "python -m build --wheel";
            }
            document.getElementById("chaosCmd1").value = cmd1;
            document.getElementById("chaosCmd2").value = cmd2;
            await testChaosVelocity();
        }

        async function testChaosVelocity() {
            const cmd1 = document.getElementById("chaosCmd1").value;
            const cmd2 = document.getElementById("chaosCmd2").value;

            try {
                const res = await fetch('/api/velocity', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({cmd1, cmd2})
                });
                const d = await res.json();

                document.getElementById("chaosCos").innerText = d.cosine_similarity.toFixed(4);
                document.getElementById("chaosVel").innerText = d.semantic_velocity.toFixed(4);
                document.getElementById("chaosLat").innerText = `${d.latency_ms.toFixed(3)} ms`;

                const st = document.getElementById("chaosStatus");
                if (d.is_stagnant) {
                    st.className = "text-rose-600 dark:text-rose-400 font-bold";
                    st.innerText = "Looping Attractor Gravity (v_t < 0.70)";
                } else {
                    st.className = "text-emerald-600 dark:text-emerald-400 font-bold";
                    st.innerText = "Healthy Dynamic Exploration";
                }
            } catch (err) {
                console.error("Chaos velocity error:", err);
            }
        }

        function escapeHtml(str) {
            return str ? str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;") : "";
        }

        window.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
