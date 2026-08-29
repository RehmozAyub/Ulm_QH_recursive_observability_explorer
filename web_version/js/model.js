// Recursive Observability Filter (ROF) model — JS port of the Python ground truth.
// Math must match model/*.py exactly.
(function (global) {
  "use strict";

  const EXP_CLIP = 50.0;
  function safeExp(x) {
    if (x > EXP_CLIP) x = EXP_CLIP;
    else if (x < -EXP_CLIP) x = -EXP_CLIP;
    return Math.exp(x);
  }

  // ---------------------------------------------------------------------------
  // Lambert W (principal branch W0) via Halley's method
  // ---------------------------------------------------------------------------
  function lambertW0(x) {
    if (x === 0) return 0.0;
    const EM = -1.0 / Math.E; // -0.3678794...
    if (x < EM) return NaN; // outside principal-branch real domain
    let w;
    if (x < 0) {
      // series init for -1/e <= x < 0
      w = x * (1.0 - x);
    } else if (x <= 1.0) {
      // near origin: series-based init works well; use w=x for small/moderate
      w = x / (1.0 + x);
    } else {
      w = Math.log(x) - Math.log(Math.log(x));
    }
    for (let i = 0; i < 40; i++) {
      const ew = Math.exp(w);
      const we = w * ew;
      const num = we - x;
      const denom = ew * (w + 1.0) - (w + 2.0) * num / (2.0 * w + 2.0);
      const dw = num / denom;
      w -= dw;
      if (Math.abs(dw) < 1e-14 * (1.0 + Math.abs(w))) break;
    }
    return w;
  }

  // ---------------------------------------------------------------------------
  // Registries
  // ---------------------------------------------------------------------------
  const F_REGISTRY = {
    linear: (I, p) => I,
    superlinear: (I, p) => I * I,
    lambert: (I, p) => I * safeExp(I),
    exponential: (I, p) => safeExp(I),
    saturating: (I, p) => I / (1.0 + I / p.K),
  };

  const O_REGISTRY = {
    increasing: (I, p) => 1.0 - safeExp(-p.lam * I),
    decreasing: (I, p) => safeExp(-p.lam * I),
    peaked: (I, p) => I * safeExp(-p.lam * I),
    threshold: (I, p) => {
      const arg = p.threshold_sign * p.k * (I - p.Ic);
      return 1.0 / (1.0 + safeExp(-arg));
    },
  };

  const E_REGISTRY = {
    linear: (I, R, p) => I,
    kardashev: (I, R, p) => I * I,
  };
  const B_REGISTRY = {
    linear: (I, R, p) => I,
    decaying: (I, R, p) => I * safeExp(-p.lam * I),
  };
  const X_REGISTRY = {
    linear: (I, R, p) => I,
    inward: (I, R, p) => 0.0,
  };
  const C_REGISTRY = {
    linear: (I, R, p) => I * R,
    superlinear: (I, R, p) => I * I * R,
  };
  const S_REGISTRY = {
    linear: (I, R, p) => I * R,
    superlinear: (I, R, p) => I * I * R,
  };

  // ---------------------------------------------------------------------------
  // Detection chain
  // ---------------------------------------------------------------------------
  function hDetect(O, p) {
    const Opos = Math.max(O, 0.0);
    return 1.0 - safeExp(-p.kappa * Opos);
  }
  function pDet(O, p) {
    return hDetect(O, p) * p.P_search;
  }
  function nObs(O, p) {
    return p.N_true * p.P_surv * hDetect(O, p) * p.P_search;
  }

  // ---------------------------------------------------------------------------
  // Time-varying drivers
  // ---------------------------------------------------------------------------
  function driverValue(name, tau, p) {
    const base = p[name];
    if (!p.time_varying) return base;
    if (name === "A") return base * (1.0 + 0.05 * tau);
    if (name === "A_rec") {
      const tauMid = p.tau_max * 0.4;
      return base * (1.0 + 1.5 / (1.0 + Math.exp(-0.2 * (tau - tauMid))));
    }
    if (name === "A_ref") return base * (1.0 + 0.02 * tau);
    if (name === "Q") return base * Math.exp(-0.015 * tau);
    return base;
  }

  // ---------------------------------------------------------------------------
  // ODE right-hand side
  // ---------------------------------------------------------------------------
  function rhs(tau, y, p, dynamic) {
    const I = y[0];
    const R = y[1];
    const O = dynamic ? y[2] : 0.0;

    const A = driverValue("A", tau, p);
    const A_rec = driverValue("A_rec", tau, p);
    const A_ref = driverValue("A_ref", tau, p);
    const Q_val = driverValue("Q", tau, p);

    const FI = F_REGISTRY[p.F_key](I, p);

    const dI = p.a * A * I + p.b * A_rec * FI - p.c * R * I - p.sI * I * I;
    const dR = p.u * A_ref + p.v * Q_val - p.w * A_rec - p.sR * R;

    if (!dynamic) return [dI, dR];

    const dO =
      p.p * E_REGISTRY[p.E_key](I, R, p) +
      p.q * B_REGISTRY[p.B_key](I, R, p) +
      p.r * X_REGISTRY[p.X_key](I, R, p) -
      p.m * C_REGISTRY[p.C_key](I, R, p) -
      p.n * S_REGISTRY[p.S_key](I, R, p);
    return [dI, dR, dO];
  }

  // ---------------------------------------------------------------------------
  // Dormand–Prince RK45 adaptive integrator with dense (quartic) interpolation
  // Mirrors scipy.integrate.solve_ivp(method="RK45")
  // ---------------------------------------------------------------------------
  // Butcher tableau (Dormand-Prince)
  const DP_C = [0, 1 / 5, 3 / 10, 4 / 5, 8 / 9, 1, 1];
  const DP_A = [
    [],
    [1 / 5],
    [3 / 40, 9 / 40],
    [44 / 45, -56 / 15, 32 / 9],
    [19372 / 6561, -25360 / 2187, 64448 / 6561, -212 / 729],
    [9017 / 3168, -355 / 33, 46732 / 5247, 49 / 176, -5103 / 18656],
    [35 / 384, 0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84],
  ];
  const DP_B = [35 / 384, 0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84, 0];
  // Error estimate coefficients E = b - b_hat (5th order minus 4th order)
  const DP_E = [
    71 / 57600, 0, -71 / 16695, 71 / 1920, -17253 / 339200, 22 / 525, -1 / 40,
  ];
  // Dense output interpolation coefficients (scipy P matrix), 7 stages x 4
  const DP_P = [
    [1, -8048581381 / 2820520608, 8663915743 / 2820520608, -12715105075 / 11282082432],
    [0, 0, 0, 0],
    [0, 131558114200 / 32700410799, -68118460800 / 10900136933, 87487479700 / 32700410799],
    [0, -1754552775 / 470086768, 14199869525 / 1410260304, -10690763975 / 1880347072],
    [0, 127303824393 / 49829197408, -318862633887 / 49829197408, 701980252875 / 199316789632],
    [0, -282668133 / 205662961, 2019193451 / 616988883, -1453857185 / 822651844],
    [0, 40617522 / 29380423, -110615467 / 29380423, 69997945 / 29380423],
  ];

  function vadd(a, b, s) {
    const n = a.length;
    const out = new Array(n);
    for (let i = 0; i < n; i++) out[i] = a[i] + b[i] * s;
    return out;
  }

  function rk45(fn, t0, t1, y0, rtol, atol) {
    // Returns array of {t, y} for dense output; we sample later.
    const n = y0.length;
    let t = t0;
    let y = y0.slice();
    let f = fn(t, y);

    // initial step selection (scipy-like)
    const dir = t1 > t0 ? 1 : -1;
    function norm(v) {
      let s = 0;
      for (let i = 0; i < n; i++) s += v[i] * v[i];
      return Math.sqrt(s / n);
    }
    // select initial step
    const scale0 = new Array(n);
    for (let i = 0; i < n; i++) scale0[i] = atol + Math.abs(y[i]) * rtol;
    let d0 = 0, d1 = 0;
    for (let i = 0; i < n; i++) {
      d0 += (y[i] / scale0[i]) ** 2;
      d1 += (f[i] / scale0[i]) ** 2;
    }
    d0 = Math.sqrt(d0 / n);
    d1 = Math.sqrt(d1 / n);
    let h;
    if (d0 < 1e-5 || d1 < 1e-5) h = 1e-6;
    else h = 0.01 * d0 / d1;
    const y1try = vadd(y, f, h * dir);
    const f1 = fn(t + h * dir, y1try);
    let d2 = 0;
    for (let i = 0; i < n; i++) d2 += ((f1[i] - f[i]) / scale0[i]) ** 2;
    d2 = Math.sqrt(d2 / n) / h;
    let h1;
    const maxd = Math.max(d1, d2);
    if (maxd <= 1e-15) h1 = Math.max(1e-6, h * 1e-3);
    else h1 = (0.01 / maxd) ** (1 / 5);
    h = Math.min(100 * h, h1, Math.abs(t1 - t0));

    const segments = [];
    const SAFETY = 0.9, MIN_FACTOR = 0.2, MAX_FACTOR = 10.0;
    const order = 5;
    let steps = 0;
    // Cap total steps: RK45 on a well-posed problem needs only thousands.
    // A much larger cap prevents UI freezes on stiff/explosive parameter sets.
    const MAX_STEPS = 120000;
    const span = Math.abs(t1 - t0);
    const H_MIN = Math.max(1e-12, span * 1e-11); // minimum meaningful step

    function allFinite(v) { for (let i = 0; i < v.length; i++) if (!isFinite(v[i])) return false; return true; }

    while ((t1 - t) * dir > 0) {
      if (steps++ > MAX_STEPS) break;
      let hAbs = Math.min(Math.abs(h), Math.abs(t1 - t));
      if (hAbs < H_MIN) hAbs = H_MIN;
      let accepted = false;
      let yNew, fNew, K;
      let innerTries = 0;
      while (!accepted) {
        if (innerTries++ > 60) { accepted = true; } // stop refining; accept to progress
        const hs = hAbs * dir;
        K = new Array(7);
        K[0] = f;
        for (let s = 1; s < 7; s++) {
          let ys = y.slice();
          for (let j = 0; j < s; j++) {
            const aij = DP_A[s][j];
            if (aij !== 0) for (let i = 0; i < n; i++) ys[i] += hs * aij * K[j][i];
          }
          K[s] = fn(t + DP_C[s] * hs, ys);
        }
        yNew = y.slice();
        for (let s = 0; s < 7; s++) {
          const bs = DP_B[s];
          if (bs !== 0) for (let i = 0; i < n; i++) yNew[i] += hs * bs * K[s][i];
        }
        fNew = fn(t + hs, yNew); // FSAL: K[6] approximates this, but recompute for dense
        // error estimate
        let errNorm = 0;
        for (let i = 0; i < n; i++) {
          let e = 0;
          for (let s = 0; s < 7; s++) e += DP_E[s] * K[s][i];
          e *= hs;
          const scale = atol + Math.max(Math.abs(y[i]), Math.abs(yNew[i])) * rtol;
          errNorm += (e / scale) ** 2;
        }
        errNorm = Math.sqrt(errNorm / n);
        // Non-finite state (overflow / blow-up): accept & stop integration cleanly.
        if (!isFinite(errNorm) || !allFinite(yNew)) {
          accepted = true;
          h = hAbs;
          break;
        }
        if (errNorm < 1) {
          accepted = true;
          let factor;
          if (errNorm === 0) factor = MAX_FACTOR;
          else factor = Math.min(MAX_FACTOR, SAFETY * errNorm ** (-1 / order));
          h = hAbs * factor;
        } else {
          hAbs *= Math.max(MIN_FACTOR, SAFETY * errNorm ** (-1 / order));
          if (hAbs < H_MIN) { accepted = true; hAbs = H_MIN; h = hAbs; } // give up shrinking
        }
      }
      // Abort if the new state is non-finite — record nothing further.
      if (!allFinite(yNew)) { break; }
      // store segment with dense coefficients Q = K^T . P  (n x 4)
      const hs = hAbs * dir;
      const Q = [];
      for (let i = 0; i < n; i++) {
        const row = [0, 0, 0, 0];
        for (let s = 0; s < 7; s++) {
          const ks = K[s][i];
          for (let d = 0; d < 4; d++) row[d] += ks * DP_P[s][d];
        }
        Q.push(row);
      }
      segments.push({ t0: t, t1: t + hs, h: hs, y0: y.slice(), Q: Q });
      t = t + hs;
      y = yNew;
      f = fNew;
    }
    return { segments, tEnd: t };
  }

  function denseEval(seg, t) {
    // x in [0,1]
    const x = (t - seg.t0) / seg.h;
    const n = seg.y0.length;
    // p = [x, x^2, x^3, x^4] cumulative product then * h
    const p1 = x, p2 = x * x, p3 = p2 * x, p4 = p3 * x;
    const out = new Array(n);
    for (let i = 0; i < n; i++) {
      const q = seg.Q[i];
      const dy = seg.h * (q[0] * p1 + q[1] * p2 + q[2] * p3 + q[3] * p4);
      out[i] = seg.y0[i] + dy;
    }
    return out;
  }

  function linspace(a, b, n) {
    const out = new Array(n);
    if (n === 1) { out[0] = a; return out; }
    const step = (b - a) / (n - 1);
    for (let i = 0; i < n; i++) out[i] = a + step * i;
    out[n - 1] = b;
    return out;
  }

  // ---------------------------------------------------------------------------
  // integrate() — mirrors solver.integrate
  // ---------------------------------------------------------------------------
  function integrate(params, y0, tauSpan) {
    const p = params;
    if (!tauSpan) tauSpan = [0.0, p.tau_max];
    const dynamic = p.obs_mode === "dynamic";
    const tEval = linspace(tauSpan[0], tauSpan[1], p.n_points);

    const y0vec = dynamic ? [y0[0], y0[1], y0[2]] : [y0[0], y0[1]];
    const fn = (t, y) => rhs(t, y, p, dynamic);

    const rtol = p.rtol || 1e-6;
    const atol = p.atol || 1e-9;
    const sol = rk45(fn, tauSpan[0], tauSpan[1], y0vec, rtol, atol);

    const N = tEval.length;
    const tau = tEval;
    const I = new Array(N), R = new Array(N), O = new Array(N);

    let segIdx = 0;
    const segs = sol.segments;
    const lastSeg = segs.length ? segs[segs.length - 1] : null;
    const tCoverEnd = lastSeg ? lastSeg.t1 : tauSpan[0];
    function hold(i, def) { return i > 0 ? [I[i - 1], R[i - 1], O[i - 1]] : def; }
    for (let i = 0; i < N; i++) {
      const t = tEval[i];
      let yv;
      if (segs.length === 0) {
        yv = y0vec;
      } else if ((t - tCoverEnd) * (tauSpan[1] >= tauSpan[0] ? 1 : -1) > 1e-9) {
        // t is past where integration reached (early stop / blow-up) -> hold last value
        const h = hold(i, y0vec); I[i] = h[0]; R[i] = h[1]; if (dynamic) O[i] = h[2] || 0; continue;
      } else {
        while (segIdx < segs.length - 1 && t > segs[segIdx].t1) segIdx++;
        yv = denseEval(segs[segIdx], t);
      }
      // sanitize non-finite (overflow): hold previous finite value
      if (!isFinite(yv[0]) || !isFinite(yv[1]) || (dynamic && !isFinite(yv[2]))) {
        const h = hold(i, y0vec); I[i] = h[0]; R[i] = h[1]; if (dynamic) O[i] = h[2] || 0; continue;
      }
      I[i] = yv[0];
      R[i] = yv[1];
      if (dynamic) O[i] = yv[2];
    }

    if (!dynamic) {
      const Ofunc = O_REGISTRY[p.O_key];
      for (let i = 0; i < N; i++) O[i] = Ofunc(I[i], p);
    }

    const O_eff = new Array(N), h = new Array(N), P_det = new Array(N), N_obs = new Array(N);
    for (let i = 0; i < N; i++) {
      O_eff[i] = Math.max(O[i], 0.0);
      h[i] = hDetect(O_eff[i], p);
      P_det[i] = pDet(O_eff[i], p);
      N_obs[i] = nObs(O_eff[i], p);
    }

    return {
      tau, I, R, O, O_eff, h, P_det, N_obs, params: p,
      success: sol.segments.length > 0, message: "ok",
    };
  }

  // ---------------------------------------------------------------------------
  // Lambert boundary computations
  // ---------------------------------------------------------------------------
  function lambertIsValid(p) { return p.F_key === "lambert"; }
  function lambertBoundaryTrivial(p) { return p.A_ref <= 0.0; }

  function C_R(p, R) {
    const R_safe = Math.max(R, p.eps);
    const logTerm = Math.log1p(Math.max(p.A_ref, 0.0));
    return p.c * Math.pow(R_safe, p.eta) * logTerm * p.E;
  }
  function I_crit(p, R) {
    if (!lambertIsValid(p)) return null;
    const cr = C_R(p, R);
    const denom = p.b * p.A_rec + p.eps;
    const arg = cr / denom;
    return lambertW0(arg);
  }
  function fallbackThreshold(p, R) {
    const R_safe = Math.max(R, p.eps);
    const denom = p.b * p.A_rec + p.eps;
    const arg = p.c * R_safe / denom;
    if (arg <= 0) return null;
    return Math.log(arg);
  }
  function lambertBoundaryGrid(p, ArecGrid, Rgrid) {
    const logTerm = Math.log1p(Math.max(p.A_ref, 0.0));
    const nr = Rgrid.length, na = ArecGrid.length;
    const grid = [];
    for (let ri = 0; ri < nr; ri++) {
      const CRvec = p.c * Math.pow(Math.max(Rgrid[ri], p.eps), p.eta) * logTerm * p.E;
      const row = new Array(na);
      for (let ai = 0; ai < na; ai++) {
        const arg = CRvec / (p.b * ArecGrid[ai] + p.eps);
        let w = lambertW0(arg);
        if (!isFinite(w) || w < 0) w = NaN;
        row[ai] = w;
      }
      grid.push(row);
    }
    return grid;
  }

  // ---------------------------------------------------------------------------
  // Regime classifier — mirrors regimes.classify_regime EXACTLY
  // ---------------------------------------------------------------------------
  const REGIME_DESCRIPTIONS = {
    "pre-detectable":
      "Civilisation has not yet developed sufficient capability or observability to be detectable by external observers.",
    "visible-technological":
      "Civilisation is in a technological phase with non-negligible detection probability — it leaks signals/waste heat.",
    "expansionist-visible":
      "Advanced, high-capability civilisation maintaining high observability through expansion, energy use, or broadcasts.",
    "runaway":
      "Recursive amplification has outstripped regulatory capacity. The system is beyond the modelled regulatory envelope.",
    "collapse-proxy":
      "Runaway conditions were met AND regulation/observability collapsed. Note: this is a *model proxy* for collapse, not proof.",
    "optimized-low-observable":
      "Advanced civilisation with sufficient regulation and LOW observability — capable but quiet. NOT physically invisible; thermodynamic waste persists but is minimised/redirected.",
    "uncertain":
      "Classification is ambiguous — no single regime criterion was robustly satisfied. Consider perturbing parameters.",
  };

  function arrMax(a) { let m = -Infinity; for (let i = 0; i < a.length; i++) if (a[i] > m) m = a[i]; return m; }
  function arrMin(a) { let m = Infinity; for (let i = 0; i < a.length; i++) if (a[i] < m) m = a[i]; return m; }

  function fmt(x, d) { return Number(x).toFixed(d); }

  function classifyRegime(result, p) {
    const I = result.I, R = result.R, O = result.O;
    const I_final = I[I.length - 1];
    const R_final = R[R.length - 1];
    const O_final = O[O.length - 1];
    const I_peak = arrMax(I);
    const O_peak = arrMax(O);
    const R_min_val = arrMin(R);

    const h_final = hDetect(Math.max(O_final, 0.0), p);
    const P_det_final = h_final * p.P_search;

    const reasons = [];
    const arec_over_R = p.A_rec / (R_final + p.eps);
    const runaway = I_final > p.I_runaway || arec_over_R > p.Theta;
    if (I_final > p.I_runaway)
      reasons.push(`I_final (${fmt(I_final, 2)}) > I_runaway (${p.I_runaway})`);
    if (arec_over_R > p.Theta)
      reasons.push(`A_rec/(R+ε) = ${fmt(arec_over_R, 2)} > Θ (${p.Theta})`);

    let collapse = false;
    if (runaway) {
      if (R_min_val < p.R_min) {
        reasons.push(`R_min (${fmt(R_min_val, 4)}) < R_min threshold (${p.R_min})`);
        collapse = true;
      }
      if (O_peak > p.O_detectable && O_final < p.O_detectable) {
        reasons.push(`O peaked (${fmt(O_peak, 3)}) then fell below O_detectable (${p.O_detectable})`);
        collapse = true;
      }
    }
    if (collapse) return { label: "collapse-proxy", reasons };
    if (runaway) return { label: "runaway", reasons };

    if (O_peak < p.O_detectable && I_peak < p.I_advanced) {
      reasons.push(`Peak O (${fmt(O_peak, 4)}) < O_detectable (${p.O_detectable}) and peak I (${fmt(I_peak, 2)}) < I_advanced (${p.I_advanced})`);
      return { label: "pre-detectable", reasons };
    }
    if (I_final >= p.I_advanced && R_final >= p.R_min && O_final < p.O_detectable) {
      reasons.push(`I_final (${fmt(I_final, 2)}) ≥ I_advanced (${p.I_advanced}), R_final (${fmt(R_final, 4)}) ≥ R_min (${p.R_min}), O_final (${fmt(O_final, 4)}) < O_detectable (${p.O_detectable})`);
      return { label: "optimized-low-observable", reasons };
    }
    if (I_final >= p.I_advanced && O_final >= p.O_detectable) {
      reasons.push(`I_final (${fmt(I_final, 2)}) ≥ I_advanced (${p.I_advanced}) and O_final (${fmt(O_final, 3)}) ≥ O_detectable (${p.O_detectable})`);
      return { label: "expansionist-visible", reasons };
    }
    if (P_det_final > 0.01) {
      reasons.push(`P_det_final (${fmt(P_det_final, 4)}) > 0.01 — civilisation is detectable`);
      return { label: "visible-technological", reasons };
    }
    reasons.push("No regime criterion was robustly satisfied.");
    return { label: "uncertain", reasons };
  }

  // ---------------------------------------------------------------------------
  // Claim strength
  // ---------------------------------------------------------------------------
  const CLAIM_STRENGTH = {
    "pre-detectable": { label: "Plausible", color: "blue", icon: "🔵" },
    "visible-technological": { label: "Plausible", color: "blue", icon: "🔵" },
    "uncertain": { label: "Plausible", color: "blue", icon: "🔵" },
    "expansionist-visible": { label: "Hypothetical", color: "yellow", icon: "🟡" },
    "optimized-low-observable": { label: "Hypothetical", color: "yellow", icon: "🟡" },
    "collapse-proxy": { label: "Hypothetical", color: "yellow", icon: "🟡" },
    "runaway": { label: "Speculative", color: "red", icon: "🔴" },
  };

  // ---------------------------------------------------------------------------
  // Drake decomposition
  // ---------------------------------------------------------------------------
  function computeDrake(O_value, p, drake) {
    const h = hDetect(Math.max(O_value, 0.0), p);
    const d = Object.assign({ R_star: 1, f_p: 1, n_e: 1, f_l: 1, f_i: 1, f_c: 1, L: 1 }, drake || {});
    const N_classical = d.R_star * d.f_p * d.n_e * d.f_l * d.f_i * d.f_c * d.L;
    const P_sig = h;
    const N_obs_rof = p.N_true * p.P_surv * P_sig * p.P_search;
    return { ...d, N_true: p.N_true, P_surv: p.P_surv, P_sig, P_search: p.P_search, N_classical, N_obs_rof };
  }

  global.ROF = {
    safeExp, lambertW0,
    F_REGISTRY, O_REGISTRY, E_REGISTRY, B_REGISTRY, X_REGISTRY, C_REGISTRY, S_REGISTRY,
    hDetect, pDet, nObs, driverValue, rhs, rk45, denseEval, linspace, integrate,
    lambertIsValid, lambertBoundaryTrivial, C_R, I_crit, fallbackThreshold, lambertBoundaryGrid,
    classifyRegime, REGIME_DESCRIPTIONS, CLAIM_STRENGTH, computeDrake,
    arrMax, arrMin,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = global.ROF;
})(typeof window !== "undefined" ? window : globalThis);
