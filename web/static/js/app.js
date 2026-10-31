/**
 * app.js - Main Application Orchestration, Smooth Scroll Navigation & UI Utilities
 */

const App = {
    init() {
        this.initTheme();
        if (window.DebuggerEngine) DebuggerEngine.init();
        if (window.SandboxEngine) SandboxEngine.init();
        if (window.DuelEngine) DuelEngine.init();
        if (window.ManifoldCanvas) ManifoldCanvas.init();
        if (window.ChaosEngine) ChaosEngine.computeDistance();

        this.initScrollSpy();

        // Keyboard Shortcut: Ctrl+Enter / Cmd+Enter runs heal
        window.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const active = document.activeElement;
                if (active && (active.id === 'sandboxActionInput' || active.id === 'sandboxObsInput')) {
                    if (window.SandboxEngine) SandboxEngine.submitStep();
                } else {
                    if (window.DebuggerEngine) DebuggerEngine.runHeal();
                }
            }
        });

        // Window resize re-renders canvas
        window.addEventListener('resize', () => {
            if (window.ManifoldCanvas) ManifoldCanvas.render();
        });
    },

    scrollToSection(sectionId) {
        const el = document.getElementById(sectionId);
        if (el) {
            const offset = 70; // Header height
            const bodyRect = document.body.getBoundingClientRect().top;
            const elementRect = el.getBoundingClientRect().top;
            const elementPosition = elementRect - bodyRect;
            const offsetPosition = elementPosition - offset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    },

    initScrollSpy() {
        const sections = ['duel-section', 'debugger-section', 'sandbox-section', 'canvas-section', 'benchmarks-section'];
        const navMap = {
            'duel-section': 'nav-duel',
            'debugger-section': 'nav-debugger',
            'sandbox-section': 'nav-sandbox',
            'canvas-section': 'nav-canvas',
            'benchmarks-section': 'nav-benchmarks'
        };

        window.addEventListener('scroll', () => {
            const scrollPos = window.scrollY + 120;
            let current = 'duel-section';

            for (const id of sections) {
                const el = document.getElementById(id);
                if (el && el.offsetTop <= scrollPos) {
                    current = id;
                }
            }

            Object.entries(navMap).forEach(([secId, navId]) => {
                const btn = document.getElementById(navId);
                if (btn) {
                    if (secId === current) {
                        btn.className = "nav-tab-active px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition shadow-sm whitespace-nowrap";
                    } else {
                        btn.className = "nav-tab-inactive px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition whitespace-nowrap text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white";
                    }
                }
            });
        });
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
