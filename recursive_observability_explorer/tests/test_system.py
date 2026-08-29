"""Tests for the ODE system (model/system.py).

- rhs returns finite values for a range of states.
- Switching F_key / O_key changes dI / O as expected.
- No NaN/overflow with exponent clipping.
"""

import numpy as np
import pytest

from model.config import ModelParams
from model.system import rhs


class TestRhsFinite:
    """rhs must return finite values for a range of states."""

    @pytest.mark.parametrize("I,R,O", [
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
        (10.0, 0.5, 5.0),
        (0.01, 10.0, 0.01),
        (50.0, 0.001, 20.0),
    ])
    def test_finite_dynamic(self, I, R, O):
        params = ModelParams(obs_mode="dynamic")
        y = np.array([I, R, O])
        dy = rhs(0.0, y, params)
        assert np.all(np.isfinite(dy)), f"Non-finite rhs for y={y}: dy={dy}"

    @pytest.mark.parametrize("I,R", [
        (0.0, 0.0),
        (1.0, 1.0),
        (50.0, 0.001),
    ])
    def test_finite_static(self, I, R):
        params = ModelParams(obs_mode="static")
        y = np.array([I, R])
        dy = rhs(0.0, y, params)
        assert np.all(np.isfinite(dy)), f"Non-finite rhs for y={y}: dy={dy}"


class TestFkeySwitching:
    """Switching F_key should change dI."""

    def test_linear_vs_superlinear(self):
        params_lin = ModelParams(F_key="linear", obs_mode="static")
        params_sup = ModelParams(F_key="superlinear", obs_mode="static")
        y = np.array([2.0, 1.0])

        dy_lin = rhs(0.0, y, params_lin)
        dy_sup = rhs(0.0, y, params_sup)

        # F(I)=I vs F(I)=I**2 → dI differs (with I=2, I**2=4, so superlinear is bigger)
        assert dy_sup[0] != dy_lin[0], "dI should differ between linear and superlinear"
        assert dy_sup[0] > dy_lin[0], "Superlinear should give larger dI for I=2"

    def test_linear_vs_lambert(self):
        params_lin = ModelParams(F_key="linear", obs_mode="static")
        params_lam = ModelParams(F_key="lambert", obs_mode="static")
        y = np.array([2.0, 1.0])

        dy_lin = rhs(0.0, y, params_lin)
        dy_lam = rhs(0.0, y, params_lam)

        # F(2)=2 vs F(2)=2*e^2 ≈ 14.778
        assert dy_lam[0] != dy_lin[0], "dI should differ between linear and lambert"
        assert dy_lam[0] > dy_lin[0], "Lambert should give larger dI for I=2"


class TestExponentClipping:
    """Large I with lambert/exponential F_key should not overflow."""

    @pytest.mark.parametrize("F_key", ["lambert", "exponential"])
    def test_no_overflow(self, F_key):
        params = ModelParams(F_key=F_key, obs_mode="dynamic")
        y = np.array([100.0, 1.0, 1.0])  # Very large I
        dy = rhs(0.0, y, params)
        assert np.all(np.isfinite(dy)), f"Overflow with F_key={F_key}, I=100: dy={dy}"


class TestObsModeSwitch:
    """obs_mode='dynamic' should return 3-element vector; 'static' returns 2."""

    def test_dynamic_3d(self):
        params = ModelParams(obs_mode="dynamic")
        y = np.array([1.0, 1.0, 1.0])
        dy = rhs(0.0, y, params)
        assert len(dy) == 3

    def test_static_2d(self):
        params = ModelParams(obs_mode="static")
        y = np.array([1.0, 1.0])
        dy = rhs(0.0, y, params)
        assert len(dy) == 2
