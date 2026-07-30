# Lessons Learned — Recursive Observability Explorer

**Working notes toward a publication.** This document is the accumulating evidence base for a
LaTeX submission on the Recursive Observability Filter (ROF) framework and its simulator.
It records what the artifact set contains, what was verified and how, what was found broken,
how it was fixed, and what remains open.

- **Status:** iteration 2 — three structural defects found *and resolved*; figures unblocked.
- **Last pass:** 2026-07-30
- **Source of record for theory:** `The_Fermi_Paradox_v3.docx` → converted to `The_Fermi_Paradox_v3.md`
- **Code changes:** see `CHANGELOG.md` [0.2.0]
- **Convention:** **[Verified]** = measured in this pass; **[Observed]** = read from source;
  **[Open]** = needs a team decision.

---

## 0. How to read this document

Sections 1–3 describe the artifact. Section 4 is the verification methodology — the material
that makes the paper's reproducibility section credible. Section 5 is what holds up. Section 6
is the defect record: what was wrong, why it mattered, and how it was fixed. Section 7 covers
manuscript↔code consistency, including the one issue that remains genuinely open. Sections 8–11
are the forward plan.

**The methodological story for the paper lives in §4 and §6.** A model that was found to be
producing its headline result through an artefact, diagnosed with independent oracles, and then
corrected at the level of the equations is a stronger contribution than a model that was never
stress-tested. Write it up that way rather than quietly shipping the fixed version.

---

## 1. Artifact inventory

Two independent implementations of the same model, plus the theory manuscript.

| Component | Path | Runtime | Notes |
| --- | --- | --- | --- |
| Theory manuscript | `The_Fermi_Paradox_v3.docx` / `.md` | — | 786 paragraphs, 19 tables, 247 equations |
| Python simulator | `recursive_observability_explorer/` | Python + Streamlit + SciPy | Reference implementation |
| Browser simulator | `web_html_version/` | Any browser, **no Python** | Self-contained JS port |
| Test suite | `recursive_observability_explorer/tests/` | pytest | 62 tests, 7.1 s |

### 1.1 The two versions

**Python version** — the ground truth. Streamlit UI (`app.py`, `ui/`), Plotly figures
(`viz/plots.py`), model core in `model/`: `config.py`, `system.py`, `functions.py`,
`solver.py`, `lambert.py`, `regimes.py`, `stages.py`, `drake.py`.

**HTML version** — **runs with no Python and no backend.** Open `index.html` in a browser.
Contains its own Dormand–Prince RK45 with dense output, a hand-rolled Lambert W₀ via Halley
iteration, and mirrors of the parameter defaults, stage presets, regime classifier and Drake panel.

> **Caveat on "no install needed":** it needs **network access** — Plotly 2.35.2, KaTeX 0.16.9
> and Google Fonts load from CDNs. Python-free but not offline-capable. Vendoring these three
> would make it genuinely self-contained; worth doing before the artifact is cited, since CDN
> versions drift and papers outlive CDNs. **[Observed]**

---

## 2. The model as implemented

Dimensionless time τ. State `[I, R, O]` (or `[I, R]` when `obs_mode="static"`).

$$\frac{dI}{d\tau} = a\,A\,I \;+\; b\,A_{rec}\,F(I) \;-\; c\,R\,I \;-\; s_I I^2$$
$$\frac{dR}{d\tau} = (u\,A_{ref} + v\,Q)(1-R) \;-\; (w\,A_{rec} + s_R)\,R$$
$$\frac{dO}{d\tau} = p\,E_{use} + q\,B_{cast} + r\,X_{expand} \;-\; (O - O_{floor})\,(m\,C_{compress} + n\,S_{stealth})$$

Detection chain:
$$h(O) = 1 - e^{-\kappa O}, \qquad P_{det} = h(O)\,P_{search}, \qquad N_{obs} = N_{true}\,P_{surv}\,h(O)\,P_{search}$$

The capability and detection equations match the manuscript §6.2 and §6.5 term for term. The
regulation and observability equations are **corrected forms** — see §6.1 and §6.2 for why, and
§7.1 for what the manuscript needs to say instead. **[Verified]**

### 2.1 Two structural guarantees

These are the point of the corrected forms, and both should be stated as propositions in the paper:

- **`O ≥ O_floor` always.** At `O = O_floor` the sink term vanishes identically and production is
  non-negative, so the boundary cannot be crossed. No clamping; the RHS stays smooth.
