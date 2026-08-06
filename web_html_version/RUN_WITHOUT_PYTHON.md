# ▶ HTML VERSION — NO PYTHON REQUIRED

**This folder is the browser build of the Recursive Observability Explorer.**

## How to run it

**Open `index.html` in any web browser.**

That is the entire procedure. There is:

- no `pip install`
- no Streamlit
- no server or backend
- no build step
- no Python of any kind

All of the mathematics — the adaptive Dormand–Prince RK45 ODE solver with dense output,
the Lambert W₀ function, the regime classifier, the Drake decomposition — is implemented
in JavaScript (`js/model.js`) and runs entirely in the browser.

## One caveat: internet connection needed

This version is **Python-free but not offline-capable**. `index.html` loads three
dependencies from CDNs:

| Dependency | Source |
| --- | --- |
| Plotly 2.35.2 | `cdn.plot.ly` |
| KaTeX 0.16.9 | `cdn.jsdelivr.net` |
| Space Grotesk / JetBrains Mono | `fonts.googleapis.com` |

Vendoring these locally would make the folder fully self-contained.

## The other version

The Python/Streamlit implementation of the same model is in
[`../recursive_observability_explorer/`](../recursive_observability_explorer/).
That one **does** need Python:

```bash
cd ../recursive_observability_explorer
pip install -r requirements.txt
streamlit run app.py
```

## Are the two versions equivalent?

Yes — this was verified numerically, not assumed. Both implementations were run on the same
20 configurations (8 stage presets, 5 `F(I)` kernels, 4 static `O(I)` models, time-varying
drivers, a Lambert configuration, and a non-default component setup) and compared pointwise:

| Quantity | Worst difference across all 20 configurations |
| --- | --- |
| `I(τ)` | 3.36 × 10⁻⁵ |
| `R(τ)` | 1.22 × 10⁻⁷ |
| `O(τ)` | 5.76 × 10⁻⁵ |
| `I_crit` (Lambert) | 2.2 × 10⁻¹² relative |
| Regime label | identical in 20 / 20 |

That is agreement at the level of the solver tolerance itself (`rtol = 1e-6`), between two
independently written adaptive integrators. Full methodology and evidence:
[`../lessons_learned.md`](../lessons_learned.md) §4.

## Known issue in this folder

`validate.js` **does not run as shipped.** It does `require("/home/user/workspace/fermi_reference.json")`
— an absolute path from the original development machine — and that reference file is not in
the repository. Running it fails with `Error: Cannot find module`. The claim in `README.md`
that "all 25 checks pass" therefore cannot currently be reproduced by anyone who clones this.
See `../lessons_learned.md` §3.
