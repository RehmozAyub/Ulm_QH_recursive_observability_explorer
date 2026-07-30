"""Regenerate every data figure for the ROF paper, deterministically.

Usage:  python make_figures.py            (writes paper/figures/*.pdf)

Figures 1-4 are TikZ and live in the LaTeX source.  This script produces
figures 5-10.  Figure 10 needs js_dump.json; run  node js_dump.js  first
(it is optional -- the figure is skipped with a warning if absent).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.integrate import solve_ivp
from scipy.special import lambertw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "recursive_observability_explorer"))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

from model.config import ModelParams                      # noqa: E402
from model.solver import integrate                        # noqa: E402
from model.stages import get_stage, stage_keys, STAGE_LABELS  # noqa: E402
from model.regimes import classify_regime                 # noqa: E402
from model.functions import O_REGISTRY                    # noqa: E402
from model.lambert import lambert_boundary                # noqa: E402

# --------------------------------------------------------------------------
# Style — Okabe-Ito colourblind-safe palette, serif to match the LaTeX body
# --------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9,
    "legend.fontsize": 7.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.linewidth": 0.7,
    "lines.linewidth": 1.4,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "figure.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

C_I, C_R, C_O = "#0072B2", "#009E73", "#D55E00"          # capability, regulation, observability
STAGE_COLORS = ["#999999", "#0072B2", "#56B4E9", "#009E73",
                "#D55E00", "#E69F00", "#CC79A7", "#7570B3"]

TEXTWIDTH = 6.5   # inches, matches \textwidth of the article class at 11pt


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path)
    plt.close(fig)
    print("wrote", os.path.relpath(path, REPO))


# ==========================================================================
# Figure 5 — stage trajectories
# ==========================================================================
def fig05():
    fig, axes = plt.subplots(1, 3, figsize=(TEXTWIDTH, 2.25))
    handles = []
    for i, key in enumerate(stage_keys()):
        p, y0 = get_stage(key)
        res = integrate(p, y0)
        col = STAGE_COLORS[i]
        axes[0].plot(res.tau, res.I, color=col)
        axes[1].plot(res.tau, res.R, color=col)
        axes[2].plot(res.tau, np.maximum(res.O, 1e-4), color=col)
        handles.append(Line2D([], [], color=col, label=STAGE_LABELS[key].replace("Stage ", "S")))

    axes[0].set_ylabel(r"capability $I(\tau)$")
    axes[1].set_ylabel(r"regulation $R(\tau)$")
    axes[2].set_ylabel(r"observability $O(\tau)$")
    axes[1].set_ylim(-0.02, 1.02)
    axes[2].set_yscale("log")
    for ax in axes:
        ax.set_xlabel(r"dimensionless time $\tau$")
    axes[1].axhline(0.05, color="k", ls=":", lw=0.8)
    axes[1].text(0.98, 0.07, r"$R_{\min}$", transform=axes[1].get_yaxis_transform(),
                 ha="right", va="bottom", fontsize=7)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.16),
               ncol=4, frameon=False)
    save(fig, "fig05_stage_trajectories.pdf")


# ==========================================================================
# Figure 6 — the four static observability models
# ==========================================================================
def fig06():
    p = ModelParams()
    I = np.linspace(0, 20, 600)
    labels = {
        "increasing": r"A: $1-e^{-\lambda I}$",
        "decreasing": r"B: $e^{-\lambda I}$",
        "peaked":     r"C: $I e^{-\lambda I}$",
        "threshold":  r"D: $\sigma(k(I-I_c))$",
    }
    fig, ax = plt.subplots(figsize=(TEXTWIDTH * 0.62, 2.1))
    for (key, lab), col in zip(labels.items(), [C_I, C_O, C_R, "#CC79A7"]):
        ax.plot(I, O_REGISTRY[key](I, p), color=col, label=lab)
    ax.axhline(p.O_detectable, color="k", ls=":", lw=0.8)
    ax.text(19.6, p.O_detectable * 1.15, r"$O_{\rm detectable}$", ha="right", fontsize=7)
    ax.set_xlabel(r"capability $I$")
    ax.set_ylabel(r"observability $O(I)$")
    ax.legend(frameon=False, loc="upper right")
    save(fig, "fig06_observability_models.pdf")


# ==========================================================================
# Figure 7 — SIGNATURE FIGURE: absolute vs fractional suppression
# ==========================================================================
def _legacy_rhs(tau, y, p):
    """The superseded formulation, reproduced for the comparison only.

    dO/dtau subtracted an absolute flux (no dependence on O) and dR/dtau
    eroded R at a constant rate, so both could pass through zero.
    """
    I, R, O = float(y[0]), float(y[1]), float(y[2])
    FI = I / (1.0 + I / p.K)                       # saturating kernel
    dI = p.a * p.A * I + p.b * p.A_rec * FI - p.c * R * I - p.sI * I ** 2
    dR = p.u * p.A_ref + p.v * p.Q - p.w * p.A_rec - p.sR * R      # old form
    dO = (p.p * I + p.q * I + p.r * I) - p.m * (I * R) - p.n * (I * R)   # old form
    return [dI, dR, dO]


def fig07():
    # legacy stage-4c preset (pre-correction values)
    leg = ModelParams(A_rec=1.0, a=0.50, c=0.20, sI=0.05, m=2.0, n=2.0,
                      p=0.3, q=0.2, r=0.2, tau_max=50.0)
    sol = solve_ivp(_legacy_rhs, (0, leg.tau_max), [3.0, 1.5, 0.5], args=(leg,),
                    method="RK45", rtol=1e-6, atol=1e-9,
                    t_eval=np.linspace(0, leg.tau_max, 1000))

    p, y0 = get_stage("s4c")
    res = integrate(p, y0)

    fig, axes = plt.subplots(1, 2, figsize=(TEXTWIDTH, 2.3))

    ax = axes[0]
    ax.plot(sol.t, sol.y[2], color=C_O)
    ax.axhline(0.0, color="k", lw=0.8)
    ax.axhline(p.O_detectable, color="k", ls=":", lw=0.8)
    ax.set_xlabel(r"dimensionless time $\tau$")
    ax.set_ylabel(r"observability $O(\tau)$")
    ax.set_title(r"(a) absolute suppression $-mC-nS$", fontsize=8.5)
    ax.annotate(rf"$O_{{\rm final}} = {sol.y[2][-1]:.0f}$",
                xy=(sol.t[-1], sol.y[2][-1]), xytext=(0.45, 0.35),
                textcoords="axes fraction", fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.text(0.04, 0.08, "classified\n'optimized low-observable'", transform=ax.transAxes,
            fontsize=7, style="italic", va="bottom")

    ax = axes[1]
    ax.plot(res.tau, res.O, color=C_O)
    ipk = int(np.argmax(res.O))
    ax.plot(res.tau[ipk], res.O[ipk], "o", ms=3.5, color=C_O)
    ax.axhline(p.O_floor, color="k", ls="--", lw=0.8)
    ax.axhline(p.O_detectable, color="k", ls=":", lw=0.8)
    ax.set_xlabel(r"dimensionless time $\tau$")
    ax.set_ylabel(r"observability $O(\tau)$")
    ax.set_title(r"(b) fractional suppression $-(O-O_{\rm floor})(mC+nS)$", fontsize=8.5)
    ax.set_ylim(0, max(res.O) * 1.25)
    ax.annotate(rf"peak {res.O[ipk]:.3f}", xy=(res.tau[ipk], res.O[ipk]),
                xytext=(0.35, 0.75), textcoords="axes fraction", fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.text(0.97, 0.30, rf"$O_{{\rm final}} = {res.O[-1]:.3f}$", transform=ax.transAxes,
            ha="right", fontsize=7.5)
    ax.text(0.97, 0.16, r"$O_{\rm detectable}$", transform=ax.transAxes, ha="right", fontsize=7)
    ax.text(0.97, 0.04, r"$O_{\rm floor}$", transform=ax.transAxes, ha="right", fontsize=7)
    save(fig, "fig07_suppression_comparison.pdf")


# ==========================================================================
# Figure 8 — phase portrait in the (I, R) plane
# ==========================================================================
def fig08():
    fig, ax = plt.subplots(figsize=(TEXTWIDTH * 0.66, 2.7))
    for i, key in enumerate(stage_keys()):
        p, y0 = get_stage(key)
        res = integrate(p, y0)
        lab, _ = classify_regime(res, p)
        col = STAGE_COLORS[i]
        ax.plot(res.I, res.R, color=col, lw=1.3,
                label=f"{key}: {lab}")
        ax.plot(res.I[0], res.R[0], "o", ms=3, color=col)
        ax.plot(res.I[-1], res.R[-1], "D", ms=3.5, color=col)

    p = ModelParams()
    ax.axvline(p.I_advanced, color="k", ls="--", lw=0.8)
    ax.axhline(p.R_min, color="k", ls=":", lw=0.8)
    ax.text(p.I_advanced * 1.03, 0.95, r"$I_{\rm advanced}$", fontsize=7, rotation=90, va="top")
    ax.text(0.2, p.R_min + 0.02, r"$R_{\min}$", fontsize=7)
    ax.set_xlabel(r"capability $I$")
    ax.set_ylabel(r"regulation $R$")
    ax.set_ylim(-0.02, 1.02)
    ax.set_xscale("symlog", linthresh=1.0)
    ax.legend(frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))
    save(fig, "fig08_phase_portrait.pdf")


# ==========================================================================
# Figure 9 — Lambert boundary
# ==========================================================================
def fig09():
    p = ModelParams(F_key="lambert")
    A_rec = np.linspace(0.05, 3.0, 240)
    R = np.linspace(0.02, 1.0, 240)
    grid = lambert_boundary(p, A_rec, R)

    fig, ax = plt.subplots(figsize=(TEXTWIDTH * 0.62, 2.4))
    cf = ax.contourf(A_rec, R, grid, levels=18, cmap="viridis")
    cs = ax.contour(A_rec, R, grid, levels=[0.5, 1.0, 2.0, 3.0], colors="w", linewidths=0.7)
    ax.clabel(cs, inline=True, fontsize=6.5, fmt="%.1f")
    cb = fig.colorbar(cf, ax=ax, pad=0.02)
    cb.set_label(r"$I_{\rm crit} = W\!\left(C_R / (b A_{\rm rec})\right)$")
    cb.ax.tick_params(labelsize=7)
    ax.set_xlabel(r"recursive amplification $A_{\rm rec}$")
    ax.set_ylabel(r"regulation $R$")
    save(fig, "fig09_lambert_boundary.pdf")


# ==========================================================================
# Figure 10 — Python / JavaScript cross-validation
# ==========================================================================
def fig10():
    js_path = os.path.join(HERE, "js_dump.json")
    if not os.path.exists(js_path):
        print("WARNING: js_dump.json missing -- run `node js_dump.js` first; skipping Fig 10")
        return
    js = json.load(open(js_path))

    keys = ["s3", "s4a", "s4c"]
    fig, axes = plt.subplots(2, 1, figsize=(TEXTWIDTH * 0.72, 3.4),
                             sharex=True, gridspec_kw={"height_ratios": [2.1, 1]})
    for key, col in zip(keys, [C_I, C_R, C_O]):
        p, y0 = get_stage(key)
        res = integrate(p, y0)
        jtau = np.array(js[key]["tau"]); jI = np.array(js[key]["I"])
        pI = np.interp(jtau, res.tau, res.I)
        axes[0].plot(res.tau, res.I, color=col, lw=1.3, label=f"{key} (Python/SciPy)")
        axes[0].plot(jtau[::2], jI[::2], ls="none", marker="o", ms=2.6,
                     mfc="none", mec=col, mew=0.7, label=f"{key} (JavaScript)")
        axes[1].semilogy(jtau, np.abs(pI - jI) + 1e-16, color=col, lw=1.0)

    axes[0].set_ylabel(r"capability $I(\tau)$")
    axes[0].legend(frameon=False, ncol=2, fontsize=6.8)
    axes[1].set_ylabel(r"$|I_{\rm py}-I_{\rm js}|$")
    axes[1].set_xlabel(r"dimensionless time $\tau$")
    axes[1].axhline(1e-6, color="k", ls=":", lw=0.8)
    axes[1].text(0.99, 1.6e-6, "solver tolerance", ha="right", fontsize=6.5,
                 transform=axes[1].get_yaxis_transform())
    axes[1].set_ylim(1e-16, 1e-3)
    save(fig, "fig10_cross_validation.pdf")


if __name__ == "__main__":
    fig05(); fig06(); fig07(); fig08(); fig09(); fig10()
    print("done.")