- **`R ∈ [0, 1]` always.** `dR/dτ ≥ 0` at `R = 0` and `≤ 0` at `R = 1`, with equilibrium
  `R_∞ = (uA_ref + vQ)/(uA_ref + vQ + wA_rec + s_R)` — the "building share".

Both were confirmed empirically across 300 randomised parameter sets, zero violations. **[Verified]**

### 2.2 Swappable function registries

No functional form is hardcoded; everything is a dict lookup, so adding a variant is one line
and the solver never changes.

| Registry | Options |
| --- | --- |
| `F(I)` recursion | `linear` I · `superlinear` I² · `lambert` I·eᴵ · `exponential` eᴵ · `saturating` I/(1+I/K) |
| `O(I)` static | `increasing` 1−e^(−λI) · `decreasing` e^(−λI) · `peaked` I·e^(−λI) · `threshold` sigmoid |
| `E_use` | `linear` I · `kardashev` I² |
| `B_cast` | `linear` I · `decaying` I·e^(−λI) |
| `X_expand` | `linear` I · `inward` 0 |
| `C_compress`, `S_stealth` | `linear` I·R · `superlinear` I²·R |

This satisfies the manuscript's own falsifiability requirement (§9.2, §9.4) and is a genuine
methodological contribution — argue it as one. **[Observed]**

### 2.3 Regime classifier

Seven labels in strict priority order: `collapse-proxy` → `runaway` → `pre-detectable` →
`optimized-low-observable` → `expansionist-visible` → `visible-technological` → `uncertain`.
Order matters and is not commutative — state this explicitly, because a trajectory satisfying two
criteria silently gets the earlier label.

---

## 3. Provenance gaps

- `model/lambert.py` cites **"Section 9.1 of GEMINI.md"**. **No `GEMINI.md` exists in the
  repository.** The derivation does appear in the manuscript (§8.2); repoint the reference. **[Observed]**
- `web_html_version/validate.js` requires `/home/user/workspace/fermi_reference.json` — an
  absolute path from the original development sandbox, and the file is not in the repo. The
  harness **cannot run**: `Error: Cannot find module`. The web README claims "All 25 checks pass",
  which no third party can reproduce. Still the most damaging reproducibility issue. **[Verified]**

---

## 4. Verification methodology

The model was tested *independently*, not by re-running its own tests. Six oracles.

| # | Oracle | Independent of the solver? | Result (post-fix) |
| --- | --- | --- | --- |
| A | `R(τ)` vs exact closed-form solution | Yes — analytic | 19/19, worst \|err\| 2.3×10⁻⁶ |
| B | Default RK45 vs DOP853 @ `rtol=1e-12` | Yes — different method & tolerance | **20/20** |
| C | `O(τ)` vs direct quadrature of `dO/dτ` | Partly — reuses solver's I,R | 12/12 non-singular, ≤1.5×10⁻⁴ |
| D | Lambert `I_crit` vs defining identity | Yes — algebraic | 2304/2304, 4.4×10⁻¹⁶ |
| E | Structural invariants under random sweep | Yes — property-based | **300 configs, 0 violations** |
| F | Python vs JavaScript, same configs | Yes — separate implementation | **20/20**, identical labels |

Test matrix: 8 stage presets + 5 `F(I)` variants + 4 static `O(I)` variants + time-varying
drivers + a Lambert configuration + a non-default component configuration = **20 configurations**.

### 4.1 Oracle A — regulation has a closed form

`dR/dτ` is linear in `R` with constant coefficients and does not depend on `I` or `O`, so it
integrates exactly:

$$R(\tau) = R_\infty + (R_0 - R_\infty)e^{-(B+W)\tau}, \quad B = uA_{ref}+vQ,\; W = wA_{rec}+s_R,\; R_\infty = \tfrac{B}{B+W}$$

Every configuration matches to `≤ 2.3×10⁻⁶`, consistent with `rtol=1e-6`. This closed form is
also a publishable analytic result in its own right — and it is what exposed the parameter-regime
defect in §6.3. **[Verified]**

### 4.2 Oracle B — independent high-accuracy integrator

Every configuration re-integrated with **DOP853** at `rtol=1e-12, atol=1e-14` and compared
against the shipped RK45 at `rtol=1e-6`. All 20 agree.

