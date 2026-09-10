// App orchestration: builds controls, wires debounced recompute, renders everything.
(function () {
  "use strict";
  const CFG = window.ROF_CONFIG;
  const P = window.ROF_PLOTS;

  // ---- state ----
  let params = CFG.makeParams();
  let y0 = [1.0, 0.8, 0.2];
  let currentStage = "";
  let lastResult = null;
  const overlayState = {}; // stage_key -> bool
  const drakeFactors = { R_star: 1, f_p: 1, n_e: 1, f_l: 1, f_i: 1, f_c: 1, L: 1 };

  // ---- Recursive Take-off (RSI) tab ----
  // A curated recursive-transition civilisation whose take-off is dramatic
  // enough to read at a glance. Verified against the Python model: the "holds"
  // branch lands expansionist-visible (survives), the "fails" branch lands
  // collapse-proxy. The two branches differ ONLY in w (how fast recursion
  // erodes regulation), so the fork is attributable to regulation alone.
  const RSI_DEMO_PARAMS = {
    a: 0.60, b: 0.10, c: 0.40, sI: 0.16,
    u: 0.30, v: 0.25, w: 0.25, sR: 0.40,
    p: 0.50, q: 0.30, r: 0.40, m: 0.50, n: 0.30,
    A: 1.0, A_rec: 1.2, A_ref: 1.0, Q: 1.0,
    F_key: "superlinear", O_key: "peaked", obs_mode: "dynamic",
    E_key: "linear", B_key: "linear", X_key: "linear", C_key: "linear", S_key: "linear",
    tau_max: 30.0,
  };
  const RSI_DEMO_Y0 = [0.8, 0.85, 0.10];
  const RSI_W_HOLD = 0.25;   // regulation keeps pace with recursion
  const RSI_W_FAIL = 1.80;   // recursion erodes regulation faster than it rebuilds

  const $ = (id) => document.getElementById(id);
  const fmtNum = (v) => {
    if (v === 0) return "0";
    const a = Math.abs(v);
    if (a >= 1e5 || (a < 1e-3 && a > 0)) return v.toExponential(2);
    if (Number.isInteger(v)) return String(v);
    return parseFloat(v.toPrecision(4)).toString();
  };

  // ================= Build selectors =================
  function opt(v, label) { const o = document.createElement("option"); o.value = v; o.textContent = label || v; return o; }

  function buildSelect(id, values, labels) {
    const sel = $(id); sel.innerHTML = "";
    values.forEach((v, i) => sel.appendChild(opt(v, labels ? labels[i] : v)));
  }

  function buildStaticSelectors() {
    // stages
    const stageSel = $("stage-select");
    stageSel.innerHTML = "";
    stageSel.appendChild(opt("", "— Custom / Defaults —"));
    CFG.STAGE_ORDER.forEach(k => stageSel.appendChild(opt(k, CFG.STAGE_LABELS[k])));

    buildSelect("F_key", CFG.F_OPTIONS);
    buildSelect("O_key", CFG.O_OPTIONS);
    buildSelect("obs_mode", CFG.OBS_MODES);
    buildSelect("threshold_sign", ["1", "-1"], ["+1 (rising)", "−1 (falling)"]);
    Object.keys(CFG.COMPONENT_OPTIONS).forEach(k => buildSelect(k, CFG.COMPONENT_OPTIONS[k]));
  }

  // ================= Build IC + parameter sliders =================
  function makeSlider(name, min, max, val, label, onInput, decimals) {
    const wrap = document.createElement("div");
    wrap.className = "slider-item";
    const step = (max - min) / 1000;
    wrap.innerHTML = `
      <div class="sl-head">
        <span class="sl-label">${label}</span>
        <span class="sl-val" id="val-${name}">${fmtNum(val)}</span>
      </div>
      <input type="range" min="${min}" max="${max}" step="${step}" value="${val}" id="sl-${name}" />`;
    const input = wrap.querySelector("input");
    input.addEventListener("input", () => {
      const v = parseFloat(input.value);
      $("val-" + name).textContent = fmtNum(v);
      onInput(v);
    });
    return wrap;
  }

  function buildICsliders() {
    const grid = $("ic-grid"); grid.innerHTML = "";
    [["I0", 0, 10, 0], ["R0", 0, 5, 1], ["O0", 0, 5, 2]].forEach(([lbl, mn, mx, idx]) => {
      grid.appendChild(makeSlider("ic" + idx, mn, mx, y0[idx], lbl, (v) => { y0[idx] = v; markCustom(); schedule(); }));
    });
  }

  function buildParamGroups() {
    const container = $("param-groups"); container.innerHTML = "";
    Object.entries(CFG.PARAM_GROUPS).forEach(([group, keys], gi) => {
      const det = document.createElement("details");
      det.className = "pgroup";
      if (gi < 3) det.open = true;
      const sum = document.createElement("summary");
      sum.innerHTML = `<span>${group}</span>`;
      det.appendChild(sum);
      const body = document.createElement("div");
      body.className = "pgroup-body";
      keys.forEach(k => {
        const [mn, mx] = CFG.BOUNDS[k];
        body.appendChild(makeSlider(k, mn, mx, params[k], CFG.PARAM_LABELS[k], (v) => { params[k] = v; markCustom(); schedule(); }));
      });
      det.appendChild(body);
      container.appendChild(det);
    });
  }

  // update all slider positions/values to match params & y0 (after preset load)
  function syncSliders() {
    Object.keys(CFG.BOUNDS).forEach(k => {
      const sl = $("sl-" + k), vl = $("val-" + k);
      if (sl) { sl.value = params[k]; vl.textContent = fmtNum(params[k]); }
    });
    [0, 1, 2].forEach(i => {
      const sl = $("sl-ic" + i), vl = $("val-ic" + i);
      if (sl) { sl.value = y0[i]; vl.textContent = fmtNum(y0[i]); }
    });
    // selectors
    ["F_key", "O_key", "obs_mode", "E_key", "B_key", "X_key", "C_key", "S_key"].forEach(k => { const s = $(k); if (s) s.value = params[k]; });
    $("threshold_sign").value = String(params.threshold_sign);
    $("time_varying").checked = !!params.time_varying;
  }

  function markCustom() { currentStage = ""; $("stage-select").value = ""; }

  // ================= Overlay chips (phase) =================
  function buildOverlayChips() {
    const box = $("overlay-chips"); box.innerHTML = "";
    const lead = document.createElement("span");
    lead.style.cssText = "font-size:.78rem;color:var(--text-faint);align-self:center;margin-right:4px";
    lead.textContent = "Overlay:";
    box.appendChild(lead);
    const palette = ["#00d4ff", "#ff6b6b", "#ffd43b", "#845ef7", "#51cf66", "#ff922b", "#22b8cf", "#e599f7"];
    CFG.STAGE_ORDER.forEach((k, i) => {
      const chip = document.createElement("span");
      chip.className = "chip" + (overlayState[k] ? " on" : "");
      chip.textContent = CFG.STAGE_LABELS[k].replace(/^Stage /, "S").split(" — ")[0];
      chip.title = CFG.STAGE_LABELS[k];
      chip.style.setProperty("--c", palette[i % palette.length]);
      chip.dataset.key = k;
      chip.dataset.color = palette[i % palette.length];
      chip.addEventListener("click", () => {
        overlayState[k] = !overlayState[k];
        chip.classList.toggle("on", overlayState[k]);
        renderPhase();
      });
      box.appendChild(chip);
    });
  }

  function computeOverlays() {
    const out = [];
    const palette = {};
    document.querySelectorAll(".chip[data-key]").forEach(c => palette[c.dataset.key] = c.dataset.color);
    CFG.STAGE_ORDER.forEach(k => {
      if (overlayState[k]) {
        const sp = CFG.stageParams(k);
        const res = ROF.integrate(sp.params, sp.y0);
        out.push({ label: CFG.STAGE_LABELS[k].split(" — ")[0], res, color: palette[k] || "#888" });
      }
    });
    return out;
  }

  // ================= Drake sliders =================
  function buildDrakeSliders() {
    const box = $("drake-sliders"); box.innerHTML = "";
    const labels = { R_star: "R★ (star formation)", f_p: "f_p (planets)", n_e: "n_e (habitable)", f_l: "f_l (life)", f_i: "f_i (intelligence)", f_c: "f_c (technology)", L: "L (longevity)" };
    Object.keys(labels).forEach(k => {
      box.appendChild(makeSlider("dk_" + k, 0, 10, drakeFactors[k], labels[k], (v) => { drakeFactors[k] = v; renderDrake(); }));
    });
  }

  // ================= Recompute pipeline =================
  // rAF throttle (not debounce): coalesces rapid slider input to one recompute
  // per frame so the plots update WHILE dragging, not only on release.
  let rafPending = false;
  function schedule() {
    if (rafPending) return;
    rafPending = true;
    const raf = window.requestAnimationFrame || ((cb) => setTimeout(cb, 16));
    raf(() => { rafPending = false; recompute(); });
  }

  function recompute() {
    lastResult = ROF.integrate(params, y0);
    renderActiveTab();
    renderVerdict();
    renderDrake();
    render3D();
    renderSummary();
  }

  // 3D state-space view (I, R, O). Rendered twice for comparison: Plotly 3D and
  // three.js WebGL. Both guarded so the app runs even if either is unavailable.
  let three3d = null;
  function render3D() {
    if (!lastResult) return;
    if (window.ROF_PLOTS3D) {
      const el = $("plot3d-plotly");
      if (el) window.ROF_PLOTS3D.renderPlotly3D(el, lastResult);
    }
    if (three3d) three3d.update(lastResult);
    renderNarrative("3d", "narr-3d");
  }
  function setup3D() {
    if (window.ROF_PLOTS3D && window.THREE) {
      const el = $("plot3d-three");
      if (el) {
        try { three3d = new window.ROF_PLOTS3D.ThreeTrajectory(el); }
        catch (e) { three3d = null; }
      }
    } else {
      const el = $("plot3d-three");
      if (el && !window.THREE) el.innerHTML = '<div class="three-fallback">WebGL / three.js unavailable (offline or blocked). The Plotly 3D view on the left still works.</div>';
    }
  }

  // ================= Narrative interpretations =================
  // Build the value-context the narrative cases (js/narratives.js) test against.
  function narrCtx() {
    const r = lastResult, p = params, last = (a) => a[a.length - 1];
    let crit = null, lambertApplicable = ROF.lambertIsValid(p), lambertTrivial = false, lambertExceeded = false;
    if (lambertApplicable) {
      lambertTrivial = ROF.lambertBoundaryTrivial(p);
      crit = ROF.I_crit(p, last(r.R));
      lambertExceeded = crit !== null && last(r.I) > crit;
    }
    const O_peak = ROF.arrMax(r.O), O_final = last(r.O);
    return {
      I_final: last(r.I), R_final: last(r.R), O_final,
      I_peak: ROF.arrMax(r.I), O_peak, R_min: ROF.arrMin(r.R),
      P_det: last(r.P_det), N_obs: last(r.N_obs),
      regime: ROF.classifyRegime(r, p).label,
      crit, lambertApplicable, lambertTrivial, lambertExceeded,
      O_key: p.O_key, F_key: p.F_key, obs_mode: p.obs_mode,
      oPeakedThenFell: O_peak > 1e-6 && O_final < 0.7 * O_peak,
      th: { O_detectable: p.O_detectable, I_advanced: p.I_advanced, I_runaway: p.I_runaway, R_min: p.R_min, Theta: p.Theta, P_search: p.P_search },
    };
  }
  function renderNarrative(key, elId) {
    const el = $(elId);
    if (!el || !window.ROF_NARRATIVES || !lastResult) return;
    const m = window.ROF_NARRATIVES.match(key, narrCtx());
    if (!m) { el.innerHTML = ""; el.className = "narrative"; return; }
    el.className = "narrative " + (m.tone || "neutral");
    el.innerHTML = `<span class="narr-dot"></span><div class="narr-body"><p class="narr-title">${escapeHtml(m.title)}</p><p class="narr-text">${escapeHtml(m.text)}</p></div>`;
  }
  function renderSummary() {
    const el = $("narr-summary");
    if (!el || !window.ROF_NARRATIVES || !window.ROF_NARRATIVES.buildSummary || !lastResult) return;
    const s = window.ROF_NARRATIVES.buildSummary(narrCtx());
    el.className = "narrative narr-summary " + (s.tone || "neutral");
    el.innerHTML = `<span class="narr-dot"></span><div class="narr-body"><p class="narr-title">${escapeHtml(s.title)}</p><p class="narr-text" id="summary-text">${escapeHtml(s.text)}</p></div>`;
  }

  // ================= Renderers =================
  function activeTab() { return document.querySelector(".tab-btn.active").dataset.tab; }

  function renderActiveTab() {
    const t = activeTab();
    if (t === "traj") renderTraj();
    else if (t === "rsi") renderRSI();
    else if (t === "phase") renderPhase();
    else if (t === "lambert") renderLambert();
    else if (t === "ofunc") renderOFunc();
    else if (t === "regime") renderRegimeDetail();
    else if (t === "drake") { /* drake rendered separately */ }
  }

  function renderTraj() {
    if (!lastResult) return;
    P.plotIR($("plot-ir"), lastResult, params);
    P.plotO($("plot-o"), lastResult);
    P.plotN($("plot-n"), lastResult, params);
    renderNarrative("trajectories", "narr-traj");
  }
  function renderPhase() {
    if (!lastResult) return;
    P.plotPhase($("plot-phase"), lastResult, params, computeOverlays());
    renderNarrative("phase", "narr-phase");
  }

  // ---- Recursive Take-off (RSI) ----
  // First τ where the recursive growth term b·A_rec·F(I) overtakes ordinary
  // growth a·A·I — i.e. where capability starts improving itself faster than
  // it grows normally. Base drivers (no time-varying) match the marker's intent.
  function rsiOnsetTau(p, res) {
    const F = ROF.F_REGISTRY[p.F_key];
    for (let i = 0; i < res.I.length; i++) {
      const rec = p.b * p.A_rec * F(res.I[i], p);
      const ord = p.a * p.A * res.I[i];
      if (rec > ord) return res.tau[i];
    }
    return null;
  }
  // Two branches from the CURRENT settings, forking only on regulation erosion w.
  function computeRSIBranches() {
    const pHold = Object.assign({}, params, { w: RSI_W_HOLD });
    const pFail = Object.assign({}, params, { w: RSI_W_FAIL });
    const resHold = ROF.integrate(pHold, y0);
    const resFail = ROF.integrate(pFail, y0);
    return {
      hold: { res: resHold, params: pHold, regime: ROF.classifyRegime(resHold, pHold).label },
      fail: { res: resFail, params: pFail, regime: ROF.classifyRegime(resFail, pFail).label },
      onsetTau: rsiOnsetTau(pFail, resFail),
    };
  }
  function renderRSI() {
    const b = computeRSIBranches();
    P.plotRSI($("plot-rsi-cap"), $("plot-rsi-reg"), b, params);
    renderRSINarrative(b);
  }
  function renderRSINarrative(b) {
    const el = $("narr-rsi");
    if (!el) return;
    const onset = b.onsetTau;
    const onsetTxt = onset == null
      ? "Recursion never overtakes ordinary growth for these settings — load the demo, or raise the recursive terms (b, A_rec) or use a super-linear F(I), to see the take-off."
      : `Recursive self-improvement overtakes ordinary growth at τ ≈ ${onset.toFixed(1)}.`;
    const surv = /expansionist|optimized|visible/.test(b.hold.regime);
    const coll = /collapse|runaway/.test(b.fail.regime);
    const holdTxt = surv
      ? "with regulation intact, capability climbs to an advanced but controlled level and the civilisation survives"
      : `with strong regulation the civilisation ends in the ${b.hold.regime.replace(/-/g, " ")} regime`;
    const failTxt = coll
      ? "when recursion erodes control past its floor, capability runs away and self-control collapses"
      : `with weak regulation the civilisation ends in the ${b.fail.regime.replace(/-/g, " ")} regime`;
    el.className = "narrative " + (coll ? "warn" : "neutral");
    el.innerHTML = `<span class="narr-dot"></span><div class="narr-body">`
      + `<p class="narr-title">Same take-off, two fates</p>`
      + `<p class="narr-text">${escapeHtml(onsetTxt)} From that point on the branches diverge on one thing only — regulation: ${escapeHtml(holdTxt)}; ${escapeHtml(failTxt)}.</p>`
      + `</div>`;
  }
  function loadRSIDemo() {
    params = CFG.makeParams(RSI_DEMO_PARAMS);
    y0 = RSI_DEMO_Y0.slice();
    currentStage = "";
    $("stage-select").value = "";
    syncSliders();
    // make sure the tab is showing
    const btn = document.querySelector('.tab-btn[data-tab="rsi"]');
    if (btn && !btn.classList.contains("active")) btn.click();
    recompute();
  }
  function renderOFunc() { P.plotOFunc($("plot-ofunc"), params); renderNarrative("ofunc", "narr-ofunc"); }

  function renderLambert() {
    renderNarrative("lambert", "narr-lambert");
    const content = $("lambert-content");
    if (!ROF.lambertIsValid(params)) {
      content.innerHTML = `<div class="warn-panel"><strong>⚠ Lambert-W boundary is not applicable</strong>
        The Lambert-W critical boundary is only mathematically valid when the recursion has the form F(I) = I·e<sup>I</sup> — i.e. <code style="color:var(--gold)">F_key = "lambert"</code>.
        The current F(I) is <b>${params.F_key}</b>. For other forms a logarithmic fallback threshold applies instead:
        I = ln(c·R / (b·A_rec + ε))${(() => { const R = lastResult ? lastResult.R[lastResult.R.length - 1] : params.A_ref; const fb = ROF.fallbackThreshold(params, R); return fb === null ? " — no real solution for the current parameters." : ` ≈ <b>${fb.toFixed(3)}</b> at R_final.`; })()}
        <br><br>Switch F(I) to <b>lambert</b> in the sidebar to view the contour.</div>`;
      return;
    }
    if (ROF.lambertBoundaryTrivial(params)) {
      content.innerHTML = `<div class="warn-panel"><strong>⚠ Trivial boundary (A_ref ≤ 0)</strong>
        With A_ref ≤ 0 the regulation capacity C_R = c·R<sup>η</sup>·ln(1+A_ref)·E collapses to 0, so I_crit = W(0) = 0 everywhere — every capability level is "above" the boundary. Increase A_ref above 0 for a meaningful boundary.</div>`;
      return;
    }
    // ensure plot div exists
    content.innerHTML = `<div class="plot plot-tall" id="plot-lambert"></div><div class="lambert-status" id="lambert-status"></div>`;
    const R_final = lastResult ? lastResult.R[lastResult.R.length - 1] : 1.0;
    P.plotLambert($("plot-lambert"), params, R_final);
    // status
    const I_final = lastResult ? lastResult.I[lastResult.I.length - 1] : 0;
    const crit = ROF.I_crit(params, R_final);
    const exceeded = crit !== null && I_final > crit;
    $("lambert-status").innerHTML = `
      <span class="pill">I_crit(R_final) = ${crit === null ? "—" : crit.toFixed(3)}</span>
      <span class="pill">I_final = ${I_final.toFixed(3)}</span>
      <span class="pill ${exceeded ? "exceed" : "safe"}">${exceeded ? "⚠ Exceeded — past critical threshold" : "✓ Safe — below critical threshold"}</span>`;
  }

  function renderVerdict() {
    if (!lastResult) return;
    const { label, reasons } = ROF.classifyRegime(lastResult, params);
    const claim = ROF.CLAIM_STRENGTH[label];
    $("regime-name").textContent = label.replace(/-/g, " ");
    const badge = $("claim-badge");
    badge.className = "badge " + claim.color;
    badge.textContent = `${claim.icon} ${claim.label}`;
    $("regime-desc").textContent = ROF.REGIME_DESCRIPTIONS[label];
    $("regime-reasons").innerHTML = reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("");

    const r = lastResult;
    const I_f = r.I[r.I.length - 1], R_f = r.R[r.R.length - 1], O_f = r.O[r.O.length - 1];
    const N_f = r.N_obs[r.N_obs.length - 1], Pd_f = r.P_det[r.P_det.length - 1];
    const stats = [
      ["I_final", fmtNum(I_f)], ["R_final", fmtNum(R_f)], ["O_final", fmtNum(O_f)],
      ["I_peak", fmtNum(ROF.arrMax(r.I))], ["O_peak", fmtNum(ROF.arrMax(r.O))],
      ["P_det", fmtNum(Pd_f)], ["N_obs", fmtNum(N_f)],
    ];
    $("stat-strip").innerHTML = stats.map(([k, v]) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");
  }

  function renderRegimeDetail() {
    if (!lastResult) return;
    renderNarrative("regime", "narr-regime");
    const r = lastResult, p = params;
    const { label, reasons } = ROF.classifyRegime(r, p);
    const claim = ROF.CLAIM_STRENGTH[label];
    const I_f = r.I[r.I.length - 1], R_f = r.R[r.R.length - 1], O_f = r.O[r.O.length - 1];
    const I_pk = ROF.arrMax(r.I), O_pk = ROF.arrMax(r.O), R_mn = ROF.arrMin(r.R);
    const h_f = ROF.hDetect(Math.max(O_f, 0), p), Pd = h_f * p.P_search;
    const arec = p.A_rec / (R_f + p.eps);
    const runaway = I_f > p.I_runaway || arec > p.Theta;
    const rows = [
      ["1. Runaway", `I_final > I_runaway (${p.I_runaway}) OR A_rec/(R+ε) > Θ (${p.Theta})`, runaway],
      ["2. Collapse-proxy", `runaway AND (R_min < ${p.R_min} OR O peaked then < ${p.O_detectable})`, label === "collapse-proxy"],
      ["3. Runaway (final)", "runaway but not collapse", label === "runaway"],
      ["4. Pre-detectable", `O_peak < ${p.O_detectable} AND I_peak < ${p.I_advanced}`, label === "pre-detectable"],
      ["5. Optimized low-observable", `I_final ≥ ${p.I_advanced} AND R_final ≥ ${p.R_min} AND O_final < ${p.O_detectable}`, label === "optimized-low-observable"],
      ["6. Expansionist-visible", `I_final ≥ ${p.I_advanced} AND O_final ≥ ${p.O_detectable}`, label === "expansionist-visible"],
      ["7. Visible-technological", `P_det_final > 0.01`, label === "visible-technological"],
      ["8. Uncertain", "no criterion robustly met", label === "uncertain"],
    ];
    $("regime-detail").innerHTML = `
      <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:16px">
        <span class="badge ${claim.color}">${claim.icon} ${claim.label}</span>
        <span style="font-size:1.5rem;font-weight:700;text-transform:capitalize">${label.replace(/-/g, " ")}</span>
      </div>
      <p class="desc" style="color:var(--text-dim)">${ROF.REGIME_DESCRIPTIONS[label]}</p>
      <div class="stat-strip" style="margin:16px 0">
        ${[["I_final", I_f], ["R_final", R_f], ["O_final", O_f], ["I_peak", I_pk], ["O_peak", O_pk], ["R_min", R_mn], ["h(O)", h_f], ["P_det", Pd]]
          .map(([k, v]) => `<div class="stat"><div class="k">${k}</div><div class="v">${fmtNum(v)}</div></div>`).join("")}
      </div>
      <p class="reasons-title" style="color:var(--text-faint);text-transform:uppercase;letter-spacing:.12em;font-size:.72rem">Ordered decision trace</p>
      <div style="display:flex;flex-direction:column;gap:6px;margin-top:8px">
        ${rows.map(([n, cond, fired]) => `
          <div style="display:flex;gap:12px;align-items:center;padding:9px 12px;border-radius:10px;border:1px solid var(--glass-border);background:${fired ? "rgba(81,207,102,.08)" : "rgba(10,14,32,.4)"}">
            <span style="width:20px;flex:0 0 auto">${fired ? "✅" : "▫️"}</span>
            <span style="font-weight:600;min-width:190px;font-size:.85rem">${n}</span>
            <span style="color:var(--text-dim);font-family:var(--mono);font-size:.76rem">${escapeHtml(cond)}</span>
          </div>`).join("")}
      </div>
      <p class="reasons-title" style="color:var(--text-faint);text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;margin-top:18px">Reasons emitted</p>
      <ul class="reasons">${reasons.map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>`;
  }

  function renderDrake() {
    if (!lastResult) return;
    renderNarrative("drake", "narr-drake");
    const O_final = lastResult.O[lastResult.O.length - 1];
    const d = ROF.computeDrake(O_final, params, drakeFactors);
    $("drake-classical-out").textContent = "N = " + fmtNum(d.N_classical);
    $("drake-rof-out").textContent = "N_obs = " + fmtNum(d.N_obs_rof);

    const cf = [["R★", d.R_star], ["f_p", d.f_p], ["n_e", d.n_e], ["f_l", d.f_l], ["f_i", d.f_i], ["f_c", d.f_c], ["L", d.L]];
    $("drake-classical-chain").innerHTML = chainHtml(cf);
    const rf = [["N_true", d.N_true], ["P_surv", d.P_surv], ["P_sig=h(O)", d.P_sig], ["P_search", d.P_search]];
    $("drake-rof-chain").innerHTML = chainHtml(rf);
  }
  function chainHtml(pairs) {
    return pairs.map((p, i) => `${i > 0 ? '<span class="op">×</span>' : ""}<span class="factor"><span class="fk">${p[0]}</span><span class="fv">${fmtNum(p[1])}</span></span>`).join("");
  }

  function escapeHtml(s) { return String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
  function legacyCopy(txt) {
    try {
      const ta = document.createElement("textarea");
      ta.value = txt; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); document.body.removeChild(ta);
    } catch (e) { /* clipboard unavailable */ }
  }

  // ================= Load stage / reset =================
  function loadStage(key) {
    if (!key) return;
    const sp = CFG.stageParams(key);
    params = sp.params;
    y0 = sp.y0.slice();
    currentStage = key;
    syncSliders();
    recompute();
  }
  function loadDefaults() {
    params = CFG.makeParams();
    y0 = [1.0, 0.8, 0.2];
    currentStage = "";
    $("stage-select").value = "";
    syncSliders();
    recompute();
  }

  // ================= Wire events =================
  function wire() {
    $("stage-select").addEventListener("change", (e) => loadStage(e.target.value));
    ["F_key", "O_key", "obs_mode", "E_key", "B_key", "X_key", "C_key", "S_key"].forEach(k => {
      $(k).addEventListener("change", (e) => { params[k] = e.target.value; markCustom(); schedule(); });
    });
    $("threshold_sign").addEventListener("change", (e) => { params.threshold_sign = parseInt(e.target.value, 10); markCustom(); schedule(); });
    $("time_varying").addEventListener("change", (e) => { params.time_varying = e.target.checked; markCustom(); schedule(); });
    $("reset-btn").addEventListener("click", () => { if (currentStage) loadStage(currentStage); else loadDefaults(); });
    $("defaults-btn").addEventListener("click", loadDefaults);
    const rsiBtn = $("rsi-demo-btn");
    if (rsiBtn) rsiBtn.addEventListener("click", loadRSIDemo);

    const cp = $("copy-findings");
    if (cp) cp.addEventListener("click", () => {
      const t = $("summary-text");
      if (!t) return;
      const txt = t.textContent;
      const done = () => { const o = cp.textContent; cp.textContent = "Copied"; cp.classList.add("copied"); setTimeout(() => { cp.textContent = o; cp.classList.remove("copied"); }, 1400); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(done).catch(() => { legacyCopy(txt); done(); });
      } else { legacyCopy(txt); done(); }
    });

    document.querySelectorAll(".tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
        btn.classList.add("active");
        document.querySelector(`.tab-panel[data-panel="${btn.dataset.tab}"]`).classList.add("active");
        // resize/redraw plots on tab show
        renderActiveTab();
        setTimeout(() => window.dispatchEvent(new Event("resize")), 60);
      });
    });
  }

  // ================= KaTeX =================
  function renderKatex() {
    if (!window.katex) { setTimeout(renderKatex, 120); return; }
    document.querySelectorAll(".katex-line[data-eq]").forEach(el => {
      try { katex.render(el.dataset.eq, el, { displayMode: !el.style.display, throwOnError: false }); }
      catch (e) { el.textContent = el.dataset.eq; }
    });
  }

  // ================= Init =================
  function init() {
    buildStaticSelectors();
    buildICsliders();
    buildParamGroups();
    buildOverlayChips();
    buildDrakeSliders();
    wire();
    syncSliders();
    renderKatex();
    setup3D();
    // start on Stage 3 (defaults match s3 shape) — show something dynamic
    recompute();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
