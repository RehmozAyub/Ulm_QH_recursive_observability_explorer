"""Tests for the regime classifier (model/regimes.py).

- Stage s4a classifies as collapse-proxy or runaway.
- Stage s4c classifies as optimized-low-observable.
- Stage s1 classifies as visible-technological or pre-detectable.
- All three are distinct from each other.
"""

import pytest

from model.config import ModelParams
from model.stages import get_stage
from model.solver import integrate
from model.regimes import classify_regime


class TestStageClassification:
    """Each canonical stage preset should classify into its expected regime."""

    def test_s0_pre_detectable(self):
        """Stage 0 should classify as pre-detectable."""
        params, y0 = get_stage("s0")
        result = integrate(params, y0)
        label, reasons = classify_regime(result, params)
        assert label == "pre-detectable", (
            f"s0 classified as '{label}', expected pre-detectable. Reasons: {reasons}"
        )

    def test_s1_visible_technological(self):
        """Stage 1 must classify as visible-technological.

        Previously this accepted 'visible-technological OR pre-detectable'.
        That disjunction is why the stage-1 defect went unnoticed: regulatory
        damping drove capability to ~1e-9 and the stage silently classified as
        pre-detectable, contradicting manuscript 7.2 ("observability rises").
        The disjunction is removed deliberately — see lessons_learned.md 6.3.
        """
        params, y0 = get_stage("s1")
        result = integrate(params, y0)
        label, reasons = classify_regime(result, params)
        assert label == "visible-technological", (
            f"s1 classified as '{label}', expected visible-technological. Reasons: {reasons}"
        )

    def test_s2_visible_technological(self):
        """Stage 2 should classify as visible-technological."""
        params, y0 = get_stage("s2")
        result = integrate(params, y0)
        label, reasons = classify_regime(result, params)
        assert label == "visible-technological", (
            f"s2 classified as '{label}', expected visible-technological. Reasons: {reasons}"
        )

    def test_s3_visible_or_expansionist(self):
        """Stage 3 should classify as visible-technological or expansionist-visible."""
        params, y0 = get_stage("s3")
        result = integrate(params, y0)
        label, reasons = classify_regime(result, params)
        assert label in ("visible-technological", "expansionist-visible"), (
            f"s3 classified as '{label}', expected visible-technological or expansionist-visible. "
            f"Reasons: {reasons}"
        )

    def test_s4a_collapse_or_runaway(self):
        """Stage 4a (collapse) should classify as collapse-proxy or runaway."""
        params, y0 = get_stage("s4a")
        result = integrate(params, y0)
        label, reasons = classify_regime(result, params)
        assert label in ("collapse-proxy", "runaway"), (
            f"s4a classified as '{label}', expected collapse-proxy or runaway. "
            f"Reasons: {reasons}"
        )

    def test_s4b_expansionist_visible(self):
        """Stage 4b should classify as expansionist-visible."""
        params, y0 = get_stage("s4b")
        result = integrate(params, y0)
        label, reasons = classify_regime(result, params)
        assert label == "expansionist-visible", (
            f"s4b classified as '{label}', expected expansionist-visible. Reasons: {reasons}"
        )

    def test_s4c_low_observable(self):
        """Stage 4c should classify as optimized-low-observable."""
        params, y0 = get_stage("s4c")
        result = integrate(params, y0)
        label, reasons = classify_regime(result, params)
        assert label == "optimized-low-observable", (
            f"s4c classified as '{label}', expected optimized-low-observable. "
            f"Reasons: {reasons}"
        )

    def test_s5_speculative(self):
        """Stage 5 is speculative and can return any valid label."""
        params, y0 = get_stage("s5")
        result = integrate(params, y0)
        label, reasons = classify_regime(result, params)
        from model.regimes import REGIMES
        assert label in REGIMES, f"s5 returned invalid label '{label}'"

    def test_distinct_regimes(self):
        """s4a, s4c, and s1 should classify into distinct regimes."""
        labels = {}
        for key in ("s4a", "s4c", "s1"):
            params, y0 = get_stage(key)
            result = integrate(params, y0)
            label, _ = classify_regime(result, params)
            labels[key] = label

        # At minimum, s4c should be distinct from s1
        assert labels["s4c"] != labels["s1"], (
            f"s4c and s1 should have different regimes, both got '{labels['s1']}'"
        )
        # s4a and s4c should be distinct
        assert labels["s4a"] != labels["s4c"], (
            f"s4a and s4c should have different regimes, both got '{labels['s4c']}'"
        )
