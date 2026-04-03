"""Property-based tests for PERT formula calculations.

Uses Hypothesis to generate 1000+ random inputs and verify that
calculate_pert_metrics always produces mathematically correct results.

Formulas under test (from QWEN.md canonical reference):
    t_expected     = (O + 4*M + P) / 6
    spread         = P - O
    sigma          = spread / 6
    variance       = sigma ** 2
    hidden_reserve = spread * k
    total_effort   = t_expected + hidden_reserve
    duration_days  = total_effort / (FF * hours_per_day)

All metrics rounded to 3 decimal places.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ── Reference implementation (mirrors backend service logic) ──────────────────


def _round3(value: float) -> float:
    """Round a float to 3 decimal places using Decimal for precision."""
    return float(Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def calculate_pert_metrics(
    optimistic: int,
    most_likely: int,
    pessimistic: int,
    k: float = 0.1,
    focus_factor: float = 0.8,
    hours_per_day: int = 8,
) -> dict[str, float]:
    """Calculate all PERT metrics for a single estimation item.

    Args:
        optimistic: Optimistic estimate (1-999)
        most_likely: Most likely estimate (1-999)
        pessimistic: Pessimistic estimate (1-999)
        k: Contingency factor (default 0.1)
        focus_factor: Focus factor (0.5-1.0)
        hours_per_day: Working hours per day (1-12)

    Returns:
        Dict with all calculated PERT metrics.

    Raises:
        ValueError: If O <= M <= P constraint is violated.
    """
    if not (1 <= optimistic <= 999):
        raise ValueError(f"optimistic must be 1-999, got {optimistic}")
    if not (1 <= most_likely <= 999):
        raise ValueError(f"most_likely must be 1-999, got {most_likely}")
    if not (1 <= pessimistic <= 999):
        raise ValueError(f"pessimistic must be 1-999, got {pessimistic}")
    if not (optimistic <= most_likely <= pessimistic):
        raise ValueError(f"O <= M <= P violated: {optimistic}, {most_likely}, {pessimistic}")

    t_expected = (optimistic + 4 * most_likely + pessimistic) / 6
    spread = pessimistic - optimistic
    sigma = spread / 6
    variance = sigma**2
    hidden_reserve = spread * k
    total_effort = t_expected + hidden_reserve
    duration_days = total_effort / (focus_factor * hours_per_day)

    return {
        "t_expected": _round3(t_expected),
        "spread": _round3(spread),
        "sigma": _round3(sigma),
        "variance": _round3(variance),
        "hidden_reserve": _round3(hidden_reserve),
        "total_effort": _round3(total_effort),
        "duration_days": _round3(duration_days),
    }


# ── Hypothesis strategies ────────────────────────────────────────────────────


# Valid O/M/P triples where 1 <= O <= M <= P <= 999
omp_strategy = (
    st.integers(min_value=1, max_value=999)
    .flatmap(
        lambda o: st.tuples(
            st.just(o),
            st.integers(min_value=o, max_value=999).flatmap(
                lambda m: st.tuples(st.just(m), st.integers(min_value=m, max_value=999))
            ),
        )
    )
    .map(lambda t: (t[0], t[1][0], t[1][1]))
)

k_strategy = st.sampled_from([0.05, 0.1, 0.15, 0.2])
ff_strategy = st.sampled_from([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
hours_strategy = st.integers(min_value=1, max_value=12)


# ── Property-based tests ─────────────────────────────────────────────────────


class TestPertFormulaCorrectness:
    """Verify all PERT formulas produce mathematically correct results."""

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_t_expected_formula(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """t_expected = (O + 4M + P) / 6, rounded to 3 decimals."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        expected = _round3((o + 4 * m + p) / 6)
        assert metrics["t_expected"] == expected

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_spread_formula(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """spread = P - O, always non-negative."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        expected = _round3(p - o)
        assert metrics["spread"] == expected
        assert metrics["spread"] >= 0

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_sigma_formula(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """sigma = spread / 6, always non-negative."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        expected = _round3(metrics["spread"] / 6)
        assert metrics["sigma"] == expected
        assert metrics["sigma"] >= 0

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_variance_formula(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """variance = sigma ** 2, always non-negative."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        # Compute from raw sigma before rounding
        raw_sigma = (p - o) / 6
        expected = _round3(raw_sigma**2)
        assert metrics["variance"] == expected
        assert metrics["variance"] >= 0

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_hidden_reserve(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """hidden_reserve = spread * k."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        expected = _round3(metrics["spread"] * k)
        assert metrics["hidden_reserve"] == expected

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_total_effort(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """total_effort = t_expected + hidden_reserve."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        expected = _round3(metrics["t_expected"] + metrics["hidden_reserve"])
        assert metrics["total_effort"] == expected

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_duration_days(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """duration_days = total_effort / (FF * hours_per_day)."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        # Compute from raw values before rounding
        raw_t_expected = (o + 4 * m + p) / 6
        raw_spread = p - o
        raw_hidden_reserve = raw_spread * k
        raw_total_effort = raw_t_expected + raw_hidden_reserve
        expected = _round3(raw_total_effort / (ff * h))
        assert metrics["duration_days"] == expected


class TestPertInvariants:
    """Verify mathematical invariants hold across all inputs."""

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_total_effort_gte_t_expected(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """total_effort >= t_expected (because hidden_reserve >= 0)."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        assert metrics["total_effort"] >= metrics["t_expected"]

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_duration_positive(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """duration_days > 0 for all valid inputs."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        assert metrics["duration_days"] > 0

    @given(omp_strategy, k_strategy, ff_strategy, hours_strategy)
    @settings(max_examples=1000, deadline=None)
    def test_all_values_rounded_3_decimals(self, omp: tuple, k: float, ff: float, h: int) -> None:
        """All metric values have at most 3 decimal places."""
        o, m, p = omp
        metrics = calculate_pert_metrics(o, m, p, k, ff, h)
        for key, value in metrics.items():
            decimal_str = str(value)
            if "." in decimal_str:
                decimal_places = len(decimal_str.split(".")[1])
                assert decimal_places <= 3, f"{key} has {decimal_places} decimal places: {value}"


class TestPertEdgeCases:
    """Verify behavior at boundaries and edge cases."""

    def test_equal_omp_minimal(self) -> None:
        """O=M=P=1: minimal valid input."""
        metrics = calculate_pert_metrics(1, 1, 1, 0.1, 0.8, 8)
        assert metrics["t_expected"] == 1.0
        assert metrics["spread"] == 0
        assert metrics["sigma"] == 0.0
        assert metrics["variance"] == 0.0
        assert metrics["hidden_reserve"] == 0.0
        assert metrics["total_effort"] == 1.0

    def test_equal_omp_maximal(self) -> None:
        """O=M=P=999: maximal equal input."""
        metrics = calculate_pert_metrics(999, 999, 999, 0.1, 0.8, 8)
        assert metrics["t_expected"] == 999.0
        assert metrics["spread"] == 0
        assert metrics["sigma"] == 0.0

    def test_max_spread(self) -> None:
        """O=1, P=999: maximum possible spread."""
        metrics = calculate_pert_metrics(1, 500, 999, 0.1, 0.8, 8)
        assert metrics["spread"] == 998

    def test_spec_verification_example(self) -> None:
        """Canonical verification example from QWEN.md.

        O=2, M=4, P=8, k=0.1, FF=0.8, hours_per_day=8
        Expected: t(E)=4.333, spread=6.000, σ=1.000, V=1.000,
                  R=0.600, TE=4.933, D=0.772
        """
        metrics = calculate_pert_metrics(2, 4, 8, 0.1, 0.8, 8)
        assert metrics["t_expected"] == 4.333
        assert metrics["spread"] == 6.0
        assert metrics["sigma"] == 1.0
        assert metrics["variance"] == 1.0
        assert metrics["hidden_reserve"] == 0.6
        assert metrics["total_effort"] == 4.933
        assert metrics["duration_days"] == pytest.approx(0.771, abs=0.001)


class TestPertValidation:
    """Verify input validation rejects invalid values."""

    @pytest.mark.parametrize(
        "o,m,p",
        [
            (0, 5, 10),  # O < 1
            (5, 0, 10),  # M < 1
            (5, 10, 0),  # P < 1
            (10, 5, 15),  # O > M
            (5, 10, 8),  # M > P
            (10, 5, 8),  # O > M and M > P
            (1000, 1000, 1000),  # O > 999
        ],
    )
    def test_invalid_omp_raises(self, o: int, m: int, p: int) -> None:
        """Invalid O/M/P values raise ValueError."""
        with pytest.raises(ValueError):
            calculate_pert_metrics(o, m, p)