For the two finite-time blow-up kernels (`lambert`, `exponential`) the comparison is restricted
to the pre-abort interval, since the runaway guard (§6.4) deliberately stops RK45 early while the
reference has no guard. Within that interval they agree at 50% of tolerance.

**Conclusion: the default solver tolerances are adequate. Integration was never the problem** —
every defect in §6 was a modeling or bookkeeping issue. **[Verified]**

### 4.3 Oracle D — the Lambert identity

`I_crit` must satisfy `I·e^I = C_R/(b·A_rec)`. Tested over 576 parameter combinations × 4 values
of `R`: max relative residual **4.4×10⁻¹⁶** — machine precision. The validity guard behaves as
documented (`I_crit()` returns `None` for every non-`lambert` kernel).

The JS hand-rolled `lambertW0` was checked separately over x ∈ [10⁻⁶, 10⁶] and the negative
branch x ∈ [−1/e, 0): max relative residual **1.03×10⁻¹⁵**; `W(0)=0`, `W(e)=1`, `W(−0.5)=NaN`
(correctly outside the principal-branch real domain). Only blemish: `W(−1/e)` carries ~1.1×10⁻⁹
error at the branch point where the derivative is singular — do not quote it beyond 8 digits.
**[Verified]**

### 4.4 Oracle E — property-based invariant testing

The strongest evidence that the §6.1/§6.2 fixes are structural rather than tuned: 300 randomised
parameter sets drawn across the full declared bounds, with random recursion kernels and
compression/stealth forms.

> **0 violations.** Global `min O = 2.16×10⁻³` (above the floor), `R ∈ [4.0×10⁻³, 0.999]`.

**[Verified]**

### 4.5 Oracle F — cross-language agreement

| Quantity | Worst absolute difference across all 20 configs |
| --- | --- |
| `I(τ)` | 5.2×10⁻⁵ |
| `R(τ)` | 3.1×10⁻⁷ |
| `O(τ)` | 2.7×10⁻⁵ |
| `I_crit` | 2.2×10⁻¹² relative |
| Regime label | **20/20 identical** |

Two independently written adaptive RK45 implementations, different dense-output interpolation and
different initial-step heuristics, both at `rtol=1e-6`. This is agreement at the level of the
solver tolerance itself.

**Claim licensed for the paper:** *the browser implementation is numerically equivalent to the
Python reference to within solver tolerance across all tested configurations, including regime
classification.* **[Verified]**

### 4.6 Reproducing this pass

```bash
cd recursive_observability_explorer
PYTHONPATH=. python -m pytest tests -q          # 62 passed in 7.1 s
```

Environment: Python 3.11, numpy 2.4.2, scipy 1.17.1, pytest 9.0.2; Node v24.11.1 for the JS side.
The analytic oracles and the cross-language harness are **not yet committed**; they should live
under `tests/verification/` so the paper can cite them. **[Open]**

---

## 5. What is confirmed correct

1. **Capability and detection equations match the manuscript** term for term. **[Verified]**
2. **Numerical integration is sound** — validated against an analytic solution and an independent
   high-order integrator. **[Verified]**
3. **The Lambert W machinery is mathematically correct** and correctly guarded: W is never
   invoked unless `F_key == "lambert"`, and the fallback for other kernels is the logarithm,
   exactly as §8.1 demands. **[Verified]**
4. **The two implementations agree**, including all regime labels. **[Verified]**
5. **The detection chain uses the correct form** `N_obs = N_true·P_surv·h(O)·P_search` — not the
   inconsistent form in the manuscript's own abstract (§6.5 below). **[Verified]**
6. **`O` and `R` are now bounded by construction**, verified over 300 random configurations. **[Verified]**
7. **Every stage reproduces its manuscript-specified qualitative behaviour** (§6.3 table). **[Verified]**

---

## 6. Defects found — and how they were fixed

All three original defects are **resolved** in `CHANGELOG.md` [0.2.0]. The diagnosis is retained
in full because it is the paper's methodological evidence, not just a bug list.

### 6.1 Observability became large and negative — RESOLVED

**Was:** `dO/dτ = pE + qB + rX − mC − nS` subtracted an absolute flux independent of `O`, so
suppression kept draining past zero.

| Config | min `O` (before) | Regime assigned |
| --- | --- | --- |
| `stage:s4c` | **−1.431×10³** | `optimized-low-observable` |
| `stage:s5` | **−4.707×10²** | `uncertain` |
| `F:exponential` | −1.187 | `uncertain` |

