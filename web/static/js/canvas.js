/**
 * canvas.js - True 1024-D Unit Sphere Manifold Projection Canvas
 * Renders real mathematical projections of agent trajectories using
 * deterministic Johnson-Lindenstrauss orthonormal random projection vectors.
 */

const ManifoldCanvas = {
    canvas: null,
    ctx: null,
    points: [],
    mode: 'live',

    init() {
        this.canvas = document.getElementById("manifoldCanvas");
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext("2d");
        this.resize();
        this.render();
    },

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = Math.min(680, rect.width - 32);
        this.canvas.height = 360;
    },

    clearPoints() {
        this.points = [];
        this.render();
    },

    addPoint(step, x, y, isDeadlock, label) {
        this.points.push({
            step: step,
            x: x,
            y: y,
            isDeadlock: isDeadlock,
            label: label || `Turn ${step}`
        });
        this.render();
    },

    setMode(newMode) {
        this.mode = newMode;
        if (newMode === 'spiral') {
            this.simulateSpiralBasin();
        } else if (newMode === 'deflect') {
            this.simulateDeflection();
        }
    },

    async simulateSpiralBasin() {
        // Fetch projection of 6 paraphrased commands that collapse into attractor
        const actions = [
            "grep -rn 'def authenticate_user' tests/",
            "find . -name '*test_auth*.py'",
            "python -m pytest -k 'test_auth'",
            "grep -i 'test_auth' src/",
            "python -c 'import auth; print(dir(auth))'",
            "grep -rn 'authenticate_user' ."
        ];
        try {
            const res = await fetch('/api/vector_projection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ actions })
            });
            const data = await res.json();
            this.points = data.points.map((p, idx) => ({
                step: idx + 1,
                x: p.x,
                y: p.y,
                isDeadlock: idx >= 3,
                label: p.action
            }));
            this.render();
        } catch (err) {
            console.error("Failed to project actions:", err);
        }
    },

    async simulateDeflection() {
        await this.simulateSpiralBasin();
        // Add deflection point
        if (this.points.length > 0) {
            const last = this.points[this.points.length - 1];
            this.points.push({
                step: this.points.length + 1,
                x: last.x + 0.65,
                y: last.y - 0.45,
                isDeadlock: false,
                isDeflection: true,
                label: "Capybala Atomic Deflection"
            });
            this.render();
        }
    },

    toCanvasX(x) {
        const cx = this.canvas.width / 2;
        const scale = (this.canvas.width / 2) * 0.75;
        return cx + x * scale;
    },

    toCanvasY(y) {
        const cy = this.canvas.height / 2;
        const scale = (this.canvas.height / 2) * 0.75;
        return cy + y * scale;
    },

    render() {
        if (!this.ctx || !this.canvas) return;
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Clear dark space background
        ctx.fillStyle = "#090d16";
        ctx.fillRect(0, 0, w, h);

        // Draw Coordinate Grid & Unit Sphere Bounds
        ctx.strokeStyle = "#161f30";
        ctx.lineWidth = 1;

        const cx = w / 2;
        const cy = h / 2;

        // Center Crosshair
        ctx.beginPath();
        ctx.moveTo(0, cy);
        ctx.lineTo(w, cy);
        ctx.moveTo(cx, 0);
        ctx.lineTo(cx, h);
        ctx.stroke();

        // Unit Sphere Boundary Circle
        ctx.strokeStyle = "#1e293b";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.arc(cx, cy, (h / 2) * 0.75, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Axis labels
        ctx.fillStyle = "#475569";
        ctx.font = "9px 'JetBrains Mono', monospace";
        ctx.fillText("Projection Dimension 1 (v · w_x)", w - 160, cy - 8);
        ctx.fillText("Dimension 2 (v · w_y)", cx + 8, 16);

        if (this.points.length === 0) {
            ctx.fillStyle = "#64748b";
            ctx.font = "11px 'JetBrains Mono', monospace";
            ctx.textAlign = "center";
            ctx.fillText("Run Sandbox Step or Click 'Simulate Spiral Basin' to plot manifold trajectory", cx, cy + 40);
            ctx.textAlign = "start";
            return;
        }

        // Draw Trajectory Path Lines
        for (let i = 0; i < this.points.length - 1; i++) {
            const p1 = this.points[i];
            const p2 = this.points[i + 1];

            const x1 = this.toCanvasX(p1.x);
            const y1 = this.toCanvasY(p1.y);
            const x2 = this.toCanvasX(p2.x);
            const y2 = this.toCanvasY(p2.y);

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);

            if (p2.isDeflection) {
                ctx.strokeStyle = "#f59e0b"; // Gold Deflection
                ctx.lineWidth = 3;
                ctx.setLineDash([6, 3]);
            } else if (p2.isDeadlock) {
                ctx.strokeStyle = "#f43f5e"; // Rose Deadlock
                ctx.lineWidth = 2.5;
                ctx.setLineDash([]);
            } else {
                ctx.strokeStyle = "#10b981"; // Emerald Forward
                ctx.lineWidth = 2;
                ctx.setLineDash([]);
            }
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // Draw Nodes
        this.points.forEach((p, idx) => {
            const px = this.toCanvasX(p.x);
            const py = this.toCanvasY(p.y);

            ctx.beginPath();
            ctx.arc(px, py, p.isDeflection ? 6 : 4.5, 0, Math.PI * 2);

            if (p.isDeflection) {
                ctx.fillStyle = "#fbbf24";
                ctx.shadowColor = "#f59e0b";
                ctx.shadowBlur = 10;
            } else if (p.isDeadlock) {
                ctx.fillStyle = "#f43f5e";
                ctx.shadowColor = "#e11d48";
                ctx.shadowBlur = 8;
            } else {
                ctx.fillStyle = "#10b981";
                ctx.shadowColor = "#059669";
                ctx.shadowBlur = 6;
            }

            ctx.fill();
            ctx.shadowBlur = 0;

            // Draw Step Number
            ctx.fillStyle = "#cbd5e1";
            ctx.font = "10px 'JetBrains Mono', monospace";
            ctx.fillText(`T${p.step}`, px + 7, py - 4);
        });
    }
};

window.addEventListener("resize", () => {
    if (window.ManifoldCanvas) {
        ManifoldCanvas.resize();
        ManifoldCanvas.render();
    }
});
