// Animated deep-space background: parallax starfield + burning meteors.
// Performant (rAF, capped particle counts), respects prefers-reduced-motion.
(function () {
  "use strict";
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d", { alpha: true });
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let W = 0, H = 0, DPR = Math.min(window.devicePixelRatio || 1, 2);
  let stars = [];
  const LAYERS = [
    { count: 90, speed: 0.015, size: [0.4, 0.9], alpha: 0.5 },
    { count: 55, speed: 0.045, size: [0.7, 1.4], alpha: 0.75 },
    { count: 26, speed: 0.09, size: [1.0, 2.0], alpha: 1.0 },
  ];

  function resize() {
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    buildStars();
  }

  function rand(a, b) { return a + Math.random() * (b - a); }

  function buildStars() {
    stars = [];
    // scale counts by area so large screens aren't sparse, small aren't overloaded
    const scale = Math.min(1.4, Math.max(0.5, (W * H) / (1440 * 900)));
    LAYERS.forEach((L, li) => {
      const n = Math.round(L.count * scale);
      for (let i = 0; i < n; i++) {
        stars.push({
          x: Math.random() * W,
          y: Math.random() * H,
          r: rand(L.size[0], L.size[1]),
          a: L.alpha * rand(0.5, 1),
          sp: L.speed,
          tw: Math.random() * Math.PI * 2,
          tws: rand(0.006, 0.02),
          hue: Math.random() < 0.15 ? rand(190, 230) : (Math.random() < 0.5 ? 210 : 45),
          layer: li,
        });
      }
    });
  }

  // Meteors
  let meteors = [];
  const MAX_METEORS = 3;
  function spawnMeteor() {
    if (meteors.length >= MAX_METEORS) return;
    const fromTop = Math.random() < 0.6;
    const startX = rand(W * 0.15, W * 1.05);
    const startY = fromTop ? rand(-40, H * 0.25) : rand(-40, -10);
    const angle = rand(Math.PI * 0.62, Math.PI * 0.82); // down-left-ish
    const speed = rand(6.5, 11);
    meteors.push({
      x: startX, y: startY,
      vx: -Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      len: rand(90, 200),
      life: 0, maxLife: rand(60, 120),
      size: rand(1.4, 2.8),
      trail: [],
      embers: [],
    });
  }

  function drawMeteor(m) {
    // trail as fiery gradient line
    const tx = m.x - m.vx * (m.len / 10);
    const ty = m.y - m.vy * (m.len / 10);
    const grad = ctx.createLinearGradient(m.x, m.y, tx, ty);
    grad.addColorStop(0, "rgba(255,255,235,0.95)");
    grad.addColorStop(0.15, "rgba(255,200,90,0.85)");
    grad.addColorStop(0.5, "rgba(255,120,40,0.45)");
    grad.addColorStop(1, "rgba(255,60,20,0)");
    ctx.strokeStyle = grad;
    ctx.lineWidth = m.size;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(m.x, m.y);
    ctx.lineTo(tx, ty);
    ctx.stroke();

    // glowing head
    const hg = ctx.createRadialGradient(m.x, m.y, 0, m.x, m.y, m.size * 6);
    hg.addColorStop(0, "rgba(255,250,230,0.9)");
    hg.addColorStop(0.4, "rgba(255,170,60,0.5)");
    hg.addColorStop(1, "rgba(255,90,30,0)");
    ctx.fillStyle = hg;
    ctx.beginPath();
    ctx.arc(m.x, m.y, m.size * 6, 0, Math.PI * 2);
    ctx.fill();

    // ember particles
    for (const e of m.embers) {
      ctx.globalAlpha = e.a;
      ctx.fillStyle = e.c;
      ctx.beginPath();
      ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  function updateMeteor(m) {
    m.x += m.vx;
    m.y += m.vy;
    m.life++;
    // spawn embers occasionally
    if (Math.random() < 0.6) {
      m.embers.push({
        x: m.x + rand(-2, 2), y: m.y + rand(-2, 2),
        vx: -m.vx * 0.08 + rand(-0.6, 0.6),
        vy: -m.vy * 0.08 + rand(-0.6, 0.6),
        r: rand(0.6, 1.8), a: rand(0.6, 1),
        c: Math.random() < 0.5 ? "rgba(255,180,80,1)" : "rgba(255,110,50,1)",
      });
    }
    for (const e of m.embers) {
      e.x += e.vx; e.y += e.vy; e.a -= 0.03; e.r *= 0.985;
    }
    m.embers = m.embers.filter((e) => e.a > 0.03);
  }

  let last = 0, meteorTimer = 0, nextMeteorGap = rand(2200, 5000);
  function frame(ts) {
    const dt = ts - last; last = ts;
    ctx.clearRect(0, 0, W, H);

    // stars
    for (const s of stars) {
      s.x -= s.sp * (dt * 0.06);
      if (s.x < -3) { s.x = W + 3; s.y = Math.random() * H; }
      s.tw += s.tws;
      const tw = 0.6 + 0.4 * Math.sin(s.tw);
      const alpha = s.a * tw;
      if (s.hue === 45) ctx.fillStyle = `rgba(255,220,150,${alpha})`;
      else if (s.hue > 190) ctx.fillStyle = `rgba(150,200,255,${alpha})`;
      else ctx.fillStyle = `rgba(220,228,255,${alpha})`;
      if (s.layer === 2 && s.r > 1.4) {
        ctx.shadowColor = "rgba(120,170,255,.6)"; ctx.shadowBlur = 4;
      } else { ctx.shadowBlur = 0; }
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    // meteors
    meteorTimer += dt;
    if (meteorTimer > nextMeteorGap) {
      meteorTimer = 0; nextMeteorGap = rand(2600, 6500);
      spawnMeteor();
    }
    for (const m of meteors) { updateMeteor(m); drawMeteor(m); }
    meteors = meteors.filter((m) => m.life < m.maxLife && m.x > -260 && m.y < H + 260);

    rafId = requestAnimationFrame(frame);
  }

  let rafId = null;
  function drawStatic() {
    ctx.clearRect(0, 0, W, H);
    for (const s of stars) {
      ctx.fillStyle = s.hue === 45 ? `rgba(255,220,150,${s.a})` : `rgba(210,224,255,${s.a})`;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
    }
  }

  window.addEventListener("resize", () => {
    clearTimeout(window.__bgrt);
    window.__bgrt = setTimeout(() => { resize(); if (reduced) drawStatic(); }, 150);
  });

  resize();
  if (reduced) {
    drawStatic();
  } else {
    rafId = requestAnimationFrame(frame);
    // pause when tab hidden to save CPU
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) { if (rafId) { cancelAnimationFrame(rafId); rafId = null; } }
      else if (!rafId) { last = performance.now(); rafId = requestAnimationFrame(frame); }
    });
  }
})();