Stage 4c — the *central case of the framework* — earned "optimized low-observable" from
`O_final = −1431 < O_detectable = 0.1`. Arithmetically true, scientifically vacuous: the
trajectory was not quiet, it was off the bottom of the model. A clamped `O_eff` existed but fed
only the detection chain; the classifier, all plots and both UIs read raw `O`.

**Root cause:** compression and stealth reduce the signal you *emit* — a fractional reduction —
but were modelled as an absolute subtraction. You cannot compress emissions you are not making.

**Fix:** fractional suppression with an explicit thermodynamic floor:

$$\frac{dO}{d\tau} = \underbrace{pE + qB + rX}_{\text{production}} - (O - O_{floor})\underbrace{(mC + nS)}_{\text{fractional rate}}$$

**Consequences, all favourable:**

- `O ≥ O_floor` structurally. `O_floor` encodes the manuscript's §4.4 thermodynamic caveat *in the
  equations* rather than only in prose — "low observability is not invisibility" becomes a model
  property, not a disclaimer.
- **Peak-then-decline is now derived, not assumed.** The quasi-steady state is
  `O* = O_floor + production/suppression`, which falls once suppression outgrows production in `I`
  (i.e. `C, S ~ I²R` against production `~ I`). The central ROF claim no longer depends on
  selecting `O_key = "peaked"` — which directly answers the §9.4 failure criterion about assuming
  the conclusion. **This is the single most publication-relevant improvement in this pass.**
- Stage 4c now: `O: 0.100 → peak 0.231 at τ=0.65 → 0.037`, strictly positive throughout. **[Verified]**

**Cost:** `m` and `n` changed units (fractional rates, not fluxes) and needed re-tuning. And the
equation became stiff — see §6.4.

### 6.2 Regulation became negative and inverted the damping term — RESOLVED

**Was:** `dR/dτ = uA_ref + vQ − wA_rec − s_R R` eroded `R` at a constant rate regardless of how
much regulation existed.

| Config | `R_∞` (before) | min `R` (before) |
| --- | --- | --- |
| `stage:s3` | −0.333 | −0.333 |
| `stage:s4a` | **−25.400** | −25.400 |
| `timevarying` | 1.333 | −2.296 |

Negative regulatory capacity has no interpretation, and it was not inert: with `R < 0` the
capability term `−c·R·I` became **positive**, so degraded governance actively accelerated
capability. Stage 4a reached `I = 130.3`, `O = 1.26×10⁵` that way. It *was* labelled
`collapse-proxy` — the right answer for the wrong reason, which is not a validated model.

**Fix:** erosion proportional to `R`, building on the remaining headroom:

$$\frac{dR}{d\tau} = (uA_{ref} + vQ)(1-R) - (wA_{rec} + s_R)R$$

`R` is now a **regulation quality index in [0, 1]** — which is also what §5.4 describes it as
(alignment, governance, coherence: a quality, naturally normalised). Stage 4a now collapses
through `R → 0.0438 < R_min = 0.05` **without going negative**, which is the §7.5 mechanism.
**[Verified]**

### 6.3 Regulation-dominated defaults drove capability to zero — RESOLVED

**Was:** with the old equilibrium, `c·R_∞ > a·A` in 13 of 20 configurations, so `I` decayed to
~10⁻⁹. Stage 1 classified `pre-detectable` while the manuscript (§7.2) and README both say
observability *rises*: `a·A/(c·R_∞) = 0.129 < 1`.

**Root cause:** a scale mismatch. `R` and `I` were multiplied as though commensurate, while `R`
equilibrated near 4.7 against a growth rate of 0.30. Hand-tuning `c` would only have hidden it.

**Fix:** (i) bounding `R` to `[0, 1]` (§6.2) makes `c` the maximum fractional damping and removes
the mismatch by construction; (ii) stage presets may now declare which terms are active
(`term_damping`), so the reduced models of §7.1–7.3 are reproduced *literally* rather than
approximated by tuning.

**Result — every stage now matches its specification:**

