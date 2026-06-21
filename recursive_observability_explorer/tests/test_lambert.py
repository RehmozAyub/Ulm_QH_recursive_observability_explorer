"""Tests for Lambert W special case (model/lambert.py).

- For F_key="lambert", assert I_crit*exp(I_crit) recovers C_R/(b*A_rec) within 1e-6.
- Assert lambert_is_valid returns False for every non-lambert F_key.
- Assert fallback log threshold is used for non-lambert keys.
"""

import math

import numpy as np
import pytest

from model.config import ModelParams
from model.lambert import (
    lambert_is_valid, lambert_boundary_is_trivial, C_R, I_crit, fallback_threshold
)


class TestLambertValidity:
    """lambert_is_valid should return True ONLY for F_key='lambert'."""

    @pytest.mark.parametrize("F_key", ["linear", "superlinear", "exponential", "saturating"])
    def test_non_lambert_invalid(self, F_key):
        params = ModelParams(F_key=F_key)
        assert lambert_is_valid(params) is False

    def test_lambert_valid(self):
        params = ModelParams(F_key="lambert")
        assert lambert_is_valid(params) is True

    def test_lambert_boundary_is_trivial(self):
        params = ModelParams(A_ref=0.0)
        assert lambert_boundary_is_trivial(params) is True
        params = ModelParams(A_ref=1.0)
        assert lambert_boundary_is_trivial(params) is False


class TestICrit:
    """For F_key='lambert', I_crit * exp(I_crit) should recover C_R/(b*A_rec)."""

    @pytest.mark.parametrize("R_val", [0.5, 1.0, 2.0, 3.0])
    def test_roundtrip(self, R_val):
        params = ModelParams(F_key="lambert", b=0.2, A_rec=1.0, c=0.5, eta=1.0, E=1.0, A_ref=1.0)
        cr = C_R(params, R_val)
        denom = params.b * params.A_rec + params.eps
        expected_arg = cr / denom

        ic = I_crit(params, R_val)
        assert ic is not None, "I_crit should not be None for F_key='lambert'"
        recovered = ic * math.exp(ic)
        assert abs(recovered - expected_arg) < 1e-6, (
            f"I_crit*exp(I_crit)={recovered:.8f} != C_R/(b*A_rec)={expected_arg:.8f}"
        )

    def test_returns_none_for_non_lambert(self):
        params = ModelParams(F_key="saturating")
        assert I_crit(params, 1.0) is None


class TestFallback:
    """Fallback log threshold for non-lambert F_keys."""

    def test_fallback_computed(self):
        params = ModelParams(F_key="saturating", b=0.2, A_rec=1.0, c=0.5)
        fb = fallback_threshold(params, 1.0)
        assert fb is not None
        # e^fb = c*R / (b*A_rec) => fb = ln(c*R / (b*A_rec))
        expected = math.log(params.c * 1.0 / (params.b * params.A_rec))
        assert abs(fb - expected) < 1e-4

    def test_fallback_none_for_negative_arg(self):
        # Make c*R / (b*A_rec) <= 0 — shouldn't happen normally but guard
        params = ModelParams(F_key="saturating", b=0.2, A_rec=1.0, c=0.0)
        fb = fallback_threshold(params, 1.0)
        assert fb is None  # log(0) is undefined
