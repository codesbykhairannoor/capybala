"""
web.app
~~~~~~~
FastAPI Modular Application Server for Capybala.
Production-Grade AI Agent Debugger, Context Profiler & Healing Engine.
"""

import os
import sys
import copy
import json
import time
import math
import random
from typing import Dict, Any, List, Optional
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
from capybala.validator import SchemaValidator
from web.scenarios import DUEL_SCENARIOS, DEBUGGER_PRESETS

# Deterministic orthonormal-like pseudo-random weights for Johnson-Lindenstrauss
# 1024-D -> 2D unit sphere projection (Pure Python, Sub-microsecond)
_PROJ_RNG = random.Random(42)
_WX = [_PROJ_RNG.gauss(0, 1) for _ in range(1024)]
_WY = [_PROJ_RNG.gauss(0, 1) for _ in range(1024)]

# Normalize projection basis vectors
_norm_x = math.sqrt(sum(w * w for w in _WX)) or 1.0
_norm_y = math.sqrt(sum(w * w for w in _WY)) or 1.0
PROJ_WX = [w / _norm_x for w in _WX]
PROJ_WY = [w / _norm_y for w in _WY]


def project_1024d_to_2d(vec: List[float]) -> Dict[str, float]:
    """Projects a 1024-D unit sphere feature vector to 2D coordinates in range [-1.5, 1.5]."""
    if not vec or len(vec) != 1024:
        return {"x": 0.0, "y": 0.0}
    x = sum(v * w for v, w in zip(vec, PROJ_WX))
    y = sum(v * w for v, w in zip(vec, PROJ_WY))
    return {"x": round(x * 1.5, 4), "y": round(y * 1.5, 4)}