| Stage | Specified behaviour | Simulator (post-fix) | Regime |
| --- | --- | --- | --- |
| 0 | `dI/dτ ≈ 0`, no technosignature | `I = 0.010`, `O = 0.003` | `pre-detectable` |
| 1 | `I → aA/s_I = 3.0`, `O → 0.5934`, rising | `I = 3.0000`, `O = 0.5934` | `visible-technological` |
| 2 | capability grows, `O` still rising | `I = 3.000`, `O: 0.10 → 1.82` | `visible-technological` |
| 3 | full model, recursion on | `I = 2.75`, `O = 3.43` | `visible-technological` |
| 4a | regulation collapses | `R → 0.0438 < R_min`, `R ≥ 0` | `collapse-proxy` |
| 4b | high `I`, high `O` sustained | `I = 9.80`, `O = 27.0` | `expansionist-visible` |
| 4c | `O` peaks then declines | `0.100 → 0.231 → 0.037` | `optimized-low-observable` |
| 5 | speculative | `I = 3.04`, `O: 0.30 → 0.16` | `visible-technological` |

**Why the old suite missed all of this:** `test_regimes.py` accepted
`"visible-technological" OR "pre-detectable"` for stage 1 — a disjunction that passes either way.
There was no test asserting `O ≥ 0`, none asserting `R ≥ 0`, and none asserting that stage-1
observability actually rises. The suite pinned *behaviour* rather than *intent*.

`tests/test_invariants.py` now adds 26 tests that assert intent: the structural bounds for every
stage and across a random sweep, the analytic stage-1 solution, 4c peak-then-decline, 4a collapse
without sign inversion, and that the damping term can never become a source. The stage-1
disjunction has been removed. **[Verified]**

### 6.4 No runaway guard in the Python solver — RESOLVED (found while fixing the above)

`superlinear` and `exponential` kernels blow up in finite τ. The browser solver capped its step
count; Python did not, so the adaptive stepper ground indefinitely against the singularity — a
Streamlit session could hang on a user-selectable parameter combination.

Integration now terminates cleanly via an event once `I > I_abort` (default `10⁴`, 200× the
default `I_runaway`), and remaining samples hold the **terminal** state. Padding with the last
`t_eval` sample was actively misleading: the singularity usually falls *between* output samples,
so the array could report `max I ≈ 31` for a trajectory that had actually diverged. The browser
solver gained the matching check. **[Verified]**

### 6.5 Manuscript-internal inconsistency in `N_obs` — NOT a code issue

- **Abstract and §1.4:** `N_obs = N_true · P_surv · P_det · P_search`
- **§6.5:** `P_det = h(O)·P_search`, and `N_obs = N_true · P_surv · h(O) · P_search`

Substituting gives `N_true · P_surv · h(O) · P_search²` — **`P_search` counted twice.** The code
implements the §6.5 form, which is correct. **Fix the abstract and §1.4.** **[Verified]**

### 6.6 Minor items

- **`log` vs `ln`.** §8.2 writes `C_R = c·R^η·log(1+A_ref)·E`; the code uses natural log
  (`log1p`). Consistent — write `\ln` in the LaTeX. **[Observed]**
- **README file list is stale** — omits `tests/test_lambert.py`. **[Observed]**
- **Lambert module is opt-in.** `F_key` defaults to `"saturating"`, so `I_crit()` returns `None`
  unless the Lambert kernel is selected. Say so, rather than implying it is the operating point. **[Observed]**

---

## 7. Manuscript ↔ implementation consistency

### 7.1 Consistency matrix

| Manuscript element | § | Status |
| --- | --- | --- |
| Capability equation | 6.2 | **Exact match** |
| Regulation equation | 6.3 | **Corrected** — manuscript needs updating to the bounded form (§6.2) |
| Observability equation | 6.4 | **Corrected** — manuscript needs updating to fractional suppression (§6.1) |
| Detection `h(O) = 1−e^(−κO)` | 6.5 | **Exact match** |
| `N_obs` chain | 6.5 | Matches §6.5; **abstract is inconsistent** (§6.5 above) |
| Collapse conditions (3 forms) | 6.6 | All three implemented |
| Low-observability condition | 6.7 | Implemented; now meaningful (`O` bounded) |
| `F(I)` — 5 variants | 6.2 | All 5 present |
| `O(I)` Models A–D | 4.3 | All 4 present |
| Stage 0–5 reduced models | 7.1–7.8 | **Now reproduced literally** via `term_damping` |
| Lambert boundary | 8.2 | Exact, machine precision |
| Anti-decorative-Lambert guard | 8.1 | Enforced |
| Regime table | 10.5 | All 7 regimes present |
| Required plots 1–5 | 10.3 | Present in both versions |
| Claim-strength labels | 2.4 | Present in both |

