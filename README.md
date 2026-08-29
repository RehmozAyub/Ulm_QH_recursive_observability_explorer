# Recursive Observability Explorer

**A dynamical-systems framework for civilizational detectability and the Fermi Paradox.**

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
browser (no backend) and features six linked views, a 3D state-space view of the
(I, R, O) trajectory, plain-language interpretations on every plot, and a
synthesised findings summary of the current case.

The site is served from [`web_version/`](web_version) by the workflow in
[`.github/workflows/pages.yml`](.github/workflows/pages.yml).

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
| `dO/dτ = p·E + q·B + r·X − (O − O_floor)·(m·C + n·S)` | Observability from energy/broadcast/expansion, suppressed above a thermodynamic floor |

Detection chain: `N_obs = N_true · P_surv · h(O) · P_search`.

When `F(I) = I·eᴵ`, the capability threshold `I·eᴵ = C` is solved exactly by the
**Lambert W function** (`I_crit = W(C)`), enforced through a validity guard so
that W is never used decoratively.

### Regime classification

| Regime | Condition | Claim strength |
|---|---|---|
| `pre-detectable` | Low `I`, low `O` | Plausible |
| `visible-technological` | Moderate `I`, sufficient `O` | Plausible |
| `expansionist-visible` | High `I`, high `O` | Hypothetical |
| `optimized-low-observable` | High `I`, sufficient `R`, low `O` | Hypothetical |
| `collapse-proxy` | `A_rec/R > θ` or `R < R_min` | Hypothetical |
| `runaway` | `I > I_runaway` | Speculative |
| `uncertain` | None of the above | Plausible |

Every output is labeled **Established / Plausible / Hypothetical / Speculative**.

---

## Repository layout

```
.
├── web_version/                  # Interactive browser simulator (deployed to Pages)
│   ├── index.html                #   welcome  ·  explorer.html  ·  guide.html
│   └── css/  js/                 #   vanilla JS + Plotly + three.js + KaTeX (via CDN)
├── recursive_observability_explorer/   # Python / Streamlit reference implementation
│   ├── app.py                    #   Streamlit entry point
│   ├── model/                    #   ODE system, solver, Lambert boundary, regimes, Drake
│   ├── ui/  viz/                 #   sidebar, tabs, Plotly figures
│   └── tests/                    #   pytest suite
└── .github/workflows/            # GitHub Pages deployment
```

---

## Running locally

**The browser simulator** (no build step):

```bash
git clone https://github.com/RehmozAyub/Ulm_QH_recursive_observability_explorer.git
cd Ulm_QH_recursive_observability_explorer/web_version
python -m http.server 8000
# open http://localhost:8000/
```

It loads KaTeX, Plotly, three.js and fonts from CDNs, so it needs internet access.

**The Python reference model:**

```bash
cd recursive_observability_explorer
pip install -r requirements.txt
pytest                # verify the model
streamlit run app.py  # opens at http://localhost:8501
```

The browser build mirrors this Python model; its adaptive RK45 solver and Lambert
W implementation are cross-checked against the SciPy reference.

---

## Citation

If you use this framework or simulator, please cite:

```bibtex
@misc{ayub2026recursive,
  title        = {The Recursive Observability Filter: A Dynamical-Systems Framework
                  for Civilizational Detectability and the Fermi Paradox},
  author       = {Ayub, Muhammad Rehmoz Salahuddin and Saghir, Dilawaiz and Witter, Raiker},
  year         = {2026},
  howpublished = {\url{https://github.com/RehmozAyub/Ulm_QH_recursive_observability_explorer}},
  note         = {Ulm University Quantum Hackathon}
}
```

---

*Built for the Ulm University Quantum Hackathon, 2026.*
