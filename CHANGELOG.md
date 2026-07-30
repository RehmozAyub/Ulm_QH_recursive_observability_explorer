# Changelog

All notable changes to the Recursive Observability Explorer are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.2.0] — 2026-07-30

Structural correction release. Three defects found during the independent
verification pass (see `lessons_learned.md` §6) are fixed at the level of the
model equations rather than by clamping outputs or tuning presets. All changes
are mirrored in both the Python reference and the browser implementation.

### Fixed

#### 1. Observability could become large and negative

`dO/dτ` subtracted an *absolute* suppression flux that did not depend on `O`, so
compression and stealth kept draining observability past zero. Stage 4c — the
flagship "optimized low-observable" case — reached `O = −1431` and earned its
regime label from that value. A clamped `O_eff` existed but was used only in the
detection chain; the regime classifier, every plot and both UIs read the raw `O`.

Suppression is now a *fractional* rate acting on the signal actually being
emitted, plus an explicit thermodynamic floor:

```
before:  dO/dτ = p·E + q·B + r·X − m·C − n·S
after:   dO/dτ = p·E + q·B + r·X − (O − O_floor)·(m·C + n·S)
```

At `O = O_floor` the sink vanishes identically and production is non-negative, so
`O ≥ O_floor` holds **structurally** — no clamping and no discontinuity in the
right-hand side. `O_floor` encodes the manuscript's own thermodynamic caveat
(§4.4): a civilisation using energy is never perfectly invisible.

A consequence worth stating: peak-then-decline is now **derived** rather than
assumed. The quasi-steady state is

```
O* = O_floor + (p·E + q·B + r·X) / (m·C + n·S)
```

so observability falls once suppression outgrows production in `I`. The central
ROF claim no longer depends on selecting `O_key = "peaked"`.

#### 2. Regulation could become negative and invert the damping term

`dR/dτ` eroded `R` at a constant rate `−w·A_rec` regardless of how much
regulation existed, driving `R` to `−25.4` in stage 4a. Because the capability
equation contains `−c·R·I`, negative `R` turned regulatory damping into positive
feedback: failing governance *accelerated* capability growth.

Erosion is now proportional to the regulation that exists, and building acts on
the remaining headroom:

```
before:  dR/dτ = u·A_ref + v·Q − w·A_rec − s_R·R
after:   dR/dτ = (u·A_ref + v·Q)·(1 − R) − (w·A_rec + s_R)·R
```

`R` is therefore a **regulation quality index confined to [0, 1]** by
construction (`dR/dτ ≥ 0` at `R = 0`, `≤ 0` at `R = 1`), with equilibrium

```
R_∞ = (u·A_ref + v·Q) / (u·A_ref + v·Q + w·A_rec + s_R)
```

— the "building share". Collapse now occurs through `R → small` rather than
`R → negative`, which is the mechanism the manuscript describes in §7.5.

#### 3. Regulation-dominated defaults drove capability to zero

With the previous equilibrium, `c·R_∞` exceeded `a·A` in 13 of 20 tested
configurations, so capability decayed to ~10⁻⁹. Stage 1 classified as
`pre-detectable` although both the manuscript (§7.2) and the README specify
*rising* observability.

The root cause was a scale mismatch: `R` and `I` were multiplied as though
commensurate while `R` equilibrated near 4.7 against a growth rate of 0.3.
Bounding `R` to `[0, 1]` (fix 2) makes `c` directly interpretable as the maximum
fractional damping and removes the mismatch by construction.

In addition, stage presets may now declare which terms are active, so the
reduced stage models of §7.1–7.3 are reproduced literally instead of being
approximated by parameter tuning. Stage 1 now integrates
`dI/dτ = a·A·I − s_I·I²` and reaches its analytic limits exactly:

| Quantity | Manuscript §7.2 | Simulator |
| --- | --- | --- |
| `I(∞) = a·A/s_I` | 3.0 | 3.0000 |
| `O(∞) = 1 − e^(−λI)` | 0.5934 | 0.5934 |

#### 4. No runaway guard in the Python solver (found while fixing the above)

