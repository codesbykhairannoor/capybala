/**
 * sandbox.js - Live Turn-by-Turn Agent Sandbox & Dynamical Telemetry HUD
 * Lets developers simulate an agent step-by-step, observing Semantic Velocity,
 * Markov Entropy, and 1024-D Manifold coordinates updating in real time.
 */

const SandboxEngine = {
    history: [],
    trajectoryPoints: [],

    init() {
        this.reset();
    },

    reset() {
        this.history = [];
        this.trajectoryPoints = [];

        const log = document.getElementById("sandboxStepLog");
        if (log) {
            log.innerHTML = `<div class="text-slate-400 text-xs italic p-4">// Ready. Submit an action or select a quick preset below to begin simulation...</div>`;
        }

        this.updateGauges(1.0, 4.16, 0.0);
        this.hideAlert();
        document.getElementById("sandboxStepCount").textContent = "Step 0";

        if (window.ManifoldCanvas) {
            ManifoldCanvas.clearPoints();
        }
    },

    setQuickAction(act, obs, fail) {
        document.getElementById("sandboxActionInput").value = act;
        document.getElementById("sandboxObsInput").value = obs;
        document.getElementById("sandboxFailCheck").checked = !!fail;
    },

    async submitStep() {
        const actInput = document.getElementById("sandboxActionInput");
        const obsInput = document.getElementById("sandboxObsInput");
        const failCheck = document.getElementById("sandboxFailCheck");
        const submitBtn = document.getElementById("sandboxSubmitBtn");

        const action = actInput ? actInput.value.trim() : "";
        const obs = obsInput ? obsInput.value.trim() : "";
        const isFailing = failCheck ? failCheck.checked : false;

        if (!action) {
            alert("Please provide an action string (e.g. pytest tests/ or grep symbol)");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>Computing Step...</span>`;

        try {
            const res = await fetch('/api/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: action,
                    observation: obs,
                    fail: isFailing,
                    history: this.history
                })
            });

            if (!res.ok) throw new Error("Step analysis failed: " + res.status);
            const stepData = await res.json();

            // Record into local history
            this.history.push({
                action: action,
                observation: obs,
                fail: isFailing,
                velocity: stepData.semantic_velocity,
                entropy: stepData.markov_entropy,
                coord: stepData.coord_2d,
                is_deadlock: stepData.is_deadlock
            });

            this.appendStepToLog(stepData);
            this.updateGauges(stepData.semantic_velocity, stepData.markov_entropy, stepData.latency_ms);
            document.getElementById("sandboxStepCount").textContent = `Step ${this.history.length}`;

            // Add real 1024-D projection to Manifold Canvas
            if (window.ManifoldCanvas && stepData.coord_2d) {
                ManifoldCanvas.addPoint(this.history.length, stepData.coord_2d.x, stepData.coord_2d.y, stepData.is_deadlock, action);
            }

            if (stepData.is_deadlock) {
                this.showAlert(stepData);
            } else {
                this.hideAlert();
            }

        } catch (err) {
            alert("Sandbox Step Error: " + err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `
                <svg class="w-4 h-4 fill-current mr-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                <span>Execute Step</span>
            `;
        }
    },

    appendStepToLog(step) {
        const log = document.getElementById("sandboxStepLog");
        if (!log) return;

        // Clear placeholder on first step
        if (this.history.length === 1) {
            log.innerHTML = "";
        }

        const stepDiv = document.createElement("div");
        stepDiv.className = `p-3 rounded-lg border font-mono text-xs transition space-y-1.5 shadow-sm ${
            step.is_deadlock
                ? "bg-rose-50 dark:bg-rose-950/40 border-rose-400 dark:border-rose-800"
                : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
        }`;

        const isLowVel = step.semantic_velocity < 0.70;
        const velBadgeClass = isLowVel ? "text-rose-600 dark:text-rose-400 font-bold" : "text-emerald-600 dark:text-emerald-400 font-semibold";

        stepDiv.innerHTML = `
            <div class="flex justify-between items-center pb-1 border-b border-slate-100 dark:border-slate-800">
                <span class="font-bold text-slate-900 dark:text-white">Turn ${step.step_number}</span>
                <div class="flex items-center space-x-2 text-[11px]">
                    <span class="${velBadgeClass}">v_t: ${step.semantic_velocity.toFixed(3)}</span>
                    <span class="text-slate-400">|</span>
                    <span class="text-sky-600 dark:text-sky-400">H: ${step.markov_entropy.toFixed(2)}</span>
                    <span class="text-slate-400">|</span>
                    <span class="text-slate-500">${step.latency_ms.toFixed(3)}ms</span>
                </div>
            </div>
            <div class="text-slate-800 dark:text-slate-200 font-semibold truncate"><span class="text-amber-600 font-bold">&gt;</span> ${this.escapeHtml(step.action)}</div>
            ${step.details ? `<div class="text-[11px] text-slate-500 dark:text-slate-400 truncate">${this.escapeHtml(step.details)}</div>` : ''}
            ${step.is_deadlock ? `
                <div class="mt-2 p-2 rounded bg-rose-100 dark:bg-rose-950/80 border border-rose-300 text-rose-900 dark:text-rose-200 text-[11px] font-bold">
                    🚨 [DEADLOCK TRIPPED]: ${step.deadlock_type} (${step.details})
                </div>
            ` : ''}
        `;

        log.appendChild(stepDiv);
        log.scrollTop = log.scrollHeight;
    },

    updateGauges(vel, entropy, lat) {
        // Semantic Velocity Gauge (0.0 to 2.0 scale)
        const velVal = document.getElementById("gaugeVelVal");
        const velBar = document.getElementById("gaugeVelBar");
        const velStatus = document.getElementById("gaugeVelStatus");

        if (velVal) velVal.textContent = vel.toFixed(3);
        if (velBar) {
            const pct = Math.min(100, Math.max(0, (vel / 2.0) * 100));
            velBar.style.width = `${pct}%`;
            if (vel < 0.70) {
                velBar.className = "h-2 rounded-full bg-rose-500 transition-all duration-300";
                if (velStatus) {
                    velStatus.textContent = "STAGNANT / ATTRACTOR BASIN (v_t < 0.70)";
                    velStatus.className = "text-[10px] font-mono font-bold text-rose-600 dark:text-rose-400";
                }
            } else {
                velBar.className = "h-2 rounded-full bg-emerald-500 transition-all duration-300";
                if (velStatus) {
                    velStatus.textContent = "DYNAMIC EXPLORATION (Healthy)";
                    velStatus.className = "text-[10px] font-mono font-semibold text-emerald-600 dark:text-emerald-400";
                }
            }
        }

        // Markov Entropy Gauge (0.0 to 4.16 scale)
        const entVal = document.getElementById("gaugeEntVal");
        const entBar = document.getElementById("gaugeEntBar");
        if (entVal) entVal.textContent = entropy.toFixed(2);
        if (entBar) {
            const pct = Math.min(100, Math.max(0, (entropy / 4.16) * 100));
            entBar.style.width = `${pct}%`;
            entBar.className = entropy < 1.50 
                ? "h-2 rounded-full bg-rose-500 transition-all duration-300"
                : "h-2 rounded-full bg-sky-500 transition-all duration-300";
        }

        const latEl = document.getElementById("gaugeLatencyVal");
        if (latEl) latEl.textContent = `${lat.toFixed(3)} ms`;
    },

    showAlert(step) {
        const banner = document.getElementById("sandboxDeadlockAlert");
        const typeEl = document.getElementById("sandboxDeadlockType");
        const dirEl = document.getElementById("sandboxDeadlockDirective");

        if (banner) banner.classList.remove("hidden");
        if (typeEl) typeEl.textContent = `${step.deadlock_type} (${step.details})`;
        if (dirEl) dirEl.textContent = step.directive || "Switch strategic approach to break attractor loop.";
    },

    hideAlert() {
        const banner = document.getElementById("sandboxDeadlockAlert");
        if (banner) banner.classList.add("hidden");
    },

    transferToDebugger() {
        // Convert sandbox history to OpenAI messages format and switch to Tab 1
        const msgs = [
            { role: "system", content: "You are an autonomous engineering agent." },
            { role: "user", content: "Execute the assigned programming task." }
        ];

        this.history.forEach((h, i) => {
            msgs.push({
                role: "assistant",
                content: `Executing: ${h.action}`,
                tool_calls: [{
                    id: `call_${i + 1}`,
                    type: "function",
                    function: { name: "run_command", arguments: JSON.stringify({ command: h.action }) }
                }]
            });
            if (h.observation) {
                msgs.push({
                    role: "tool",
                    tool_call_id: `call_${i + 1}`,
                    content: h.observation
                });
            }
        });

        // Switch tab
        if (window.App) {
            App.switchTab('tab-debugger');
        }

        const input = document.getElementById("debuggerJsonInput");
        if (input) {
            input.value = JSON.stringify(msgs, null, 2);
        }

        // Auto trigger heal
        if (window.DebuggerEngine) {
            DebuggerEngine.runHeal();
        }
    },

    escapeHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
};

