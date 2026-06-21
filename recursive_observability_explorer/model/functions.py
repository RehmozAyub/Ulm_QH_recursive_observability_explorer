"""Swappable model functions — F(I) recursion, O(I) static observability,
observability component terms, detection h(O), and driver hooks.

Every function variant lives in a registry (plain dict).  Adding a new variant
= appending one entry.  The solver/UI never references a specific form.
"""

from __future__ import annotations

import numpy as np
from typing import Callable, Dict

from model.config import ModelParams

# ---------------------------------------------------------------------------
# Numerical safety helpers
# ---------------------------------------------------------------------------

_EXP_CLIP = 50.0  # clip exponent arguments to [-_EXP_CLIP, _EXP_CLIP]


def _safe_exp(x):
    """Element-wise exp with exponent clipping to prevent overflow."""
    return np.exp(np.clip(x, -_EXP_CLIP, _EXP_CLIP))


# ===================================================================
# F(I) RECURSION REGISTRY  (Section 6.4)
# ===================================================================
# Signature:  f(I, params) -> float/array

def _F_linear(I, params: ModelParams):
    """F(I) = I — linear recursion."""
    return I


def _F_superlinear(I, params: ModelParams):
    """F(I) = I**2 — superlinear recursion."""
    return I ** 2


def _F_lambert(I, params: ModelParams):
    """F(I) = I*exp(I) — Lambert-type recursive threshold.

    Clipped for numerical safety.
    """
    return I * _safe_exp(I)


def _F_exponential(I, params: ModelParams):
    """F(I) = exp(I) — exponential recursion (clipped)."""
    return _safe_exp(I)


def _F_saturating(I, params: ModelParams):
    """F(I) = I / (1 + I/K) — saturating (Michaelis–Menten style)."""
    return I / (1.0 + I / params.K)


F_REGISTRY: Dict[str, Callable] = {
    "linear":      _F_linear,
    "superlinear": _F_superlinear,
    "lambert":     _F_lambert,
    "exponential": _F_exponential,
    "saturating":  _F_saturating,
}


# ===================================================================
# O(I) STATIC OBSERVABILITY REGISTRY  (Section 6.5)
# ===================================================================
# Signature:  o(I, params) -> float/array

def _O_increasing(I, params: ModelParams):
    """Model A: O(I) = 1 - exp(-λ*I) — monotone increasing."""
    return 1.0 - _safe_exp(-params.lam * I)


def _O_decreasing(I, params: ModelParams):
    """Model B: O(I) = exp(-λ*I) — monotone decreasing."""
    return _safe_exp(-params.lam * I)


def _O_peaked(I, params: ModelParams):
    """Model C: O(I) = I*exp(-λ*I) — rises then falls."""
    return I * _safe_exp(-params.lam * I)


def _O_threshold(I, params: ModelParams):
    """Model D: O(I) = 1/(1 + exp(-sign*k*(I-Ic))) — sigmoid.

    threshold_sign = +1 gives a rising sigmoid; -1 gives a falling one.
    """
    arg = params.threshold_sign * params.k * (I - params.Ic)
    return 1.0 / (1.0 + _safe_exp(-arg))


O_REGISTRY: Dict[str, Callable] = {
    "increasing": _O_increasing,
    "decreasing": _O_decreasing,
    "peaked":     _O_peaked,
    "threshold":  _O_threshold,
}


# ===================================================================
# OBSERVABILITY COMPONENT TERMS  (Section 6.3)
# ===================================================================
# Each term is a pure function (I, R, params) -> float/array.
# The default forms are intentionally simple and registry-swappable.

# ===================================================================
# OBSERVABILITY COMPONENT REGISTRIES  (Fix 1)
# ===================================================================

E_REGISTRY: Dict[str, Callable[[float, float, ModelParams], float]] = {
    "linear": lambda I, R, params: I,
    "kardashev": lambda I, R, params: I ** 2,
}

B_REGISTRY: Dict[str, Callable[[float, float, ModelParams], float]] = {
    "linear": lambda I, R, params: I,
    "decaying": lambda I, R, params: I * _safe_exp(-params.lam * I),
}

X_REGISTRY: Dict[str, Callable[[float, float, ModelParams], float]] = {
    "linear": lambda I, R, params: I,
    "inward": lambda I, R, params: 0.0,
}

C_REGISTRY: Dict[str, Callable[[float, float, ModelParams], float]] = {
    "linear": lambda I, R, params: I * R,
    "superlinear": lambda I, R, params: (I ** 2) * R,
}

S_REGISTRY: Dict[str, Callable[[float, float, ModelParams], float]] = {
    "linear": lambda I, R, params: I * R,
    "superlinear": lambda I, R, params: (I ** 2) * R,
}


def E_use(I, R, params: ModelParams):
    """Energy-use signature grows with capability."""
    return E_REGISTRY[params.E_key](I, R, params)


def B_cast(I, R, params: ModelParams):
    """Broadcast leakage grows with capability."""
    return B_REGISTRY[params.B_key](I, R, params)


def X_expand(I, R, params: ModelParams):
    """Expansion footprint grows with capability."""
    return X_REGISTRY[params.X_key](I, R, params)


def C_compress(I, R, params: ModelParams):
    """Efficiency/compression scales with capability & regulation."""
    return C_REGISTRY[params.C_key](I, R, params)


def S_stealth(I, R, params: ModelParams):
    """Deliberate/emergent quietness scales with capability & regulation."""
    return S_REGISTRY[params.S_key](I, R, params)


# ===================================================================
# DETECTION  (Section 6.6)
# ===================================================================

def h_detect(O, params: ModelParams):
    """Detection function h(O) = 1 - exp(-κ*O).

    O is clamped to >= 0 before detection.
    """
    O_pos = np.maximum(O, 0.0)
    return 1.0 - _safe_exp(-params.kappa * O_pos)


def P_det(O, params: ModelParams):
    """Detection probability P_det = h(O) * P_search."""
    return h_detect(O, params) * params.P_search


def N_obs(O, params: ModelParams):
    """Observed civilisation count N_obs = N_true * P_surv * h(O) * P_search."""
    return params.N_true * params.P_surv * h_detect(O, params) * params.P_search


# ===================================================================
# TIME-DEPENDENT DRIVER HOOK  (Section 5 — default: constant)
# ===================================================================

def driver_value(name: str, tau: float, params: ModelParams) -> float:
    """Return the driver value at time tau.

    If params.time_varying is False (default), returns the constant stored
    in params.  Override/extend this function to implement time profiles.
    """
    base = getattr(params, name)
    if not params.time_varying:
        return base

    # Implement illustrative time-varying profiles (Section 5)
    if name == "A":
        # Ordinary growth pressure increases linearly as baseline tech/leverage expands
        return base * (1.0 + 0.05 * tau)
    elif name == "A_rec":
        # Recursive growth pressure (intelligence explosion) modeled as an S-curve transition
        tau_mid = params.tau_max * 0.4
        return base * (1.0 + 1.5 / (1.0 + np.exp(-0.2 * (tau - tau_mid))))
    elif name == "A_ref":
        # Reflective learning / wisdom capacity grows gradually over time
        return base * (1.0 + 0.02 * tau)
    elif name == "Q":
        # Institutional quality decays slowly due to organizational friction and complexity
        return base * np.exp(-0.015 * tau)

    return base
