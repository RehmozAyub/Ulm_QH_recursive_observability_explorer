"""Plotly visualization functions — each returns a ``go.Figure``.

Plot catalogue (Section 11 of GEMINI.md):
    plot_1  — Capability & Regulation  [I(τ), R(τ)]
    plot_2  — Observability            [O(τ)]
    plot_3  — Detected population      [N_obs(τ), P_det(τ)]
    plot_4  — Phase diagram            [(I, O) trajectory + regime shading]
    plot_5  — Lambert boundary         [I_crit contours, survival corridor]
    plot_obs_functions — O(I) comparison [all four static O(I)]
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from model.config import ModelParams
from model.solver import Result
from model.functions import O_REGISTRY
from model.lambert import lambert_is_valid, lambert_boundary, lambert_boundary_is_trivial


# ---------------------------------------------------------------------------
# Shared styling constants
# ---------------------------------------------------------------------------

_DARK_BG = "#0e1117"
_GRID_COLOR = "rgba(255,255,255,0.06)"
_FONT_FAMILY = "Inter, system-ui, sans-serif"

# Curated palette (vibrant yet harmonious)
_COLOR_I = "#00d4ff"       # cyan
_COLOR_R = "#ff6b6b"       # coral-red
_COLOR_O = "#ffd43b"       # gold
_COLOR_NOBS = "#51cf66"    # green
_COLOR_PDET = "#845ef7"    # purple
_COLOR_LAMBERT = "#ff922b"  # orange


def _base_layout(title: str, xaxis_title: str = "τ (dimensionless time)") -> dict:
    """Return a dark-theme layout dict used by all figures."""
    return dict(
        title=dict(text=title, font=dict(size=18, color="white")),
        template="plotly_dark",
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_DARK_BG,
        font=dict(family=_FONT_FAMILY, color="white"),
        xaxis=dict(
            title=xaxis_title,
            gridcolor=_GRID_COLOR,
            zeroline=False,
        ),
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
        ),
        hovermode="x unified",
    )


# ===================================================================
# Plot 1 — Capability & Regulation
# ===================================================================

def plot_1(result: Result, params: Optional[ModelParams] = None) -> go.Figure:
    """I(τ) and R(τ) on twin y-axes.

    Takeaway annotation: 'Does capability outrun regulation?'
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=result.tau, y=result.I,
            name="I (capability)", mode="lines",
            line=dict(color=_COLOR_I, width=2.5),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=result.tau, y=result.R,
            name="R (regulation)", mode="lines",
            line=dict(color=_COLOR_R, width=2.5, dash="dash"),
        ),
        secondary_y=True,
    )

    layout = _base_layout("Capability & Regulation")
    fig.update_layout(**layout)
    fig.update_yaxes(
        title_text="I (capability)", secondary_y=False,
        gridcolor=_GRID_COLOR,
    )
    fig.update_yaxes(
        title_text="R (regulation)", secondary_y=True,
        gridcolor=_GRID_COLOR,
    )

    # 1. Crossover of I and R
    crossings = np.where(result.I > result.R)[0]
    if len(crossings) > 0:
        tau_cross = float(result.tau[crossings[0]])
        fig.add_vline(x=tau_cross, line_width=1.5, line_dash="dash", line_color="rgba(255,255,255,0.4)")
        fig.add_annotation(
            x=tau_cross, y=float(result.I[crossings[0]]),
            text=f"I crosses R (τ ≈ {tau_cross:.1f})",
            showarrow=True, arrowhead=1,
            ax=40, ay=-30,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0.6)",
        )

    # 2. Regulatory collapse (R < R_min)
    if params is not None:
        collapse_indices = np.where(result.R < params.R_min)[0]
        if len(collapse_indices) > 0:
            tau_collapse = float(result.tau[collapse_indices[0]])
            fig.add_vline(x=tau_collapse, line_width=1.5, line_dash="dot", line_color="#ff6b6b")
            fig.add_annotation(
                x=tau_collapse, y=float(result.R[collapse_indices[0]]),
                yref="y2",
                text=f"R < R_min (τ ≈ {tau_collapse:.1f})",
                showarrow=True, arrowhead=2,
                ax=-50, ay=35,
                font=dict(size=10, color="#ff8b8b"),
                bgcolor="rgba(0,0,0,0.6)",
            )

    # Takeaway annotation
    fig.add_annotation(
        text="Does capability outrun regulation?",
        xref="paper", yref="paper", x=1.0, y=1.08,
        showarrow=False,
        font=dict(size=12, color="rgba(255,255,255,0.5)", style="italic"),
    )

    return fig


