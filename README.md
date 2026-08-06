# Recursive Observability Explorer

**Ulm University Quantum Hackathon — June 2026**

A dynamical-systems simulation for the [Fermi Paradox](https://en.wikipedia.org/wiki/Fermi_paradox), built around the *Recursive Observability Filter* framework. The central question is not just *"how many civilizations exist?"* but *"how does detectability evolve as a civilization passes through stages of recursive intelligence?"*

### ▶ Run it in your browser — nothing to install

**<https://rehmozayub.github.io/Ulm_QH_recursive_observability_explorer/>**

Every stage preset loads with one click and every parameter is a slider.
See [Deploying the simulator](#deploying-the-simulator) if the link is not live yet.

The accompanying paper is in [`paper/main.pdf`](paper/main.pdf).

---

## The Core Idea

Classical approaches conflate three distinct quantities:

```
N_true  ≥  N_detectable  ≥  N_observed
```

A civilization can **exist** without being detectable, and be detectable without being **observed**. This project models all three separately via a coupled ODE system:

| Equation | Meaning |
|---|---|
| `dI/dτ = a·A·I + b·A_rec·F(I) − c·R·I − s_I·I²` | Capability growth, recursive amplification, regulatory damping |
| `dR/dτ = (u·A_ref + v·Q)·(1 − R) − (w·A_rec + s_R)·R` | Regulation built on remaining headroom, eroded in proportion to what exists |
| `dO/dτ = p·E + q·B + r·X − (O − O_floor)·(m·C + n·S)` | Observability driven by energy/broadcast/expansion, suppressed **fractionally** above a thermodynamic floor |

Detection chain: `N_obs = N_true · P_surv · h(O) · P_search`

The `R` and `O` equations are written this way on purpose. Erosion must be
proportional to the regulation that exists, and suppression must act on the
signal actually being emitted — you cannot suppress emissions that are not being
made. Together these bound `R ∈ [0,1]` and `O ≥ O_floor` **by construction**
rather than by clamping. See `CHANGELOG.md` for the earlier forms and why they
failed.

---

## Civilizational Stages

| Stage | Name | Observability behaviour |
|---|---|---|
| 0 | Pre-technological | No technosignatures |
| 1 | Early technological | Rising — radio leakage, industrial signatures |
| 2 | Planetary technological | High — global energy, broadcasts |
| 3 | Recursive intelligence transition | Inflection — branches to 4a / 4b / 4c |
| 4a | Collapse | Brief spike, then crash |
| 4b | Expansionist advanced | Stays high — megastructures, expansion |
| 4c | Optimized low-observable | Declining — efficiency, directed comms |
| 5 | Post-biological / unknown | Poorly constrained — speculative |

---

## The Lambert Filter (Special Case)

When `F(I) = I·eᴵ`, the capability threshold becomes `I·eᴵ = C`, solved exactly by the **Lambert W function**: `I_crit = W(C)`. The code enforces this via `lambert_is_valid()` — W is never used decoratively.

---

## Project Structure

```
recursive_observability_explorer/
│
├── app.py                  # Streamlit entry point
├── requirements.txt
│
├── model/
│   ├── config.py           # ModelParams dataclass — all coefficients and selectors
│   ├── system.py           # ODE right-hand side (rhs)
│   ├── functions.py        # F(I), O(I), detection chain, component term registries
│   ├── lambert.py          # Lambert W boundary, validity guard
│   ├── solver.py           # scipy RK45 solver, Result dataclass
│   ├── regimes.py          # Regime classifier (7 regimes)
│   ├── stages.py           # 8 stage presets (S0–S5 including 4a/4b/4c)
│   └── drake.py            # Drake equation decomposition
│
├── ui/
│   ├── sidebar.py          # Sliders, presets, function selectors
│   └── tabs.py             # Tab renderers + claim-strength legend
│
├── viz/
│   └── plots.py            # Plotly figures — Plot 1–5 + observability functions
│
└── tests/
    ├── test_system.py      # RHS finiteness, F_key switching, dynamic vs static mode
    └── test_regimes.py     # Each preset integrates and returns the expected regime label
```

---

## Quick Start

```bash
git clone https://github.com/RehmozAyub/Ulm_QH_recursive_observability_explorer.git
cd Ulm_QH_recursive_observability_explorer/recursive_observability_explorer
pip install -r requirements.txt
pytest
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Deploying the simulator

The `web_html_version/` directory is a self-contained static site — plain HTML,
CSS and JavaScript, no build step and no server-side code. That makes GitHub
Pages the natural place to host it, and it is free for public repositories.

`.github/workflows/pages.yml` in this repository already does the publishing.
It needs **one manual step**, because GitHub will not enable Pages for you:

1. Go to **Settings → Pages** in the repository on github.com.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Push to `main` (or open **Actions → Deploy simulator to GitHub Pages → Run
   workflow** to trigger it by hand).

The site then appears at

```
https://rehmozayub.github.io/Ulm_QH_recursive_observability_explorer/
```

and redeploys automatically on every push to `main`.

**Why a workflow rather than the simpler "deploy from a branch" option?**
Branch-based Pages can only serve the repository root or a folder named `docs/`.
The simulator lives in `web_html_version/`, so serving it that way would mean
either moving the directory or duplicating it. The workflow just uploads that
one directory as the site root, which keeps the repository layout intact.

**Note on external resources.** The page loads KaTeX, Plotly and Google Fonts
from CDNs, so a viewer needs internet access. That is fine for a hosted link.
If you ever need it to work fully offline, vendor those three dependencies into
`web_html_version/` and switch the `<script>`/`<link>` tags to relative paths.

---

## Plots

| Plot | What it shows |
|---|---|
| 1 — Capability & Regulation | `I(τ)` vs `R(τ)` — does capability outrun regulation? |
| 2 — Observability | `O(τ)` under the chosen observability model |
| 3 — Detected Population | `N_obs` and `P_det` — the full detection chain |
| 4 — Phase Diagram | `I` vs `R` state space with regime regions |
| 5 — Lambert Boundary | `I_crit = W(C)` contour over `(R, A_rec)` grid |
| Obs Functions | Side-by-side comparison of Models A–D |

---

## Observability Models

| Model | Formula | Behaviour |
|---|---|---|
| A — increasing | `1 − exp(−λI)` | Rises monotonically with capability |
| B — decreasing | `exp(−λI)` | Falls monotonically — compression/stealth |
| C — peaked | `I · exp(−λI)` | Rises during expansion, falls after optimization |
| D — threshold | `sigmoid(±k(I − Ic))` | Step-like transition at capability threshold |

---

## Regime Classification

| Regime | Condition | Claim strength |
|---|---|---|
| `pre-detectable` | Low `I`, low `O` | 🔵 Plausible |
| `visible-technological` | Moderate `I`, sufficient `O` | 🔵 Plausible |
| `expansionist-visible` | High `I`, high `O` | 🟡 Hypothetical |
| `optimized-low-observable` | High `I`, sufficient `R`, low `O` | 🟡 Hypothetical |
| `collapse-proxy` | `A_rec/R > θ` or `R < R_min` | 🟡 Hypothetical |
| `runaway` | `I > I_runaway` | 🔴 Speculative |
| `uncertain` | None of the above | 🔵 Plausible |

All claims in the UI are labeled **Established / Plausible / Hypothetical / Speculative** per the dossier's claim-strength rubric.

---

## Dependencies

| Package | Min version |
|---|---|
| streamlit | 1.36 |
| numpy | 1.26 |
| scipy | 1.13 |
| plotly | 5.22 |
| pandas | 2.2 |
| pytest | 8.2 |

---

## Scientific Framing

This is a **modeling framework**, not a solution to the Fermi Paradox. It asks:

> *Which assumptions about recursive intelligence, regulation, and observability produce cosmic silence — and which produce visible civilizations?*

Every significant output is labeled by claim strength. The model does not assert civilizations must become invisible; it asks what follows **if** recursive feedback occurs and **if** observability changes with capability.

---

*Built for the Ulm University Quantum Hackathon, June 2026.*
