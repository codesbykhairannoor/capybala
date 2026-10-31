/**
 * debugger.js - Production-Grade JSON Conversation Debugger & Context Profiler
 * Connects directly to Capybala's live /api/heal endpoint for real AST surgery.
 */

const DebuggerEngine = {
    presets: {},
    currentResult: null,

    async init() {
        try {
            const res = await fetch('/api/presets');
            this.presets = await res.json();
            this.populatePresetSelector();
            // Default select first preset
            this.selectPreset('swebench_oscillation');
        } catch (err) {
            console.error("Failed to load debugger presets:", err);
        }
    },

    populatePresetSelector() {
        const sel = document.getElementById("debuggerPresetSelect");
        if (!sel) return;
        sel.innerHTML = "";
        for (const [key, p] of Object.entries(this.presets)) {
            const opt = document.createElement("option");
            opt.value = key;
            opt.textContent = `${p.title} (${p.messages.length} turns)`;
            sel.appendChild(opt);
        }
    },

    selectPreset(key) {
        const p = this.presets[key];
        if (!p) return;

        const sel = document.getElementById("debuggerPresetSelect");
        if (sel) sel.value = key;

        const provSel = document.getElementById("debuggerProviderSelect");
        if (provSel && p.provider) provSel.value = p.provider;

        const desc = document.getElementById("presetDescription");
        if (desc) desc.textContent = p.description || "";

        const input = document.getElementById("debuggerJsonInput");
        if (input) {
            input.value = JSON.stringify(p.messages, null, 2);
        }

        this.resetResults();
    },

    formatInput() {
        const input = document.getElementById("debuggerJsonInput");
        if (!input) return;
        try {
            const parsed = JSON.parse(input.value);
            input.value = JSON.stringify(parsed, null, 2);
        } catch (err) {
            alert("Invalid JSON format: " + err.message);
        }
    },

    resetResults() {
        this.currentResult = null;
        const resCard = document.getElementById("debuggerResultsContainer");
        if (resCard) resCard.classList.add("hidden");
    },

    async runHeal() {
        const input = document.getElementById("debuggerJsonInput");
        const provSel = document.getElementById("debuggerProviderSelect");
        const btn = document.getElementById("runHealBtn");

        if (!input) return;

        let messages;
        try {
            messages = JSON.parse(input.value);
            if (!Array.isArray(messages)) throw new Error("Root element must be a JSON array of messages");
        } catch (err) {
            alert("JSON Syntax Error: " + err.message);
            return;
        }

        const provider = provSel ? provSel.value : "openai";

        btn.disabled = true;
        btn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-slate-900 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Analyzing Context...</span>
        `;

        const t0 = performance.now();

        try {
            const res = await fetch('/api/heal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: messages,
                    provider: provider,
                    repetition_threshold: 3
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Server returned " + res.status);
            }

            const data = await res.json();
            this.currentResult = data;
            this.renderResults(data);
        } catch (err) {
            alert("Capybala Engine Error: " + err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = `
                <svg class="w-4 h-4 fill-current mr-1.5" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                <span>Analyze & Surgically Heal (Live Engine)</span>
            `;
        }
    },

    renderResults(data) {
        const container = document.getElementById("debuggerResultsContainer");
        if (!container) return;
        container.classList.remove("hidden");

        // Deadlock Status Badge
        const statusBadge = document.getElementById("resStatusBadge");
        if (data.is_deadlock) {
            statusBadge.className = "px-3 py-1 rounded-full text-xs font-mono font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-300 dark:border-rose-800";
            statusBadge.textContent = `🚨 DEADLOCK: ${data.deadlock_type.toUpperCase()}`;
        } else {
            statusBadge.className = "px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800";
            statusBadge.textContent = `✅ CLEAN FORWARD TRAJECTORY (No Deadlock)`;
        }

        // Metrics
        document.getElementById("resLatency").textContent = `${data.latency_ms.toFixed(3)} ms`;
        document.getElementById("resTokensBefore").textContent = `${data.tokens_before.toLocaleString()} tokens`;
        document.getElementById("resTokensAfter").textContent = `${data.tokens_after.toLocaleString()} tokens`;
        document.getElementById("resTokensSaved").textContent = `${data.tokens_saved.toLocaleString()} (${data.percent_saved}%)`;
        document.getElementById("resTurnsCount").textContent = `${data.original_turn_count} ➔ ${data.healed_turn_count} turns`;
        document.getElementById("resCostSaved").textContent = `$${data.cost_saved_usd.toFixed(4)}`;

        // Doctor Directive Box
        const directiveCard = document.getElementById("resDirectiveCard");
        const directiveText = document.getElementById("resDirectiveText");
        if (data.doctor_directive && data.is_deadlock) {
            directiveCard.classList.remove("hidden");
            directiveText.textContent = data.doctor_directive;
        } else {
            directiveCard.classList.add("hidden");
        }

        // Render Side-by-Side Diff View
        this.renderDiffViews(data.original_messages, data.healed_messages);

        // Scroll to results smoothly
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    renderDiffViews(origMsgs, healedMsgs) {
        const origCol = document.getElementById("diffOriginalCol");
        const healedCol = document.getElementById("diffHealedCol");
        if (!origCol || !healedCol) return;

        origCol.innerHTML = "";
        healedCol.innerHTML = "";

        const healedCount = healedMsgs.length;

        // Render Original Messages
        origMsgs.forEach((msg, idx) => {
            const isPruned = idx >= (healedCount - 1) && healedCount < origMsgs.length;
            const card = document.createElement("div");
            card.className = `p-3 rounded-lg border text-xs font-mono transition ${
                isPruned 
                    ? "bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-800 line-through opacity-75 text-rose-900 dark:text-rose-300"
                    : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200"
            }`;

            const role = msg.role || "unknown";
            let contentStr = typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content);
            if (msg.tool_calls) {
                contentStr += " " + JSON.stringify(msg.tool_calls);
            }

            card.innerHTML = `
                <div class="flex justify-between items-center mb-1">
                    <span class="font-bold uppercase text-[10px] ${this.getRoleBadgeColor(role)}">${role}</span>
                    <span class="text-[10px] text-slate-400">#${idx + 1} ${isPruned ? "• [PRUNED]" : ""}</span>
                </div>
                <div class="whitespace-pre-wrap break-words leading-relaxed">${this.escapeHtml(contentStr || "(empty content)")}</div>
            `;
            origCol.appendChild(card);
        });

        // Render Healed Messages
        healedMsgs.forEach((msg, idx) => {
            const isInjected = JSON.stringify(msg).includes("CAPYBALA DOCTOR INTERVENTION") || JSON.stringify(msg).includes("CAPYBALA STATE ROLLBACK");
            const card = document.createElement("div");
            card.className = `p-3 rounded-lg border text-xs font-mono transition ${
                isInjected
                    ? "bg-amber-50 dark:bg-amber-950/50 border-amber-400 dark:border-amber-700 text-amber-900 dark:text-amber-200 shadow-sm"
                    : "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800/60 text-slate-800 dark:text-slate-200"
            }`;

            const role = msg.role || "unknown";
            let contentStr = typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content);

            card.innerHTML = `
                <div class="flex justify-between items-center mb-1">
                    <span class="font-bold uppercase text-[10px] ${isInjected ? "text-amber-700 dark:text-amber-400 font-extrabold" : this.getRoleBadgeColor(role)}">
                        ${isInjected ? "🦫 DOCTOR DIRECTIVE INJECTED" : role}
                    </span>
                    <span class="text-[10px] text-slate-400">#${idx + 1}</span>
                </div>
                <div class="whitespace-pre-wrap break-words leading-relaxed">${this.escapeHtml(contentStr || "(empty content)")}</div>
            `;
            healedCol.appendChild(card);
        });
    },

    getRoleBadgeColor(role) {
        switch (role) {
            case "system": return "text-purple-600 dark:text-purple-400";
            case "user": return "text-sky-600 dark:text-sky-400";
            case "assistant": return "text-emerald-600 dark:text-emerald-400";
            case "tool": return "text-amber-600 dark:text-amber-400";
            default: return "text-slate-500";
        }
    },

    copyHealedJSON() {
        if (!this.currentResult || !this.currentResult.healed_messages) {
            alert("No healed messages available to copy.");
            return;
        }
        const text = JSON.stringify(this.currentResult.healed_messages, null, 2);
        navigator.clipboard.writeText(text).then(() => {
            alert("✅ Healed JSON copied to clipboard!");
        }).catch(err => {
            alert("Failed to copy: " + err);
        });
    },

    downloadHealedJSON() {
        if (!this.currentResult || !this.currentResult.healed_messages) return;
        const text = JSON.stringify(this.currentResult.healed_messages, null, 2);
        const blob = new Blob([text], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `capybala_healed_context_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
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
