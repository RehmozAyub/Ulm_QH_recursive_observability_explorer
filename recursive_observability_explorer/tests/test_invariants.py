"""Structural invariants and qualitative stage signatures.

These tests encode *intent*, not current behaviour.  They exist because the
original suite passed while three structural defects were present:

  - observability O ran to large negative values (min -1431 in stage 4c),
  - regulation R ran negative (-25.4 in stage 4a), flipping -c*R*I into
    positive feedback,
  - capability decayed to ~1e-9 in most configurations, so stage 1 classified
    as pre-detectable despite the manuscript specifying rising observability.

None of these were caught, because the stage tests asserted a *disjunction* of
acceptable labels rather than the qualitative behaviour each stage is supposed
to exhibit.  See lessons_learned.md sections 6.1-6.3.
"""

from __future__ import annotations

import numpy as np
import pytest

from model.config import ModelParams, BOUNDS
from model.functions import F_REGISTRY
from model.solver import integrate
from model.stages import get_stage, stage_keys


# ===================================================================
# Structural invariants — must hold for EVERY parameter combination
# ===================================================================

class TestStructuralInvariants:
    """O is bounded below by O_floor; R is confined to [0, 1]."""

    @pytest.mark.parametrize("stage_key", stage_keys())
    def test_observability_never_negative(self, stage_key):
        """O is a signature strength — it can never be negative."""
        params, y0 = get_stage(stage_key)
        result = integrate(params, y0)
        assert np.min(result.O) >= -1e-9, (
            f"{stage_key}: O reached {np.min(result.O):.4e}. Observability is a "
            f"physical signature strength and must stay >= 0."
        )

    @pytest.mark.parametrize("stage_key", stage_keys())
    def test_regulation_within_unit_interval(self, stage_key):
        """R is a regulation *quality index* confined to [0, 1]."""
        params, y0 = get_stage(stage_key)
        result = integrate(params, y0)
        assert np.min(result.R) >= -1e-9, (
            f"{stage_key}: R reached {np.min(result.R):.4f}. Negative regulation "
            f"flips the -c*R*I damping term into positive feedback."
        )
        assert np.max(result.R) <= 1.0 + 1e-9, (
            f"{stage_key}: R reached {np.max(result.R):.4f}, above the unit interval."
        )

    def test_regulation_equilibrium_is_non_negative_by_construction(self):
        """R_inf = B/(B+W) is a ratio of non-negative quantities, so R_inf >= 0."""
        rng = np.random.default_rng(0)
        for _ in range(200):
            p = ModelParams(
                u=rng.uniform(0, 2), v=rng.uniform(0, 2),
                w=rng.uniform(0, 3), sR=rng.uniform(0.01, 1),
                A_ref=rng.uniform(0, 5), Q=rng.uniform(0, 5),
                A_rec=rng.uniform(0, 5),
            )
            build = p.u * p.A_ref + p.v * p.Q
            erode = p.w * p.A_rec + p.sR
            R_inf = build / (build + erode)
            assert 0.0 <= R_inf <= 1.0

    def test_invariants_hold_under_random_parameters(self):
        """The bounds are structural, not the result of preset tuning.

        The recursion kernel is restricted to the non-explosive variants.  With
        ``exponential``/``lambert`` and a large ``b*A_rec`` the capability
        equation blows up super-exponentially and the adaptive solver spends
        unbounded time resolving the singularity — that is a solver-robustness
        concern (tracked separately), not an invariant question.
        """
        rng = np.random.default_rng(20260730)
        tame_kernels = ["linear", "superlinear", "saturating"]
        checked = 0
        for _ in range(40):
            kw = {
                key: float(rng.uniform(lo, min(hi, 2.0)))
                for key, (lo, hi) in BOUNDS.items()
                if key not in ("N_true", "I_runaway", "tau_max")
            }
            kw["F_key"] = str(rng.choice(tame_kernels))
            kw["C_key"] = str(rng.choice(["linear", "superlinear"]))
            kw["S_key"] = str(rng.choice(["linear", "superlinear"]))
            kw["obs_mode"] = "dynamic"
            kw["tau_max"] = 15.0
            # Keep the suite fast.  Runtime here is dominated by *stiffness*:
            # the dO/dtau relaxation rate is m*C + n*S ~ I^2*R, and an explicit
            # RK45 needs h <~ 2.8/rate, so cost grows with the suppression
            # weights and with how far capability climbs before I_abort fires.
            # Capping the suppression weights and the recursion strength keeps
            # this test to a few seconds without weakening the invariant, which
            # is structural (at O = O_floor the sink vanishes identically).
            kw["m"] = float(rng.uniform(0.0, 1.0))
            kw["n"] = float(rng.uniform(0.0, 1.0))
            kw["b"] = float(rng.uniform(0.0, 0.5))
            kw["A_rec"] = float(rng.uniform(0.0, 1.5))
            params = ModelParams(**kw)
            y0 = (rng.uniform(0.01, 2.0), rng.uniform(0.0, 1.0), rng.uniform(0.0, 1.0))
            result = integrate(params, y0)
            if not np.all(np.isfinite(result.O)):
                continue          # overflow under extreme recursion
            checked += 1
            assert np.min(result.O) >= -1e-8, f"O went negative: {np.min(result.O):.4e}"
            assert np.min(result.R) >= -1e-8, f"R went negative: {np.min(result.R):.4e}"
            assert np.max(result.R) <= 1.0 + 1e-8, f"R exceeded 1: {np.max(result.R):.4f}"
        assert checked > 15, "too few configurations actually exercised"