> **Action:** §6.3 and §6.4 of the manuscript must be rewritten to the corrected equations, with
> the derivations in §6.1/§6.2 above. This is a manuscript edit, not a code change. **[Open]**

### 7.2 The Lambert boundary is a diagnostic, not a property of the simulated system

**This remains open and is the sharpest scientific point in the review. A referee will find it.**

The §8.2 derivation is admirably honest. It starts from the natural balance
`b·A_rec·I·e^I = c·R·I`, observes that `I` **cancels**, leaving `b·A_rec·e^I = c·R` — solved by a
**logarithm, not by W**. It then states: *"to retain Lambert structure, the threshold must compare
`I·e^I` directly against a regulation capacity not multiplied by `I`"*, and introduces
`C_R = c·R^η·ln(1+A_ref)·E`.

So the Lambert form is obtained by **choosing a different balance** than the one the ODE contains.
`C_R` appears nowhere in `dI/dτ`. The integrated system's own damping term is `−c·R·I` and its
natural threshold is logarithmic — which is exactly what `fallback_threshold()` computes for
non-Lambert kernels.

§9.4's failure criterion — *"uses Lambert W without an `I·e^I` threshold"* — is satisfied to the
letter. But the `I·e^I` threshold justifying W is **not** the threshold governing the dynamics
being plotted.

**Recommendation:** do not paper over this. Present the Lambert boundary explicitly as an
*auxiliary stability diagnostic under a stated auxiliary balance*, say plainly that the dynamical
threshold of the integrated system is logarithmic, and keep the honest §8.2 derivation in the main
text. Handled openly it demonstrates exactly the mathematical discipline the framework claims;
handled quietly it is the paper's biggest vulnerability. **[Open — needs a framing decision]**

---

## 8. Figure plan

Appendix F lists nine figures. **The §6 fixes unblock figures 4 and 6.**

| # | Figure | Source | Status |
| --- | --- | --- | --- |
| 1 | Existence / detectability / observation | Conceptual | To draw (TikZ) |
| 2 | Drake decomposition | `model/drake.py` | Panel exists; needs export |
| 3 | Civilization-stage ladder | Conceptual | To draw (TikZ) |
| 4 | `I, R, O` trajectory panel | Plot 1 + 2 | **Unblocked** |
| 5 | Observability-function comparison A–D | `viz/plots.py` | Ready |
| 6 | Phase diagram | Plot 4 | **Unblocked** (`R` now confined to [0,1] — bounded axis) |
| 7 | Lambert boundary | Plot 5 | Ready; label as auxiliary per §7.2 |
| 8 | Claim-strength dashboard | `ui/tabs.py` | Ready |
| 9 | Literature matrix | Appendix G | Ready — transcribe |

**Two proposed additions, both genuine contributions:**

- **Cross-validation panel** — Python and JS trajectories overlaid with a residual sub-panel at
  10⁻⁵. Very few simulation papers demonstrate two independent implementations agreeing to solver
  tolerance. Costs nothing extra and is strong evidence of correctness.
- **Before/after observability panel** — stage 4c under the old absolute-suppression form
  (running to −1431) against the corrected fractional form (peaking at 0.231 and decaying to
  0.037). This makes the §6.1 methodological argument visible in one figure, and shows
  peak-then-decline being *derived*.

**Export convention:** PDF/vector via `kaleido`, one figure per file, no baked-in titles (use
`\caption`), font ≥ 9 pt at final column width.

---

## 9. Literature

The manuscript carries ~70 references in nine clusters plus a literature matrix (Appendix G):

Classical Fermi/SETI (Cocconi & Morrison 1959; Hart 1975; Tipler 1980; Brin 1983; Gray 2015;
Webb 2015) · Drake/exoplanets (Borucki 2016; Batalha 2014; Dressing & Charbonneau 2015) ·
Great Filter & x-risk (Hanson 1998; Bostrom 2002, 2013; Ćirković 2018; Ord 2020) ·
Technosignatures (Dyson 1960; Kardashev 1964; Tarter 2001; Wright 2014, 2018; Sheikh 2020) ·
Colonization/percolation (Landis 1998; Armstrong & Sandberg 2013; Prantzos 2013, 2020) ·
Hard steps & grabby aliens (Carter 1983; Watson 2008; Kipping 2020; Hanson et al. 2021) ·
AI risk & recursive intelligence (Good 1965; Omohundro 2008; Bostrom 2014; Russell 2019) ·
Nonlinear dynamics (Strogatz 2015; Kuznetsov 1998; Murray 2002) · Lambert W (Corless et al. 1996) ·
Quantum computing (Shor 1994; Nielsen & Chuang 2010; Preskill 2018).

