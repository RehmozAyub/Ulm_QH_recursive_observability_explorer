// ============================================================================
// NARRATIVES: plain-language interpretations for every view.
// One editable place. Each context (regime, trajectories, phase, lambert,
// ofunc, drake, 3d) holds an ORDERED list of cases. Each case has a `when(c)`
// test against the current values and a title + text. The FIRST case whose test
// passes wins; the last case is the catch-all default.
//
// `c` (the context object, built in app.js) exposes:
//   I_final R_final O_final I_peak O_peak R_min P_det N_obs
//   regime  (classifier label)
//   crit  lambertApplicable  lambertTrivial  lambertExceeded
//   O_key F_key obs_mode
//   oPeakedThenFell   (observability peaked then fell > 30%)
//   th: { O_detectable, I_advanced, I_runaway, R_min, Theta, P_search }
// Edit the ranges/text below freely; nothing else needs to change.
// ============================================================================
(function (global) {
  "use strict";

  const collapse = (c) => c.regime === "collapse-proxy";
  const runaway = (c) => c.regime === "runaway";
  const advanced = (c) => c.I_final >= c.th.I_advanced;
  const visible = (c) => c.O_final >= c.th.O_detectable;

  const CTX = {
    // ---- overall verdict ----
    regime: [
      { when: collapse, tone: "bad", title: "Overreach, then collapse",
        text: "Recursive amplification outran regulation and the system destabilised. Any signal was a brief flare from the breakdown, not a lasting beacon." },
      { when: runaway, tone: "warn", title: "Runaway capability",
        text: "Capability shot past its safe ceiling faster than regulation could answer. The outcome is unstable, and the model stops short of predicting where it lands." },
      { when: (c) => c.regime === "optimized-low-observable", tone: "neutral", title: "Advanced, and hiding",
        text: "High capability, low visibility. The civilisation optimised itself into quiet. Still present, but leaking little we could catch, and a strong candidate explanation for the silence." },
      { when: (c) => c.regime === "expansionist-visible", tone: "good", title: "Loud and far-reaching",
        text: "Both capability and visibility stayed high. If this trajectory is common, the Great Silence gets harder to explain, because civilisations like this should be findable." },
      { when: (c) => c.regime === "visible-technological", tone: "good", title: "Detectable, for now",
        text: "A real detection probability built up. Point the right instrument the right way and this is the kind of civilisation we would see." },
      { when: (c) => c.regime === "pre-detectable", tone: "neutral", title: "Too young to see",
        text: "Capability and observability never rose far enough to leave a technosignature. Silence here means youth, not absence." },
      { when: () => true, tone: "neutral", title: "An ambiguous fate",
        text: "No single outcome dominates. Nudge a parameter and the story could tip toward visibility, hiding, or collapse." },
    ],

    // ---- time-series (Trajectories tab) ----
    trajectories: [
      { when: (c) => collapse(c) || runaway(c), tone: "bad", title: "A sharp, unstable climb",
        text: "Capability races ahead while regulation falls behind. The curves diverge instead of settling, the signature of overreach." },
      { when: (c) => c.oPeakedThenFell && advanced(c), tone: "neutral", title: "Grew loud, then went quiet",
        text: "Observability climbs during expansion and then falls as the civilisation optimises. On this plot you can watch it peak and fade toward hiding." },
      { when: (c) => visible(c), tone: "good", title: "Still shining",
        text: "Observability holds up over time and the detected-population curve stays above the floor, so this trajectory remains findable." },
      { when: (c) => c.O_peak < c.th.O_detectable, tone: "neutral", title: "Nothing to show yet",
        text: "Neither capability nor observability climbs enough to register. The technosignature never really switches on." },
      { when: () => true, tone: "neutral", title: "A mixed trajectory",
        text: "The three curves tell a middling story. Worth comparing against the phase and regime views." },
    ],

    // ---- (I, O) phase plane, by quadrant ----
    phase: [
      { when: (c) => advanced(c) && visible(c), tone: "good", title: "Top-right: expansionist and visible",
        text: "The path ends in high capability and high visibility. This is the loud, findable corner of the diagram." },
      { when: (c) => advanced(c) && !visible(c), tone: "neutral", title: "Bottom-right: advanced but hidden",
        text: "The path ends in high capability yet low visibility. The civilisation is out there, but it has gone quiet." },
      { when: (c) => !advanced(c) && visible(c), tone: "good", title: "Top-left: early but noisy",
        text: "Modest capability, but enough leakage to be seen. A short detectable window before things change." },
      { when: () => true, tone: "neutral", title: "Bottom-left: pre-detectable",
        text: "The path stays in the quiet corner. Too early or too faint to leave a signature." },
    ],

    // ---- Lambert boundary ----
    lambert: [
      { when: (c) => !c.lambertApplicable, tone: "neutral", title: "Boundary not in play",
        text: "The Lambert-W boundary only applies to the Lambert recursion form. With the current F(I) there is no critical line to cross here." },
      { when: (c) => c.lambertTrivial, tone: "neutral", title: "A degenerate boundary",
        text: "With these settings the critical capability collapses to zero everywhere, so the boundary carries no information. Raise the reflective amplification to make it meaningful." },
      { when: (c) => c.lambertExceeded, tone: "warn", title: "Past the critical line",
        text: "The operating point sits beyond the Lambert threshold. In this region recursive amplification tends to win, pushing the system toward runaway." },
      { when: () => true, tone: "good", title: "Below the critical line",
        text: "The operating point stays under the Lambert threshold, the subcritical side, where regulation can still contain amplification." },
    ],

    // ---- observability function shape (by O_key) ----
    ofunc: [
      { when: (c) => c.O_key === "increasing", tone: "neutral", title: "Louder with growth",
        text: "The increasing model: visibility rises with capability. This is the optimistic, findable assumption." },
      { when: (c) => c.O_key === "decreasing", tone: "neutral", title: "Quieter with growth",
        text: "The decreasing model: growth brings efficiency and concealment, so visibility falls as capability rises." },
      { when: (c) => c.O_key === "peaked", tone: "neutral", title: "Loud, then quiet",
        text: "The peaked model: a civilisation grows visible during expansion and fades after it optimises. This is the case the framework cares about most." },
      { when: () => true, tone: "neutral", title: "A visibility switch",
        text: "The threshold model: visibility flips on or off around a critical capability." },
    ],

    // ---- Drake decomposition ----
    drake: [
      { when: (c) => c.P_det < 0.01, tone: "neutral", title: "The count collapses",
        text: "The observability correction shrinks the classical Drake estimate toward zero. Many may exist, but our searches would catch almost none of them." },
      { when: (c) => c.P_det < 0.2, tone: "neutral", title: "A thin slice survives",
        text: "Only a small fraction of the classical count survives the survival, signal and search factors. Detection is possible but unlikely." },
      { when: () => true, tone: "good", title: "Some survive the filter",
        text: "A meaningful fraction of the classical count makes it through the filter, so a real detection probability remains." },
    ],

    // ---- 3D state space ----
    "3d": [
      { when: (c) => collapse(c) || runaway(c), tone: "bad", title: "A path that breaks off",
        text: "In state space the trajectory veers rather than settling: capability climbing while regulation drops away." },
      { when: (c) => c.oPeakedThenFell && advanced(c), tone: "neutral", title: "A loop toward quiet",
        text: "The path rises in observability and then curls back down as the civilisation optimises, ending deep in the low-visibility region." },
      { when: (c) => visible(c), tone: "good", title: "Ends in the visible zone",
        text: "The trajectory settles where observability stays high: the findable part of the space." },
      { when: () => true, tone: "neutral", title: "A path to read",
        text: "Orbit the cube to see how capability, regulation and observability trade off along the way." },
    ],
  };

  function match(key, c) {
    const list = CTX[key];
    if (!list) return null;
    for (const cse of list) {
      try { if (cse.when(c)) return cse; } catch (e) { /* skip malformed case */ }
    }
    return list[list.length - 1];
  }

  // ---- overall FINDINGS: one synthesised paragraph across every value ----
  function nfmt(v) {
    if (v === 0) return "0";
    const a = Math.abs(v);
    if (a >= 1e4 || a < 1e-3) return v.toExponential(2);
    return String(parseFloat(v.toPrecision(3)));
  }
  function buildSummary(c) {
    const f = nfmt, p = [];
    let tone = "neutral";
    const reg = c.regime;

    // 1) opening — what this civilisation is / its fate
    if (reg === "collapse-proxy") {
      tone = "bad";
      const regPhrase = c.R_min < 0 ? "regulation collapses below zero" : `regulation falls to R ≈ ${f(c.R_min)}`;
      p.push(`With these settings the civilisation overreaches and collapses: capability peaks near I ≈ ${f(c.I_peak)} while ${regPhrase}, and amplification wins out.`);
    } else if (reg === "runaway") {
      tone = "warn";
      const regPhrase = c.R_final < 0 ? "as regulation collapses below zero" : `outpacing regulation (R ≈ ${f(c.R_final)})`;
      p.push(`Capability runs away to I ≈ ${f(c.I_final)}, ${regPhrase} before the system can stabilise.`);
    } else if (reg === "optimized-low-observable") {
      const obsPhrase = c.O_final < 0
        ? `observability collapses well below zero, far under the detection floor of ${f(c.th.O_detectable)}`
        : `observability settles at only O ≈ ${f(c.O_final)}, below the detection floor of ${f(c.th.O_detectable)}`;
      p.push(`This is an advanced but quiet civilisation: capability reaches I ≈ ${f(c.I_final)}, yet ${obsPhrase}.`);
    } else if (reg === "expansionist-visible") {
      tone = "good";
      p.push(`This civilisation grows both capable and loud, ending at I ≈ ${f(c.I_final)} with observability O ≈ ${f(c.O_final)}, well above the detection floor.`);
    } else if (reg === "visible-technological") {
      tone = "good";
      p.push(`This civilisation stays technologically visible, holding a detection probability of P_det ≈ ${f(c.P_det)}.`);
    } else if (reg === "pre-detectable") {
      p.push(`This civilisation never crosses into visibility: capability peaks at only I ≈ ${f(c.I_peak)} and observability at O ≈ ${f(c.O_peak)}, so it leaves no technosignature.`);
    } else {
      p.push(`The outcome is ambiguous: no single regime rule fires cleanly at I ≈ ${f(c.I_final)}, R ≈ ${f(c.R_final)}, O ≈ ${f(c.O_final)}.`);
    }

    // 2) observability behaviour over time
    if (c.oPeakedThenFell) {
      const fallPhrase = c.O_final < 0 ? "falls away entirely" : `falls back to O ≈ ${f(c.O_final)}`;
      p.push(`Observability rises to a peak of O ≈ ${f(c.O_peak)} and then ${fallPhrase} — the peaked signature the framework is built around, loud during expansion and quiet after optimisation.`);
    } else if (c.O_final >= c.th.O_detectable) {
      p.push(`Observability holds up through the run, so the window for detection stays open.`);
    } else {
      p.push(`Observability never clears the detection floor, so the window for us to notice it is narrow at best.`);
    }

    // 3) detection outcome
    if (c.P_det < 0.01) {
      p.push(`In detection terms the count collapses: with P_det ≈ ${f(c.P_det)}, almost none of an in-principle population would ever be observed.`);
    } else if (c.P_det < 0.2) {
      p.push(`Detection is possible but unlikely, with P_det ≈ ${f(c.P_det)} surviving the survival, signal and search factors.`);
    } else {
      p.push(`A real detection probability survives, P_det ≈ ${f(c.P_det)}, so a fraction of such civilisations would actually be seen.`);
    }

    // 4) Lambert boundary, only when it carries information
    if (c.lambertApplicable && !c.lambertTrivial && c.crit != null) {
      if (c.lambertExceeded) p.push(`The operating point sits past the Lambert critical capability (I_crit ≈ ${f(c.crit)}), on the runaway side of the boundary.`);
      else p.push(`The operating point stays below the Lambert critical capability (I_crit ≈ ${f(c.crit)}), where regulation can still contain amplification.`);
    }

    // 5) closing — what it means for the Fermi question
    if (reg === "optimized-low-observable" || (c.oPeakedThenFell && c.I_final >= c.th.I_advanced)) {
      p.push(`For the Fermi question this is the quiet answer: a civilisation that is present but effectively hidden.`);
    } else if (reg === "expansionist-visible" || reg === "visible-technological") {
      p.push(`If trajectories like this are common, the Great Silence becomes harder to explain.`);
    } else if (reg === "collapse-proxy" || reg === "runaway") {
      p.push(`Here the silence would be explained by fragility, not stealth: the civilisation destabilises before it can be found.`);
    } else {
      p.push(`On its own this case leaves the Fermi question open; compare it against the other presets to see how sensitive the outcome is.`);
    }

    return { tone, title: "Findings for this case", text: p.join(" ") };
  }

  global.ROF_NARRATIVES = { match, CTX, buildSummary };
})(typeof window !== "undefined" ? window : globalThis);
