"""
Tests for IRR and NPV calculations.

Verifies Newton-Raphson IRR, XIRR, NPV, equity multiples,
and edge cases. Expected values cross-checked against Excel.
"""

from datetime import date

import pytest

from app.calculations.irr import (
    annual_to_monthly_irr,
    calculate_irr,
    calculate_multiple,
    calculate_npv,
    calculate_profit,
    calculate_xirr,
    calculate_xnpv,
    monthly_to_annual_irr,
)


# ── NPV ──────────────────────────────────────────────────────────────────────


class TestCalculateNPV:
    def test_simple_npv(self):
        """NPV of [-1000, 500, 600] at 10% should match hand calc."""
        cfs = [-1000.0, 500.0, 600.0]
        result = calculate_npv(cfs, 0.10)
        # -1000 + 500/1.1 + 600/1.21 = -1000 + 454.545 + 495.868 = -49.587
        assert result == pytest.approx(-49.5868, rel=1e-3)

    def test_npv_zero_rate(self):
        """At 0% discount, NPV equals the simple sum."""
        cfs = [-100.0, 50.0, 60.0]
        assert calculate_npv(cfs, 0.0) == pytest.approx(10.0)

    def test_npv_single_cashflow(self):
        """NPV of a single cash flow is just that cash flow."""
        assert calculate_npv([500.0], 0.10) == pytest.approx(500.0)

    def test_npv_all_positive(self):
        """NPV with all positive cash flows is always positive."""
        cfs = [100.0, 200.0, 300.0]
        assert calculate_npv(cfs, 0.05) > 0

    def test_npv_high_discount_rate(self):
        """At very high discount rate, future cash flows approach zero."""
        cfs = [-1000.0, 500.0, 500.0, 500.0]
        result = calculate_npv(cfs, 100.0)
        # At 10000% discount rate, future CFs are negligible
        assert result < 0


# ── IRR ──────────────────────────────────────────────────────────────────────


class TestCalculateIRR:
    def test_known_irr_simple(self):
        """IRR of [-1000, 1100] should be 10%."""
        cfs = [-1000.0, 1100.0]
        assert calculate_irr(cfs) == pytest.approx(0.10, abs=1e-5)

    def test_known_irr_multi_period(self):
        """IRR of [-1000, 300, 400, 500] ~ 9.265%."""
        cfs = [-1000.0, 300.0, 400.0, 500.0]
        result = calculate_irr(cfs)
        assert result == pytest.approx(0.09265, abs=1e-3)

    def test_irr_matches_excel(self):
        """Classic Excel IRR example: invest 10000, receive 2000/yr for 7 years."""
        cfs = [-10000.0] + [2000.0] * 7
        result = calculate_irr(cfs)
        # Excel IRR gives ~9.20%
        assert result == pytest.approx(0.0920, abs=1e-3)

    def test_irr_zero_npv_verification(self):
        """At the IRR, NPV should be approximately zero."""
        cfs = [-5000.0, 1500.0, 2000.0, 2500.0]
        rate = calculate_irr(cfs)
        npv = calculate_npv(cfs, rate)
        assert abs(npv) < 0.01

    def test_irr_requires_two_cashflows(self):
        with pytest.raises(ValueError, match="At least 2"):
            calculate_irr([100.0])

    def test_irr_requires_mixed_signs(self):
        with pytest.raises(ValueError, match="positive and negative"):
            calculate_irr([100.0, 200.0])

    def test_irr_all_negative(self):
        with pytest.raises(ValueError, match="positive and negative"):
            calculate_irr([-100.0, -200.0])

    def test_irr_with_custom_guess(self):
        """Should converge with a different initial guess."""
        cfs = [-1000.0, 500.0, 600.0, 200.0]
        result = calculate_irr(cfs, guess=0.05)
        assert result == pytest.approx(calculate_irr(cfs, guess=0.20), abs=1e-5)


# ── XNPV ─────────────────────────────────────────────────────────────────────


