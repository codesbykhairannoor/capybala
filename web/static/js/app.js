/**
 * app.js - Main Application Orchestration & UI Utilities
 */

const App = {
    init() {
        this.initTheme();
        DuelEngine.init();
        ManifoldCanvas.init();
        ChaosEngine.computeDistance();

        // Window resize re-renders canvas
        window.addEventListener('resize', () => {
            ManifoldCanvas.render();
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
        ManifoldCanvas.render();
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

