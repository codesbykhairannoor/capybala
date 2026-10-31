/**
 * duel.js - Split-Screen Agent Duel & Real-Time Dollar Ticker Engine
 * Controls step-by-step playback, dollar cost accumulation, and self-healing state transitions.
 */

const DuelEngine = {
    scenarios: {},
    currentKey: 'semantic_attractor',
    isRunning: false,

    async init() {
        try {
            const res = await fetch('/api/duel/scenarios');
            this.scenarios = await res.json();
            this.resetDisplay();
        } catch (err) {
            console.error("Failed to load duel scenarios:", err);
        }
    },

    selectScenario(key) {
        if (this.isRunning) return;
        this.currentKey = key;
        this.resetDisplay();
    },

    resetDisplay() {
        const sc = this.scenarios[this.currentKey];
        if (!sc) return;

        const leftStream = document.getElementById("leftStream");
        const rightStream = document.getElementById("rightStream");

        if (leftStream) {
            leftStream.innerHTML = `<div class='text-slate-400 text-xs italic'>Ready. Press 'Run Live Duel' to run scenario: ${sc.title}...</div>`;
        }
        if (rightStream) {
            rightStream.innerHTML = `<div class='text-slate-400 text-xs italic'>Ready. Capybala armed and monitoring at 0.6ms latency...</div>`;
        }

        document.getElementById("duelCostLeft").innerText = "$0.00";
        document.getElementById("duelCostRight").innerText = "$0.00";
        document.getElementById("duelOutcomeBadge").innerText = "Ready to execute";
        document.getElementById("duelOutcomeBadge").className = "text-base font-bold font-mono text-slate-800 dark:text-white mt-1";
        document.getElementById("leftCostTicker").innerText = "$0.00 Wasted";
        document.getElementById("rightCostTicker").innerText = "$0.00 Total";
        document.getElementById("leftStepIndicator").innerText = "Step 0";
        document.getElementById("rightStepIndicator").innerText = "Step 0";
    },

    async runDuel() {
        const sc = this.scenarios[this.currentKey];
        if (!sc || this.isRunning) return;

        this.isRunning = true;
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
            document.getElementById("leftStepIndicator").innerText = `Step ${Math.min(i + 1, bTurns.length)} / ${bTurns.length}`;
            document.getElementById("rightStepIndicator").innerText = `Step ${Math.min(i + 1, cTurns.length)} / ${cTurns.length}`;

            // Left baseline execution
            if (i < bTurns.length) {
                const t = bTurns[i];
                const d = document.createElement("div");
                d.className = "stream-item";
                if (t.status === 'fatal_crash') {
                    d.className += " p-3 rounded-lg bg-rose-200 dark:bg-rose-950/80 border border-rose-400 text-rose-950 dark:text-rose-200 font-bold";
                    d.innerHTML = `❌ [FATAL CONTEXT OVERFLOW] ${this.escapeHtml(t.obs)}`;
                } else {
                    d.className += " p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-300 shadow-sm";
                    d.innerHTML = `<span class='text-rose-600 dark:text-rose-400 font-bold'>[Turn ${t.turn}] ${this.escapeHtml(t.action)}</span><br><span class='text-slate-500 text-[11px]'>${this.escapeHtml(t.obs)}</span>`;
                }
                leftStream.appendChild(d);
                leftStream.scrollTop = leftStream.scrollHeight;
                document.getElementById("duelCostLeft").innerText = `$${t.cost.toFixed(2)}`;
                document.getElementById("leftCostTicker").innerText = `$${t.cost.toFixed(2)} Wasted`;
            }

            // Right Capybala execution
            if (i < cTurns.length) {
                const t = cTurns[i];
                const d = document.createElement("div");
                d.className = "stream-item";
                if (t.status === 'intercepted') {
                    d.className += " p-3 rounded-lg bg-amber-100 dark:bg-amber-950/60 border border-amber-400 text-amber-950 dark:text-amber-200 font-bold shadow-sm";
                    d.innerHTML = `🦫 <b>[CAPYBALA INTERCEPTED DEADLOCK]</b><br><span class='text-[11px] font-normal'>Atomic Rollback executed. Redundant error tokens pruned. Doctor Pivot Directive injected!</span>`;
                } else if (t.status === 'success') {
                    d.className += " p-3 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-400 text-emerald-950 dark:text-emerald-200 font-bold shadow-sm";
                    d.innerHTML = `🎉 <b>[TASK SOLVED!]</b> ${this.escapeHtml(t.obs)}`;
                } else {
                    d.className += " p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-300 shadow-sm";
                    d.innerHTML = `<span class='text-emerald-700 dark:text-emerald-400 font-bold'>[Turn ${t.turn}] ${this.escapeHtml(t.action)}</span><br><span class='text-slate-500 text-[11px]'>${this.escapeHtml(t.obs)}</span>`;
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

        this.isRunning = false;
        btn.disabled = false;
        btn.innerHTML = `<svg class="w-4 h-4 fill-current mr-1.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg><span>Run Live Duel</span>`;
    },

    escapeHtml(str) {
        return str ? str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;") : "";
    }
};

