# Publication Plan — Recursive Observability Filter

**Purpose.** Agree what goes into the first LaTeX draft *before* writing it. This is the
contract for `paper/main.tex`.

- **Date:** 2026-07-30
- **Inputs:** `The_Fermi_Paradox_v3.md` (theory), `lessons_learned.md` (verification evidence),
  `CHANGELOG.md` (model corrections), the two simulator implementations.
- **Status:** awaiting sign-off on §11 decisions, then drafting begins.

---

## 1. Paper identity

| Field | Proposal |
| --- | --- |
| **Title** | *The Recursive Observability Filter: A Dynamical-Systems Framework for Civilizational Detectability and the Fermi Paradox* |
| **Type** | Methods / modelling-framework paper with simulation results |
| **Target venue** | *International Journal of Astrobiology* (CUP) — **recommended** |
| **Alternatives** | *Acta Astronautica*; *JBIS*; arXiv preprint (astro-ph.EP / physics.soc-ph) first |
| **Length** | ~9,000 words main text, 10 figures, 6 tables, ~70 references |
| **Authors** | **[DECISION NEEDED — §11]** |

**Why IJA.** It publishes Fermi-paradox and Drake-equation modelling papers (Prantzos 2013, 2020;
Verendel & Häggström 2017; Sheikh 2020 are all IJA), accepts framework//methods contributions
without requiring new observational data, and has no hard length ceiling that would force us to
cut the verification section — which is our main differentiator.

---

## 2. Thesis and claims

**Thesis.** The Fermi paradox should be modelled not only through *how many* civilisations exist,
but through *how long they remain externally observable* — and observability should be a dynamical
variable with its own equation, not a fixed coefficient.

Three claims, each tagged with the strength label it will carry in the paper:

| # | Claim | Strength |
| --- | --- | --- |
| C1 | Existence, detectability and observation are distinct and must be modelled separately; non-observation constrains their product, not existence alone. | **Established** (logical/decompositional) |
| C2 | If observability is given its own dynamics, a civilisation can be simultaneously high-capability and low-observability without collapsing or hiding — and this regime is reachable under plausible parameters. | **Hypothetical** (model result) |
| C3 | Peak-then-decline observability *emerges* whenever signal suppression scales faster in capability than signal production, rather than needing to be assumed. | **Plausible** (derived, but from chosen functional forms) |

**What we explicitly do not claim.** That extraterrestrial civilisations exist; that advanced
civilisations become invisible; that recursive AI causes collapse; that the Fermi paradox is
solved. This disclaimer goes in the abstract *and* §1.

---

## 3. Contributions (honest accounting)

The dynamical core is a simple 3-ODE system, and we should not oversell it. The defensible
contributions are:

1. **An observability-aware decomposition** `N_obs = N_true · P_surv · h(O) · P_search` that
   separates survival, signal production and search coverage, and shows where the framework acts
   on the Drake equation.
2. **Two structural propositions** guaranteeing the model stays physical: `O ≥ O_floor` and
   `R ∈ [0,1]` hold by construction, not by clamping. **This is new in this work** and is what
   makes the low-observability regime interpretable at all (§6 of `lessons_learned.md`).
3. **Peak-then-decline as a derived result** (C3) rather than an imposed functional form — which
   answers the standard "you assumed your conclusion" objection.
4. **A registry architecture that makes falsifiability operational**: 5 recursion kernels × 4
   observability models × 2 forms each for five component terms, all swappable without touching
   the solver, so "does the conclusion survive changing the functions?" is a menu selection.
5. **A verification protocol unusual for this literature**: six independent oracles including
   closed-form solutions, an independent high-order integrator, property-based invariant testing
   over 300 randomised parameter sets, and *two independently written implementations agreeing to
   solver tolerance*.
6. **An honest treatment of the Lambert W special case**, including a negative result: the
   `I·e^I` threshold that justifies W is *not* the threshold governing the integrated system.

Contribution 5 is, realistically, the strongest and most distinctive. Lead with it in the abstract.

---

## 4. Section outline

Target lengths are guidance, not limits.