**Actions:** (i) export to BibTeX with DOIs — currently plain text; (ii) Hanson (1998) is a web
essay and needs a stable citation; (iii) the quantum-computing cluster is cited but **not used** by
the model — connect it (e.g. `A_rec` as compute scaling) or cut it, because a referee will ask why
a quantum hackathon framing has no quantum content in the equations. **[Open]**

---

## 10. Open questions

Resolved since iteration 1: bounding `O`, bounding `R`, and stage-preset fidelity (§6.1–6.3).

Still open:

1. **Lambert framing** — how prominently to present the auxiliary-balance caveat? (§7.2) *This is
   the one that decides how a referee reads the paper.*
2. **Manuscript equations** — §6.3 and §6.4 must be rewritten to the corrected forms. (§7.1)
3. **Stiff solver** — adopt LSODA/Radau to remove the `dO/dτ` stiffness ceiling, at the cost of
   numerical parity with the browser RK45? (§11)
4. **Collapse dynamics** — add a mortality term so stage 4a produces a collapse *trajectory*
   rather than only collapse *flags*? (§11)
5. **Quantum content** — connect it to the model or drop it from the framing? (§9)
6. **Artifact packaging** — vendor the CDN dependencies and ship `fermi_reference.json` so
   `validate.js` runs? (§1.1, §3)
7. **Nondimensionalisation** — rescaling `I` by `aA/s_I`, `R` by its equilibrium and `τ` by the
   growth rate would collapse ~30 parameters into a few dimensionless groups, making the phase
   diagram a genuine 2-parameter map and sensitivity analysis tractable. Recommended before the
   final figures.
8. **Target venue** — *International Journal of Astrobiology* fits the modelling-framework framing;
   *Acta Astronautica* is an alternative. Decide early: it sets length and figure count.

---

## 11. Known limitations of the corrected model

State these in the paper rather than letting a referee find them.

- **`dO/dτ` is stiff.** Its relaxation rate `m·C + n·S` grows like `I²·R`, and explicit RK45
  requires `h ≲ 2.8/rate`. Measured cost scaling: `m = n = 0` → 0.014 s; `0.5` → 7.4 s; `2.0` →
  30 s; `8.0` → 122 s — linear in the suppression weight. `I_abort` bounds the worst case. This is
  a direct trade-off introduced by the §6.1 fix; a stiff-capable integrator would remove it.
- **Collapse is a proxy, not a trajectory.** Stage 4a raises the collapse flags but capability does
  not actually fall — there is no mortality term, so the "transient spike then disappearance"
  signature of §7.5 is not reproduced dynamically. The manuscript already calls it a *collapse
  proxy* (§6.6), so this is honest, but it is a real gap between the narrative and the dynamics.
- **The Lambert boundary is auxiliary** (§7.2).
- **`validate.js` still cannot run** as shipped (§3).

---

## 12. Running log

**Iteration 1 — 2026-07-30.** Converted the manuscript to Markdown with all 247 equations
preserved as LaTeX. Read both implementations end to end. Built five independent verification
oracles. Numerics and Lambert mathematics correct, implementations equivalent; found three
structural modeling defects (unbounded negative `O`, negative `R`, regulation-dominated defaults),
one manuscript-internal inconsistency (`N_obs` double-counts `P_search`), and one broken validation
harness. Figures deferred.

**Iteration 2 — 2026-07-30.** Fixed all three defects at the level of the equations: fractional
suppression with a thermodynamic floor (`O ≥ O_floor` structurally), bounded regulation
(`R ∈ [0,1]` structurally), and literal reproduction of the reduced stage models. Found and fixed
a fourth issue — no runaway guard in the Python solver. Added 26 invariant/intent tests and removed
the disjunction that had masked the stage-1 defect. Re-verified: 62 tests pass in 7.1 s; invariants
hold across 300 random configurations with zero violations; Python and JS agree 20/20 including
regime labels. Peak-then-decline is now derived rather than assumed. Figures 4 and 6 unblocked.
Remaining open items are the Lambert framing (§7.2) and the manuscript equation updates (§7.1).
