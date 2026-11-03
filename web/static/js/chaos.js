/**
 * chaos.js - Chaos Injection Panel & Live Distance Calculator
 * Tests synthetic loop patterns and measures 1024-D semantic velocity live via backend API.
 */

/**
 * chaos.js - Mathematical Physics, Phase-Space Telemetry & Live Vector Distance Calculator
 * Grounded in IEEE Phase-Space Dynamics: Tracks 1024-D directional velocity, variance, and doctor pivot.
 */

const ChaosEngine = {
    currentMode: 'vortex',

    init() {
        this.setTrajectoryMode('vortex');
        this.computeDistance();
    },

    setTrajectoryMode(mode) {
        this.currentMode = mode;
        const pipeline = document.getElementById("trajectoryPipeline");
        const gaugeVal = document.getElementById("telemetryVelocityVal");
        const gaugeBar = document.getElementById("telemetryVelocityBar");
        const stateBadge = document.getElementById("telemetryStateBadge");
        const narrative = document.getElementById("telemetryNarrative");

        // Update active button styling
        ['btnModeVortex', 'btnModeDoctor', 'btnModeHealthy'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.className = "px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold transition shadow-sm " +
                    (id === `btnMode${mode.charAt(0).toUpperCase() + mode.slice(1)}` 
                        ? "bg-amber-500 text-slate-950 border-amber-600 font-bold" 
                        : "border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-100");
            }
        });

        if (mode === 'vortex') {
            if (gaugeVal) gaugeVal.innerText = "0.184";
            if (gaugeBar) {
                gaugeBar.style.width = "18%";
                gaugeBar.className = "h-full bg-rose-500 transition-all duration-500";
            }
            if (stateBadge) {
                stateBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30";
                stateBadge.innerText = "🚨 Attractor Well Trap (v_t < 0.70)";
            }
            if (narrative) {
                narrative.innerHTML = "Agent trapped in repetitive semantic basin. Directional velocity collapsed to <strong>0.184</strong> with variance <strong>&sigma;&sup2; &le; 0.04</strong>. Capybala triggers interception in <strong>&lt;0.64ms</strong>.";
            }
            if (pipeline) {
                pipeline.innerHTML = `
                    <div class="p-3 rounded-xl bg-slate-900/80 border border-emerald-500/30 flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                            <span class="font-mono text-xs text-slate-300 font-bold">Turn 1: Initial Dispatch</span>
                            <code class="text-[10px] text-slate-400 font-mono">grep -rn 'authenticate_user' tests/</code>
                        </div>
                        <span class="text-xs font-mono font-bold text-emerald-400">v_t = 0.950</span>
                    </div>
                    <div class="p-3 rounded-xl bg-slate-900/80 border border-amber-500/30 flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                            <span class="font-mono text-xs text-slate-300 font-bold">Turn 2: Search Narrowing</span>
                            <code class="text-[10px] text-slate-400 font-mono">find . -name '*test_auth*.py'</code>
                        </div>
                        <span class="text-xs font-mono font-bold text-amber-400">v_t = 0.742</span>
                    </div>
                    <div class="p-3 rounded-xl bg-rose-950/40 border-2 border-rose-500/60 flex items-center justify-between shadow-lg">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
                            <span class="font-mono text-xs text-rose-300 font-bold">Turn 3: Deadlock Singularity</span>
                            <code class="text-[10px] text-rose-200 font-mono">grep -rn 'def authenticate' src/</code>
                        </div>
                        <span class="text-xs font-mono font-black text-rose-400">v_t = 0.184 (COLLAPSE)</span>
                    </div>
                `;
            }
        } else if (mode === 'doctor') {
            if (gaugeVal) gaugeVal.innerText = "1.250";
            if (gaugeBar) {
                gaugeBar.style.width = "90%";
                gaugeBar.className = "h-full bg-purple-500 transition-all duration-500";
            }
            if (stateBadge) {
                stateBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/30";
                stateBadge.innerText = "🩺 Doctor Pivot &Delta;u Surgery";
            }
            if (narrative) {
                narrative.innerHTML = "Capybala executed an <strong>Atomic Context Rollback</strong>, preserving vendor prompt cache hashes. Injected strategic <strong>Doctor Directive</strong>, deflecting the agent trajectory back to forward progress.";
            }
            if (pipeline) {
                pipeline.innerHTML = `
                    <div class="p-3 rounded-xl bg-slate-900/80 border border-rose-500/40 flex items-center justify-between opacity-60">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                            <span class="font-mono text-xs text-slate-400 font-bold">Turn 3: Deadlock Intercepted</span>
                            <code class="text-[10px] text-slate-500 font-mono">[Rolled Back redundant traceback spam]</code>
                        </div>
                        <span class="text-xs font-mono text-rose-400">v_t = 0.184</span>
                    </div>
                    <div class="p-3.5 rounded-xl bg-purple-950/40 border-2 border-purple-500/70 flex items-center justify-between shadow-lg">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-purple-400 animate-pulse"></span>
                            <span class="font-mono text-xs text-purple-300 font-bold">Turn 4: Doctor Pivot Surgery</span>
                            <code class="text-[10px] text-purple-200 font-mono">&Delta;u Injected: Refactor HMAC HS256</code>
                        </div>
                        <span class="text-xs font-mono font-black text-purple-400">&Delta;u = +1.250</span>
                    </div>
                    <div class="p-3 rounded-xl bg-emerald-950/40 border-2 border-emerald-500/60 flex items-center justify-between shadow-md">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                            <span class="font-mono text-xs text-emerald-300 font-bold">Turn 5: Orbit Escaped & Resolved</span>
                            <code class="text-[10px] text-emerald-200 font-mono">pytest tests/test_auth.py -> PASSED [100%]</code>
                        </div>
                        <span class="text-xs font-mono font-bold text-emerald-400">v_t = 1.120</span>
                    </div>
                `;
            }
        } else if (mode === 'healthy') {
            if (gaugeVal) gaugeVal.innerText = "0.942";
            if (gaugeBar) {
                gaugeBar.style.width = "82%";
                gaugeBar.className = "h-full bg-emerald-500 transition-all duration-500";
            }
            if (stateBadge) {
                stateBadge.className = "px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30";
                stateBadge.innerText = "✅ Dynamic Forward Progression";
            }
            if (narrative) {
                narrative.innerHTML = "Agent trajectory maintains healthy directional entropy. Mean semantic velocity <strong>v_t = 0.942 &gt; 0.70</strong>. Capybala supervisor operates with zero false alarms and <strong>0ms</strong> non-intrusive pass-through.";
            }
            if (pipeline) {
                pipeline.innerHTML = `
                    <div class="p-3 rounded-xl bg-slate-900/80 border border-emerald-500/30 flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <span class="font-mono text-xs text-slate-300 font-bold">Turn 1: Inspect Codebase</span>
                            <code class="text-[10px] text-slate-400 font-mono">cat pyproject.toml</code>
                        </div>
                        <span class="text-xs font-mono font-bold text-emerald-400">v_t = 0.980</span>
                    </div>
                    <div class="p-3 rounded-xl bg-slate-900/80 border border-emerald-500/30 flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <span class="font-mono text-xs text-slate-300 font-bold">Turn 2: Run Build Tool</span>
                            <code class="text-[10px] text-slate-400 font-mono">python -m build --wheel</code>
                        </div>
                        <span class="text-xs font-mono font-bold text-emerald-400">v_t = 0.942</span>
                    </div>
                    <div class="p-3 rounded-xl bg-slate-900/80 border border-emerald-500/30 flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            <span class="font-mono text-xs text-slate-300 font-bold">Turn 3: Run Unit Test Suite</span>
                            <code class="text-[10px] text-slate-400 font-mono">pytest tests/test_core.py</code>
                        </div>
                        <span class="text-xs font-mono font-bold text-emerald-400">v_t = 0.895</span>
                    </div>
                `;
            }
        }
    },

    async injectPreset(type) {
        let cmd1 = "grep -rn 'def test_auth' tests/";
        let cmd2 = "find . -name '*test_auth*.py'";

        if (type === 'direct_repetition') {
            cmd1 = "pytest tests/test_api.py -k test_login";
            cmd2 = "pytest tests/test_api.py -k test_login";
        } else if (type === 'oscillation') {
            cmd1 = "git checkout HEAD~1 config/settings.py";
            cmd2 = "git checkout -b fix-auth && git cherry-pick 3a9f01";
        } else if (type === 'clean_progress') {
            cmd1 = "cat pyproject.toml | grep -E 'version|dependencies'";
            cmd2 = "python -m build --sdist --wheel";
        }

        const input1 = document.getElementById("chaosCmd1");
        const input2 = document.getElementById("chaosCmd2");
        if (input1) input1.value = cmd1;
        if (input2) input2.value = cmd2;

        await this.computeDistance();
    },

    async computeDistance() {
        const cmd1 = document.getElementById("chaosCmd1") ? document.getElementById("chaosCmd1").value : "";
        const cmd2 = document.getElementById("chaosCmd2") ? document.getElementById("chaosCmd2").value : "";

        try {
            const res = await fetch('/api/velocity', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cmd1, cmd2})
            });
            const d = await res.json();

            const cosEl = document.getElementById("chaosCos");
            const velEl = document.getElementById("chaosVel");
            const latEl = document.getElementById("chaosLat");
            const stEl = document.getElementById("chaosStatus");

            if (cosEl) cosEl.innerText = d.cosine_similarity.toFixed(4);
            if (velEl) velEl.innerText = d.semantic_velocity.toFixed(4);
            if (latEl) latEl.innerText = `${d.latency_ms.toFixed(3)} ms`;

            if (stEl) {
                if (d.is_stagnant) {
                    stEl.className = "text-rose-600 dark:text-rose-400 font-bold";
                    stEl.innerText = "Looping Attractor Gravity (v_t < 0.70)";
                } else {
                    stEl.className = "text-emerald-600 dark:text-emerald-400 font-bold";
                    stEl.innerText = "Healthy Dynamic Exploration";
                }
            }
        } catch (err) {
            console.error("Chaos velocity calculation error:", err);
        }
    }
};