class TestCalculateXNPV:
    def test_xnpv_one_year(self):
        """XNPV of [-1000 today, 1100 in one year] at 10%."""
        cfs = [-1000.0, 1100.0]
        dates = [date(2025, 1, 1), date(2026, 1, 1)]
        result = calculate_xnpv(cfs, dates, 0.10)
        # -1000 + 1100/1.10^(365/365) = -1000 + 1000 = 0
        assert result == pytest.approx(0.0, abs=1.0)

    def test_xnpv_mismatched_lengths(self):
        with pytest.raises(ValueError, match="same length"):
            calculate_xnpv([100.0], [date(2025, 1, 1), date(2025, 6, 1)], 0.10)


# ── XIRR ─────────────────────────────────────────────────────────────────────


class TestCalculateXIRR:
    def test_xirr_annual_cashflows(self):
        """XIRR with annual cash flows should match IRR."""
        cfs = [-10000.0, 3000.0, 4000.0, 5000.0]
        dates = [
            date(2025, 1, 1),
            date(2026, 1, 1),
            date(2027, 1, 1),
            date(2028, 1, 1),
        ]
        result = calculate_xirr(cfs, dates)
        assert result == pytest.approx(0.0965, abs=0.01)

    def test_xirr_irregular_dates(self):
        """XIRR with irregular dates."""
        cfs = [-10000.0, 5000.0, 7000.0]
        dates = [
            date(2025, 1, 1),
            date(2025, 7, 1),
            date(2026, 1, 1),
        ]
        result = calculate_xirr(cfs, dates)
        assert result > 0.15  # Should be a high return (fast payback)

    def test_xirr_requires_two_cashflows(self):
        with pytest.raises(ValueError, match="At least 2"):
            calculate_xirr([100.0], [date(2025, 1, 1)])

    def test_xirr_requires_mixed_signs(self):
        with pytest.raises(ValueError, match="positive and negative"):
            calculate_xirr(
                [100.0, 200.0],
                [date(2025, 1, 1), date(2026, 1, 1)],
            )

    def test_xirr_mismatched_lengths(self):
        with pytest.raises(ValueError, match="same length"):
            calculate_xirr(
                [-100.0, 200.0, 300.0],
                [date(2025, 1, 1), date(2026, 1, 1)],
            )

    def test_xirr_real_estate_example(self):
        """Typical RE deal: buy at -41.5M, monthly income, sell at exit."""
        # Simplified 3-year hold with annual cash flows
        cfs = [-41500.0, 2500.0, 2600.0, 55000.0]
        dates = [
            date(2025, 1, 1),
            date(2026, 1, 1),
            date(2027, 1, 1),
            date(2028, 1, 1),
        ]
        result = calculate_xirr(cfs, dates)
        assert 0.05 < result < 0.30


# ── Equity Multiple ──────────────────────────────────────────────────────────


class TestCalculateMultiple:
    def test_double_your_money(self):
        """Invest 100, get back 200 → 2.0x."""
        assert calculate_multiple([-100.0, 200.0]) == pytest.approx(2.0)

    def test_multiple_with_interim(self):
        """Multiple with interim cash flows."""
        cfs = [-1000.0, 200.0, 300.0, 1500.0]
        result = calculate_multiple(cfs)
        assert result == pytest.approx(2.0)

    def test_no_outflows(self):
        with pytest.raises(ValueError, match="No investment"):
            calculate_multiple([100.0, 200.0])


# ── Profit ───────────────────────────────────────────────────────────────────


class TestCalculateProfit:
    def test_profit(self):
        assert calculate_profit([-1000.0, 500.0, 600.0]) == pytest.approx(100.0)

    def test_profit_loss(self):
        assert calculate_profit([-1000.0, 400.0]) == pytest.approx(-600.0)


# ── IRR Conversion ───────────────────────────────────────────────────────────


class TestIRRConversion:
    def test_monthly_to_annual_roundtrip(self):
        annual = 0.12
        monthly = annual_to_monthly_irr(annual)
        recovered = monthly_to_annual_irr(monthly)
        assert recovered == pytest.approx(annual, abs=1e-10)

    def test_monthly_to_annual_value(self):
        """1% monthly → ~12.68% annual (compounded)."""
        result = monthly_to_annual_irr(0.01)
        assert result == pytest.approx(0.126825, abs=1e-4)

    def test_annual_to_monthly_value(self):
        """12% annual → ~0.949% monthly."""
        result = annual_to_monthly_irr(0.12)
        assert result == pytest.approx(0.00949, abs=1e-4)
