"""
web.app
~~~~~~~
FastAPI Modular Application Server for Capybala.
Connects the clean web front-end to Capybala's post-IF-ELSE detection engine.
"""

import os
import sys
import time
import math
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

# Ensure root workspace and capybala core package are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "capybala"))

from capybala.detector import DeadlockDetector
from capybala.attractor import SemanticAttractorDetector
from capybala.healer import AgentHealer
from capybala.pruner import ContextPruner
from web.scenarios import DUEL_SCENARIOS

app = FastAPI(
    title="Capybala Agent Guardrail",
    description="Deterministic deadlock detection and surgical self-healing.",
    version="0.8.0"
)

# Mount static assets directory (CSS & JS)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Renders the modular, clean-code developer UI template."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/duel/scenarios")
async def get_duel_scenarios():
    """Returns curated benchmark scenarios for the live split-screen duel."""
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

        telemetry.append({
            "step": idx + 1,
            "action": action,
            "observation_snippet": observation[:120] + ("..." if len(observation) > 120 else ""),
            "is_failing": fail_flag,
            "semantic_velocity": round(curr_vel, 4),
            "markov_entropy": round(curr_entropy, 3),
            "is_attractor": is_attr,
            "latency_ms": round(step_latency_ms, 3)
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

    return {
        "command_1": cmd1,
        "command_2": cmd2,
        "cosine_similarity": round(cos_sim, 4),
        "semantic_velocity": round(velocity, 4),
        "is_stagnant": velocity < attractor.velocity_threshold,
        "latency_ms": round(latency_ms, 3),
        "active_buckets_cmd1": sum(1 for val in v1 if val > 0),
        "active_buckets_cmd2": sum(1 for val in v2 if val > 0)
    }
