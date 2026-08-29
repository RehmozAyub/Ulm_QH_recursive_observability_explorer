// 3D state-space (I, R, O) trajectory — TWO implementations for side-by-side
// comparison: Plotly 3D (scatter3d) and three.js (WebGL). Both take the same
// solved result and draw the path capability->regulation->observability.
(function (global) {
  "use strict";

  // downsample a long trajectory to keep 3D redraws smooth during slider drags
  function decimate(res, N) {
    const L = res.tau.length;
    if (L <= N) return { I: res.I, R: res.R, O: res.O, tau: res.tau };
    const step = Math.ceil(L / N);
    const idx = [];
    for (let i = 0; i < L; i += step) idx.push(i);
    if (idx[idx.length - 1] !== L - 1) idx.push(L - 1);
    const pick = (a) => idx.map((i) => a[i]);
    return { I: pick(res.I), R: pick(res.R), O: pick(res.O), tau: pick(res.tau) };
  }

  /* ============================ Plotly 3D ============================ */
  // travelling bead: a timer moves marker trace #3 along the path. A Plotly
  // redraw cancels an in-progress orbit drag, so the bead MUST pause while the
  // user is interacting with the plot (Plotly cannot redraw and orbit at once).
  // It resumes shortly after the pointer is released, so it still animates
  // whenever you are not actively dragging.
  function startPlotlyBead(div) {
    if (div._beadStarted) return;
    div._beadStarted = true;
    let resumeT = null;
    const pause = () => { div._beadPaused = true; if (resumeT) { clearTimeout(resumeT); resumeT = null; } };
    const resume = () => { if (resumeT) clearTimeout(resumeT); resumeT = setTimeout(() => { div._beadPaused = false; }, 250); };
    div.addEventListener("pointerdown", pause);
    div.addEventListener("wheel", () => { pause(); resume(); }, { passive: true });
    window.addEventListener("pointerup", resume);
    const tick = () => {
      if (div._beadPts && global.Plotly && div.isConnected && !div._beadPaused) {
        const d = div._beadPts, n = d.I.length;
        div._beadIdx = ((div._beadIdx || 0) + 1) % n;
        const i = div._beadIdx;
        try { global.Plotly.restyle(div, { x: [[d.I[i]]], y: [[d.R[i]]], z: [[d.O[i]]] }, [3]); } catch (e) { /* mid-react */ }
      }
      div._beadTimer = setTimeout(tick, 70);
    };
    tick();
  }
  function renderPlotly3D(div, res) {
    if (!div || !global.Plotly) return;
    const d = decimate(res, 240);
    const n = d.I.length;
    div._beadPts = d;
    if (div._beadIdx == null || div._beadIdx >= n) div._beadIdx = 0;
    const bi = div._beadIdx;
    const traces = [
      {
        type: "scatter3d", mode: "lines", name: "trajectory",
        x: d.I, y: d.R, z: d.O,
        line: { width: 6, color: d.tau, colorscale: [[0, "#6b4a1f"], [0.5, "#e0a24c"], [1, "#f6c877"]] },
        hovertemplate: "I=%{x:.3f}<br>R=%{y:.3f}<br>O=%{z:.3f}<extra></extra>",
      },
      { type: "scatter3d", mode: "markers", name: "start", x: [d.I[0]], y: [d.R[0]], z: [d.O[0]], marker: { size: 5, color: "#5ac37d" } },
      { type: "scatter3d", mode: "markers", name: "end", x: [d.I[n - 1]], y: [d.R[n - 1]], z: [d.O[n - 1]], marker: { size: 6, color: "#e8746e", symbol: "diamond" } },
      // trace #3: the travelling "now" bead
      { type: "scatter3d", mode: "markers", name: "now", x: [d.I[bi]], y: [d.R[bi]], z: [d.O[bi]], marker: { size: 7, color: "#ffe0a0", line: { color: "#e0a24c", width: 1 } } },
    ];
    const ax = (t) => ({
      title: { text: t, font: { size: 12, color: "#e0a24c" } },
      color: "#b6b6ae", gridcolor: "rgba(230,230,220,0.09)",
      zerolinecolor: "rgba(230,230,220,0.18)", backgroundcolor: "rgba(0,0,0,0)", showbackground: true,
    });
    const layout = {
      paper_bgcolor: "rgba(0,0,0,0)",
      font: { family: "JetBrains Mono, monospace", color: "#b6b6ae", size: 10 },
      margin: { l: 0, r: 0, t: 0, b: 0 }, showlegend: false,
      uirevision: "keep", // preserve the user's camera rotation across live redraws
      scene: { xaxis: ax("I"), yaxis: ax("R"), zaxis: ax("O"), bgcolor: "rgba(0,0,0,0)", camera: { eye: { x: 1.5, y: 1.4, z: 1.1 } } },
    };
    global.Plotly.react(div, traces, layout, { responsive: true, displaylogo: false, displayModeBar: false });
    startPlotlyBead(div);
  }

  /* ============================ three.js ============================ */
  function normalize(arr) {
    let mn = Infinity, mx = -Infinity;
    for (const v of arr) { if (v < mn) mn = v; if (v > mx) mx = v; }
    const span = (mx - mn) || 1;
    return { map: (v) => ((v - mn) / span) * 2 - 1, mn, mx };
  }
  function fmt(v) {
    const a = Math.abs(v);
    if (v === 0) return "0";
    if (a >= 100 || a < 0.01) return v.toExponential(1);
    return String(parseFloat(v.toPrecision(3)));
  }

  class ThreeTrajectory {
    constructor(container) {
      const THREE = global.THREE;
      this.THREE = THREE;
      this.container = container;
      const w = container.clientWidth || 420, h = container.clientHeight || 320;

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(48, w / h, 0.1, 100);
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.renderer.setSize(w, h);
      container.appendChild(this.renderer.domElement);

      // reference frame: faint bounding cube + colored axes at the (-1,-1,-1) corner
      const box = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.BoxGeometry(2, 2, 2)),
        new THREE.LineBasicMaterial({ color: 0x2a2e3e })
      );
      this.scene.add(box);
      const axes = new THREE.AxesHelper(0.7);
      axes.position.set(-1, -1, -1);
      this.scene.add(axes);

      this.group = new THREE.Group();
      this.scene.add(this.group);
      this.labelGroup = new THREE.Group();
      this.scene.add(this.labelGroup);

      // orbit state (hand-rolled: no OrbitControls dependency)
      this.radius = 4.4; this.theta = 0.9; this.phi = 1.05;
      this.target = new THREE.Vector3(0, 0, 0);
      this.dragging = false; this.autoRotate = true;
      this._bindControls();
      this._updateCamera();

      this.line = null; this.startDot = null; this.endDot = null; this.comet = null;
      this.pts = []; this.cometI = 0;

      this._onResize = this._onResize.bind(this);
      if (window.ResizeObserver) { this._ro = new ResizeObserver(this._onResize); this._ro.observe(container); }
      else window.addEventListener("resize", this._onResize);

      this._loop = this._loop.bind(this);
      this._raf = requestAnimationFrame(this._loop);
    }

    _bindControls() {
      const el = this.renderer.domElement;
      el.style.cursor = "grab";
      let px = 0, py = 0;
      const down = (e) => { this.dragging = true; this.autoRotate = false; el.style.cursor = "grabbing"; px = e.clientX; py = e.clientY; };
      const move = (e) => {
        if (!this.dragging) return;
        const dx = e.clientX - px, dy = e.clientY - py; px = e.clientX; py = e.clientY;
        this.theta -= dx * 0.01;
        this.phi = Math.max(0.15, Math.min(Math.PI - 0.15, this.phi - dy * 0.01));
        this._updateCamera();
      };
      const up = () => { this.dragging = false; el.style.cursor = "grab"; };
      el.addEventListener("pointerdown", down);
      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up);
      el.addEventListener("wheel", (e) => {
        e.preventDefault();
        this.radius = Math.max(2.4, Math.min(9, this.radius + Math.sign(e.deltaY) * 0.4));
        this._updateCamera();
      }, { passive: false });
      this._teardownControls = () => {
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerup", up);
      };
    }

    _updateCamera() {
      this.camera.position.set(
        this.target.x + this.radius * Math.sin(this.phi) * Math.cos(this.theta),
        this.target.y + this.radius * Math.cos(this.phi),
        this.target.z + this.radius * Math.sin(this.phi) * Math.sin(this.theta)
      );
      this.camera.lookAt(this.target);
    }

    _onResize() {
      const w = this.container.clientWidth, h = this.container.clientHeight;
      if (!w || !h) return;
      this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    }

    update(res) {
      const THREE = this.THREE;
      const d = decimate(res, 220);
      const nI = normalize(d.I), nR = normalize(d.R), nO = normalize(d.O);
      const pts = d.I.map((_, i) => new THREE.Vector3(nI.map(d.I[i]), nR.map(d.R[i]), nO.map(d.O[i])));
      this.pts = pts;
      this.cometI = 0;

      // clear previous
      while (this.group.children.length) {
        const c = this.group.children.pop();
        if (c.geometry) c.geometry.dispose();
        if (c.material) c.material.dispose();
        this.group.remove(c);
      }

      // gradient trajectory line (dark amber -> bright)
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const cols = new Float32Array(pts.length * 3);
      const c0 = new THREE.Color(0x6b4a1f), c1 = new THREE.Color(0xf6c877), tmp = new THREE.Color();
      for (let i = 0; i < pts.length; i++) {
        tmp.copy(c0).lerp(c1, i / (pts.length - 1));
        cols[i * 3] = tmp.r; cols[i * 3 + 1] = tmp.g; cols[i * 3 + 2] = tmp.b;
      }
      geo.setAttribute("color", new THREE.BufferAttribute(cols, 3));
      this.line = new THREE.Line(geo, new THREE.LineBasicMaterial({ vertexColors: true, linewidth: 2 }));
      this.group.add(this.line);

      const dot = (color, p, r) => {
        const m = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 16), new THREE.MeshBasicMaterial({ color }));
        m.position.copy(p); return m;
      };
      this.startDot = dot(0x5ac37d, pts[0], 0.04); this.group.add(this.startDot);
      this.endDot = dot(0xe8746e, pts[pts.length - 1], 0.05); this.group.add(this.endDot);
      this.comet = dot(0xffe0a0, pts[0], 0.045); this.group.add(this.comet);

      // axis tick numbers + axis names. Throttled: creating canvas-texture
      // sprites is the costly part, so rebuild at most ~5x/sec even though the
      // geometry above updates every frame during a slider drag.
      const now = (window.performance && performance.now) ? performance.now() : Date.now();
      if (!this._lastLabelT || now - this._lastLabelT > 180) {
        this._lastLabelT = now;
        while (this.labelGroup.children.length) {
          const c = this.labelGroup.children.pop();
          if (c.material) { if (c.material.map) c.material.map.dispose(); c.material.dispose(); }
          this.labelGroup.remove(c);
        }
        const ranges = { I: nI, R: nR, O: nO };
        const addTicks = (axis, toVec) => {
          const rg = ranges[axis];
          [-1, 0, 1].forEach((t) => {
            const real = rg.mn + ((t + 1) / 2) * (rg.mx - rg.mn);
            const sp = this._label(fmt(real), 0.17, "#9c9c95");
            sp.position.copy(toVec(t));
            this.labelGroup.add(sp);
          });
        };
        addTicks("I", (t) => new THREE.Vector3(t, -1.14, -1.14));
        addTicks("R", (t) => new THREE.Vector3(-1.14, t, -1.14));
        addTicks("O", (t) => new THREE.Vector3(-1.14, -1.14, t));
        const nm = (txt, pos) => { const sp = this._label(txt, 0.3, "#e0a24c"); sp.position.copy(pos); this.labelGroup.add(sp); };
        nm("I", new THREE.Vector3(1.32, -1.14, -1.14));
        nm("R", new THREE.Vector3(-1.14, 1.32, -1.14));
        nm("O", new THREE.Vector3(-1.14, -1.14, 1.32));
      }
    }

    _label(text, size, color) {
      const THREE = this.THREE;
      const s = 128;
      const cv = document.createElement("canvas");
      cv.width = cv.height = s;
      const g = cv.getContext("2d");
      g.font = "bold 40px 'JetBrains Mono', monospace";
      g.fillStyle = color; g.textAlign = "center"; g.textBaseline = "middle";
      g.fillText(text, s / 2, s / 2);
      const tex = new THREE.CanvasTexture(cv);
      tex.minFilter = THREE.LinearFilter;
      const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false });
      const sp = new THREE.Sprite(mat);
      sp.scale.set(size, size, 1);
      return sp;
    }

    _loop() {
      if (this.autoRotate && !this.dragging) { this.theta += 0.0016; this._updateCamera(); }
      // travel the comet head along the path to show direction of time
      if (this.pts.length && this.comet) {
        this.cometI = (this.cometI + 1) % this.pts.length;
        this.comet.position.copy(this.pts[this.cometI]);
      }
      this.renderer.render(this.scene, this.camera);
      this._raf = requestAnimationFrame(this._loop);
    }

    dispose() {
      if (this._raf) cancelAnimationFrame(this._raf);
      if (this._ro) this._ro.disconnect();
      if (this._teardownControls) this._teardownControls();
      this.renderer.dispose();
      if (this.renderer.domElement.parentNode) this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
  }

  global.ROF_PLOTS3D = { renderPlotly3D, ThreeTrajectory };
})(typeof window !== "undefined" ? window : globalThis);
