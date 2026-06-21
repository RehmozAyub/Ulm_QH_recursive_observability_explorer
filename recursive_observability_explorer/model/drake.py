"""Drake equation decomposition — classical vs ROF-modified N_obs.

This module is a *teaching / display* panel, not the dynamical core.
It maps the current detection function h(O) to a signal probability P_sig
and shows how the ROF modifies the classical Drake estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from model.config import ModelParams
from model.functions import h_detect


@dataclass
class DrakeDecomposition:
    """Holds the decomposition values for display."""

    # Classical Drake reference (user can fill these; we provide defaults)
    R_star: float = 1.0    # star formation rate (normalised)
    f_p:    float = 1.0    # fraction with planets
    n_e:    float = 1.0    # habitable planets per system
    f_l:    float = 1.0    # fraction developing life
    f_i:    float = 1.0    # fraction developing intelligence
    f_c:    float = 1.0    # fraction developing technology
    L:      float = 1.0    # longevity (normalised)

    # ROF additions
    N_true:   float = 1.0   # N_true from params
    P_surv:   float = 0.8   # survival probability
    P_sig:    float = 0.5   # signal probability = h(O)
    P_search: float = 0.5   # search coverage

    @property
    def N_classical(self) -> float:
        """Classical Drake estimate (product of all factors)."""
        return self.R_star * self.f_p * self.n_e * self.f_l * self.f_i * self.f_c * self.L

    @property
    def N_obs_rof(self) -> float:
        """ROF-modified observed count: N_true * P_surv * P_sig * P_search."""
        return self.N_true * self.P_surv * self.P_sig * self.P_search


def compute_decomposition(
    O_value: float,
    params: ModelParams,
    R_star: float = 1.0,
    f_p: float = 1.0,
    n_e: float = 1.0,
    f_l: float = 1.0,
    f_i: float = 1.0,
    f_c: float = 1.0,
    L: float = 1.0,
) -> DrakeDecomposition:
    """Build a DrakeDecomposition from the current observability and params.

    Parameters
    ----------
    O_value : float
        Current (or final) observability value.
    params : ModelParams
        Model parameters for detection.
    R_star : float, default 1.0
    f_p : float, default 1.0
    n_e : float, default 1.0
    f_l : float, default 1.0
    f_i : float, default 1.0
    f_c : float, default 1.0
    L : float, default 1.0

    Returns
    -------
    DrakeDecomposition
    """
    h = float(h_detect(max(O_value, 0.0), params))
    return DrakeDecomposition(
        R_star=R_star,
        f_p=f_p,
        n_e=n_e,
        f_l=f_l,
        f_i=f_i,
        f_c=f_c,
        L=L,
        N_true=params.N_true,
        P_surv=params.P_surv,
        P_sig=h,              # h(O) maps to P_sig
        P_search=params.P_search,
    )
