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
    """Stage 0 — Pre-technological: I ≈ 0, no tech observability."""
    params = ModelParams(
        stage_key="s0",
        A_rec=0.0,
        F_key="linear",
        O_key="increasing",
        obs_mode="static",
        p=0.0, q=0.0, r=0.0,   # no tech signatures
        a=0.10, b=0.0,          # minimal growth
    )
    y0 = (0.01, 0.5, 0.0)       # tuned
    return params, y0


def _stage_s1() -> StageSpec:
    """Stage 1 — Early technological: O rising, no recursion."""
    params = ModelParams(
        stage_key="s1",
        A_rec=0.0,
        F_key="linear",
        O_key="increasing",
        obs_mode="static",
        a=0.30, b=0.0,
    )
    y0 = (0.2, 0.5, 0.0)        # tuned
    return params, y0


def _stage_s2() -> StageSpec:
    """Stage 2 — Planetary technological: I grows, R relevant, O rising."""
    params = ModelParams(
        stage_key="s2",
        A_rec=0.2,
        F_key="saturating",
        O_key="increasing",
        obs_mode="dynamic",
    )
    y0 = (0.5, 0.5, 0.1)        # tuned
    return params, y0


def _stage_s3() -> StageSpec:
    """Stage 3 — Recursive transition: recursion turns on."""
    params = ModelParams(
        stage_key="s3",
        A_rec=1.5,
        F_key="saturating",
        O_key="peaked",
        obs_mode="dynamic",
    )
    y0 = (1.0, 0.8, 0.2)        # tuned
    return params, y0


def _stage_s4a() -> StageSpec:
    """Stage 4a — Collapse: A_rec >> R, transient O spike then collapse."""
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
    y0 = (1.5, 0.1, 0.1)        # R0 low — regulation already weak
    return params, y0


def _stage_s4b() -> StageSpec:
    """Stage 4b — Expansionist advanced: high I, high O for a long period."""
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
    y0 = (2.0, 1.0, 0.5)        # tuned
    return params, y0


def _stage_s4c() -> StageSpec:
    """Stage 4c — Optimized low-observable: high I, peak then decline in O."""
    params = ModelParams(
        stage_key="s4c",
        A_rec=1.0,
        a=0.50,                  # stronger growth to sustain high I
        c=0.20,                  # weaker regulatory damping on capability
        sI=0.05,                 # less capability saturation
        m=2.0, n=2.0,            # strong compression & stealth
        p=0.3, q=0.2, r=0.2,    # moderate emission
        F_key="saturating",
        O_key="peaked",
        obs_mode="dynamic",
        I_advanced=2.0,          # lower "advanced" threshold for this stage
    )
    y0 = (3.0, 1.5, 0.5)        # start with moderately high I
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
        tau_max=100.0,           # longer horizon for speculative phase
    )
    y0 = (5.0, 3.0, 0.3)        # tuned
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