| § | Title | Words | Content |
| --- | --- | --- | --- |
| — | **Abstract** | 250 | Problem; observability as dynamical variable; the two propositions; derived peak-decline; dual-implementation verification; explicit non-claims. |
| 1 | **Introduction** | 1200 | Fermi paradox as an *inference* problem. `existence ≠ detectability ≠ observation`. Why observability deserves its own ODE. Contributions list. Roadmap. |
| 2 | **Background** | 1200 | Drake equation and what exoplanet science settled. Great Filter (Hanson, Bostrom, Ord, Ćirković). Technosignatures (Dyson, Kardashev, Wright, Sheikh). Expansion/percolation (Hart, Tipler, Landis, Armstrong & Sandberg). Hard steps & grabby aliens (Carter, Kipping, Hanson et al. 2021). Recursive intelligence (Good, Bostrom, Russell). **Table 1** literature matrix. Gap: all treat detectability as static. |
| 3 | **Observability decomposition** | 800 | `N_true ≥ N_detectable ≥ N_observed`. Derivation of `N_obs = N_true·P_surv·h(O)·P_search`. Relation to Drake `L`. Why non-detection is weak evidence. **Fig 1**, **Fig 2**. |
| 4 | **The dynamical model** | 1800 | Variables `I, R, O` and what they are *not* (esp. `I` ≠ IQ). Mechanism-balance derivation of each equation. **Proposition 1** (`O ≥ O_floor`) and **Proposition 2** (`R ∈ [0,1]`) with proofs — short, ~5 lines each. Registry of functional variants. Regime classifier and its priority ordering. **Fig 3**, **Fig 4**, **Tables 2–4**. |
| 5 | **The Lambert special case** | 800 | When W is genuinely required (`x·e^x = y`) vs when a logarithm suffices. The §8.2 derivation *including* the cancellation of `I`. The auxiliary balance `C_R`. `I_crit = W(C_R/(b·A_rec))`. Explicit statement that this is a diagnostic, not the dynamical threshold. **Fig 9**. |
| 6 | **Numerical methods and verification** | 1300 | RK45 with dense output; tolerances; the runaway guard and why it is needed. The six oracles and their results. Property-based invariant testing. Dual-implementation agreement. **Table 5**, **Fig 10**. |
| 7 | **Results** | 1800 | Stage trajectories 0–5 (**Fig 5**). Observability-model comparison A–D and robustness of conclusions across them (**Fig 6**). The derived peak-decline result, with the before/after contrast (**Fig 7**). Phase diagram and regime boundaries (**Fig 8**). Detection chain: how much of the "silence" is rarity vs collapse vs quietness vs search coverage. |
| 8 | **Discussion** | 1200 | What the model does and does not show. Comparison with Great Filter, grabby aliens, zoo hypothesis, percolation. Thermodynamic constraints: why `O_floor > 0` matters and why "invisible" is not available. Implications for technosignature search strategy (favours waste-heat/IR over narrowband if C2 holds). **Table 6** claim-strength summary. |
| 9 | **Limitations and failure criteria** | 700 | Stiffness of `dO/dτ`. Collapse is a proxy, not a trajectory. Lambert boundary is auxiliary. No empirical calibration — parameters are dimensionless and unconstrained. Explicit falsification conditions (from manuscript §9.4). |
| 10 | **Conclusions** | 400 | Restate thesis, the three claims with their labels, and the artifact. |

**Appendices:** A Notation · B Closed-form solutions (`R(τ)`; stage-1 logistic) · C Full parameter
table with bounds and defaults · D Verification protocol and reproduction commands · E Artifact
availability.

---

## 5. Figures

Ten figures. Status is honest about what exists.

