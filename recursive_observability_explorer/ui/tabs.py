"""Tab renderers — one function per tab, called from app.py.

Each renderer receives the solved Result, ModelParams, and y0, then
displays the relevant plots and information panels.
"""

from __future__ import annotations

from typing import Tuple, Optional

import numpy as np
import streamlit as st

from model.config import ModelParams
from model.solver import Result, integrate
from model.regimes import classify_regime, REGIME_DESCRIPTIONS
from model.drake import compute_decomposition
from model.lambert import lambert_is_valid, I_crit, fallback_threshold
from model.stages import get_stage, stage_keys, STAGE_LABELS
from viz.plots import plot_1, plot_2, plot_3, plot_4, plot_5, plot_obs_functions


# ---------------------------------------------------------------------------
# Claim-strength legend (always visible via caller)
# ---------------------------------------------------------------------------

CLAIM_LEGEND = (
    "🟢 <b>Established</b> &nbsp;|&nbsp; "
    "🔵 <b>Plausible</b> &nbsp;|&nbsp; "
    "🟡 <b>Hypothetical</b> &nbsp;|&nbsp; "
    "🔴 <b>Speculative</b>"
)


def render_claim_legend():
    """Render the persistent claim-strength legend."""
    st.markdown(
        f"<div style='text-align:center; padding:4px 0; opacity:0.7; font-size:0.85em;'>"
        f"{CLAIM_LEGEND}</div>",
        unsafe_allow_html=True,
    )


def render_disclaimer():
    """Render the persistent disclaimer banner."""
    st.info(
        "⚠️ **Disclaimer:** This is a modeling tool for exploring assumptions, "
        "not evidence about extraterrestrial civilizations. "
        "``existence ≠ detectability ≠ observation``",
        icon="🔬",
    )


# ---------------------------------------------------------------------------
# Trajectory Narrative Generator
# ---------------------------------------------------------------------------

def generate_trajectory_narrative(result: Result, params: ModelParams) -> str:
    """Analyze the result trajectory and generate a friendly, plain-English narrative."""
    # Find peak values and final values
    idx_peak_I = int(np.argmax(result.I))
    peak_I = float(result.I[idx_peak_I])
    tau_peak_I = float(result.tau[idx_peak_I])
    
    idx_peak_O = int(np.argmax(result.O))
    peak_O = float(result.O[idx_peak_O])
    tau_peak_O = float(result.tau[idx_peak_O])
    
    final_I = float(result.I[-1])
    final_R = float(result.R[-1])
    final_O = float(result.O[-1])
    
    label, reasons = classify_regime(result, params)
    
    narrative = []
    
    # 1. Growth phase
    if final_I > params.I_advanced:
        narrative.append(
            f"📈 **Technological Growth:** The civilization successfully transitions past the 'advanced' threshold "
            f"(set at {params.I_advanced}), reaching a final technical capability of **I = {final_I:.2f}** "
            f"(peaking at {peak_I:.2f})."
        )
    else:
        narrative.append(
            f"🌱 **Limited Development:** The civilization stays below the advanced threshold, peaking at capability "
            f"**I = {peak_I:.2f}** around τ = {tau_peak_I:.1f}. Growth is slow or highly damped by regulation."
        )
        
    # 2. Regulation & Stability
    if final_R < params.R_min:
        narrative.append(
            f"🚨 **Regulatory Collapse:** Regulation decay dominates (ending at R = {final_R:.3f}, below the safe limit "
            f"of {params.R_min}). This indicates that governance, alignment, or safety protocols failed to keep pace "
            f"with growth, leading to systemic instability (collapse/runaway)."
        )
    elif final_R > 1.5 * params.R_min:
        narrative.append(
            f"🛡️ **Robust Governance:** The civilization maintains solid regulation (ending at R = {final_R:.2f}), "
            f"indicating a stable balance between technical capability and institutional alignment."
        )
    else:
        narrative.append(
            f"⚠️ **Fragile Stability:** Regulation is maintained but remains low (R = {final_R:.2f}), indicating vulnerability to further shocks."
        )
        
    # 3. Observability & Detection
    if label == "optimized-low-observable":
        narrative.append(
            f"🔍 **Stealth Transition (Low-Observable):** After peaking at observability **O = {peak_O:.2f}** at τ = {tau_peak_O:.1f}, "
            f"the civilization successfully compresses its electromagnetic signature or leaks less energy, leaving final observability at **O = {final_O:.2f}** (detectability P_det = {result.P_det[-1]*100:.1f}%). "
            f"This explains why a highly advanced civilization could exist but remain undetected (the 'Great Silence')."
        )
    elif label == "collapse-proxy":
        narrative.append(
            f"💥 **Post-Collapse Silence:** The civilization experienced a transient observability spike of **O = {peak_O:.2f}** at τ = {tau_peak_O:.1f}, "
            f"but as capability and regulation collapsed, the technical signature faded back to near-zero. They are quiet because they collapsed."
        )
    elif label == "expansionist-visible" or final_O > params.O_detectable * 2:
        narrative.append(
            f"📡 **High Visibility:** Observability remains high at **O = {final_O:.2f}** (detectability P_det = {result.P_det[-1]*100:.1f}%). "
            f"This civilization would be readily detectable by sky surveys if they are within search range."
        )
    else:
        narrative.append(
            f"🌌 **Low Observability:** Observability remains low (O = {final_O:.2f}), making detection extremely difficult (P_det = {result.P_det[-1]*100:.1f}%)."
        )
        
    return "\n\n".join(narrative)


