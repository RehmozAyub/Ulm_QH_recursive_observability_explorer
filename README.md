# Recursive Observability Explorer

**A dynamical-systems framework for civilizational detectability and the Fermi Paradox.**
Built for the Ulm University Quantum Hackathon, 2026.

[![License: MIT](https://img.shields.io/badge/License-MIT-e0a24c.svg)](LICENSE)
&nbsp;·&nbsp; [Live simulator](https://rehmozayub.github.io/Ulm_QH_recursive_observability_explorer/)
&nbsp;·&nbsp; [Paper (PDF)](paper/main.pdf)

The Fermi Paradox is usually argued as a question of *number*: how many
civilizations exist? This project reframes it as a question of *visibility*: how
does a civilization's detectability evolve as it grows more capable, and would we
ever catch it? The **Recursive Observability Filter (ROF)** is a small system of
coupled differential equations for watching that visibility rise, peak, or fade.

> This is a modeling framework, not a solution to the Fermi Paradox.

---

## ▶ Try it in your browser — nothing to install

**<https://rehmozayub.github.io/Ulm_QH_recursive_observability_explorer/>**

An interactive, single-page simulator. Pick a civilization stage or tune any
parameter with a slider and the model re-solves live. It runs entirely in the
browser (no backend) and features:

- **Six linked views** — trajectories, the (I, O) phase diagram, the Lambert-W
  boundary, the four observability functions, the full regime decision trace, and
  the Drake decomposition.
- **A 3D state-space view** of the (I, R, O) trajectory you can orbit and zoom.
- **Plain-language interpretations** on every view (for example *"grew loud, then
  went quiet"* or *"past the critical line"*), driven by the current values.
- **A synthesised findings paragraph** that reads out what this exact parameter
  set means, with the numbers, and a one-click copy.

---

## The core idea

Classical approaches conflate three distinct quantities:

```
N_true  ≥  N_detectable  ≥  N_observed
```

A civilization can **exist** without being detectable, and be detectable without
being **observed**. The ROF models all three separately through a coupled ODE
system over capability `I`, regulation `R`, and observability `O`, in
dimensionless time `τ`:

| Equation | Meaning |
|---|---|
| `dI/dτ = a·A·I + b·A_rec·F(I) − c·R·I − s_I·I²` | Capability growth, recursive amplification, regulatory damping |
| `dR/dτ = (u·A_ref + v·Q)·(1 − R) − (w·A_rec + s_R)·R` | Regulation built on remaining headroom, eroded in proportion to what exists |
| `dO/dτ = p·E + q·B + r·X − (O − O_floor)·(m·C + n·S)` | Observability from energy/broadcast/expansion, suppressed fractionally above a thermodynamic floor |

Detection chain: `N_obs = N_true · P_surv · h(O) · P_search`.

The `R` and `O` equations are written so that erosion is proportional to the
regulation that exists and suppression acts only on the signal actually emitted.
Together these bound `R ∈ [0, 1]` and `O ≥ O_floor` **by construction** rather
than by clamping. See [`CHANGELOG.md`](CHANGELOG.md) for the earlier forms and why
they failed.

### The Lambert filter (special case)

When `F(I) = I·eᴵ`, the capability threshold becomes `I·eᴵ = C`, solved exactly by
the **Lambert W function**: `I_crit = W(C)`. The code enforces this through a
validity guard so that W is never used decoratively.

---

## Civilizational stages

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

### Observability models

| Model | Formula | Behaviour |
|---|---|---|
| A — increasing | `1 − exp(−λI)` | Rises monotonically with capability |
| B — decreasing | `exp(−λI)` | Falls monotonically — compression / stealth |
| C — peaked | `I · exp(−λI)` | Rises during expansion, falls after optimization |
| D — threshold | `sigmoid(±k(I − Ic))` | Step-like transition at a capability threshold |

### Regime classification

| Regime | Condition | Claim strength |
|---|---|---|
| `pre-detectable` | Low `I`, low `O` | 🔵 Plausible |
| `visible-technological` | Moderate `I`, sufficient `O` | 🔵 Plausible |
| `expansionist-visible` | High `I`, high `O` | 🟡 Hypothetical |
| `optimized-low-observable` | High `I`, sufficient `R`, low `O` | 🟡 Hypothetical |
| `collapse-proxy` | `A_rec/R > θ` or `R < R_min` | 🟡 Hypothetical |
| `runaway` | `I > I_runaway` | 🔴 Speculative |
| `uncertain` | None of the above | 🔵 Plausible |

Every output in the interface is labeled **Established / Plausible / Hypothetical
/ Speculative** per the paper's claim-strength rubric.

---

## Repository structure

```
.
├── web_html_version_brutalist/   # The interactive simulator (this is what is deployed)
│   ├── index.html                #   welcome page  ·  explorer.html  ·  guide.html
│   ├── css/  js/                 #   vanilla JS + Plotly + three.js + KaTeX (via CDN)
│   └── README.md
├── web_html_version/             # Earlier build of the browser simulator (kept for history)
├── recursive_observability_explorer/   # Python / Streamlit reference implementation
│   ├── app.py                    #   Streamlit entry point
│   ├── model/                    #   ODE system, solver, Lambert boundary, regimes, Drake
│   ├── ui/  viz/                 #   sidebar, tabs, Plotly figures
│   └── tests/                    #   RHS + regime tests (pytest)
├── paper/                        # LaTeX source and compiled PDF of the write-up
├── CHANGELOG.md                  # Model history: earlier equation forms and why they changed
└── The_Fermi_Paradox_v3.md       # Extended background dossier
```

---

## Running locally

### The browser simulator (no build step)

```bash
git clone https://github.com/RehmozAyub/Ulm_QH_recursive_observability_explorer.git
cd Ulm_QH_recursive_observability_explorer/web_html_version_brutalist
python -m http.server 8000
# then open http://localhost:8000/
```

It needs internet access, because KaTeX, Plotly, three.js and the fonts load from
CDNs. To run fully offline, vendor those dependencies into the folder and switch
the `<script>` / `<link>` tags to relative paths.

### The Python reference model

```bash
cd recursive_observability_explorer
pip install -r requirements.txt
pytest                # verify the model
streamlit run app.py  # opens at http://localhost:8501
```

The browser build mirrors this Python model; its adaptive RK45 solver and Lambert
W implementation are cross-checked against the SciPy reference.

---

## The paper

The write-up is in [`paper/main.pdf`](paper/main.pdf), with LaTeX source under
`paper/`. Extended background is in [`The_Fermi_Paradox_v3.md`](The_Fermi_Paradox_v3.md).

### Citation

If you use this framework or simulator, please cite it. Update the author list to
match the paper before publishing:

```bibtex
@misc{recursive_observability_explorer_2026,
  title        = {Recursive Observability Explorer: A Dynamical-Systems Framework
                  for Civilizational Detectability, Recursive Intelligence, and the
                  Fermi Paradox},
  author       = {{The Recursive Observability Explorer authors}},
  year         = {2026},
  howpublished = {\url{https://github.com/RehmozAyub/Ulm_QH_recursive_observability_explorer}},
  note         = {Ulm University Quantum Hackathon}
}
```

---

## License

Released under the [MIT License](LICENSE) — free to use, modify, and redistribute
with attribution. This permissive license is chosen to encourage reproduction and
reuse of the model alongside the paper. The compiled paper and its figures remain
the intellectual work of the authors; if you reuse the text or figures, cite the
paper as above.

---

## Acknowledgements

Built for the **Ulm University Quantum Hackathon, 2026**. The model is a framework
for reasoning about detectability, not a claim about what extraterrestrial
civilizations actually do.