| # | Figure | Type | Source | Status |
| --- | --- | --- | --- | --- |
| 1 | Existence / detectability / observation | TikZ | conceptual | **to author** |
| 2 | Drake → observability decomposition | TikZ | conceptual | **to author** |
| 3 | Civilisation-stage ladder, stages 0–5 → variables | TikZ | manuscript §5.1 | **to author** |
| 4 | Model schematic: `I`, `R`, `O` couplings and signs | TikZ | model | **to author** |
| 5 | Stage trajectory panel — `I`, `R`, `O` for all 8 presets | 3×8 grid | `stages.py` | **data ready** |
| 6 | Observability models A–D compared | 2×2 | `functions.py` | **data ready** |
| 7 | **Derived peak-decline: absolute vs fractional suppression** | 2-panel | before/after fix | **data ready** |
| 8 | Phase diagram `I`–`R` with regime regions | contour | `regimes.py` | **data ready** |
| 9 | Lambert boundary `I_crit` over `(R, A_rec)` | contour | `lambert.py` | **data ready** |
| 10 | Python vs JavaScript cross-validation + residuals | 2-panel | verification harness | **data ready** |

**Figure 7 is the paper's signature figure.** Left panel: stage 4c under the original absolute
suppression, observability diving to −1431 — physically meaningless yet still classified
"optimized low-observable". Right panel: the corrected fractional form, rising to 0.231 and
decaying to 0.037, strictly positive. It makes the methodological argument visible in one image
and demonstrates C3.

**Figure 10** is unusual for this literature and worth the space: two independently written
integrators agreeing to 5×10⁻⁵ is direct evidence of implementation correctness.

**Production conventions.** Vector PDF via `kaleido`; one figure per file; no titles baked into
the image (use `\caption`); ≥9 pt at final column width; colourblind-safe palette; consistent
colour per variable (`I` / `R` / `O`) across every figure. A single script
`paper/make_figures.py` regenerates all of them deterministically (fixed seeds), writing to
`paper/figures/`.

---

## 6. Tables

| # | Table | Content |
| --- | --- | --- |
| 1 | Literature matrix | Cluster → key question → representative sources (manuscript App. G) |
| 2 | Model variables | Symbol, meaning, range, interpretation, what it is *not* |
| 3 | Function registry | All swappable variants for `F`, `O`, `E`, `B`, `X`, `C`, `S` |
| 4 | Stage presets | Specified behaviour vs simulated outcome vs regime (the §6.3 validation table) |
| 5 | Verification results | Six oracles, scope, outcome |
| 6 | Claim-strength summary | Every substantive claim tagged Established / Plausible / Hypothetical / Speculative |

Table 6 is a distinctive feature — few papers in this area label claim strength systematically,
and it directly pre-empts the "unfalsifiable speculation" objection.

---

## 7. Citations

- **Base:** ~70 references already in the manuscript, in nine clusters — reusable as-is.
- **Format:** BibTeX, `refs.bib`, Harvard/author-date (IJA house style).
- **Work needed:**
  - Convert the plain-text bibliography to BibTeX with **DOIs** for every entry.
  - Hanson (1998) *The Great Filter* is a web essay — needs a stable archived citation.
  - Verify page ranges for the pre-2000 QJRAS entries (Hart, Tipler, Brin).
  - **Add** (currently missing, and referees will expect them): Haqq-Misra & Baum (2009) on
    sustainability solutions; Forgan (2019) *Solving Fermi's Paradox* (CUP) as the standard
    monograph; Balbi & Ćirković (2021) on the anthropics of silence; Wright et al. (2022) on the
    technosignature search-space "haystack".
  - **Decide on the quantum cluster** (Shor, Nielsen & Chuang, Preskill): currently cited but
    unused by the model. Either connect it — the honest route is `A_rec` as a compute-scaling
    driver, explicitly flagged **Speculative** — or cut it. A referee will ask why a paper from a
    quantum hackathon has no quantum content in its equations. **[DECISION — §11]**

---

## 8. LaTeX structure

```
paper/
├── main.tex               # document class, packages, front matter
├── refs.bib
├── sections/
│   ├── 01_introduction.tex ... 10_conclusions.tex
│   └── appendix_a..e.tex
├── figures/               # PDFs from make_figures.py + TikZ sources
├── tables/                # generated tables (booktabs)
├── make_figures.py        # regenerates every figure deterministically
└── Makefile               # `make` -> main.pdf ; `make figures` ; `make clean`
```