# ===================================================================
# Tab 1 — Trajectories
# ===================================================================

def render_trajectories(result: Result, params: ModelParams):
    """Plots 1, 2, 3 + current regime label."""
    label, reasons = classify_regime(result, params)

    # Regime badge
    regime_colors = {
        "pre-detectable": "gray",
        "visible-technological": "#00d4ff",
        "expansionist-visible": "#51cf66",
        "runaway": "#ff6b6b",
        "collapse-proxy": "#ff3333",
        "optimized-low-observable": "#ffd43b",
        "uncertain": "#aaa",
    }
    color = regime_colors.get(label, "#aaa")
    st.markdown(
        f"**Current regime:** "
        f"<span style='color:{color}; font-weight:bold; font-size:1.1em;'>{label}</span>",
        unsafe_allow_html=True,
    )

    # Show description of current regime
    desc = REGIME_DESCRIPTIONS.get(label, "")
    st.markdown(f"*{desc}*")

    # Show reasons for the classification
    with st.expander("🔬 Classification Details / Triggered Criteria", expanded=False):
        for reason in reasons:
            st.markdown(f"- {reason}")

    # Tag speculative stages
    if params.stage_key == "stage_s5" or params.stage_key == "s5" or params.A_rec > 3.0 or label == "uncertain":
        st.caption("🔴 Speculative regime — interpret with caution")

    # Newcomer explanation
    st.markdown(
        """
        ### Welcome to the Recursive Observability Filter (ROF) Explorer!
        This simulation models how a civilization's **Capability (I)**, **Regulation (R)**, and **Observability (O)** co-evolve over time (τ):
        - **I (Capability)**: Technical leverage, computation power, AI, and energy use.
        - **R (Regulation)**: Safety alignment, institutional quality, and coordination.
        - **O (Observability)**: The electromagnetic leak, waste heat, and spatial footprint visible to outer space.
        """
    )

    # Trajectory narrative callout
    st.markdown("#### 📖 Simulation Narrative")
    st.info(generate_trajectory_narrative(result, params), icon="📝")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_1(result, params), use_container_width=True)
    with col2:
        st.plotly_chart(plot_2(result, params), use_container_width=True)

    st.plotly_chart(plot_3(result, params), use_container_width=True)


# ===================================================================
# Tab 2 — Phase Diagram
# ===================================================================

