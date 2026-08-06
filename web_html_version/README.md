# Recursive Observability Explorer

An interactive, single-page dynamical-systems simulator for the Fermi Paradox — a
browser implementation of the **Recursive Observability Filter (ROF)** model.

Built from
[RehmozAyub/Ulm_QH_recursive_observability_explorer](https://github.com/RehmozAyub/Ulm_QH_recursive_observability_explorer)
— Ulm University Quantum Hackathon, June 2026.

> A modeling framework, not a solution to the Fermi Paradox.

## What it does

Solves three coupled ODEs over capability (I), regulation (R) and observability (O)
in dimensionless time τ, classifies the resulting trajectory into one of seven
civilisation regimes, and renders six Plotly visualizations, a regime verdict card,
a Lambert-W critical-boundary contour and a Drake-equation decomposition — all
recomputed live in the browser (no backend).

## Stack

- Vanilla JS + Plotly.js (CDN) + KaTeX (CDN)
- Adaptive Dormand–Prince RK45 solver with dense output (mirrors SciPy `solve_ivp`)
- Lambert W₀ via Halley iteration
- Animated canvas starfield + burning meteors (respects `prefers-reduced-motion`)

## Files

| File | Purpose |
| --- | --- |
| `index.html` | App shell, controls, tabs, equations |
| `css/style.css` | Deep-space glassmorphic theme |
| `js/config.js` | ModelParams defaults, bounds, groups, labels, stage presets |
| `js/model.js` | ODE system, RK45 solver, Lambert W, registries, regime classifier, Drake |
| `js/plots.js` | Six Plotly dark-theme visualizations |
| `js/background.js` | Parallax starfield + meteor animation |
| `js/app.js` | UI orchestration, debounced recompute, renderers |
| `validate.js` | Node harness cross-checking JS math vs. the Python reference |

## Validation

`node validate.js` cross-checks the JS math against values produced by the original
Python/SciPy model: Lambert-W identities (W(1)≈0.5671432904, W(e)=1, W(0)=0), the
default trajectory at τ = 10/25/50 (within 1%), and the classified regime for all
eight stage presets. All 25 checks pass; 8/8 preset regimes match.
