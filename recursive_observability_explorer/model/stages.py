"""Stage presets — 8 canonical civilisation development stages.

Each preset returns a (ModelParams, y0) tuple where y0 = (I0, R0, O0).
Qualitative behaviour matters more than exact numeric tuning at this point.
Values marked # TODO: tune.
"""

from __future__ import annotations

from typing import Dict, Tuple

from model.config import ModelParams


# Type alias
StageSpec = Tuple[ModelParams, Tuple[float, float, float]]


def _stage_s0() -> StageSpec:
    """Stage 0 — Pre-technological.

    Manuscript §7.1:  dI/dτ ≈ 0,  O_tech = 0.
    Ordinary growth is switched off (a = 0) and the damping term is disabled,
    so capability stays at its initial near-zero value instead of being driven
    to zero by regulation.  No technological signature terms.
    """
    params = ModelParams(
        stage_key="s0",
        A_rec=0.0,
        F_key="linear",
        O_key="increasing",
        obs_mode="static",
        p=0.0, q=0.0, r=0.0,     # no tech signatures
        a=0.0, b=0.0,            # dI/dτ ≈ 0 per §7.1
        term_damping=False,      # reduced model
    )
    y0 = (0.01, 0.5, 0.0)
    return params, y0


def _stage_s1() -> StageSpec:
    """Stage 1 — Early technological: observability rises.

    Manuscript §7.2 exactly:  dI/dτ = a·A·I − s_I·I²,  O(I) = 1 − e^(−λI).
    Logistic growth to I → a·A/s_I = 3.0, hence O → 1 − e^(−0.9) ≈ 0.593.
    """
    params = ModelParams(
        stage_key="s1",
        A_rec=0.0,
        F_key="linear",
        O_key="increasing",
        obs_mode="static",
        a=0.30, b=0.0,
        term_damping=False,      # reduced model per §7.2
    )
    y0 = (0.2, 0.5, 0.0)
    return params, y0


def _stage_s2() -> StageSpec:
    """Stage 2 — Planetary technological: I grows, R relevant, O still rising.

    Manuscript §7.3:  dI/dτ = a·A·I − s_I·I²  with regulation becoming
    relevant.  No recursive amplification yet (A_rec = 0).
    """
    params = ModelParams(
        stage_key="s2",
        A_rec=0.0,               # recursion appears only at stage 3
        F_key="saturating",
        O_key="increasing",
        obs_mode="dynamic",
        term_damping=False,      # reduced model per §7.3
    )
    y0 = (0.5, 0.5, 0.1)
    return params, y0


def _stage_s3() -> StageSpec:
    """Stage 3 — Recursive transition: full model, recursion turns on.

    Manuscript §7.4 — the complete capability and regulation equations.
    """
    params = ModelParams(
        stage_key="s3",
        A_rec=1.5,
        F_key="saturating",
        O_key="peaked",
        obs_mode="dynamic",
    )
    y0 = (1.0, 0.7, 0.2)         # R0 <= 1 (R is now a quality index)
    return params, y0


def _stage_s4a() -> StageSpec:
    """Stage 4a — Collapse: recursive erosion drives regulation toward zero.

    With the bounded regulation equation the equilibrium is
        R_inf = (u·A_ref + v·Q) / (u·A_ref + v·Q + w·A_rec + s_R)
              = 0.38 / 8.68 ≈ 0.0438  <  R_min = 0.05
    so regulation decays to below the collapse threshold *without going
    negative* — the mechanism of §7.5 rather than a sign inversion.
    """
    params = ModelParams(
        stage_key="s4a",
        A_rec=4.0,
        A_ref=0.2,
        w=2.0,
        F_key="saturating",
        O_key="peaked",
        obs_mode="dynamic",
        sR=0.30,                 # faster regulation decay
    )
    y0 = (1.5, 0.3, 0.1)         # regulation already weak, still in [0, 1]
    return params, y0


