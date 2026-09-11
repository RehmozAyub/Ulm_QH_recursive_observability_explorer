// ModelParams defaults, bounds, groups, labels, and stage presets — mirrors config.py + stages.py
(function (global) {
  "use strict";

  const DEFAULTS = {
    a: 0.30, b: 0.20, c: 0.50, sI: 0.10,
    u: 0.40, v: 0.30, w: 0.50, sR: 0.15,
    p: 0.50, q: 0.30, r: 0.40, m: 0.50, n: 0.30,
    A: 1.0, A_rec: 1.0, A_ref: 1.0, Q: 1.0,
    F_key: "saturating", O_key: "peaked", obs_mode: "dynamic",
    E_key: "linear", B_key: "linear", X_key: "linear", C_key: "linear", S_key: "linear",
    K: 5.0, lam: 0.30, k: 1.0, Ic: 5.0, threshold_sign: 1,
    kappa: 1.0, P_search: 0.50, P_surv: 0.80, N_true: 1.0,
    eta: 1.0, E: 1.0,
    Theta: 5.0, I_runaway: 50.0, R_min: 0.05, I_advanced: 5.0, O_detectable: 0.10, O_floor: 1e-3, eps: 1e-6,
    tau_max: 50.0, n_points: 1000, rtol: 1e-6, atol: 1e-9,
    term_damping: true, time_varying: false, stage_key: "",
  };

  const BOUNDS = {
    a: [0, 2], b: [0, 2], c: [0, 3], sI: [0, 1],
    u: [0, 2], v: [0, 2], w: [0, 3], sR: [0, 1],
    p: [0, 3], q: [0, 3], r: [0, 3], m: [0, 3], n: [0, 3],
    A: [0, 5], A_rec: [0, 5], A_ref: [0, 5], Q: [0, 5],
    K: [0.1, 50], lam: [0.01, 3], k: [0.1, 10], Ic: [0, 50],
    kappa: [0.01, 10], P_search: [0, 1], P_surv: [0, 1], N_true: [0, 1e6],
    eta: [0.1, 3], E: [0.01, 5],
    Theta: [0.1, 50], I_runaway: [1, 1000], R_min: [0, 1], I_advanced: [0, 100], O_detectable: [0, 1], O_floor: [0, 0.1],
    tau_max: [1, 500],
  };

  const PARAM_GROUPS = {
    "Capability (dI/dτ)": ["a", "b", "c", "sI"],
    "Regulation (dR/dτ)": ["u", "v", "w", "sR"],
    "Observability (dO/dτ)": ["p", "q", "r", "m", "n"],
    "Drivers": ["A", "A_rec", "A_ref", "Q"],
    "Shape parameters": ["K", "lam", "k", "Ic"],
    "Detection": ["kappa", "P_search", "P_surv", "N_true"],
    "Lambert": ["eta", "E"],
    "Thresholds": ["Theta", "I_runaway", "R_min", "I_advanced", "O_detectable", "O_floor"],
    "Solver / Time": ["tau_max"],
  };

  const PARAM_LABELS = {
    a: "a (ordinary growth)", b: "b (recursive growth)", c: "c (regulatory damping)", sI: "sI (capability saturation)",
    u: "u (reflective learning)", v: "v (institutional quality gain)", w: "w (erosion by A_rec)", sR: "sR (regulation decay)",
    p: "p (energy-use weight)", q: "q (broadcast weight)", r: "r (expansion weight)", m: "m (compression weight)", n: "n (stealth weight)",
    A: "A (amplification pressure)", A_rec: "A_rec (recursive amplification)", A_ref: "A_ref (reflective amplification)", Q: "Q (institutional quality)",
    K: "K (half-saturation)", lam: "λ (observability scale)", k: "k (sigmoid steepness)", Ic: "Ic (sigmoid midpoint)",
    kappa: "κ (detection sensitivity)", P_search: "P_search (search coverage)", P_surv: "P_surv (survival probability)", N_true: "N_true (true civ count)",
    eta: "η (regulation exponent)", E: "E (alignment factor)",
    Theta: "Θ (collapse threshold)", I_runaway: "I_runaway (runaway threshold)", R_min: "R_min (minimum regulation)",
    I_advanced: "I_advanced (advanced threshold)", O_detectable: "O_detectable (detection floor)", O_floor: "O_floor (thermodynamic floor)",
    tau_max: "τ_max (simulation time)",
  };

  const F_OPTIONS = ["linear", "superlinear", "lambert", "exponential", "saturating"];
  const O_OPTIONS = ["increasing", "decreasing", "peaked", "threshold"];
  const OBS_MODES = ["dynamic", "static"];
  const COMPONENT_OPTIONS = {
    E_key: ["linear", "kardashev"],
    B_key: ["linear", "decaying"],
    X_key: ["linear", "inward"],
    C_key: ["linear", "superlinear"],
    S_key: ["linear", "superlinear"],
  };

  // Stage presets: {overrides, y0}
  const STAGES = {
    s0: { over: { A_rec: 0, F_key: "linear", O_key: "increasing", obs_mode: "static", p: 0, q: 0, r: 0, a: 0.10, b: 0.0 }, y0: [0.01, 0.5, 0.0] },
    s1: { over: { A_rec: 0, F_key: "linear", O_key: "increasing", obs_mode: "static", a: 0.30, b: 0.0 }, y0: [0.2, 0.5, 0.0] },
    s2: { over: { A_rec: 0.2, F_key: "saturating", O_key: "increasing", obs_mode: "dynamic" }, y0: [0.5, 0.5, 0.1] },
    s3: { over: { A_rec: 1.5, F_key: "saturating", O_key: "peaked", obs_mode: "dynamic" }, y0: [1.0, 0.8, 0.2] },
    s4a: { over: { A_rec: 4.0, A_ref: 0.2, w: 2.0, F_key: "saturating", O_key: "peaked", obs_mode: "dynamic", sR: 0.30 }, y0: [1.5, 0.1, 0.1] },
    s4b: { over: { A_rec: 1.0, a: 0.50, c: 0.15, sI: 0.05, r: 2.0, m: 0.1, n: 0.1, F_key: "saturating", O_key: "increasing", obs_mode: "dynamic" }, y0: [2.0, 1.0, 0.5] },
    s4c: { over: { A_rec: 1.0, a: 0.50, c: 0.20, sI: 0.05, m: 2.0, n: 2.0, p: 0.3, q: 0.2, r: 0.2, F_key: "saturating", O_key: "peaked", obs_mode: "dynamic", I_advanced: 2.0 }, y0: [3.0, 1.5, 0.5] },
    s5: { over: { A_rec: 2.0, A_ref: 2.0, F_key: "saturating", O_key: "peaked", obs_mode: "dynamic", m: 2.5, n: 2.5, tau_max: 100.0 }, y0: [5.0, 3.0, 0.3] },
  };

  const STAGE_LABELS = {
    s0: "Stage 0 — Pre-technological",
    s1: "Stage 1 — Early technological",
    s2: "Stage 2 — Planetary technological",
    s3: "Stage 3 — Recursive transition",
    s4a: "Stage 4a — Collapse",
    s4b: "Stage 4b — Expansionist advanced",
    s4c: "Stage 4c — Optimized low-observable",
    s5: "Stage 5 — Post-biological (Speculative)",
  };
  const STAGE_ORDER = ["s0", "s1", "s2", "s3", "s4a", "s4b", "s4c", "s5"];

  function makeParams(overrides) {
    return Object.assign({}, DEFAULTS, overrides || {});
  }
  // Build full params for a stage: fresh defaults + stage overrides + stage_key
  function stageParams(key) {
    const s = STAGES[key];
    const p = makeParams(s.over);
    p.stage_key = key;
    return { params: p, y0: s.y0.slice() };
  }

  global.ROF_CONFIG = {
    DEFAULTS, BOUNDS, PARAM_GROUPS, PARAM_LABELS,
    F_OPTIONS, O_OPTIONS, OBS_MODES, COMPONENT_OPTIONS,
    STAGES, STAGE_LABELS, STAGE_ORDER, makeParams, stageParams,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = global.ROF_CONFIG;
})(typeof window !== "undefined" ? window : globalThis);