def render_phase_diagram(result: Result, params: ModelParams, y0: Tuple[float, float, float]):
    """Phase diagram with multi-preset overlay selector."""
    st.markdown("### Phase Diagram — (I, O) Plane")
    
    st.markdown(
        """
        The **Phase Diagram** plots **Observability (O)** directly against **Capability (I)**. 
        Instead of plotting time, this allows us to see the *evolutionary pathway* that a civilization follows 
        through the state-space.
        
        The shaded boxes represent the **approximate regimes** based on your current thresholds:
        - **Pre-detectable (gray)**: Pre-industrial or early industrial societies (low I, low O).
        - **Visible-tech (blue)**: Societies broadcasting high signals relative to capability.
        - **Expansionist-visible (green)**: Advanced societies expanding physically (large Dyson spheres).
        - **Low-observable (yellow)**: Highly advanced societies that manage emissions tightly (stealth/efficient).
        """
    )

    # Multi-preset overlay
    overlay_keys = st.multiselect(
        "Overlay additional presets to compare pathways",
        options=stage_keys(),
        format_func=lambda k: STAGE_LABELS[k],
        default=[],
        key="phase_overlay",
    )

    results_list = [("Current", result)]
    for sk in overlay_keys:
        try:
            p, y = get_stage(sk)
            r = integrate(p, y)
            results_list.append((STAGE_LABELS[sk], r))
        except Exception as e:
            st.warning(f"Could not integrate preset {sk}: {e}")

    fig = plot_4(results_list, params)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "● = start, ◆ = end. Shaded regions show approximate regime boundaries "
        "based on current threshold settings."
    )


# ===================================================================
# Tab 3 — Lambert Filter
# ===================================================================

def render_lambert(result: Result, params: ModelParams):
    """Lambert boundary plot + I_crit readout + validity warning."""
    st.markdown("### Lambert Filter Boundary")
    
    st.markdown(
        """
        The **Lambert W Special Case** explores the mathematical limits of growth when feedback is recursive 
        ($F(I) = I e^I$). 
        
        As capability ($I$) feeds back into itself exponentially, a civilization must maintain a proportional 
        level of regulation ($R$) to prevent systemic breakdown. This balance defines a critical capability 
        boundary ($I_{\\text{crit}}$).
        
        - **Survival Corridor (Contour Map)**: The region of stable growth. 
        - **The Star (⭐)** represents the current state of your system at the end of the simulation.
        """
    )

    if lambert_is_valid(params):
        st.success(f"✅ Lambert W is **valid** (F_key = '{params.F_key}')")

        # Current I_crit for final R
        R_final = float(result.R[-1])
        ic = I_crit(params, R_final)
        I_final = float(result.I[-1])

        col1, col2, col3 = st.columns(3)
        col1.metric("I_crit (at R_final)", f"{ic:.4f}" if ic is not None else "N/A")
        col2.metric("I_final", f"{I_final:.4f}")
        col3.metric("R_final", f"{R_final:.4f}")

        if ic is not None:
            if I_final < ic:
                st.info(
                    f"I_final ({I_final:.3f}) < I_crit ({ic:.3f}) — "
                    "within the **survival corridor**."
                )
            else:
                st.warning(
                    f"I_final ({I_final:.3f}) ≥ I_crit ({ic:.3f}) — "
                    "beyond modelled regulatory capacity. "
                    "*(Does NOT prove collapse — civilisation may reorganise.)*"
                )

        fig = plot_5(params, result)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(
            f"⚠️ Lambert W is **not applicable** for F_key = '{params.F_key}'. "
            "The Lambert structure requires F(I) = I·exp(I)."
        )

        # Show fallback log threshold
        R_final = float(result.R[-1])
        fb = fallback_threshold(params, R_final)
        I_final = float(result.I[-1])

        col1, col2, col3 = st.columns(3)
        col1.metric("Fallback threshold (log)", f"{fb:.4f}" if fb is not None else "N/A")
        col2.metric("I_final", f"{I_final:.4f}")
        col3.metric("R_final", f"{R_final:.4f}")

        if fb is not None:
            st.info(
                f"Fallback threshold: I = ln(cR / (bA_rec)) = {fb:.4f}. "
                "This is a logarithmic solution, not Lambert W."
            )

        # Still show plot_5 (which will render a warning banner)
        fig = plot_5(params, result)
        st.plotly_chart(fig, use_container_width=True)