# ===================================================================
# Qualitative stage signatures — what each stage is supposed to DO
# ===================================================================

class TestStageSignatures:
    """Each stage must reproduce the behaviour the manuscript specifies."""

    def test_s0_capability_stays_negligible(self):
        """Manuscript 7.1: dI/dtau ~ 0, no technological observability."""
        params, y0 = get_stage("s0")
        result = integrate(params, y0)
        assert result.I[-1] < 0.05, f"s0 capability grew to {result.I[-1]:.4f}"
        assert result.O[-1] < params.O_detectable

    def test_s1_matches_manuscript_logistic_solution(self):
        """Manuscript 7.2 exactly: I -> a*A/s_I, O -> 1 - exp(-lambda*I).

        This is the check the old suite lacked: it pins the *analytic* answer,
        not a label.
        """
        params, y0 = get_stage("s1")
        result = integrate(params, y0)
        I_expected = params.a * params.A / params.sI          # 3.0
        O_expected = 1.0 - np.exp(-params.lam * I_expected)   # 0.5934
        assert result.I[-1] == pytest.approx(I_expected, rel=1e-3), (
            f"s1 capability {result.I[-1]:.4f} != logistic limit {I_expected:.4f}"
        )
        assert result.O[-1] == pytest.approx(O_expected, rel=1e-3)

    def test_s1_observability_rises(self):
        """Stage 1 is defined by *rising* observability."""
        params, y0 = get_stage("s1")
        result = integrate(params, y0)
        assert result.O[-1] > result.O[0], "s1 observability must rise"
        assert np.all(np.diff(result.O) >= -1e-9), "s1 observability must be monotone rising"

    def test_s2_observability_rises(self):
        """Manuscript 7.3: observability still increasing at planetary stage."""
        params, y0 = get_stage("s2")
        result = integrate(params, y0)
        assert result.O[-1] > result.O[0]

    def test_s4b_stays_highly_observable(self):
        """Expansionist: high capability AND high observability sustained."""
        params, y0 = get_stage("s4b")
        result = integrate(params, y0)
        assert result.I[-1] >= params.I_advanced
        assert result.O[-1] > params.O_detectable
        second_half = result.O[len(result.O) // 2:]
        assert np.min(second_half) > params.O_detectable, "4b must stay visible"

    def test_s4c_peaks_then_declines(self):
        """The central ROF case: O rises, peaks, then falls — while staying positive.

        Peak-then-decline must be *derived* from suppression outrunning
        production, not imposed by selecting O_key='peaked'.
        """
        params, y0 = get_stage("s4c")
        result = integrate(params, y0)
        peak_idx = int(np.argmax(result.O))
        assert 0 < peak_idx < len(result.O) - 1, (
            f"s4c observability peak at index {peak_idx} — expected an interior maximum"
        )
        assert result.O[peak_idx] > result.O[0], "O must rise to its peak"
        assert result.O[-1] < result.O[peak_idx], "O must decline after the peak"
        assert result.O[-1] < params.O_detectable, "s4c must end low-observable"
        assert np.min(result.O) > 0.0, (
            "s4c must be quiet, not negative — low observability is not invisibility"
        )

    def test_s4a_regulation_collapses_without_going_negative(self):
        """Collapse must occur through R -> small, not through R -> negative."""
        params, y0 = get_stage("s4a")
        result = integrate(params, y0)
        assert np.min(result.R) < params.R_min, "s4a regulation must fall below R_min"
        assert np.min(result.R) >= 0.0, "s4a regulation must not go negative"

    def test_damping_term_never_becomes_a_source(self):
        """-c*R*I must always oppose growth: with R >= 0 it can never add to dI."""
        for key in stage_keys():
            params, y0 = get_stage(key)
            result = integrate(params, y0)
            damping = params.c * result.R * result.I
            assert np.all(damping >= -1e-9), (
                f"{key}: regulatory damping became a source term"
            )
