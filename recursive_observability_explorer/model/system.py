"""ODE right-hand side — assembles dI/dτ, dR/dτ, dO/dτ by calling
registry-selected functions.  Never hardcodes a functional form.
"""

from __future__ import annotations

import numpy as np

from model.config import ModelParams
from model.functions import (
    F_REGISTRY,
    E_REGISTRY, B_REGISTRY, X_REGISTRY, C_REGISTRY, S_REGISTRY,
    driver_value,
)


def rhs(tau: float, y: np.ndarray, params: ModelParams) -> np.ndarray:
    """Right-hand side of the ROF ODE system.

    Parameters
    ----------
    tau : float
        Dimensionless time.
    y : array-like
        State vector.  If ``obs_mode == "dynamic"`` then ``y = [I, R, O]``;
        otherwise ``y = [I, R]``.
    params : ModelParams
        Full parameter set (including function selectors).

    Returns
    -------
    dydt : np.ndarray
        Time derivatives in the same layout as *y*.
    """
    dynamic = params.obs_mode == "dynamic"

    I = float(y[0])
    R = float(y[1])
    O = float(y[2]) if dynamic else 0.0

    # --- Driver values (supports time-varying hook) ---
    A     = driver_value("A",     tau, params)
    A_rec = driver_value("A_rec", tau, params)
    A_ref = driver_value("A_ref", tau, params)
    Q_val = driver_value("Q",     tau, params)

    # --- F(I) from registry ---
    F_func = F_REGISTRY[params.F_key]
    FI = F_func(I, params)

    # --- dI/dτ = a*A*I + b*A_rec*F(I) - [c*R*I] - sI*I² ---
    # The regulatory damping term is gated by params.term_damping so that the
    # reduced stage models of manuscript §7.1-7.3 can be reproduced literally.
    damping = params.c * R * I if params.term_damping else 0.0
    dI = (params.a * A * I
          + params.b * A_rec * FI
          - damping
          - params.sI * I ** 2)

    # --- dR/dτ = (u*A_ref + v*Q)*(1 - R) - (w*A_rec + sR)*R ---
    # Building acts on the remaining headroom (1 - R); erosion is proportional
    # to the regulation that actually exists.  This confines R to [0, 1]
    # structurally — no clamping, no discontinuity in the RHS.
    build = params.u * A_ref + params.v * Q_val
    erode = params.w * A_rec + params.sR
    dR = build * (1.0 - R) - erode * R

    if not dynamic:
        return np.array([dI, dR])

    # --- dO/dτ = p*E + q*B + r*X - (O - O_floor)*(m*C + n*S) ---
    # Compression and stealth suppress the signal being emitted (a fractional
    # rate), rather than subtracting an absolute flux.  O is therefore bounded
    # below by O_floor: at O = O_floor the sink vanishes and production is >= 0.
    production = (params.p * E_REGISTRY[params.E_key](I, R, params)
                  + params.q * B_REGISTRY[params.B_key](I, R, params)
                  + params.r * X_REGISTRY[params.X_key](I, R, params))
    suppression = (params.m * C_REGISTRY[params.C_key](I, R, params)
                   + params.n * S_REGISTRY[params.S_key](I, R, params))
    dO = production - (O - params.O_floor) * suppression

    return np.array([dI, dR, dO])
