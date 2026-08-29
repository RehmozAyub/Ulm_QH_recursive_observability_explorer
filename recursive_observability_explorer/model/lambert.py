"""Lambert W special case — critical boundary computation.

The Lambert W function is justified ONLY when the recursive balance has the
form  I*e^I = C  (i.e. F_key == "lambert").  If F_key is anything else, we
use a fallback (logarithmic) threshold.

Derivation (Section 9.1 of GEMINI.md):
    b * A_rec * I * e^I = C_R
    where C_R = c * R^η * ln(1 + A_ref) * E
    ⇒  I * e^I = C_R / (b * A_rec)
    ⇒  I_crit  = W( C_R / (b * A_rec) )         (principal branch)

WARNING: The naive balance  b*A_rec*I*e^I = c*R*I  cancels I and reduces to
a LOGARITHM (e^I = cR/(bA_rec)), which does NOT need W.  The valid Lambert
structure requires the C_R form above.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy.special import lambertw

from model.config import ModelParams


# -------------------------------------------------------------------
# Validity guard
# -------------------------------------------------------------------

def lambert_is_valid(params: ModelParams) -> bool:
    """Return True ONLY if ``params.F_key == "lambert"``."""
    return params.F_key == "lambert"


def lambert_boundary_is_trivial(params: ModelParams) -> bool:
    """Return True when params.A_ref <= 0."""
    return params.A_ref <= 0.0


# -------------------------------------------------------------------
# Regulation capacity  C_R
# -------------------------------------------------------------------

def C_R(params: ModelParams, R: float) -> float:
    """Regulation capacity: ``c * R^η * ln(1 + A_ref) * E``.

    Guards against log(1+0) = 0 and R <= 0 gracefully.
    """
    R_safe = max(R, params.eps)
    log_term = np.log1p(max(params.A_ref, 0.0))  # ln(1 + A_ref)
    return params.c * (R_safe ** params.eta) * log_term * params.E


# -------------------------------------------------------------------
# Critical capability threshold  I_crit
# -------------------------------------------------------------------

def I_crit(params: ModelParams, R: float) -> Optional[float]:
    """Compute the Lambert-W critical capability.

    Returns ``W(C_R / (b * A_rec))`` (real part, principal branch).
    Returns None if ``F_key != "lambert"`` (caller should use fallback).
    """
    if not lambert_is_valid(params):
        return None

    cr = C_R(params, R)
    denom = params.b * params.A_rec + params.eps  # guard division by zero
    arg = cr / denom

    if arg < 0:
        # lambertw for negative real args can return complex; take real part
        return float(np.real(lambertw(arg)))

    return float(np.real(lambertw(arg)))


# -------------------------------------------------------------------
# Fallback threshold for non-Lambert F_key
# -------------------------------------------------------------------

def fallback_threshold(params: ModelParams, R: float) -> Optional[float]:
    """Log-based threshold used when ``F_key != "lambert"``.

    Solves  e^I = c*R / (b*A_rec)  ⇒  I = ln(c*R / (b*A_rec)).
    Returns None if the argument is non-positive (no real solution).
    """
    R_safe = max(R, params.eps)
    denom = params.b * params.A_rec + params.eps
    arg = params.c * R_safe / denom
    if arg <= 0:
        return None
    return float(np.log(arg))


# -------------------------------------------------------------------
# 2-D boundary grid  (for Plot 5)
# -------------------------------------------------------------------

def lambert_boundary(
    params: ModelParams,
    A_rec_grid: np.ndarray,
    R_grid: np.ndarray,
) -> np.ndarray:
    """Compute a 2-D grid of I_crit over the (A_rec, R) plane.

    Parameters
    ----------
    params : ModelParams
        Model parameters (eta, E, c, A_ref, b, eps are used).
    A_rec_grid : 1-D array
        Values of A_rec to scan.
    R_grid : 1-D array
        Values of R to scan.

    Returns
    -------
    I_crit_grid : 2-D ndarray, shape (len(R_grid), len(A_rec_grid))
        Critical capability at each (R, A_rec) pair.  NaN where the
        Lambert W argument is invalid.
    """
    CR_vec = params.c * (np.maximum(R_grid, params.eps) ** params.eta) * np.log1p(max(params.A_ref, 0.0)) * params.E
    args = CR_vec[:, None] / (params.b * A_rec_grid[None, :] + params.eps)
    grid = np.real(lambertw(args)).astype(float)
    grid[~np.isfinite(grid) | (grid < 0)] = np.nan
    return grid
