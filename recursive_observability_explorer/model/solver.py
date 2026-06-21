"""Solver wrapper — integrates the ROF ODE system and returns a Result
containing trajectory arrays and derived detection quantities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from model.config import ModelParams
from model.system import rhs
from model.functions import O_REGISTRY, h_detect, P_det as _P_det_func, N_obs as _N_obs_func


@dataclass
class Result:
    """Container for a single integration run."""

    tau: np.ndarray       # time grid
    I: np.ndarray         # capability trajectory
    R: np.ndarray         # regulation trajectory
    O: np.ndarray         # observability trajectory (dynamic or static)
    O_eff: np.ndarray     # effective O used for detection (clamped >= 0)
    h: np.ndarray         # detection function h(O)
    P_det: np.ndarray     # detection probability h(O)*P_search
    N_obs: np.ndarray     # observed civilisation count
    params: ModelParams   # parameters used for this run
    success: bool         # solver convergence flag
    message: str          # solver message


def integrate(
    params: ModelParams,
    y0: Tuple[float, float, float],
    tau_span: Optional[Tuple[float, float]] = None,
) -> Result:
    """Integrate the ROF system and compute derived detection arrays.

    Parameters
    ----------
    params : ModelParams
        Full model configuration (equation selectors, coefficients, solver
        settings).
    y0 : tuple of float
        Initial conditions ``(I0, R0, O0)``.
    tau_span : tuple of float, optional
        ``(tau_start, tau_end)``.  Defaults to ``(0, params.tau_max)``.

    Returns
    -------
    Result
        Trajectory arrays plus derived detection quantities.
    """
    if tau_span is None:
        tau_span = (0.0, params.tau_max)

    t_eval = np.linspace(tau_span[0], tau_span[1], params.n_points)
    dynamic = params.obs_mode == "dynamic"

    # Select initial state vector
    if dynamic:
        y0_vec = np.array([y0[0], y0[1], y0[2]], dtype=float)
    else:
        y0_vec = np.array([y0[0], y0[1]], dtype=float)

    sol = solve_ivp(
        fun=rhs,
        t_span=tau_span,
        y0=y0_vec,
        args=(params,),
        method="RK45",
        rtol=params.rtol,
        atol=params.atol,
        dense_output=True,
        t_eval=t_eval,
    )

    tau = sol.t
    I = sol.y[0]
    R = sol.y[1]

    if dynamic:
        O = sol.y[2]
    else:
        # Static mode: compute O = O_key(I) post hoc
        O_func = O_REGISTRY[params.O_key]
        O = O_func(I, params)

    # --- Derived detection arrays ---
    O_eff = np.maximum(O, 0.0)
    h = h_detect(O_eff, params)
    P_det = _P_det_func(O_eff, params)
    N_obs_arr = _N_obs_func(O_eff, params)

    return Result(
        tau=tau,
        I=I,
        R=R,
        O=O,
        O_eff=O_eff,
        h=h,
        P_det=P_det,
        N_obs=N_obs_arr,
        params=params,
        success=sol.success,
        message=sol.message,
    )