# ===================================================================
# Plot 2 — Observability
# ===================================================================

def plot_2(result: Result, params: ModelParams) -> go.Figure:
    """O(τ) vs time."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=result.tau, y=result.O,
            name="O (observability)", mode="lines",
            line=dict(color=_COLOR_O, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(255,212,59,0.08)",
        )
    )

    layout = _base_layout("Observability")
    layout["yaxis"] = dict(
        title="O (observability)", gridcolor=_GRID_COLOR, zeroline=False
    )
    fig.update_layout(**layout)

    # Peak emission annotation
    idx_peak = int(np.argmax(result.O))
    tau_peak = float(result.tau[idx_peak])
    val_peak = float(result.O[idx_peak])
    if val_peak > params.O_detectable and result.O[-1] < 0.7 * val_peak:
        fig.add_annotation(
            x=tau_peak, y=val_peak,
            text=f"Peak emission (O = {val_peak:.2f})",
            showarrow=True, arrowhead=1,
            ax=45, ay=-35,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0.6)",
        )

    mode_str = "dynamic dO/dτ" if params.obs_mode == "dynamic" else "static O(I)"
    fig.add_annotation(
        text=f"More visible, less visible, or peak & decline? ({mode_str})",
        xref="paper", yref="paper", x=1.0, y=1.08,
        showarrow=False,
        font=dict(size=12, color="rgba(255,255,255,0.5)", style="italic"),
    )

    return fig


# ===================================================================
# Plot 3 — Detected population
# ===================================================================

def plot_3(result: Result, params: Optional[ModelParams] = None) -> go.Figure:
    """N_obs(τ) and P_det(τ)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=result.tau, y=result.N_obs,
            name="N_obs", mode="lines",
            line=dict(color=_COLOR_NOBS, width=2.5),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=result.tau, y=result.P_det,
            name="P_det", mode="lines",
            line=dict(color=_COLOR_PDET, width=2, dash="dot"),
        ),
        secondary_y=True,
    )

    layout = _base_layout("Detected Population")
    fig.update_layout(**layout)
    fig.update_yaxes(
        title_text="N_obs", secondary_y=False, gridcolor=_GRID_COLOR,
    )
    fig.update_yaxes(
        title_text="P_det", secondary_y=True, gridcolor=_GRID_COLOR,
    )

    # Show N_true upper limit if params is provided
    if params is not None:
        fig.add_hline(y=params.N_true, line_width=1, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        fig.add_annotation(
            x=float(result.tau[0]), y=params.N_true,
            text="N_true (Upper limit of existences)",
            showarrow=False,
            xanchor="left", yanchor="bottom",
            font=dict(size=9, color="rgba(255,255,255,0.5)"),
        )

    final_N = float(result.N_obs[-1])
    fig.add_annotation(
        x=float(result.tau[-1]), y=final_N,
        text=f"Final N_obs ≈ {final_N:.2f}",
        showarrow=True, arrowhead=1,
        ax=-50, ay=30,
        font=dict(size=10, color="white"),
        bgcolor="rgba(0,0,0,0.6)",
    )

    fig.add_annotation(
        text="Silence from rarity, collapse, low-O, or search limits?",
        xref="paper", yref="paper", x=1.0, y=1.08,
        showarrow=False,
        font=dict(size=12, color="rgba(255,255,255,0.5)", style="italic"),
    )

    return fig


# ===================================================================
# Plot 4 — Phase diagram
# ===================================================================

def plot_4(
    results: List[Tuple[str, Result]],
    params: ModelParams,
) -> go.Figure:
    """Phase diagram in (I, O) plane with regime region shading.

    Parameters
    ----------
    results : list of (label, Result)
        One or more named trajectories (for multi-preset overlay).
    params : ModelParams
        Used for threshold values.
    """
    fig = go.Figure()

    # Regime shading (approximate rectangles in I-O space)
    _region_colors = {
        "pre-detectable":          "rgba(100,100,100,0.10)",
        "visible-technological":   "rgba(0,212,255,0.08)",
        "expansionist-visible":    "rgba(81,207,102,0.10)",
        "runaway":                 "rgba(255,107,107,0.10)",
        "collapse-proxy":          "rgba(255,60,60,0.12)",
        "optimized-low-observable":"rgba(255,212,59,0.10)",
    }

    I_max = max(
        float(np.max(r.I)) for _, r in results
    ) * 1.2 if results else 10.0
    O_max = max(
        max(float(np.max(r.O)), 0.5) for _, r in results
    ) * 1.2 if results else 1.0

    # Draw approximate regime boxes
    # Pre-detectable: low I, low O
    fig.add_shape(
        type="rect", x0=0, x1=params.I_advanced, y0=0, y1=params.O_detectable,
        fillcolor=_region_colors["pre-detectable"],
        line=dict(width=0),
        layer="below",
    )
    fig.add_annotation(
        x=params.I_advanced / 2, y=params.O_detectable / 2,
        text="Pre-detectable", showarrow=False,
        font=dict(size=10, color="rgba(255,255,255,0.35)"),
    )

    # Expansionist-visible: high I, high O
    fig.add_shape(
        type="rect", x0=params.I_advanced, x1=I_max, y0=params.O_detectable, y1=O_max,
        fillcolor=_region_colors["expansionist-visible"],
        line=dict(width=0),
        layer="below",
    )
    fig.add_annotation(
        x=(params.I_advanced + I_max) / 2, y=(params.O_detectable + O_max) / 2,
        text="Expansionist-visible", showarrow=False,
        font=dict(size=10, color="rgba(255,255,255,0.35)"),
    )

    # Optimized-low-observable: high I, low O
    fig.add_shape(
        type="rect", x0=params.I_advanced, x1=I_max, y0=0, y1=params.O_detectable,
        fillcolor=_region_colors["optimized-low-observable"],
        line=dict(width=0),
        layer="below",
    )
    fig.add_annotation(
        x=(params.I_advanced + I_max) / 2, y=params.O_detectable / 2,
        text="Low-observable", showarrow=False,
        font=dict(size=10, color="rgba(255,255,255,0.35)"),
    )

    # Visible-technological: low-mid I, O > detectable
    fig.add_shape(
        type="rect", x0=0, x1=params.I_advanced, y0=params.O_detectable, y1=O_max,
        fillcolor=_region_colors["visible-technological"],
        line=dict(width=0),
        layer="below",
    )
    fig.add_annotation(
        x=params.I_advanced / 2, y=(params.O_detectable + O_max) / 2,
        text="Visible-tech", showarrow=False,
        font=dict(size=10, color="rgba(255,255,255,0.35)"),
    )

    # Trajectory traces
    palette = [_COLOR_I, _COLOR_O, _COLOR_R, _COLOR_NOBS, _COLOR_PDET, _COLOR_LAMBERT]
    for idx, (label, res) in enumerate(results):
        color = palette[idx % len(palette)]
        fig.add_trace(
            go.Scatter(
                x=res.I, y=res.O,
                name=label, mode="lines",
                line=dict(color=color, width=2),
            )
        )
        # Start marker
        fig.add_trace(
            go.Scatter(
                x=[res.I[0]], y=[res.O[0]],
                mode="markers",
                marker=dict(color=color, size=10, symbol="circle"),
                showlegend=False,
                hoverinfo="text",
                hovertext=f"{label} start",
            )
        )
        # End marker
        fig.add_trace(
            go.Scatter(
                x=[res.I[-1]], y=[res.O[-1]],
                mode="markers",
                marker=dict(color=color, size=10, symbol="diamond"),
                showlegend=False,
                hoverinfo="text",
                hovertext=f"{label} end",
            )
        )

    layout = _base_layout("Phase Diagram (I, O)", xaxis_title="I (capability)")
    layout["yaxis"] = dict(
        title="O (observability)", gridcolor=_GRID_COLOR, zeroline=False,
    )
    fig.update_layout(**layout)

    return fig


# ===================================================================
# Plot 5 — Lambert boundary
# ===================================================================

def plot_5(params: ModelParams, result: Optional[Result] = None) -> go.Figure:
    """Lambert boundary I_crit contour over (A_rec, R) plane.

    Renders ONLY if ``lambert_is_valid(params)``; otherwise returns a
    warning-banner figure.
    """
    if not lambert_is_valid(params):
        fig = go.Figure()
        layout = _base_layout("Lambert Boundary — NOT APPLICABLE")
        fig.update_layout(**layout)
        fig.add_annotation(
            text=(
                "⚠ Lambert boundary is valid ONLY when F_key = 'lambert'.<br>"
                f"Current F_key = '{params.F_key}'. "
                "See the fallback log threshold in the Lambert tab."
            ),
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#ffd43b"),
            align="center",
        )
        return fig

    if lambert_boundary_is_trivial(params):
        fig = go.Figure()
        layout = _base_layout("Lambert Boundary — TRIVIAL BOUNDARY")
        fig.update_layout(**layout)
        fig.add_annotation(
            text="⚠ Lambert boundary is trivially zero because A_ref = 0 — increase A_ref to see structure",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#ff6b6b"),
            align="center",
        )
        return fig

    A_rec_grid = np.linspace(0.1, 5.0, 80)
    R_grid = np.linspace(0.05, 3.0, 80)
    I_grid = lambert_boundary(params, A_rec_grid, R_grid)

    fig = go.Figure()

    fig.add_trace(
        go.Contour(
            x=A_rec_grid,
            y=R_grid,
            z=I_grid,
            colorscale="Inferno",
            colorbar=dict(title="I_crit"),
            contours=dict(showlines=True),
            name="I_crit",
            hovertemplate="A_rec=%{x:.2f}<br>R=%{y:.2f}<br>I_crit=%{z:.3f}<extra></extra>",
        )
    )

    # Mark current (A_rec, R) point
    current_R = float(result.R[-1]) if result is not None else 1.0
    from model.lambert import I_crit as _I_crit_fn
    ic = _I_crit_fn(params, current_R)
    
    if result is not None and ic is not None:
        I_final = float(result.I[-1])
        if I_final < ic:
            status = f"Safe (I={I_final:.2f} < I_crit={ic:.2f})"
        else:
            status = f"Exceeded (I={I_final:.2f} >= I_crit={ic:.2f})"
    else:
        status = "Current Point"

    fig.add_trace(
        go.Scatter(
            x=[params.A_rec],
            y=[current_R],
            mode="markers+text",
            marker=dict(size=14, color="white", symbol="star"),
            text=[f"Current ({status})"],
            textposition="top center",
            textfont=dict(color="white", size=12),
            showlegend=False,
        )
    )

    layout = _base_layout("Lambert Boundary — I_crit(A_rec, R)", xaxis_title="A_rec")
    layout["yaxis"] = dict(title="R (regulation)", gridcolor=_GRID_COLOR, zeroline=False)
    fig.update_layout(**layout)

    fig.add_annotation(
        text="SPECIAL CASE — valid only for F(I) = I·exp(I)",
        xref="paper", yref="paper", x=0.5, y=1.10,
        showarrow=False,
        font=dict(size=13, color=_COLOR_LAMBERT, style="italic"),
    )

    return fig


# ===================================================================
# plot_obs_functions — O(I) comparison (all four static models)
# ===================================================================

def plot_obs_functions(params: ModelParams) -> go.Figure:
    """Plot all four static O(I) functions on a shared I axis."""
    I_arr = np.linspace(0, 20, 500)

    colors = {
        "increasing": _COLOR_I,
        "decreasing": _COLOR_R,
        "peaked":     _COLOR_O,
        "threshold":  _COLOR_PDET,
    }
    labels = {
        "increasing": "Model A: 1 − exp(−λI)",
        "decreasing": "Model B: exp(−λI)",
        "peaked":     "Model C: I·exp(−λI)",
        "threshold":  "Model D: sigmoid",
    }

    fig = go.Figure()
    for key, func in O_REGISTRY.items():
        O_vals = func(I_arr, params)
        fig.add_trace(
            go.Scatter(
                x=I_arr, y=O_vals,
                name=labels.get(key, key),
                mode="lines",
                line=dict(color=colors.get(key, "white"), width=2.5),
            )
        )

    layout = _base_layout("Static Observability Functions O(I)", xaxis_title="I (capability)")
    layout["yaxis"] = dict(title="O(I)", gridcolor=_GRID_COLOR, zeroline=False)
    fig.update_layout(**layout)

    fig.add_annotation(
        text="Compare: increasing / decreasing / peaked / threshold",
        xref="paper", yref="paper", x=1.0, y=1.08,
        showarrow=False,
        font=dict(size=12, color="rgba(255,255,255,0.5)", style="italic"),
    )

    return fig