# ===================================================================
# Tab 4 — Observability Functions
# ===================================================================

def render_obs_functions(params: ModelParams):
    """Static comparison of all four O(I) functions."""
    st.markdown("### Static Observability Functions O(I)")
    st.markdown(
        """
        How does a civilization's capability ($I$) map to its observability ($O$)? 
        Because the future of technology is uncertain, this app allows you to test **four canonical static models**
        comparing how a civilization leaks signals as its capabilities grow:
        
        - **Model A (increasing)**: Observability grows monotonically with capability (standard "more tech = more emissions" view).
        - **Model B (decreasing)**: Observability decays. Highly advanced technology goes silent or achieves absolute containment.
        - **Model C (peaked)**: Observability spikes during a transition phase (like radio-waves on Earth) but decays once advanced compression, fiber, or stealth technologies are adopted.
        - **Model D (threshold)**: Observability undergoes a sudden step-like change (sigmoid) at a critical capability $I_c$.
        """
    )

    fig = plot_obs_functions(params)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Function definitions"):
        st.latex(r"\text{Model A (increasing):} \quad O(I) = 1 - e^{-\lambda I}")
        st.latex(r"\text{Model B (decreasing):} \quad O(I) = e^{-\lambda I}")
        st.latex(r"\text{Model C (peaked):} \quad O(I) = I \cdot e^{-\lambda I}")
        st.latex(
            r"\text{Model D (threshold):} \quad O(I) = \frac{1}{1 + e^{-\mathrm{sign} \cdot k (I - I_c)}}"
        )


# ===================================================================
# Tab 5 — Regime
# ===================================================================

def render_regime(result: Result, params: ModelParams):
    """Classifier label + reasons + collapse-vs-low-observable explanation."""
    st.markdown("### Regime Classification")
    
    st.markdown(
        """
        To make sense of the simulation outcomes, the app automatically classifies the trajectory into one of seven regimes 
        using parameters defined in your sidebar thresholds.
        """
    )

    label, reasons = classify_regime(result, params)

    # Colour-coded label
    regime_colors = {
        "pre-detectable": "gray",
        "visible-technological": "#00d4ff",
        "expansionist-visible": "#51cf66",
        "runaway": "#ff6b6b",
        "collapse-proxy": "#ff3333",
        "optimized-low-observable": "#ffd43b",
        "uncertain": "#aaa",
    }
    color = regime_colors.get(label, "#aaa")
    st.markdown(
        f"<h2 style='color:{color};'>{label}</h2>",
        unsafe_allow_html=True,
    )

    # Description
    desc = REGIME_DESCRIPTIONS.get(label, "")
    st.markdown(f"*{desc}*")

    # Claim strength tag
    if params.stage_key == "stage_s5" or params.stage_key == "s5" or params.A_rec > 3.0 or label == "uncertain":
        st.caption("🔴 Speculative — interpret with caution")
    elif label in ("collapse-proxy", "optimized-low-observable"):
        st.caption("🟡 Hypothetical — model-dependent conclusion")
    elif label == "runaway":
        st.caption("🔴 Speculative — beyond modelled regulatory envelope")
    else:
        st.caption("🔵 Plausible — within model validity range")

    # Reasons
    st.markdown("**Criteria that fired:**")
    for reason in reasons:
        st.markdown(f"- {reason}")

    # Collapse vs low-observable explanation
    st.markdown("---")
    st.markdown("### Collapse vs Low-Observability")
    st.markdown(
        """
        The distinction below is central to resolving the Fermi Paradox:
        
        | Aspect | Collapse-proxy | Optimized-low-observable |
        |--------|----------------|--------------------------|
        | **R (regulation)** | Collapsed (R < R_min) | Maintained (R ≥ R_min) |
        | **O (observability)** | Spiked then collapsed | Deliberately low |
        | **I (capability)** | May be high briefly | Sustained high |
        | **Interpretation** | System failure (existential catastrophe) | Highly efficient or quiet civilization |
        | **Claim strength** | 🟡 Hypothetical | 🟡 Hypothetical |

        > **Key distinction:** Collapse implies loss of coordination/governance (the civilization dies out);
        > low-observability implies *successful* management of emissions (they remain active, but quiet).
        > Neither implies physical invisibility — thermodynamic waste heat persists.
        """
    )


