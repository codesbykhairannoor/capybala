/**
 * canvas.js - True 1024-D Unit Sphere Manifold Projection Canvas
 * Renders real mathematical projections of agent trajectories using
 * deterministic Johnson-Lindenstrauss orthonormal random projection vectors.
 * Grounded in IEEE Figure 2: Phase-Space Spiral Dynamics & Doctor Pivot.
 */

const ManifoldCanvas = {
    canvas: null,
    ctx: null,
    points: [],
    mode: 'live',
    hoveredPoint: null,
    mousePos: { x: -1, y: -1 },

    init() {
        this.canvas = document.getElementById("manifoldCanvas");
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext("2d");
        this.resize();

        // Mousemove for interactive node inspection
        this.canvas.addEventListener("mousemove", (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mousePos = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
            this.checkHover();
        });

        this.canvas.addEventListener("mouseleave", () => {
            this.hoveredPoint = null;
            this.mousePos = { x: -1, y: -1 };
            this.render();
        });

        this.render();
    },

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = Math.min(780, rect.width - 32);
        this.canvas.height = 420;
    },

    clearPoints() {
        this.points = [];
        this.hoveredPoint = null;
        this.render();
    },

    addPoint(step, x, y, isDeadlock, label, velocity) {
        this.points.push({
            step: step,
            x: x,
            y: y,
            isDeadlock: isDeadlock,
            velocity: velocity !== undefined ? velocity : (isDeadlock ? 0.32 : 1.0),
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
            
            // Clear existing and animate points sequentially
            this.points = [];
            data.points.forEach((p, idx) => {
                setTimeout(() => {
                    this.points.push({
                        step: idx + 1,
                        x: p.x,
                        y: p.y,
                        isDeadlock: idx >= 3,
                        velocity: idx >= 3 ? Math.max(0.12, 0.65 - idx * 0.1) : 0.95,
                        label: p.action
                    });
                    this.render();
                }, idx * 180);
            });
        } catch (err) {
            console.error("Failed to project actions:", err);
        }
    },

    async simulateDeflection() {
        await this.simulateSpiralBasin();
        // Add deflection point after spiral completes
        setTimeout(() => {
            if (this.points.length > 0) {
                const last = this.points[this.points.length - 1];
                this.points.push({
                    step: this.points.length + 1,
                    x: last.x + 0.68,
                    y: last.y - 0.48,
                    isDeadlock: false,
                    isDeflection: true,
                    velocity: 1.18,
                    label: "Capybala Doctor Pivot Surgery (Resolved Trajectory)"
                });
                this.render();
            }
        }, 6 * 180 + 100);
    },

    toCanvasX(x) {
        const cx = this.canvas.width / 2;
        const scale = (this.canvas.height / 2) * 0.78;
        return cx + x * scale;
    },

    toCanvasY(y) {
        const cy = this.canvas.height / 2;
        const scale = (this.canvas.height / 2) * 0.78;
        return cy + y * scale;
    },

    checkHover() {
        if (!this.canvas || this.points.length === 0) return;
        const mx = this.mousePos.x;
        const my = this.mousePos.y;
        let found = null;

        for (let i = this.points.length - 1; i >= 0; i--) {
            const p = this.points[i];
            const px = this.toCanvasX(p.x);
            const py = this.toCanvasY(p.y);
            const dist = Math.hypot(mx - px, my - py);
            if (dist <= 14) {
                found = { point: p, px, py };
                break;
            }
        }

        if (this.hoveredPoint !== found) {
            this.hoveredPoint = found;
            this.render();
        }
    },

    render() {
        if (!this.ctx || !this.canvas) return;
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const cx = w / 2;
        const cy = h / 2;
        const radius = (h / 2) * 0.78;

        // Dark deep space background
        ctx.fillStyle = "#090d16";
        ctx.fillRect(0, 0, w, h);

        // Subtly lit radial gradient towards center
        const bgGrad = ctx.createRadialGradient(cx, cy, 10, cx, cy, radius * 1.2);
        bgGrad.addColorStop(0, "rgba(225, 29, 72, 0.08)");
        bgGrad.addColorStop(0.5, "rgba(14, 165, 233, 0.03)");
        bgGrad.addColorStop(1, "rgba(9, 13, 22, 0)");
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, w, h);

        // Coordinate axes
        ctx.strokeStyle = "#161f30";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(30, cy);
        ctx.lineTo(w - 30, cy);
        ctx.moveTo(cx, 25);
        ctx.lineTo(cx, h - 25);
        ctx.stroke();

        // IEEE S^{d-1} Hypersphere Unit Manifold boundary circle (blue dashed)
        ctx.strokeStyle = "#2563eb";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Theoretical Attractor Basin Spiral (Red dashed logarithmic spiral)
        ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
        ctx.lineWidth = 1.2;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        const spiralRotations = 3;
        const maxTheta = spiralRotations * Math.PI * 2;
        for (let theta = 0.5; theta <= maxTheta; theta += 0.1) {
            const r = (radius * 0.95) * Math.pow(theta / maxTheta, 1.25);
            // Reverse spiral inward
            const curR = radius * 0.95 - (theta / maxTheta) * (radius * 0.90);
            const sx = cx + curR * Math.cos(theta);
            const sy = cy + curR * Math.sin(theta);
            if (theta === 0.5) ctx.moveTo(sx, sy);
            else ctx.lineTo(sx, sy);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // Glowing Red Singularity (Attractor Basin Center v_t -> 0)
        const coreGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, 18);
        coreGlow.addColorStop(0, "rgba(239, 68, 68, 0.9)");
        coreGlow.addColorStop(0.4, "rgba(239, 68, 68, 0.4)");
        coreGlow.addColorStop(1, "rgba(239, 68, 68, 0)");
        ctx.fillStyle = coreGlow;
        ctx.beginPath();
        ctx.arc(cx, cy, 18, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = "#ef4444";
        ctx.beginPath();
        ctx.arc(cx, cy, 4, 0, Math.PI * 2);
        ctx.fill();

        // Scientific Quadrant Callouts (matching IEEE Fig. 2)
        this.drawCalloutBadge(ctx, "Manifold S^{d-1}", cx - radius * 0.75, cy - radius * 0.72, "#38bdf8", "#0369a1");
        this.drawCalloutBadge(ctx, "Attractor Basin (v_t → 0)", cx - radius * 0.85, cy + radius * 0.78, "#f87171", "#991b1b");
        this.drawCalloutBadge(ctx, "Interception (v_t < 0.70)", cx + radius * 0.28, cy + radius * 0.15, "#fbbf24", "#b45309");

        // Axis notations
        ctx.fillStyle = "#64748b";
        ctx.font = "10px 'JetBrains Mono', monospace";
        ctx.textAlign = "right";
        ctx.fillText("Re(u)", w - 35, cy - 8);
        ctx.textAlign = "left";
        ctx.fillText("Im(u)", cx + 10, 38);

        if (this.points.length === 0) {
            ctx.fillStyle = "#94a3b8";
            ctx.font = "12px 'JetBrains Mono', monospace";
            ctx.textAlign = "center";
            ctx.fillText("Ready. Execute steps or click 'Simulate Attractor Basin' to plot trajectories", cx, cy + 55);
            ctx.textAlign = "start";
            return;
        }

        // Draw trajectory lines with directional arrows
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
                // Purple/Gold Doctor Pivot Outward Surgery
                ctx.strokeStyle = "#c084fc";
                ctx.lineWidth = 3.5;
                ctx.shadowColor = "#a855f7";
                ctx.shadowBlur = 12;
            } else if (p2.isDeadlock) {
                // Red Deadlock Spiral
                ctx.strokeStyle = "#f43f5e";
                ctx.lineWidth = 2.5;
                ctx.shadowColor = "#e11d48";
                ctx.shadowBlur = 8;
            } else {
                // Emerald Healthy
                ctx.strokeStyle = "#10b981";
                ctx.lineWidth = 2;
                ctx.shadowBlur = 0;
            }
            ctx.stroke();
            ctx.shadowBlur = 0;

            // Directional Arrowhead in center of segment
            this.drawArrowhead(ctx, x1, y1, x2, y2, p2.isDeflection ? "#c084fc" : (p2.isDeadlock ? "#f43f5e" : "#10b981"));
        }

        // Draw Nodes
        this.points.forEach((p, idx) => {
            const px = this.toCanvasX(p.x);
            const py = this.toCanvasY(p.y);
            const isLast = idx === this.points.length - 1;

            ctx.beginPath();
            ctx.arc(px, py, p.isDeflection ? 7 : (isLast ? 6 : 4.5), 0, Math.PI * 2);

            if (p.isDeflection) {
                ctx.fillStyle = "#c084fc";
                ctx.shadowColor = "#a855f7";
                ctx.shadowBlur = 14;
            } else if (p.isDeadlock) {
                ctx.fillStyle = "#f43f5e";
                ctx.shadowColor = "#e11d48";
                ctx.shadowBlur = 10;
            } else {
                ctx.fillStyle = "#10b981";
                ctx.shadowColor = "#059669";
                ctx.shadowBlur = 8;
            }

            ctx.fill();
            ctx.shadowBlur = 0;

            // Node ring stroke
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Label step
            ctx.fillStyle = "#f8fafc";
            ctx.font = "bold 10px 'JetBrains Mono', monospace";
            ctx.fillText(`T${p.step}`, px + 8, py - 4);
        });

        // If Deflection point exists, draw Doctor Pivot label & Resolved Trajectory Arc
        const deflPoint = this.points.find(p => p.isDeflection);
        if (deflPoint) {
            const dx = this.toCanvasX(deflPoint.x);
            const dy = this.toCanvasY(deflPoint.y);
            this.drawCalloutBadge(ctx, "Doctor Pivot Δu (Resolved Trajectory)", dx - 10, dy - 20, "#e879f9", "#7e22ce");

            // Green escaping arc
            ctx.strokeStyle = "#22c55e";
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(dx + 25, dy, 35, Math.PI * 0.9, Math.PI * 1.6, false);
            ctx.stroke();
        }

        // Draw Interactive Hover Tooltip if hovering a node
        if (this.hoveredPoint) {
            this.drawHoverTooltip(ctx, this.hoveredPoint);
        }
    },

    drawArrowhead(ctx, fromX, fromY, toX, toY, color) {
        const midX = (fromX + toX) / 2;
        const midY = (fromY + toY) / 2;
        const angle = Math.atan2(toY - fromY, toX - fromX);
        const headlen = 7;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(midX, midY);
        ctx.lineTo(midX - headlen * Math.cos(angle - Math.PI / 6), midY - headlen * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(midX - headlen * Math.cos(angle + Math.PI / 6), midY - headlen * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
    },

    drawCalloutBadge(ctx, text, x, y, textColor, borderColor) {
        ctx.font = "bold 9px 'JetBrains Mono', monospace";
        const metrics = ctx.measureText(text);
        const padX = 6;
        const padY = 3;
        const bw = metrics.width + padX * 2;
        const bh = 16;

        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.strokeStyle = borderColor;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(x, y - 10, bw, bh, 4);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = textColor;
        ctx.fillText(text, x + padX, y + 2);
    },

    drawHoverTooltip(ctx, { point, px, py }) {
        const text1 = `Turn ${point.step}: ${point.isDeadlock ? "🚨 DEADLOCK" : (point.isDeflection ? "🩺 DOCTOR PIVOT" : "✅ HEALTHY")}`;
        const text2 = `v_t: ${typeof point.velocity === 'number' ? point.velocity.toFixed(3) : '1.000'} | Pos: (${point.x.toFixed(2)}, ${point.y.toFixed(2)})`;
        const text3 = `Action: ${point.label.substring(0, 36)}${point.label.length > 36 ? '...' : ''}`;

        ctx.font = "bold 11px 'JetBrains Mono', monospace";
        const w1 = ctx.measureText(text1).width;
        ctx.font = "10px 'JetBrains Mono', monospace";
        const w2 = ctx.measureText(text2).width;
        const w3 = ctx.measureText(text3).width;
        const maxW = Math.max(w1, w2, w3) + 20;
        const tooltipH = 58;

        let tx = px + 12;
        let ty = py - 30;
        if (tx + maxW > this.canvas.width) tx = px - maxW - 12;
        if (ty < 10) ty = py + 15;

        // Tooltip box
        ctx.fillStyle = "rgba(15, 23, 42, 0.95)";
        ctx.strokeStyle = point.isDeadlock ? "#f43f5e" : (point.isDeflection ? "#c084fc" : "#10b981");
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.roundRect(tx, ty, maxW, tooltipH, 6);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = point.isDeadlock ? "#fda4af" : (point.isDeflection ? "#e879f9" : "#6ee7b7");
        ctx.font = "bold 10px 'JetBrains Mono', monospace";
        ctx.fillText(text1, tx + 10, ty + 16);

        ctx.fillStyle = "#cbd5e1";
        ctx.font = "9.5px 'JetBrains Mono', monospace";
        ctx.fillText(text2, tx + 10, ty + 32);

        ctx.fillStyle = "#94a3b8";
        ctx.fillText(text3, tx + 10, ty + 47);
    }
};

window.addEventListener("resize", () => {
    if (window.ManifoldCanvas) {
        ManifoldCanvas.resize();
        ManifoldCanvas.render();
    }
});