def _stage_s4b() -> StageSpec:
    """Stage 4b — Expansionist advanced: high I, high O sustained.

    Linear compression/stealth (C, S ~ I·R) keeps the quasi-steady state
        O* = O_floor + (p + q + r) / ((m + n)·R)
    large and I-independent, so observability stays high indefinitely.
    """
    params = ModelParams(
        stage_key="s4b",
        A_rec=1.0,
        a=0.50,                  # stronger growth to sustain high I
        c=0.15,                  # weaker regulatory damping on capability
        sI=0.05,                 # less capability saturation
        r=2.0,                   # strong expansion signature
        m=0.1, n=0.1,            # weak compression/stealth
        F_key="saturating",
        O_key="increasing",
        obs_mode="dynamic",
    )
    y0 = (2.0, 0.9, 0.5)
    return params, y0


def _stage_s4c() -> StageSpec:
    """Stage 4c — Optimized low-observable: O peaks, then declines.

    The central Recursive Observability Filter case.  Compression and stealth
    are *superlinear* in capability (C, S ~ I²·R) while production is linear,
    so the quasi-steady state
        O* = O_floor + (p + q + r) / ((m + n)·I·R)
    falls as capability grows.  Peak-then-decline is therefore **derived** from
    the ratio of suppression to production, not imposed by choosing
    O_key = "peaked".  O remains >= O_floor throughout.
    """
    params = ModelParams(
        stage_key="s4c",
        A_rec=1.0,
        a=0.50,                  # stronger growth to sustain high I
        c=0.20,                  # weaker regulatory damping on capability
        sI=0.05,                 # less capability saturation
        m=2.0, n=2.0,            # strong compression & stealth
        p=0.3, q=0.2, r=0.2,     # moderate emission
        C_key="superlinear",     # suppression outruns production in I
        S_key="superlinear",
        F_key="saturating",
        O_key="peaked",
        obs_mode="dynamic",
        I_advanced=2.0,          # lower "advanced" threshold for this stage
    )
    y0 = (1.0, 0.6, 0.1)         # start low so the peak is visible
    return params, y0


def _stage_s5() -> StageSpec:
    """Stage 5 — Post-biological / unknown: speculative, weak claims."""
    params = ModelParams(
        stage_key="s5",
        A_rec=2.0,
        A_ref=2.0,
        F_key="saturating",
        O_key="peaked",
        obs_mode="dynamic",
        m=2.5, n=2.5,
        C_key="superlinear",
        S_key="superlinear",
        tau_max=100.0,           # longer horizon for speculative phase
    )
    y0 = (2.0, 0.8, 0.3)
    return params, y0


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_STAGE_REGISTRY: Dict[str, callable] = {
    "s0":  _stage_s0,
    "s1":  _stage_s1,
    "s2":  _stage_s2,
    "s3":  _stage_s3,
    "s4a": _stage_s4a,
    "s4b": _stage_s4b,
    "s4c": _stage_s4c,
    "s5":  _stage_s5,
}

STAGE_LABELS: Dict[str, str] = {
    "s0":  "Stage 0 — Pre-technological",
    "s1":  "Stage 1 — Early technological",
    "s2":  "Stage 2 — Planetary technological",
    "s3":  "Stage 3 — Recursive transition",
    "s4a": "Stage 4a — Collapse",
    "s4b": "Stage 4b — Expansionist advanced",
    "s4c": "Stage 4c — Optimized low-observable",
    "s5":  "Stage 5 — Post-biological (Speculative)",
}


def get_stage(stage_key: str) -> StageSpec:
    """Return ``(ModelParams, y0)`` for the requested stage preset.

    Raises KeyError if *stage_key* is not in the registry.
    """
    return _STAGE_REGISTRY[stage_key]()


def stage_keys() -> list[str]:
    """Return ordered list of stage keys."""
    return list(_STAGE_REGISTRY.keys())
