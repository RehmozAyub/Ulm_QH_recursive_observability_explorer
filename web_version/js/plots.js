// Plotly.js dark-theme visualizations. Mirrors viz/plots.py.
// Brutalist reskin: neutral instrument axes/labels; categorical series colours
// kept (they encode I/R/O/N/P), tuned to match the shell's flatter palette.
(function (global) {
  "use strict";
  const C = {
    cyan: "#4fc7e0", coral: "#e8746e", gold: "#e6b53c",
    purple: "#9b7ff0", green: "#5ac37d",
  };

  const FONT = { family: "JetBrains Mono, ui-monospace, monospace", color: "#b6b6ae", size: 11 };
  const PLOT_BG = "rgba(0,0,0,0)";
  const GRID = "rgba(230,230,220,0.07)";
  const ZERO = "rgba(230,230,220,0.18)";

  function baseLayout(extra) {
    const L = {
      paper_bgcolor: PLOT_BG,
      plot_bgcolor: PLOT_BG,
      font: FONT,
      margin: { l: 58, r: 58, t: 18, b: 46 },
      hovermode: "x unified",
      showlegend: true,
      legend: { orientation: "h", y: 1.12, x: 0, bgcolor: "rgba(0,0,0,0)", font: { size: 11 } },
      xaxis: { gridcolor: GRID, zerolinecolor: ZERO, linecolor: GRID, title: { text: "τ (dimensionless time)", font: { size: 11 } } },
      yaxis: { gridcolor: GRID, zerolinecolor: ZERO, linecolor: GRID },
    };
    return Object.assign(L, extra || {});
  }
  const CONFIG = { responsive: true, displaylogo: false, displayModeBar: false };

  function firstCrossing(tau, a, b) {
    // first index where a > b (was <=)
    for (let i = 1; i < tau.length; i++) {
      if (a[i] > b[i] && a[i - 1] <= b[i - 1]) return i;
    }
    return -1;
  }
  function firstBelow(tau, a, thr) {
    for (let i = 0; i < tau.length; i++) if (a[i] < thr) return i;
    return -1;
  }

  // Plot 1: Capability & Regulation, twin y-axes
  function plotIR(div, res, params) {
    const t = res.tau;
    const traces = [
      { x: t, y: res.I, name: "I — capability", mode: "lines", line: { color: C.cyan, width: 2.4 }, yaxis: "y" },
      { x: t, y: res.R, name: "R — regulation", mode: "lines", line: { color: C.coral, width: 2.2, dash: "dash" }, yaxis: "y2" },
    ];
    const annotations = [];
    const cross = firstCrossing(t, res.I, res.R);
    if (cross > 0) {
      annotations.push({ x: t[cross], y: res.I[cross], xref: "x", yref: "y", text: "I crosses R", showarrow: true, arrowcolor: C.cyan, font: { color: C.cyan, size: 10 }, ax: 0, ay: -34, bgcolor: "rgba(0,20,40,.7)", bordercolor: C.cyan, borderwidth: 1, borderpad: 3 });
    }
    const below = firstBelow(t, res.R, params.R_min);
    if (below > 0) {
      annotations.push({ x: t[below], y: res.R[below], xref: "x", yref: "y2", text: "R < R_min", showarrow: true, arrowcolor: C.coral, font: { color: C.coral, size: 10 }, ax: 0, ay: 30, bgcolor: "rgba(40,0,10,.7)", bordercolor: C.coral, borderwidth: 1, borderpad: 3 });
    }
    const layout = baseLayout({
      yaxis: { title: { text: "I (capability)", font: { color: C.cyan } }, gridcolor: GRID, zerolinecolor: ZERO, tickfont: { color: C.cyan } },
      yaxis2: { title: { text: "R (regulation)", font: { color: C.coral } }, overlaying: "y", side: "right", gridcolor: "rgba(0,0,0,0)", zerolinecolor: "rgba(0,0,0,0)", tickfont: { color: C.coral } },
      annotations,
    });
    Plotly.react(div, traces, layout, CONFIG);
  }

  // Plot 2: Observability
  function plotO(div, res) {
    const t = res.tau;
    const O = res.O;
    let peakIdx = 0; for (let i = 1; i < O.length; i++) if (O[i] > O[peakIdx]) peakIdx = i;
    const annotations = [];
    const peakVal = O[peakIdx], finalVal = O[O.length - 1];
    if (peakVal > 0 && finalVal < peakVal * 0.7 && peakIdx < O.length - 1) {
      annotations.push({ x: t[peakIdx], y: peakVal, text: `peak, then −${(100 * (1 - finalVal / peakVal)).toFixed(0)}%`, showarrow: true, arrowcolor: C.gold, font: { color: C.gold, size: 10 }, ax: 20, ay: -30, bgcolor: "rgba(40,34,0,.7)", bordercolor: C.gold, borderwidth: 1, borderpad: 3 });
    }
    const traces = [
      { x: t, y: O, name: "O — observability", mode: "lines", line: { color: C.gold, width: 2.4 }, fill: "tozeroy", fillcolor: "rgba(255,212,59,0.12)" },
    ];
    const layout = baseLayout({ yaxis: { title: { text: "O (observability)", font: { color: C.gold } }, gridcolor: GRID, zerolinecolor: ZERO }, annotations, showlegend: true });
    Plotly.react(div, traces, layout, CONFIG);
  }

  // Plot 3: Detected population
  function plotN(div, res, params) {
    const t = res.tau;
    const traces = [
      { x: t, y: res.N_obs, name: "N_obs", mode: "lines", line: { color: C.green, width: 2.4 }, yaxis: "y" },
      { x: t, y: res.P_det, name: "P_det", mode: "lines", line: { color: C.purple, width: 2, dash: "dot" }, yaxis: "y2" },
    ];
    const finalN = res.N_obs[res.N_obs.length - 1];
    const layout = baseLayout({
      yaxis: { title: { text: "N_obs", font: { color: C.green } }, gridcolor: GRID, zerolinecolor: ZERO, tickfont: { color: C.green } },
      yaxis2: { title: { text: "P_det", font: { color: C.purple } }, overlaying: "y", side: "right", range: [0, 1], gridcolor: "rgba(0,0,0,0)", tickfont: { color: C.purple } },
      shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, yref: "y", y0: params.N_true, y1: params.N_true, line: { color: "rgba(200,210,255,.4)", width: 1, dash: "dash" } }],
      annotations: [
        { xref: "paper", x: 1, y: params.N_true, yref: "y", text: "N_true", showarrow: false, font: { size: 10, color: "rgba(200,210,255,.7)" }, xanchor: "right", yanchor: "bottom" },
        { x: t[t.length - 1], y: finalN, yref: "y", text: `N_obs → ${finalN.toPrecision(3)}`, showarrow: true, arrowcolor: C.green, ax: -30, ay: -22, font: { color: C.green, size: 10 }, bgcolor: "rgba(0,30,10,.7)", bordercolor: C.green, borderwidth: 1, borderpad: 3 },
      ],
    });
    Plotly.react(div, traces, layout, CONFIG);
  }

  // Plot 4: Phase diagram (I, O) with regime shading + overlays
  function plotPhase(div, mainRes, params, overlays) {
    const Ia = params.I_advanced, Od = params.O_detectable;
    // determine ranges
    let maxI = ROF.arrMax(mainRes.I), maxO = ROF.arrMax(mainRes.O);
    (overlays || []).forEach(o => { maxI = Math.max(maxI, ROF.arrMax(o.res.I)); maxO = Math.max(maxO, ROF.arrMax(o.res.O)); });
    maxI = Math.max(maxI * 1.08, Ia * 1.4, 1);
    maxO = Math.max(maxO * 1.08, Od * 2, 0.5);

    const shapes = [
      // pre-detectable: I<Ia, O<Od (bottom-left)
      rect(0, 0, Ia, Od, "rgba(77,171,247,0.08)"),
      // visible-tech / low band left-top: I<Ia, O>Od
      rect(0, Od, Ia, maxO, "rgba(81,207,102,0.06)"),
      // expansionist-visible: I>Ia, O>Od (top-right)
      rect(Ia, Od, maxI, maxO, "rgba(255,212,59,0.07)"),
      // low-observable: I>Ia, O<Od (bottom-right)
      rect(Ia, 0, maxI, Od, "rgba(132,94,247,0.08)"),
      { type: "line", x0: Ia, x1: Ia, y0: 0, y1: maxO, line: { color: "rgba(200,210,255,.28)", width: 1, dash: "dot" } },
      { type: "line", x0: 0, x1: maxI, y0: Od, y1: Od, line: { color: "rgba(200,210,255,.28)", width: 1, dash: "dot" } },
    ];
    const annotations = [
      regLabel(Ia / 2, Od / 2, "pre-detectable", "#4dabf7"),
      regLabel((Ia + maxI) / 2, (Od + maxO) / 2, "expansionist-visible", "#ffd43b"),
      regLabel((Ia + maxI) / 2, Od / 2, "low-observable", "#845ef7"),
      regLabel(Ia / 2, (Od + maxO) / 2, "visible-tech", "#51cf66"),
    ];

    const traces = [];
    (overlays || []).forEach(o => {
      traces.push({ x: o.res.I, y: o.res.O, name: o.label, mode: "lines", line: { color: o.color, width: 1.4 }, opacity: 0.6 });
    });
    traces.push({ x: mainRes.I, y: mainRes.O, name: "current", mode: "lines", line: { color: C.cyan, width: 2.6 } });
    traces.push({ x: [mainRes.I[0]], y: [mainRes.O[0]], name: "start", mode: "markers", marker: { color: C.green, size: 12, symbol: "circle", line: { color: "#fff", width: 1.5 } } });
    const li = mainRes.I.length - 1;
    traces.push({ x: [mainRes.I[li]], y: [mainRes.O[li]], name: "end", mode: "markers", marker: { color: C.coral, size: 13, symbol: "diamond", line: { color: "#fff", width: 1.5 } } });

    const layout = baseLayout({
      hovermode: "closest",
      xaxis: { title: { text: "I — capability" }, gridcolor: GRID, zerolinecolor: ZERO, range: [0, maxI] },
      yaxis: { title: { text: "O — observability" }, gridcolor: GRID, zerolinecolor: ZERO, range: [Math.min(0, ROF.arrMin(mainRes.O) * 1.05), maxO] },
      shapes, annotations,
    });
    Plotly.react(div, traces, layout, CONFIG);
  }
  function rect(x0, y0, x1, y1, color) {
    return { type: "rect", x0, y0, x1, y1, fillcolor: color, line: { width: 0 }, layer: "below" };
  }
  function regLabel(x, y, text, color) {
    return { x, y, text, showarrow: false, font: { size: 10, color }, opacity: 0.85 };
  }

  // Plot 5: Lambert boundary contour
  function plotLambert(div, params, R_final) {
    const na = 80, nr = 80;
    const Arec = ROF.linspace(0.1, 5, na);
    const Rg = ROF.linspace(0.05, 3, nr);
    const grid = ROF.lambertBoundaryGrid(params, Arec, Rg);
    const traces = [{
      z: grid, x: Arec, y: Rg, type: "contour",
      colorscale: "Inferno", colorbar: { title: { text: "I_crit", side: "right" }, tickfont: { size: 10 } },
      contours: { coloring: "heatmap" }, connectgaps: false,
    }];
    // star at current operating point
    const xStar = Math.min(Math.max(params.A_rec, 0.1), 5);
    const yStar = Math.min(Math.max(R_final, 0.05), 3);
    traces.push({ x: [xStar], y: [yStar], mode: "markers", type: "scatter", name: "operating point", marker: { color: "#ffffff", size: 16, symbol: "star", line: { color: "#000", width: 1 } }, showlegend: false });
    const layout = baseLayout({
      hovermode: "closest",
      xaxis: { title: { text: "A_rec — recursive amplification" }, gridcolor: GRID, range: [0.1, 5] },
      yaxis: { title: { text: "R — regulation" }, gridcolor: GRID, range: [0.05, 3] },
      showlegend: false, margin: { l: 58, r: 20, t: 18, b: 46 },
    });
    Plotly.react(div, traces, layout, CONFIG);
  }

  // Plot 6: O(I) function comparison
  function plotOFunc(div, params) {
    const I = ROF.linspace(0, 20, 240);
    const models = [
      { key: "increasing", name: "increasing (A): 1−e^(−λI)", color: C.green },
      { key: "decreasing", name: "decreasing (B): e^(−λI)", color: C.coral },
      { key: "peaked", name: "peaked (C): I·e^(−λI)", color: C.gold },
      { key: "threshold", name: "threshold (D): sigmoid", color: C.purple },
    ];
    const traces = models.map(m => {
      const fn = ROF.O_REGISTRY[m.key];
      const active = m.key === params.O_key;
      return {
        x: I, y: I.map(v => fn(v, params)), name: m.name + (active ? "  ●" : ""),
        mode: "lines", line: { color: m.color, width: active ? 3.4 : 1.6, dash: active ? "solid" : "dot" },
        opacity: active ? 1 : 0.6,
      };
    });
    const layout = baseLayout({
      hovermode: "x unified",
      xaxis: { title: { text: "I — capability" }, gridcolor: GRID, zerolinecolor: ZERO },
      yaxis: { title: { text: "O(I)" }, gridcolor: GRID, zerolinecolor: ZERO },
    });
    Plotly.react(div, traces, layout, CONFIG);
  }

  // Plot 7: Recursive Take-off. Two branches of one civilisation that fork only
  // on whether regulation keeps pace with recursion. Time on the x-axis; the
  // fails branch's trajectory ENDS at the collapse point (capability past the
  // runaway threshold), marked with an X. Regulation is bounded in [0, 1].
  function plotRSI(divCap, divReg, branches, params) {
    const HOLD = C.cyan, FAIL = C.coral;
    const hold = branches.hold.res, fail = branches.fail.res;
    const onset = branches.onsetTau;
    const hi = branches.hold.collapseIdx == null ? hold.tau.length - 1 : branches.hold.collapseIdx;
    const fi = branches.fail.collapseIdx == null ? fail.tau.length - 1 : branches.fail.collapseIdx;
    const failCollapsed = branches.fail.collapseIdx != null;
    const holdCollapsed = branches.hold.collapseIdx != null;
    const cut = (arr, n) => arr.slice(0, n + 1);

    function onsetShape() {
      if (onset == null) return [];
      return [{ type: "line", x0: onset, x1: onset, yref: "paper", y0: 0, y1: 1, line: { color: "rgba(200,210,255,.4)", width: 1.2, dash: "dot" } }];
    }
    function onsetAnn() {
      if (onset == null) return [];
      return [{ x: onset, yref: "paper", y: 0.5, yanchor: "middle", xanchor: "right", text: "RSI onset ", showarrow: false, font: { size: 9, color: "rgba(200,210,255,.65)" } }];
    }
    // -- Capability panel --
    const capTraces = [
      { x: cut(hold.tau, hi), y: cut(hold.I, hi), name: "regulation holds", mode: "lines", line: { color: HOLD, width: 2.7 } },
      { x: cut(fail.tau, fi), y: cut(fail.I, fi), name: "regulation fails", mode: "lines", line: { color: FAIL, width: 2.7 } },
    ];
    if (failCollapsed) capTraces.push({ x: [fail.tau[fi]], y: [fail.I[fi]], mode: "markers", marker: { color: FAIL, size: 15, symbol: "x", line: { width: 0 } }, showlegend: false, hoverinfo: "skip" });
    const yTop = Math.max(params.I_runaway * 1.12, ROF.arrMax(cut(hold.I, hi)) * 1.15, params.I_advanced * 2);
    const capShapes = onsetShape().concat([
      { type: "line", xref: "paper", x0: 0, x1: 1, y0: params.I_advanced, y1: params.I_advanced, line: { color: "rgba(200,210,255,.3)", width: 1, dash: "dash" } },
    ]);
    const capAnn = onsetAnn().concat([
      { xref: "paper", x: 0.02, y: params.I_advanced, yanchor: "bottom", xanchor: "left", text: "advanced", showarrow: false, font: { size: 9, color: "rgba(200,210,255,.5)" } },
      { x: hold.tau[hi], y: hold.I[hi], xanchor: "right", yanchor: "bottom", xshift: -4, yshift: 6, text: "stays controlled", showarrow: false, font: { size: 11, color: HOLD } },
    ]);
    if (failCollapsed) capAnn.push({ x: fail.tau[fi], y: fail.I[fi], xanchor: "left", yanchor: "middle", xshift: 14, text: "runs away, collapses", showarrow: false, font: { size: 11, color: FAIL } });
    Plotly.react(divCap, capTraces, baseLayout({
      showlegend: false,
      yaxis: { title: { text: "I — capability" }, gridcolor: GRID, zerolinecolor: ZERO, range: [0, yTop] },
      shapes: capShapes, annotations: capAnn,
    }), CONFIG);

    // -- Regulation panel -- bounded in [0, 1] by construction
    const regTraces = [
      { x: cut(hold.tau, hi), y: cut(hold.R, hi), name: "regulation holds", mode: "lines", line: { color: HOLD, width: 2.5 } },
      { x: cut(fail.tau, fi), y: cut(fail.R, fi), name: "regulation fails", mode: "lines", line: { color: FAIL, width: 2.5 } },
    ];
    if (failCollapsed) regTraces.push({ x: [fail.tau[fi]], y: [fail.R[fi]], mode: "markers", marker: { color: FAIL, size: 15, symbol: "x", line: { width: 0 } }, showlegend: false, hoverinfo: "skip" });
    const regShapes = onsetShape().concat([
      { type: "line", xref: "paper", x0: 0, x1: 1, y0: params.R_min, y1: params.R_min, line: { color: "rgba(232,116,110,.45)", width: 1, dash: "dot" } },
    ]);
    const regAnn = onsetAnn().concat([
      { xref: "paper", x: 0.02, y: params.R_min, yanchor: "bottom", xanchor: "left", text: "control floor R_min", showarrow: false, font: { size: 9, color: "rgba(232,116,110,.65)" } },
      { x: hold.tau[hi], y: hold.R[hi], xanchor: "right", yanchor: "bottom", xshift: -4, yshift: 4, text: "in control", showarrow: false, font: { size: 11, color: HOLD } },
    ]);
    if (failCollapsed) regAnn.push({ x: fail.tau[fi], y: fail.R[fi], xanchor: "left", yanchor: "middle", xshift: 14, text: "control lost", showarrow: false, font: { size: 11, color: FAIL } });
    Plotly.react(divReg, regTraces, baseLayout({
      showlegend: false,
      yaxis: { title: { text: "R — self-control" }, gridcolor: GRID, zerolinecolor: ZERO, range: [0, 1.0] },
      shapes: regShapes, annotations: regAnn,
    }), CONFIG);
  }

  global.ROF_PLOTS = { plotIR, plotO, plotN, plotPhase, plotLambert, plotOFunc, plotRSI, COLORS: C };
})(typeof window !== "undefined" ? window : globalThis);
