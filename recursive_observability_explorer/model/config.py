"""ModelParams dataclass — ALL parameters, defaults, bounds, and serialisation helpers.

Every coefficient, threshold, function selector, and solver knob lives here.
The sidebar builds sliders generically from BOUNDS; the solver reads params
directly.  No magic numbers anywhere else in the codebase.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, asdict
from typing import Dict, Tuple, Any


@dataclass
class ModelParams:
    """Complete parameter set for the Recursive Observability Filter model."""

    # --- Capability eq: dI/dtau = a*A*I + b*A_rec*F(I) - c*R*I - sI*I**2 ---
    # The -c*R*I damping term is active only when term_damping is True.  Stage
    # presets 0-2 disable it to reproduce the reduced models of manuscript
    # sections 7.1-7.3 literally.
    a:   float = 0.30     # ordinary growth coefficient
    b:   float = 0.20     # recursive growth coefficient
    c:   float = 0.50     # regulatory damping coefficient
    sI:  float = 0.10     # capability saturation

    # --- Regulation eq (bounded form, see NOTE below) ---
    # dR/dtau = (u*A_ref + v*Q)*(1 - R) - (w*A_rec + sR)*R
    #
    # NOTE: erosion is proportional to R, and building is proportional to the
    # remaining headroom (1 - R).  R is therefore a *regulation quality index*
    # confined to [0, 1] by construction:
    #     at R = 0  ->  dR/dtau = u*A_ref + v*Q >= 0   (cannot go negative)
    #     at R = 1  ->  dR/dtau = -(w*A_rec + sR) <= 0 (cannot exceed one)
    # Equilibrium is the "building share"
    #     R_inf = (u*A_ref + v*Q) / (u*A_ref + v*Q + w*A_rec + sR)
    # The previous form used a constant erosion term -w*A_rec, which drained R
    # at a rate independent of R and drove it negative (flipping -c*R*I into
    # positive feedback).  See lessons_learned.md section 6.2.
    u:   float = 0.40     # reflective learning gain
    v:   float = 0.30     # institutional quality gain
    w:   float = 0.50     # erosion by recursive amplification
    sR:  float = 0.15     # regulation decay

    # --- Observability eq coefficients ---
    # dO/dtau = p*E + q*B + r*X - (O - O_floor)*(m*C + n*S)
    #
    # NOTE: compression and stealth are *fractional* suppression rates — they
    # reduce the signal actually being emitted rather than subtracting an
    # absolute flux.  This bounds O from below by O_floor:
    #     at O = O_floor -> dO/dtau = production >= 0
    # The quasi-steady state is
    #     O* = O_floor + (p*E + q*B + r*X) / (m*C + n*S)
    # so peak-then-decline emerges when suppression grows faster in I than
    # production does (e.g. C_key/S_key = "superlinear"), rather than being
    # imposed by selecting O_key = "peaked".
    # See lessons_learned.md section 6.1.
    p:   float = 0.50     # energy-use signature weight
    q:   float = 0.30     # broadcast signature weight
    r:   float = 0.40     # expansion signature weight
    m:   float = 0.50     # compression suppression rate
    n:   float = 0.30     # stealth suppression rate

    # --- Driver levels (constant by default) ---
    A:     float = 1.0    # amplification pressure
    A_rec: float = 1.0    # recursive amplification
    A_ref: float = 1.0    # reflective amplification
    Q:     float = 1.0    # institutional quality

    # --- Function selectors (keys into registries in functions.py) ---
    F_key:   str = "saturating"   # linear | superlinear | lambert | exponential | saturating
    O_key:   str = "peaked"       # increasing | decreasing | peaked | threshold
    obs_mode: str = "dynamic"     # "dynamic" (solve dO/dtau) or "static" (O = O_key(I))

    # --- Observability component selectors ---
    E_key:   str = "linear"       # linear | kardashev
    B_key:   str = "linear"       # linear | decaying
    X_key:   str = "linear"       # linear | inward
    C_key:   str = "linear"       # linear | superlinear
    S_key:   str = "linear"       # linear | superlinear

    # --- Shape parameters for F(I) and O(I) ---
    K:   float = 5.0      # saturating F(I) half-saturation
    lam: float = 0.30     # lambda in O(I) functions
    k:   float = 1.0      # steepness in threshold O(I)
    Ic:  float = 5.0      # midpoint I_c in threshold O(I)
    threshold_sign: int = 1  # +1 => rising sigmoid; -1 => falling

    # --- Detection ---
    kappa:    float = 1.0    # detection sensitivity
    P_search: float = 0.50   # search coverage probability
    P_surv:   float = 0.80   # survival probability
    N_true:   float = 1.0    # true civ count (normalised)

    # --- Lambert special case ---
    eta: float = 1.0      # regulation exponent in C_R
    E:   float = 1.0      # alignment/consistency factor

    # --- Collapse / low-observability thresholds ---
    Theta:        float = 5.0    # collapse if A_rec/(R+eps) > Theta
    I_runaway:    float = 50.0   # collapse if I > I_runaway
    R_min:        float = 0.05   # collapse if R < R_min
    I_advanced:   float = 5.0    # "advanced" capability threshold
    O_detectable: float = 0.10   # below this O is "low-observable"
    eps:          float = 1e-6   # numerical guard

    # --- Thermodynamic observability floor ---
    # Irreducible signature strength: a civilisation using energy is never
    # perfectly invisible (manuscript section 4.4).  O is bounded below by this
    # value structurally, so "low-observable" can never mean "negative".
    O_floor: float = 1e-3

    # --- Term mask (reduced stage models, manuscript sections 7.1-7.3) ---
    term_damping: bool = True    # include -c*R*I in dI/dtau

    # --- Runaway guard ---
    # Superlinear and exponential recursion kernels produce finite-time
    # blow-up: dI/dtau ~ I^2 or e^I diverges at a finite tau.  An adaptive
    # solver approaching that singularity takes ever-smaller steps and never
    # terminates.  Integration stops cleanly once I exceeds this bound and the
    # remaining samples hold the terminal state (matching the browser
    # implementation, which caps its own step count).
    #
    # 1e4 is 200x the default I_runaway threshold, so any trajectory reaching it
    # is already classified "runaway" and further detail carries no information.
    # The bound also caps solver cost: dO/dtau is stiff (its relaxation rate
    # m*C + n*S grows like I^2*R), and an explicit RK45 needs h <~ 2.8/rate, so
    # the step count grows with both I_abort and the suppression weights.
    # Raising this materially slows strongly-suppressing configurations.
    I_abort: float = 1e4

    # --- Solver / time ---
    tau_max:  float = 50.0
    n_points: int   = 1000
    rtol:     float = 1e-6
    atol:     float = 1e-9

    # --- Time-dependent driver hook ---
    time_varying: bool = False  # TODO: tune profiles in functions.driver_value()

    # --- Preset tracking ---
    stage_key: str = ""


# ---------------------------------------------------------------------------
# BOUNDS — (min, max) for every numeric slider parameter
# ---------------------------------------------------------------------------

BOUNDS: Dict[str, Tuple[float, float]] = {
    # Capability eq
    "a":   (0.0, 2.0),
    "b":   (0.0, 2.0),
    "c":   (0.0, 3.0),
    "sI":  (0.0, 1.0),
    # Regulation eq
    "u":   (0.0, 2.0),
    "v":   (0.0, 2.0),
    "w":   (0.0, 3.0),
    "sR":  (0.0, 1.0),
    # Observability eq
    "p":   (0.0, 3.0),
    "q":   (0.0, 3.0),
    "r":   (0.0, 3.0),
    "m":   (0.0, 3.0),
    "n":   (0.0, 3.0),
    # Drivers
    "A":     (0.0, 5.0),
    "A_rec": (0.0, 5.0),
    "A_ref": (0.0, 5.0),
    "Q":     (0.0, 5.0),
    # Shape parameters
    "K":   (0.1, 50.0),
    "lam": (0.01, 3.0),
    "k":   (0.1, 10.0),
    "Ic":  (0.0, 50.0),
    # Detection
    "kappa":    (0.01, 10.0),
    "P_search": (0.0, 1.0),
    "P_surv":   (0.0, 1.0),
    "N_true":   (0.0, 1e6),
    # Lambert
    "eta": (0.1, 3.0),
    "E":   (0.01, 5.0),
    # Collapse thresholds
    "Theta":        (0.1, 50.0),
    "I_runaway":    (1.0, 1000.0),
    "R_min":        (0.0, 1.0),
    "I_advanced":   (0.0, 100.0),
    "O_detectable": (0.0, 1.0),
    "O_floor":      (0.0, 0.1),
    # Solver / time
    "tau_max":  (1.0, 500.0),
}

# Human-readable labels for sidebar groups
PARAM_GROUPS: Dict[str, list[str]] = {
    "Capability (dI/dτ)":     ["a", "b", "c", "sI"],
    "Regulation (dR/dτ)":     ["u", "v", "w", "sR"],
    "Observability (dO/dτ)":  ["p", "q", "r", "m", "n"],
    "Drivers":                ["A", "A_rec", "A_ref", "Q"],
    "Shape parameters":       ["K", "lam", "k", "Ic"],
    "Detection":              ["kappa", "P_search", "P_surv", "N_true"],
    "Lambert":                ["eta", "E"],
    "Thresholds":             ["Theta", "I_runaway", "R_min", "I_advanced", "O_detectable", "O_floor"],
    "Solver / Time":          ["tau_max"],
}

# Human-readable display names for parameters
PARAM_LABELS: Dict[str, str] = {
    "a": "a (ordinary growth)",
    "b": "b (recursive growth)",
    "c": "c (regulatory damping)",
    "sI": "sI (capability saturation)",
    "u": "u (reflective learning)",
    "v": "v (institutional quality gain)",
    "w": "w (erosion by A_rec)",
    "sR": "sR (regulation decay)",
    "p": "p (energy-use weight)",
    "q": "q (broadcast weight)",
    "r": "r (expansion weight)",
    "m": "m (compression weight)",
    "n": "n (stealth weight)",
    "A": "A (amplification pressure)",
    "A_rec": "A_rec (recursive amplification)",
    "A_ref": "A_ref (reflective amplification)",
    "Q": "Q (institutional quality)",
    "K": "K (half-saturation)",
    "lam": "λ (observability scale)",
    "k": "k (sigmoid steepness)",
    "Ic": "Ic (sigmoid midpoint)",
    "kappa": "κ (detection sensitivity)",
    "P_search": "P_search (search coverage)",
    "P_surv": "P_surv (survival probability)",
    "N_true": "N_true (true civ count)",
    "eta": "η (regulation exponent)",
    "E": "E (alignment factor)",
    "Theta": "Θ (collapse threshold)",
    "I_runaway": "I_runaway (runaway threshold)",
    "R_min": "R_min (minimum regulation)",
    "I_advanced": "I_advanced (advanced threshold)",
    "O_detectable": "O_detectable (detection floor)",
    "O_floor": "O_floor (thermodynamic floor)",
    "tau_max": "τ_max (simulation time)",
}


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def params_to_dict(params: ModelParams) -> Dict[str, Any]:
    """Convert ModelParams to a JSON-serialisable dict."""
    return asdict(params)


def params_from_dict(d: Dict[str, Any]) -> ModelParams:
    """Reconstruct ModelParams from a dict (e.g. loaded from JSON).

    Ignores unknown keys so that old/new configs are forward-compatible.
    """
    valid_names = {f.name for f in fields(ModelParams)}
    filtered = {k: v for k, v in d.items() if k in valid_names}
    return ModelParams(**filtered)


def params_to_json(params: ModelParams) -> str:
    """Serialise ModelParams to a pretty-printed JSON string."""
    return json.dumps(params_to_dict(params), indent=2)


def params_from_json(s: str) -> ModelParams:
    """Deserialise ModelParams from a JSON string."""
    return params_from_dict(json.loads(s))
