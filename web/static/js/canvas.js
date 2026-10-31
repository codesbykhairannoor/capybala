/**
 * canvas.js - Phase-Space Trajectory Manifold Canvas Renderer
 * Visualizes 1024-D unit sphere projections, ergodic gravity wells, and Capybala deflection vectors.
 */

const ManifoldCanvas = {
    canvas: null,
    ctx: null,
    mode: 'spiral', // 'spiral' or 'deflect'
    particles: [],

    init() {
        this.canvas = document.getElementById("manifoldCanvas");
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext("2d");

        // Initialize background ambient particles
        this.particles = [];
        for (let i = 0; i < 35; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                size: Math.random() * 2 + 1,
                alpha: Math.random() * 0.4 + 0.1
            });
        }

        this.render();
    },

    setMode(newMode) {
        this.mode = newMode;
        this.render();
    },

    render() {
        if (!this.ctx || !this.canvas) return;
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const cx = w / 2;
        const cy = h / 2;

        // Clear canvas with dark slate background
        ctx.fillStyle = "#0a0c10";
        ctx.fillRect(0, 0, w, h);

        // Render ambient manifold particles
        this.particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(148, 163, 184, ${p.alpha})`;
            ctx.fill();
        });

        // Draw radial coordinate grid (Unit Sphere concentric shells)
        ctx.strokeStyle = "rgba(148, 163, 184, 0.12)";
        ctx.lineWidth = 1;
        for (let r = 40; r <= 160; r += 40) {
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.stroke();

            // Radius label
            ctx.fillStyle = "rgba(148, 163, 184, 0.35)";
            ctx.font = "9px JetBrains Mono";
            ctx.fillText(`r=${(r / 160).toFixed(2)}`, cx + r + 3, cy - 4);
        }

        // Draw center gravity well (Attractor Basin)
        const grad = ctx.createRadialGradient(cx, cy, 6, cx, cy, 75);
        grad.addColorStop(0, "rgba(225, 29, 72, 0.40)");
        grad.addColorStop(0.6, "rgba(225, 29, 72, 0.15)");
        grad.addColorStop(1, "rgba(225, 29, 72, 0.0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(cx, cy, 75, 0, Math.PI * 2);
        ctx.fill();

        // Label center attractor basin
        ctx.fillStyle = "rgba(244, 63, 94, 0.9)";
        ctx.font = "10px JetBrains Mono";
        ctx.textAlign = "center";
        ctx.fillText("ATTRACTOR BASIN (v_t < 0.70)", cx, cy + 4);

        // Compute trajectory points
        const points = [];
        if (this.mode === 'spiral') {
            // Decaying spiral inwards (trapped agent loop)
            for (let t = 0; t <= 12; t += 0.2) {
                const radius = 150 * Math.exp(-0.16 * t);
                const angle = t * 1.5;
                const x = cx + Math.cos(angle) * radius;
                const y = cy + Math.sin(angle) * radius;
                points.push({x, y});
            }
        } else {
            // Trajectory captured, then deflected by Capybala
            for (let t = 0; t <= 6.2; t += 0.2) {
                const radius = 150 * Math.exp(-0.16 * t);
                const angle = t * 1.5;
                const x = cx + Math.cos(angle) * radius;
                const y = cy + Math.sin(angle) * radius;
                points.push({x, y});
            }
            // Golden deflection vector pushing outwards
            const last = points[points.length - 1];
            points.push({x: last.x + 85, y: last.y - 75});
            points.push({x: last.x + 180, y: last.y - 135});
        }

        // Draw trajectory path line
        if (points.length > 0) {
            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
            ctx.strokeStyle = this.mode === 'spiral' ? "#e11d48" : "#10b981";
            ctx.lineWidth = 2.5;
            ctx.stroke();

            // Draw milestone nodes on the trajectory
            points.forEach((p, idx) => {
                if (idx % 3 === 0 || idx === points.length - 1) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, idx === points.length - 1 ? 5 : 3, 0, Math.PI * 2);
                    ctx.fillStyle = idx === points.length - 1 ? "#f59e0b" : (this.mode === 'spiral' ? "#f43f5e" : "#10b981");
                    ctx.fill();
                }
            });

            // If deflection mode, render explicit vector arrow and label
            if (this.mode === 'deflect') {
                const pDeflect = points[points.length - 3];
                ctx.strokeStyle = "#f59e0b";
                ctx.lineWidth = 3.5;
                ctx.beginPath();
                ctx.moveTo(pDeflect.x, pDeflect.y);
                ctx.lineTo(pDeflect.x + 65, pDeflect.y - 55);
                ctx.stroke();

                ctx.fillStyle = "#f59e0b";
                ctx.font = "bold 11px JetBrains Mono";
                ctx.textAlign = "left";
                ctx.fillText("CAPYBALA ATOMIC DEFLECTION", pDeflect.x + 75, pDeflect.y - 65);
            }
        }
    }
};