def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """Rough token estimation (~4 chars per token + tool call payload)."""
    chars = 0
    for m in messages:
        chars += len(str(m.get("role", "")))
        chars += len(str(m.get("content", "") or ""))
        if "tool_calls" in m:
            chars += len(str(m["tool_calls"]))
        if "tool_call_id" in m:
            chars += len(str(m["tool_call_id"]))
    return max(1, chars // 4)


app = FastAPI(
    title="Capybala Agent Guardrail",
    description="Deterministic deadlock detection, surgical self-healing, and context profiler.",
    version="0.8.0"
)

# Mount static assets directory (CSS & JS)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Renders the modular, developer-grade UI template."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/presets")
async def get_debugger_presets():
    """Returns curated production-grade conversation failure datasets."""
    return DEBUGGER_PRESETS


@app.get("/api/duel/scenarios")
async def get_duel_scenarios():
    """Returns curated benchmark scenarios for the live split-screen duel."""
    return DUEL_SCENARIOS


@app.post("/api/heal")
async def heal_conversation(request: Request):
    """
    Core Production Endpoint: Takes real conversation JSON (OpenAI/Anthropic),
    executes live DeadlockDetector, SemanticAttractor, and ContextPruner surgery,
    and returns surgical before/after diffs with zero-token-burn metrics.
    """
    body = await request.json()
    raw_messages = body.get("messages", [])
    provider = str(body.get("provider", "openai")).lower()
    repetition_threshold = int(body.get("repetition_threshold", 3))

    if not isinstance(raw_messages, list) or len(raw_messages) == 0:
        return JSONResponse({"error": "Empty or invalid messages list provided"}, status_code=400)

    # Clone messages to preserve original
    messages_copy = copy.deepcopy(raw_messages)
    tokens_before = estimate_tokens(messages_copy)

    # 1. Parse turn sequence compliant with OpenAI & Anthropic schemas
    turns_sequence = []
    tool_call_map = {}
    tool_name_map = {}

    for msg in messages_copy:
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Anthropic content blocks
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    b_type = block.get("type")
                    if b_type == "tool_use":
                        call_id = block.get("id") or f"call_{len(tool_call_map)}"
                        fn_name = block.get("name", "tool")
                        fn_args = block.get("input", {})
                        arg_str = json.dumps(fn_args, sort_keys=True) if isinstance(fn_args, (dict, list)) else str(fn_args)
                        act_str = f"{fn_name}({arg_str})"
                        tool_call_map[call_id] = act_str
                        tool_name_map.setdefault(fn_name, []).append(act_str)
                    elif b_type == "tool_result":
                        tid = block.get("tool_use_id") or block.get("id")
                        act = tool_call_map.get(tid)
                        if not act and tid in tool_name_map and tool_name_map[tid]:
                            act = tool_name_map[tid].pop(0)
                        elif not act and tool_call_map:
                            act = list(tool_call_map.values())[-1]
                        act = act or "tool_execution"
                        turns_sequence.append((act, str(block.get("content", ""))))
            continue

        # OpenAI tool_calls
        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict):
                    call_id = tc.get("id") or f"call_{len(tool_call_map)}"
                    fn = tc.get("function", {})
                    fn_name = fn.get("name", "tool")
                    action_str = f"{fn_name}({fn.get('arguments', '')})"
                    tool_call_map[call_id] = action_str
                    tool_name_map.setdefault(fn_name, []).append(action_str)
        elif role in ("tool", "tool_response"):
            tid = msg.get("tool_call_id")
            act = tool_call_map.get(tid)
            if not act and tid in tool_name_map and tool_name_map[tid]:
                act = tool_name_map[tid].pop(0)
            elif not act and tool_call_map:
                act = list(tool_call_map.values())[-1]
            act = act or "tool_execution"
            turns_sequence.append((act, str(content)))
        elif role in ("assistant", "model"):
            turns_sequence.append((str(content), ""))
        elif role in ("system", "user") and turns_sequence:
            prev_act, _ = turns_sequence[-1]
            turns_sequence[-1] = (prev_act, str(content))

    detector = DeadlockDetector(
        repetition_threshold=repetition_threshold,
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
    pruner = ContextPruner()
    healer = AgentHealer()

    t_start = time.perf_counter()

    deadlock_detected = False
    deadlock_type = "NONE"
    deadlock_details = ""
    failing_action = ""
    last_obs = ""
    repetition_count = 0

    for action, obs in turns_sequence:
        if action:
            failing_action = action
            last_obs = obs
            # Check attractor
            is_attr, _, attr_msg = attractor.inspect_step(action, is_failing=False)
            event = detector.check(action, obs)
            if event.is_deadlock or is_attr:
                deadlock_detected = True
                deadlock_type = event.pattern_type if event.is_deadlock else "SEMANTIC_ATTRACTOR"
                deadlock_details = event.details if event.is_deadlock else attr_msg
                repetition_count = event.repetition_count
                break

    prescription = None
    healing_prompt = ""

    if deadlock_detected:
        prescription = healer.prescribe(
            deadlock_pattern=deadlock_type,
            failing_action=failing_action,
            error_signature=deadlock_details or last_obs,
            target_provider=provider,
            escalation_level=1
        )
        healing_prompt = prescription.recommended_pivot
        rollback_res = pruner.rollback_and_reflect(
            messages=messages_copy,
            failing_action=failing_action,
            deadlock_details=deadlock_details,
            reflection_guidance=healing_prompt,
            provider=provider,
            rollback_turns=repetition_threshold * 2
        )
        healed_messages = rollback_res.pruned_messages
    else:
        healed_messages, _ = SchemaValidator().validate_and_repair(messages_copy, provider=provider)

    latency_ms = (time.perf_counter() - t_start) * 1000.0
    tokens_after = estimate_tokens(healed_messages)
    tokens_saved = max(0, tokens_before - tokens_after)
    percent_saved = round((tokens_saved / max(1, tokens_before)) * 100.0, 1)
    cost_saved = round((tokens_saved / 1000.0) * 0.03, 4)

    return {
        "is_deadlock": deadlock_detected,
        "deadlock_type": deadlock_type,
        "details": deadlock_details,
        "repetition_count": repetition_count,
        "latency_ms": round(latency_ms, 3),
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "tokens_saved": tokens_saved,
        "percent_saved": percent_saved,
        "cost_saved_usd": cost_saved,
        "original_turn_count": len(raw_messages),
        "healed_turn_count": len(healed_messages),
        "original_messages": raw_messages,
        "healed_messages": healed_messages,
        "doctor_directive": healing_prompt,
        "escalation_level": prescription.escalation_level if prescription else 0
    }


@app.post("/api/step")
async def execute_agent_step(request: Request):
    """
    Interactive Sandbox Step Endpoint: Evaluates a single turn in an agent trajectory,
    computes real 1024-D projection coordinates, velocity, entropy, and deadlock status.
    """
    body = await request.json()
    action = str(body.get("action", "")).strip()
    obs = str(body.get("observation", "")).strip()
    is_failing = bool(body.get("fail", False))
    history = body.get("history", [])

    attractor = SemanticAttractorDetector()
    detector = DeadlockDetector(history_window=24, enable_attractor=True)
    healer = AgentHealer()

    # Replay prior history to seed detectors
    for past_turn in history:
        p_act = past_turn.get("action", "")
        p_obs = past_turn.get("observation", "")
        p_fail = past_turn.get("fail", False)
        if p_act:
            attractor.inspect_step(p_act, is_failing=p_fail)
            detector.check(current_action=p_act, observation=p_obs)

    t0 = time.perf_counter()
    vec = attractor._extract_feature_vector(action)
    is_attr, confidence, attr_msg = attractor.inspect_step(action, is_failing=is_failing)
    event = detector.check(current_action=action, observation=obs)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    curr_vel = list(attractor.velocity_history)[-1] if attractor.velocity_history else 1.0
    curr_entropy = (
        attractor._compute_markov_entropy(list(attractor.vector_history))
        if len(attractor.vector_history) >= 2
        else math.log(64)
    )

    coord_2d = project_1024d_to_2d(vec)
    is_deadlock = event.is_deadlock or is_attr
    deadlock_type = event.pattern_type if event.is_deadlock else ("SEMANTIC_ATTRACTOR" if is_attr else "NONE")
    deadlock_details = event.details if event.is_deadlock else attr_msg

    directive = ""
    if is_deadlock:
        rx = healer.prescribe(
            deadlock_pattern=deadlock_type,
            failing_action=action,
            error_signature=deadlock_details or obs
        )
        directive = rx.recommended_pivot

    return {
        "step_number": len(history) + 1,
        "action": action,
        "is_deadlock": is_deadlock,
        "deadlock_type": deadlock_type,
        "details": deadlock_details,
        "semantic_velocity": round(curr_vel, 4),
        "markov_entropy": round(curr_entropy, 3),
        "coord_2d": coord_2d,
        "latency_ms": round(latency_ms, 3),
        "directive": directive
    }


@app.post("/api/vector_projection")
async def get_vector_projections(request: Request):
    """Projects arbitrary actions into true 2D manifold coordinates."""
    body = await request.json()
    actions = body.get("actions", [])
    attractor = SemanticAttractorDetector()

    results = []
    for a in actions:
        v = attractor._extract_feature_vector(str(a))
        coord = project_1024d_to_2d(v)
        results.append({
            "action": a,
            "x": coord["x"],
            "y": coord["y"],
            "active_buckets": sum(1 for val in v if val > 0)
        })
    return {"points": results}


@app.post("/api/velocity")
async def calculate_velocity(request: Request):
    """Calculates live cosine similarity and semantic velocity between two command strings."""
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
