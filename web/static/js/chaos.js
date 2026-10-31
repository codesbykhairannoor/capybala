/**
 * chaos.js - Chaos Injection Panel & Live Distance Calculator
 * Tests synthetic loop patterns and measures 1024-D semantic velocity live via backend API.
 */

const ChaosEngine = {
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
            console.error("Chaos velocity calculation error:", err);
        }
    }
};

