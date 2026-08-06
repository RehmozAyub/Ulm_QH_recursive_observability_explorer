"""Regenerate every data figure for the ROF paper, deterministically.

Usage:  python make_figures.py            (writes paper/figures/*.pdf)

Figures 1-4 are TikZ and live in the LaTeX source.  This script produces
figures 5-9.

Layout policy: every figure is generated at a width that is a clean fraction
of the 6.5 in text block, and every legend is placed outside the data area.
The LaTeX source then sets an explicit \\includegraphics width, so nothing
depends on the natural size matplotlib happens to choose.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.integrate import solve_ivp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "recursive_observability_explorer"))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

from model.config import ModelParams                      # noqa: E402
from model.solver import integrate                        # noqa: E402
from model.stages import get_stage, stage_keys            # noqa: E402
from model.regimes import classify_regime                 # noqa: E402
from model.functions import O_REGISTRY                    # noqa: E402
from model.lambert import I_crit                          # noqa: E402

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
    "lines.linewidth": 1.5,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "figure.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

C_I, C_R_, C_O = "#0072B2", "#009E73", "#D55E00"   # capability, regulation, observability
STAGE_COLORS = ["#999999", "#0072B2", "#56B4E9", "#009E73",
                "#D55E00", "#E69F00", "#CC79A7", "#7570B3"]

# Short legend labels.  The full names live in the caption and in Table 1;
# a legend that runs off the page is worse than one that abbreviates.
SHORT = {
    "s0":  "0  pre-tech",
    "s1":  "1  early tech",
    "s2":  "2  planetary",
    "s3":  "3  recursive",
    "s4a": "4a  collapse",
    "s4b": "4b  expansionist",
    "s4c": "4c  optimized quiet",
    "s5":  "5  post-biological",
}

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
    fig, axes = plt.subplots(1, 3, figsize=(TEXTWIDTH, 2.45),
                             constrained_layout=True)
    handles = []
    for i, key in enumerate(stage_keys()):
        p, y0 = get_stage(key)
        res = integrate(p, y0)
        col = STAGE_COLORS[i]
        axes[0].plot(res.tau, res.I, color=col)
        axes[1].plot(res.tau, res.R, color=col)
        axes[2].plot(res.tau, np.maximum(res.O, 1e-4), color=col)
        handles.append(Line2D([], [], color=col, label=SHORT[key]))

    axes[0].set_ylabel(r"capability $I(\tau)$")
    axes[1].set_ylabel(r"regulation $R(\tau)$")
    axes[2].set_ylabel(r"observability $O(\tau)$")
    axes[1].set_ylim(-0.03, 1.03)
    axes[2].set_yscale("log")
    for ax in axes:
        ax.set_xlabel(r"time $\tau$")
    axes[1].axhline(0.05, color="k", ls=":", lw=0.8)
    # Right-hand side: the stage-4a curve dives through the left margin here.
    axes[1].text(0.98, 0.075, r"$R_{\min}$",
                 transform=axes[1].get_yaxis_transform(),
                 ha="right", va="bottom", fontsize=7)

    # Legend below the panels, four to a row, so it can never run off the page.
    fig.legend(handles=handles, loc="outside lower center",
               ncol=4, frameon=False, handlelength=1.6,
               columnspacing=1.4, borderaxespad=0.0)
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
    fig, ax = plt.subplots(figsize=(TEXTWIDTH, 2.3), constrained_layout=True)
    for (key, lab), col in zip(labels.items(), [C_I, C_O, C_R_, "#CC79A7"]):
        ax.plot(I, O_REGISTRY[key](I, p), color=col, label=lab)
    # Label the threshold in the legend, not on the axes: every horizontal
    # position along this line is crossed by one of the four curves.
    ax.axhline(p.O_detectable, color="k", ls=":", lw=0.8,
               label=r"$O_{\rm detectable}$")
    ax.set_xlabel(r"capability $I$")
    ax.set_ylabel(r"observability $O(I)$")
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 1.32)
    # Legend below, centred: an outside-right legend makes the axes look
    # off-centre on the page, because the image box includes the legend.
    fig.legend(loc="outside lower center", ncol=5, frameon=False,
               handlelength=1.8, columnspacing=1.6)
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

    fig, axes = plt.subplots(1, 2, figsize=(TEXTWIDTH, 2.5),
                             constrained_layout=True)

    # ---- (a) the broken formulation ------------------------------------
    ax = axes[0]
    ax.plot(sol.t, sol.y[2], color=C_O)
    ax.axhline(0.0, color="k", lw=0.9)
    ax.set_xlabel(r"time $\tau$")
    ax.set_ylabel(r"observability $O(\tau)$")
    ax.set_title(r"(a) absolute suppression:  $-\,mC-nS$", fontsize=8.5)
    ax.set_xlim(0, leg.tau_max)
    # Shade what the model is not allowed to reach, and say so inside it.
    lo = sol.y[2].min() * 1.08
    ax.set_ylim(lo, max(60.0, -0.04 * lo))
    ax.axhspan(lo, 0.0, color="#B2182B", alpha=0.055, lw=0)
    ax.text(0.5, 0.90, r"$O < 0$: physically impossible",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=7.5, style="italic", color="#8B1A1A")
    ax.annotate(rf"$O_{{\rm final}} = {sol.y[2][-1]:.0f}$",
                xy=(sol.t[-1], sol.y[2][-1]), xytext=(0.30, 0.30),
                textcoords="axes fraction", fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.text(0.04, 0.06, "still classified\n‘optimized low-observable’",
            transform=ax.transAxes, fontsize=7, style="italic", va="bottom")

    # ---- (b) the corrected formulation ---------------------------------
    ax = axes[1]
    ax.plot(res.tau, res.O, color=C_O)
    ipk = int(np.argmax(res.O))
    ax.plot(res.tau[ipk], res.O[ipk], "o", ms=4, color=C_O)
    ax.axhline(p.O_floor, color="k", ls="--", lw=0.8)
    ax.axhline(p.O_detectable, color="k", ls=":", lw=0.8)
    ax.set_xlabel(r"time $\tau$")
    ax.set_ylabel(r"observability $O(\tau)$")
    ax.set_title(r"(b) fractional suppression:  $-(O-O_{\rm floor})(mC+nS)$",
                 fontsize=8.5)
    ax.set_xlim(0, p.tau_max)
    ax.set_ylim(0, max(res.O) * 1.35)
    ax.annotate(rf"peak {res.O[ipk]:.3f}",
                xy=(res.tau[ipk], res.O[ipk]), xytext=(0.30, 0.80),
                textcoords="axes fraction", fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.annotate(rf"settles at {res.O[-1]:.3f}",
                xy=(res.tau[-1] * 0.80, res.O[-1]), xytext=(0.42, 0.44),
                textcoords="axes fraction", fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.text(0.985, p.O_detectable * 1.12, r"$O_{\rm detectable}$",
            transform=ax.get_yaxis_transform(), ha="right", va="bottom",
            fontsize=7)
    ax.text(0.985, p.O_floor * 1.0 + 0.004, r"$O_{\rm floor}$",
            transform=ax.get_yaxis_transform(), ha="right", va="bottom",
            fontsize=7)
    save(fig, "fig07_suppression_comparison.pdf")


# ==========================================================================
# Figure 8 — phase portrait in the (I, R) plane
# ==========================================================================
def fig08():
    fig, ax = plt.subplots(figsize=(TEXTWIDTH, 3.0), constrained_layout=True)
    for i, key in enumerate(stage_keys()):
        p, y0 = get_stage(key)
        res = integrate(p, y0)
        lab, _ = classify_regime(res, p)
        col = STAGE_COLORS[i]
        ax.plot(res.I, res.R, color=col, lw=1.4, label=f"{SHORT[key]}")
        ax.plot(res.I[0], res.R[0], "o", ms=3.5, color=col)
        ax.plot(res.I[-1], res.R[-1], "D", ms=4, color=col)

    p = ModelParams()
    ax.axvline(p.I_advanced, color="k", ls="--", lw=0.8)
    ax.axhline(p.R_min, color="k", ls=":", lw=0.8)
    # Linear axis: I spans 0 to 10, so a log/symlog axis only obscured it.
    ax.set_xlim(-0.3, 10.6)
    ax.set_ylim(-0.03, 1.03)
    ax.text(p.I_advanced + 0.32, 0.30, r"$I_{\rm advanced}$",
            fontsize=7, rotation=90, va="center")
    ax.text(0.15, p.R_min + 0.03, r"$R_{\min}$", fontsize=7)
    ax.set_xlabel(r"capability $I$")
    ax.set_ylabel(r"regulation $R$")
    fig.legend(loc="outside lower center", ncol=4, frameon=False,
               handlelength=1.8, columnspacing=1.6)
    save(fig, "fig08_phase_portrait.pdf")


# ==========================================================================
# Figure 9 — the auxiliary Lambert boundary
# ==========================================================================
def fig09():
    """Curves rather than a heat map.

    The contour version of this plot put its labels in the corners, where
    they collided with the axes.  Reading I_crit against A_rec at fixed R
    is also the comparison the text actually makes.
    """
    A_rec = np.linspace(0.05, 3.0, 300)
    R_vals = [1.0, 0.8, 0.6, 0.4, 0.2]
    cmap = plt.get_cmap("viridis")

    fig, ax = plt.subplots(figsize=(TEXTWIDTH, 2.5), constrained_layout=True)
    for j, r in enumerate(R_vals):
        y = [I_crit(ModelParams(F_key="lambert", A_rec=float(a)), float(r))
             for a in A_rec]
        col = cmap(0.12 + 0.72 * j / (len(R_vals) - 1))
        ax.plot(A_rec, y, color=col, label=rf"regulation $R={r:.1f}$"
                if j == 0 else rf"$R={r:.1f}$")

    ax.set_xlabel(r"recursive amplification $A_{\rm rec}$")
    ax.set_ylabel(r"$I_{\rm crit} = W\!\left(C_R / (b A_{\rm rec})\right)$")
    ax.set_xlim(0, 3.0)
    ax.set_ylim(bottom=0)
    fig.legend(loc="outside lower center", ncol=5, frameon=False,
               handlelength=1.8, columnspacing=1.6)
    save(fig, "fig09_lambert_boundary.pdf")


if __name__ == "__main__":
    fig05(); fig06(); fig07(); fig08(); fig09()
    print("done.")