`superlinear` and `exponential` recursion kernels produce finite-time blow-up.
The browser implementation capped its own step count, but the Python solver did
not, so an adaptive stepper approaching the singularity ran effectively forever
— a Streamlit session could hang on a user-selectable parameter combination.

Integration now stops cleanly via a terminal event once `I` exceeds `I_abort`,
and the remaining samples hold the **terminal** state. (Padding with the last
`t_eval` sample was misleading: the singularity typically falls between output
samples, so the array could read `max I ≈ 31` for a trajectory that had actually
diverged.) The browser solver gained the matching `I_abort` check.

### Added

- `ModelParams.O_floor` (default `1e-3`) — irreducible thermodynamic signature.
- `ModelParams.term_damping` (default `True`) — enables the reduced stage models.
- `ModelParams.I_abort` (default `1e4`) — runaway bound, 200× the default
  `I_runaway`, which also caps solver cost in the stiff regime.
- `tests/test_invariants.py` — 26 tests asserting *intent* rather than current
  behaviour: `O ≥ 0` and `0 ≤ R ≤ 1` for every stage and across a randomised
  parameter sweep, the analytic stage-1 solution, stage-4c peak-then-decline,
  stage-4a collapse without sign inversion, and that the damping term can never
  become a source.

### Changed

- Stage presets retuned. Initial `R₀` values brought into `[0, 1]`; stages 0–2
  use the reduced models; stages 4c and 5 use superlinear compression/stealth so
  that suppression outgrows production in `I`.
- `test_regimes.py::test_s1` no longer accepts
  `"visible-technological" OR "pre-detectable"`. That disjunction is precisely
  why the stage-1 defect went unnoticed, and it is removed deliberately.
- `m` and `n` changed meaning: fractional suppression **rates** (per unit τ),
  not absolute suppression fluxes. Existing saved configurations will need
  re-tuning of these two coefficients.

### Verification

| Oracle | Scope | Result |
| --- | --- | --- |
| `R(τ)` vs exact closed form | 19 configurations | pass, worst \|err\| 2.3×10⁻⁶ |
| RK45 vs DOP853 @ `rtol=1e-12` | 20 configurations | 20/20 pass |
| `O(τ)` vs independent quadrature | 12 non-singular configurations | pass, ≤1.5×10⁻⁴ |
| Lambert identity `I·e^I = C_R/(b·A_rec)` | 2304 evaluations | pass, 4.4×10⁻¹⁶ |
| Invariants `O ≥ 0`, `0 ≤ R ≤ 1` | 300 random configurations | **0 violations** |
| Python vs JavaScript | 20 configurations | 20/20, identical regime labels |
| Test suite | 62 tests | pass in 7.1 s |

Worst Python↔JS difference after the changes: `|ΔI| = 5.2×10⁻⁵`,
`|ΔR| = 3.1×10⁻⁷`, `|ΔO| = 2.7×10⁻⁵`, `I_crit` to 2×10⁻¹² relative.

### Known limitations

- **`dO/dτ` is stiff.** Its relaxation rate `m·C + n·S` grows like `I²·R`, and an
  explicit RK45 requires `h ≲ 2.8/rate`, so cost scales with the suppression
  weights (measured: `m = n = 0` → 0.014 s; `m = n = 8` → 122 s). `I_abort`
  bounds the worst case. A stiff-capable integrator (LSODA/Radau) would remove
  this, at the price of numerical parity with the browser RK45.
- **Collapse is still a proxy, not a trajectory.** Stage 4a raises the collapse
  flags (`R < R_min`, `A_rec/R > Θ`) but capability does not actually fall — the
  model contains no mortality term, so the "transient spike then disappearance"
  signature of §7.5 is not reproduced dynamically.
- **The Lambert boundary remains an auxiliary diagnostic.** `C_R` appears nowhere
  in `dI/dτ`; the integrated system's own threshold is logarithmic. Unchanged by
  this release and discussed in `lessons_learned.md` §7.2.
- `validate.js` still requires a `fermi_reference.json` that is not in the
  repository, so the browser validation harness cannot run as shipped.

---

## [0.1.0] — 2026-06-21

Initial release — Ulm University Quantum Hackathon, June 2026.
