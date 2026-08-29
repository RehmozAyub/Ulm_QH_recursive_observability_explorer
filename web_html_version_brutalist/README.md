# Recursive Observability Explorer — Brutalist Deep-Space Console

An alternate visual build of the [Recursive Observability Explorer](../web_html_version).
Same simulator, same math, a different skin: a flat **Swiss-scientific / brutalist
observatory** over a deep-space starfield with meteors, tumbling asteroids, a
survey grid and a single amber-phosphor accent.

The dynamical-systems engine is untouched. `js/config.js`, `js/model.js` and
`js/app.js` are byte-for-byte identical to the original build, so every ODE
solution, regime classification and Drake decomposition is guaranteed to match.

## Pages

| File | Purpose |
| --- | --- |
| `index.html` | Welcome / landing page — animated hero, six-view overview, "Launch" + "How to use" CTAs |
| `explorer.html` | The simulator itself (the reskinned app) |
| `guide.html` | How-to-use page — themed shell, content to be added later |

## What changed vs. the space-glass build

- **`index.html`** — new landing page (was the app; the app is now `explorer.html`).
- **`guide.html`** — new, intentionally empty how-to page.
- **`css/style.css`** — full brutalist restyle: flat solid panels, hairline rules,
  mono numerics, sharp corners, one amber accent. Plus a motion layer
  (entrance rise, scroll-reveal, hover micro-interactions), all gated behind
  `prefers-reduced-motion`.
- **`js/background.js`** — starfield + survey-grid "sky chart" (replaces the
  meteors); gentle twinkle, static under reduced motion.
- **`js/plots.js`** — three theme constants retuned (axis font, gridlines) so the
  Plotly charts read on the flat panel. Categorical series colours (I/R/O/N/P)
  are kept as data encodings.
- **`js/motion.js`** — new IntersectionObserver scroll-reveal helper (no scroll
  listeners).
- **`js/config.js`, `js/model.js`, `js/app.js`** — unchanged from the original.

## Run

Open `index.html` in a browser, or serve the folder:

```
python -m http.server 8000
# then visit http://localhost:8000/
```

No backend; everything is computed live in the browser (Plotly.js + KaTeX via CDN).

> A modeling framework, not a solution to the Fermi Paradox.