Packages: `amsmath`, `amssymb`, `booktabs`, `graphicx`, `siunitx`, `natbib`, `hyperref`,
`cleveref`, `tikz`, `pgfplots`, `algorithm2e` (for the integration/classification pseudocode),
`orcidlink`. One `\newcommand` block for notation so symbols stay consistent
(`\Icap`, `\Reg`, `\Obs`, `\Icrit`, …).

Build must be reproducible: `make` from a clean checkout produces `main.pdf`, and
`make figures` regenerates every figure from the simulator.

---

## 9. Anticipated referee objections — and where we answer them

Pre-empting these in-text is cheaper than a revision round.

| Objection | Our answer | Where |
| --- | --- | --- |
| "You assumed the conclusion by picking a peaked `O(I)`." | Peak-decline is *derived* from suppression outgrowing production; the peaked static form is one option among four, and results are compared across all four. | §7, Fig 6–7 |
| "Lambert W is decorative." | We show the natural balance cancels `I` and yields a logarithm, state that `C_R` is an auxiliary balance, and label the boundary a diagnostic. | §5 |
| "The parameters are arbitrary." | Conceded explicitly. Model is dimensionless and exploratory; we report robustness across functional forms rather than point predictions, and give failure criteria. | §9 |
| "This is unfalsifiable." | Table 6 claim-strength labels + explicit failure criteria + the registry making function-sensitivity testable. | §6, §9, Table 6 |
| "Low observability violates thermodynamics." | `O_floor > 0` is structural; we never permit invisibility, and say so. | §4, §8 |
| "How do we know the code is right?" | Six independent oracles; two implementations agreeing to 5×10⁻⁵. | §6, Fig 10 |
| "Another Drake-equation toy." | The contribution is that detectability is *dynamical* and bounded-by-construction, plus the verification protocol. | §1, §3 |

---

## 10. Work sequence

| Step | Output | Depends on |
| --- | --- | --- |
| 1 | LaTeX skeleton, `main.tex`, `Makefile`, notation macros | venue decision |
| 2 | `refs.bib` with DOIs + 4 additions | — |
| 3 | `make_figures.py` → Figures 5–10 | merged model fixes (PR #1) |
| 4 | TikZ Figures 1–4 | — |
| 5 | Draft §3–§7 (technical core — most reusable from existing material) | steps 1, 3 |
| 6 | Draft §1, §2, §8–§10 | step 5 |
| 7 | Tables 1–6 | step 5 |
| 8 | Internal consistency pass: every equation against the code; every number against a verification log | all |
| 9 | Manuscript corrections back-ported (§6.3/§6.4 equations, abstract `P_search` double-count) | — |

Steps 2 and 4 are independent of the code and can proceed immediately.

**Note:** Step 3 needs PR #1 merged — figures generated from the pre-fix model would show the
negative-observability artefact as if it were a result.

---

## 11. Decisions needed before drafting

1. **Venue** — IJA (recommended), Acta Astronautica, or arXiv preprint first?
2. **Authors and affiliations** — full list, order, ORCIDs, corresponding author. Which hackathon
   team members are authors vs acknowledged?
3. **Hackathon framing** — keep it visible (honest provenance, explains scope) or drop it (reads
   as less serious to some referees)? *Recommendation: one line in Acknowledgements only.*
4. **Quantum content** — connect `A_rec` to compute scaling, or cut the quantum cluster? (§7)
5. **Scope** — full framework paper as outlined, or a tighter methods paper centred on the
   verification protocol and the two propositions (~5,000 words, faster to publish)?
6. **Artifact citation** — mint a Zenodo DOI for the repository at submission?

---

## 12. What is ready now

- Theory text, equations and bibliography: **converted and available** (`The_Fermi_Paradox_v3.md`).
- Model, corrected and verified: **ready** (PR #1).
- Figure data for 6 of 10 figures: **ready**.
- Verification results for §6 and Table 5: **complete and quantified**.
- Not started: LaTeX skeleton, BibTeX conversion, figure generation script, TikZ diagrams, prose.
