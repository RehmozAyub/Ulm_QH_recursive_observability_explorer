"""Regime classifier — maps trajectory + params to a human-readable regime
label and a list of reasons (which thresholds fired).

All thresholds live in ModelParams so they are tunable from the sidebar.
"""

from __future__ import annotations

from typing import Tuple, List

import numpy as np

from model.config import ModelParams
from model.solver import Result
from model.functions import h_detect


# Canonical regime labels
REGIMES = [
    "pre-detectable",
    "visible-technological",
    "expansionist-visible",
    "runaway",
    "collapse-proxy",
    "optimized-low-observable",
    "uncertain",
]


def classify_regime(
    result: Result,
    params: ModelParams,
) -> Tuple[str, List[str]]:
    """Classify the trajectory regime.

    Parameters
    ----------
    result : Result
        Solved trajectory (tau, I, R, O, etc.).
    params : ModelParams
        Model parameters (thresholds live here).

    Returns
    -------
    label : str
        One of the canonical regime labels.
    reasons : list of str
        Human-readable explanations of which criteria fired.
    """
    reasons: List[str] = []

    I = result.I
    R = result.R
    O = result.O

    I_final = float(I[-1])
    R_final = float(R[-1])
    O_final = float(O[-1])
    I_peak = float(np.max(I))
    O_peak = float(np.max(O))
    R_min_val = float(np.min(R))

    # Detection at final time
    h_final = float(h_detect(max(O_final, 0.0), params))
    P_det_final = h_final * params.P_search

    # --- Check runaway condition ---
    arec_over_R = params.A_rec / (R_final + params.eps)
    runaway = I_final > params.I_runaway or arec_over_R > params.Theta
    if I_final > params.I_runaway:
        reasons.append(f"I_final ({I_final:.2f}) > I_runaway ({params.I_runaway})")
    if arec_over_R > params.Theta:
        reasons.append(
            f"A_rec/(R+ε) = {arec_over_R:.2f} > Θ ({params.Theta})"
        )

    # --- Check collapse-proxy: runaway + loss of R and O ---
    collapse = False
    if runaway:
        if R_min_val < params.R_min:
            reasons.append(f"R_min ({R_min_val:.4f}) < R_min threshold ({params.R_min})")
            collapse = True
        # Also check if O collapsed after a spike
        if O_peak > params.O_detectable and O_final < params.O_detectable:
            reasons.append(
                f"O peaked ({O_peak:.3f}) then fell below O_detectable ({params.O_detectable})"
            )
            collapse = True

    if collapse:
        return "collapse-proxy", reasons

    if runaway:
        return "runaway", reasons

    # --- pre-detectable: peak O ~ 0 AND I low ---
    if O_peak < params.O_detectable and I_peak < params.I_advanced:
        reasons.append(
            f"Peak O ({O_peak:.4f}) < O_detectable ({params.O_detectable}) "
            f"and peak I ({I_peak:.2f}) < I_advanced ({params.I_advanced})"
        )
        return "pre-detectable", reasons

    # --- optimized-low-observable: high I, R sufficient, O low ---
    if (I_final >= params.I_advanced
            and R_final >= params.R_min
            and O_final < params.O_detectable):
        reasons.append(
            f"I_final ({I_final:.2f}) ≥ I_advanced ({params.I_advanced}), "
            f"R_final ({R_final:.4f}) ≥ R_min ({params.R_min}), "
            f"O_final ({O_final:.4f}) < O_detectable ({params.O_detectable})"
        )
        return "optimized-low-observable", reasons

    # --- expansionist-visible: high I AND final O high ---
    if I_final >= params.I_advanced and O_final >= params.O_detectable:
        reasons.append(
            f"I_final ({I_final:.2f}) ≥ I_advanced ({params.I_advanced}) "
            f"and O_final ({O_final:.3f}) ≥ O_detectable ({params.O_detectable})"
        )
        return "expansionist-visible", reasons

    # --- visible-technological: O rising and detection non-negligible ---
    if P_det_final > 0.01:
        reasons.append(
            f"P_det_final ({P_det_final:.4f}) > 0.01 — civilisation is detectable"
        )
        return "visible-technological", reasons

    # --- uncertain: none robustly met ---
    reasons.append("No regime criterion was robustly satisfied.")
    return "uncertain", reasons


# ---------------------------------------------------------------------------
# Human-readable regime descriptions
# ---------------------------------------------------------------------------

REGIME_DESCRIPTIONS = {
    "pre-detectable":
        "Civilisation has not yet developed sufficient capability or "
        "observability to be detectable by external observers.",
    "visible-technological":
        "Civilisation is in a technological phase with non-negligible "
        "detection probability — it leaks signals/waste heat.",
    "expansionist-visible":
        "Advanced, high-capability civilisation maintaining high "
        "observability through expansion, energy use, or broadcasts.",
    "runaway":
        "Recursive amplification has outstripped regulatory capacity. "
        "The system is beyond the modelled regulatory envelope.",
    "collapse-proxy":
        "Runaway conditions were met AND regulation/observability "
        "collapsed. Note: this is a *model proxy* for collapse, not proof.",
    "optimized-low-observable":
        "Advanced civilisation with sufficient regulation and LOW "
        "observability — capable but quiet. NOT physically invisible; "
        "thermodynamic waste persists but is minimised/redirected.",
    "uncertain":
        "Classification is ambiguous — no single regime criterion was "
        "robustly satisfied. Consider perturbing parameters.",
}
