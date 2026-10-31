/**
 * app.js - Main Application Orchestration, Tab Switching & UI Utilities
 */

const App = {
    activeTab: 'tab-debugger',

    init() {
        this.initTheme();
        if (window.DebuggerEngine) DebuggerEngine.init();
        if (window.SandboxEngine) SandboxEngine.init();
        if (window.DuelEngine) DuelEngine.init();
        if (window.ManifoldCanvas) ManifoldCanvas.init();
        if (window.ChaosEngine) ChaosEngine.computeDistance();

        // Setup Keyboard Shortcut: Ctrl+Enter / Cmd+Enter
        window.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                if (this.activeTab === 'tab-debugger' && window.DebuggerEngine) {
                    DebuggerEngine.runHeal();
                } else if (this.activeTab === 'tab-sandbox' && window.SandboxEngine) {
                    SandboxEngine.submitStep();
                }
            }
        });
    },

    switchTab(tabId) {
        this.activeTab = tabId;
        const tabs = ['tab-debugger', 'tab-sandbox', 'tab-duel', 'tab-canvas', 'tab-benchmarks'];

        tabs.forEach(t => {
            const el = document.getElementById(t);
            const btn = document.getElementById(`nav-${t}`);
            if (el) {
                if (t === tabId) {
                    el.classList.remove("hidden");
                } else {
                    el.classList.add("hidden");
                }
            }
            if (btn) {
                if (t === tabId) {
                    btn.className = "nav-tab-active px-3 py-2 rounded-lg text-xs font-mono font-bold transition shadow-sm";
                } else {
                    btn.className = "nav-tab-inactive px-3 py-2 rounded-lg text-xs font-mono text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition font-medium";
                }
            }
        });

        // Trigger canvas resize when switching to canvas or sandbox
        if (tabId === 'tab-canvas' || tabId === 'tab-sandbox') {
            setTimeout(() => {
                if (window.ManifoldCanvas) {
                    ManifoldCanvas.resize();
                    ManifoldCanvas.render();
                }
            }, 50);
        }
    },

    initTheme() {
        const savedTheme = localStorage.getItem("capy_theme") || "light";
        const html = document.documentElement;
        html.classList.remove("light", "dark");
        html.classList.add(savedTheme);
        const icon = document.getElementById("themeIcon");
        if (icon) {
            icon.innerText = savedTheme === "dark" ? "☀️" : "🌙";
        }
    },

    toggleTheme() {
        const html = document.documentElement;
        const icon = document.getElementById("themeIcon");
        if (html.classList.contains("dark")) {
            html.classList.remove("dark");
            html.classList.add("light");
            if (icon) icon.innerText = "🌙";
            localStorage.setItem("capy_theme", "light");
        } else {
            html.classList.remove("light");
            html.classList.add("dark");
            if (icon) icon.innerText = "☀️";
            localStorage.setItem("capy_theme", "dark");
        }
        if (window.ManifoldCanvas) {
            ManifoldCanvas.render();
        }
    },

    copySnippet(elemId) {
        const elem = document.getElementById(elemId);
        if (!elem) return;
        navigator.clipboard.writeText(elem.innerText);
        alert("Code snippet copied to clipboard!");
    }
};

window.addEventListener('DOMContentLoaded', () => {
    App.init();
});
