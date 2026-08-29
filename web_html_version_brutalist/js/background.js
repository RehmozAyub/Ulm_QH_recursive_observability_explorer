// Living deep-space console background.
// Parallax starfield (twinkle + slow drift) + faint survey grid, with periodic
// FALLING METEORS (fast burning streaks) and TUMBLING ASTEROIDS (irregular rocks
// with a fiery leading edge, glowing trail and ember shower). Performant: capped
// counts, single rAF, pauses when the tab is hidden. Honors reduced motion by
// rendering one static frame.
(function () {
  "use strict";
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d", { alpha: true });
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let W = 0, H = 0;
  const DPR = Math.min(window.devicePixelRatio || 1, 2);
  const MINOR = 38, MAJOR = 4;
  const rand = (a, b) => a + Math.random() * (b - a);

  /* ---------------- stars (3 parallax layers) ---------------- */
  let stars = [];
  const LAYERS = [
    { count: 90, speed: 0.012, size: [0.4, 0.9], alpha: 0.5 },
    { count: 55, speed: 0.03,  size: [0.7, 1.4], alpha: 0.75 },
    { count: 28, speed: 0.06,  size: [1.0, 2.1], alpha: 1.0 },
  ];
  function buildStars() {
    stars = [];
    const scale = Math.min(1.5, Math.max(0.5, (W * H) / (1440 * 900)));
    LAYERS.forEach((L, li) => {
      const n = Math.round(L.count * scale);
      for (let i = 0; i < n; i++) {
        stars.push({
          x: Math.random() * W, y: Math.random() * H,
          r: rand(L.size[0], L.size[1]),
          a: L.alpha * rand(0.5, 1), sp: L.speed,
          tw: Math.random() * Math.PI * 2, tws: rand(0.006, 0.02),
          warm: Math.random() < 0.16, blue: Math.random() < 0.2,
          layer: li,
        });
      }
    });
  }

  /* ---------------- meteors (fast burning streaks) ---------------- */
  let meteors = [];
  const MAX_METEORS = 4;
  function spawnMeteor() {
    if (meteors.length >= MAX_METEORS) return;
    const startX = rand(W * 0.2, W * 1.1);
    const startY = rand(-60, H * 0.3);
    const angle = rand(Math.PI * 0.62, Math.PI * 0.82); // down-left
    const speed = rand(7, 12);
    meteors.push({
      x: startX, y: startY,
      vx: -Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
      len: rand(90, 210), size: rand(1.3, 2.6),
      life: 0, maxLife: rand(60, 120), embers: [],
    });
  }
  function drawMeteor(m) {
    const tx = m.x - m.vx * (m.len / 10), ty = m.y - m.vy * (m.len / 10);
    const g = ctx.createLinearGradient(m.x, m.y, tx, ty);
    g.addColorStop(0, "rgba(255,255,235,0.95)");
    g.addColorStop(0.15, "rgba(255,205,110,0.85)");
    g.addColorStop(0.5, "rgba(255,140,60,0.4)");
    g.addColorStop(1, "rgba(255,80,30,0)");
    ctx.strokeStyle = g; ctx.lineWidth = m.size; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(m.x, m.y); ctx.lineTo(tx, ty); ctx.stroke();
    const hg = ctx.createRadialGradient(m.x, m.y, 0, m.x, m.y, m.size * 6);
    hg.addColorStop(0, "rgba(255,250,230,0.9)");
    hg.addColorStop(0.4, "rgba(255,180,80,0.5)");
    hg.addColorStop(1, "rgba(255,100,40,0)");
    ctx.fillStyle = hg;
    ctx.beginPath(); ctx.arc(m.x, m.y, m.size * 6, 0, Math.PI * 2); ctx.fill();
    for (const e of m.embers) {
      ctx.globalAlpha = e.a; ctx.fillStyle = e.c;
      ctx.beginPath(); ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
  function updateMeteor(m) {
    m.x += m.vx; m.y += m.vy; m.life++;
    if (Math.random() < 0.55) m.embers.push({
      x: m.x + rand(-2, 2), y: m.y + rand(-2, 2),
      vx: -m.vx * 0.08 + rand(-0.6, 0.6), vy: -m.vy * 0.08 + rand(-0.6, 0.6),
      r: rand(0.6, 1.7), a: rand(0.6, 1),
      c: Math.random() < 0.5 ? "rgba(255,185,90,1)" : "rgba(255,115,55,1)",
    });
    for (const e of m.embers) { e.x += e.vx; e.y += e.vy; e.a -= 0.03; e.r *= 0.985; }
    m.embers = m.embers.filter((e) => e.a > 0.03);
  }

  /* ---------------- asteroids (tumbling rocks) ---------------- */
  let asteroids = [];
  const MAX_ASTEROIDS = 3;
  function makeShape(radius) {
    const n = Math.floor(rand(7, 11)), pts = [];
    for (let i = 0; i < n; i++) {
      const ang = (i / n) * Math.PI * 2;
      const rr = radius * rand(0.62, 1.12);
      pts.push([Math.cos(ang) * rr, Math.sin(ang) * rr]);
    }
    return pts;
  }
  function spawnAsteroid() {
    if (asteroids.length >= MAX_ASTEROIDS) return;
    const radius = rand(10, 20);
    const startX = rand(W * 0.15, W * 1.05);
    const angle = rand(Math.PI * 0.60, Math.PI * 0.80);
    const speed = rand(2.2, 4.2);
    asteroids.push({
      x: startX, y: rand(-80, -30),
      vx: -Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
      radius, shape: makeShape(radius),
      rot: rand(0, Math.PI * 2), vr: rand(-0.03, 0.03),
      embers: [], life: 0,
    });
  }
  function drawAsteroid(a) {
    // fiery trail behind the rock
    const tx = a.x - a.vx * 9, ty = a.y - a.vy * 9;
    const tg = ctx.createLinearGradient(a.x, a.y, tx, ty);
    tg.addColorStop(0, "rgba(255,190,90,0.55)");
    tg.addColorStop(0.5, "rgba(255,120,50,0.25)");
    tg.addColorStop(1, "rgba(255,70,30,0)");
    ctx.strokeStyle = tg; ctx.lineWidth = a.radius * 1.4; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(tx, ty); ctx.stroke();
    // embers
    for (const e of a.embers) {
      ctx.globalAlpha = e.a; ctx.fillStyle = e.c;
      ctx.beginPath(); ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
    // the rock
    ctx.save();
    ctx.translate(a.x, a.y); ctx.rotate(a.rot);
    ctx.beginPath();
    a.shape.forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)));
    ctx.closePath();
    const rg = ctx.createLinearGradient(-a.radius, -a.radius, a.radius, a.radius);
    rg.addColorStop(0, "#6b6660");
    rg.addColorStop(0.5, "#403c38");
    rg.addColorStop(1, "#2a2724");
    ctx.fillStyle = rg; ctx.fill();
    // hot leading rim (facing travel direction, roughly up-right before rotation)
    ctx.strokeStyle = "rgba(255,170,80,0.8)"; ctx.lineWidth = 1.6; ctx.stroke();
    ctx.restore();
    // glowing atmospheric halo
    const hg = ctx.createRadialGradient(a.x, a.y, a.radius * 0.5, a.x, a.y, a.radius * 2.2);
    hg.addColorStop(0, "rgba(255,160,70,0.22)");
    hg.addColorStop(1, "rgba(255,120,40,0)");
    ctx.fillStyle = hg;
    ctx.beginPath(); ctx.arc(a.x, a.y, a.radius * 2.2, 0, Math.PI * 2); ctx.fill();
  }
  function updateAsteroid(a) {
    a.x += a.vx; a.y += a.vy; a.rot += a.vr; a.life++;
    if (Math.random() < 0.7) a.embers.push({
      x: a.x + rand(-a.radius, a.radius) * 0.5, y: a.y + rand(-a.radius, a.radius) * 0.5,
      vx: -a.vx * 0.15 + rand(-0.8, 0.8), vy: -a.vy * 0.15 + rand(-0.8, 0.8),
      r: rand(0.8, 2.2), a: rand(0.6, 1),
      c: Math.random() < 0.5 ? "rgba(255,180,80,1)" : "rgba(255,110,45,1)",
    });
    for (const e of a.embers) { e.x += e.vx; e.y += e.vy; e.a -= 0.024; e.r *= 0.99; }
    a.embers = a.embers.filter((e) => e.a > 0.03);
  }

  /* ---------------- survey grid ---------------- */
  function drawGrid() {
    for (let i = 0, x = 0; x <= W; i++, x += MINOR) {
      ctx.strokeStyle = (i % MAJOR === 0) ? "rgba(200,214,255,0.045)" : "rgba(200,214,255,0.018)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(Math.round(x) + 0.5, 0); ctx.lineTo(Math.round(x) + 0.5, H); ctx.stroke();
    }
    for (let j = 0, y = 0; y <= H; j++, y += MINOR) {
      ctx.strokeStyle = (j % MAJOR === 0) ? "rgba(200,214,255,0.045)" : "rgba(200,214,255,0.018)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(0, Math.round(y) + 0.5); ctx.lineTo(W, Math.round(y) + 0.5); ctx.stroke();
    }
    ctx.strokeStyle = "rgba(224,162,76,0.14)"; ctx.lineWidth = 1;
    const step = MINOR * MAJOR;
    for (let x = step; x < W; x += step) for (let y = step; y < H; y += step) {
      ctx.beginPath();
      ctx.moveTo(x - 3, y); ctx.lineTo(x + 3, y);
      ctx.moveTo(x, y - 3); ctx.lineTo(x, y + 3); ctx.stroke();
    }
  }
  function drawStars(twinkle, dt) {
    for (const s of stars) {
      if (twinkle) {
        s.x -= s.sp * (dt * 0.06);
        if (s.x < -3) { s.x = W + 3; s.y = Math.random() * H; }
        s.tw += s.tws;
      }
      const t = twinkle ? (0.6 + 0.4 * Math.sin(s.tw)) : 1;
      const a = s.a * t;
      ctx.fillStyle = s.warm ? `rgba(240,200,140,${a})`
        : s.blue ? `rgba(150,195,255,${a})` : `rgba(214,224,255,${a})`;
      if (s.layer === 2 && s.r > 1.4) { ctx.shadowColor = "rgba(150,190,255,.55)"; ctx.shadowBlur = 4; }
      else ctx.shadowBlur = 0;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.shadowBlur = 0;
  }

  /* ---------------- loop ---------------- */
  // asteroid cadence ~30% more frequent (gaps shortened by ~1/1.3)
  let last = 0, mTimer = 0, mGap = rand(2400, 5200), aTimer = 0, aGap = rand(3800, 7700);
  function frame(ts) {
    const dt = ts - last; last = ts;
    ctx.clearRect(0, 0, W, H);
    drawStars(true, dt);
    drawGrid();

    mTimer += dt;
    if (mTimer > mGap) { mTimer = 0; mGap = rand(2600, 6000); spawnMeteor(); }
    for (const m of meteors) { updateMeteor(m); drawMeteor(m); }
    meteors = meteors.filter((m) => m.life < m.maxLife && m.x > -300 && m.y < H + 300);

    aTimer += dt;
    if (aTimer > aGap) { aTimer = 0; aGap = rand(4600, 9200); spawnAsteroid(); }
    for (const a of asteroids) { updateAsteroid(a); drawAsteroid(a); }
    asteroids = asteroids.filter((a) => a.x > -260 && a.y < H + 260 && a.x < W + 260);

    rafId = requestAnimationFrame(frame);
  }
  function drawStatic() {
    ctx.clearRect(0, 0, W, H);
    drawStars(false, 0);
    drawGrid();
  }

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * DPR; canvas.height = H * DPR;
    canvas.style.width = W + "px"; canvas.style.height = H + "px";
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    buildStars();
  }

  let rafId = null, rt;
  window.addEventListener("resize", () => {
    clearTimeout(rt);
    rt = setTimeout(() => { resize(); if (reduced) drawStatic(); }, 150);
  });

  resize();
  if (reduced) {
    drawStatic();
  } else {
    last = performance.now();
    rafId = requestAnimationFrame(frame);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) { if (rafId) { cancelAnimationFrame(rafId); rafId = null; } }
      else if (!rafId) { last = performance.now(); rafId = requestAnimationFrame(frame); }
    });
  }
})();