# ===================================================================
# Tab 6 — Drake / Decomposition
# ===================================================================

def render_drake(result: Result, params: ModelParams):
    """Classical vs ROF N_obs decomposition with current values."""
    st.markdown("### Drake Equation — ROF Decomposition")
    
    st.markdown(
        """
        The classical **Drake Equation** estimates $N$, the number of broadcasting civilizations. 
        The **Recursive Observability Filter (ROF)** framework updates this to emphasize that:
        $$\\text{existence} \\neq \\text{detectability} \\neq \\text{observation}$$
        
        A civilization might exist, but is filtered out by low-observability ($P_{\\text{sig}}$) or limited search coverage ($P_{\\text{search}}$).
        """
    )

    st.markdown("#### Classical Drake Factors (Overrides)")
    c1, c2, c3, c4 = st.columns(4)
    R_star = c1.number_input("R_* (Star formation rate)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="drake_R_star")
    f_p = c2.number_input("f_p (Fraction with planets)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="drake_f_p")
    n_e = c3.number_input("n_e (Habitable planets/system)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="drake_n_e")
    f_l = c4.number_input("f_l (Fraction developing life)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="drake_f_l")
    
    c5, c6, c7, _ = st.columns(4)
    f_i = c5.number_input("f_i (Fraction developing intelligence)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="drake_f_i")
    f_c = c6.number_input("f_c (Fraction communicating)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="drake_f_c")
    L = c7.number_input("L (Civilisation lifetime)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="drake_L")

    O_final = float(result.O[-1])
    decomp = compute_decomposition(
        O_final, params,
        R_star=R_star, f_p=f_p, n_e=n_e, f_l=f_l, f_i=f_i, f_c=f_c, L=L
    )

    st.markdown("#### Classical Drake Equation")
    st.latex(r"N = R_* \cdot f_p \cdot n_e \cdot f_l \cdot f_i \cdot f_c \cdot L")

    st.markdown("#### ROF-Modified Form")
    st.latex(r"N_{\mathrm{obs}} = N_{\mathrm{true}} \cdot P_{\mathrm{surv}} \cdot P_{\mathrm{sig}} \cdot P_{\mathrm{search}}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**ROF Decomposition (current)**")
        st.metric("N_true", f"{decomp.N_true:.4f}")
        st.metric("P_surv", f"{decomp.P_surv:.4f}")
        st.metric("P_sig = h(O)", f"{decomp.P_sig:.4f}")
        st.metric("P_search", f"{decomp.P_search:.4f}")
        st.metric("**N_obs (ROF)**", f"{decomp.N_obs_rof:.6f}")

    with col2:
        st.markdown("**Classical Drake (reference)**")
        st.caption(
            "Classical factors are set to 1.0 by default (normalised). "
            "The ROF mainly modifies P_surv and P_sig."
        )
        st.metric("N_classical", f"{decomp.N_classical:.4f}")

    st.markdown("---")
    st.markdown(
        "**Key insight:** The ROF framework adds the *observability filter* — "
        "even if civilisations exist (N_true > 0), they may be undetectable "
        "if P_sig ≈ 0 (low O) or P_search is small. The 'Great Silence' can "
        "arise from any factor, not just rarity."
    )
    st.caption("🔵 Plausible — decomposition is model-consistent but factor values are illustrative")
