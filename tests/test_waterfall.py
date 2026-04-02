"""
Tests for waterfall distribution calculations.

Covers LP/GP capital return, preferred return accruals,
multi-tier promote structures, and summary metrics.
"""

from datetime import date

import pytest

from app.calculations.waterfall import (
    DEFAULT_FINAL_SPLIT,
    DEFAULT_WATERFALL_TIERS,
    WaterfallTier,
    calculate_monthly_pref_rate,
    calculate_simple_waterfall,
    calculate_waterfall_distributions,
    calculate_waterfall_summary,
    extract_gp_cash_flows,
    extract_lp_cash_flows,
)


# ── Monthly Pref Rate ────────────────────────────────────────────────────────


class TestMonthlyPrefRate:
    def test_simple_monthly(self):
        """compound_monthly=True → simple annual/12."""
        result = calculate_monthly_pref_rate(0.06, compound_monthly=True)
        assert result == pytest.approx(0.005)

    def test_compound_monthly(self):
        """compound_monthly=False → (1+annual)^(1/12)-1."""
        result = calculate_monthly_pref_rate(0.06, compound_monthly=False)
        expected = (1.06) ** (1 / 12) - 1
        assert result == pytest.approx(expected, abs=1e-8)

    def test_zero_rate(self):
        assert calculate_monthly_pref_rate(0.0) == pytest.approx(0.0)


# ── Waterfall Distribution (Multi-tier) ──────────────────────────────────────


class TestWaterfallDistributions:
    @pytest.fixture
    def simple_inputs(self):
        """Simplified 5-period deal for testing waterfall mechanics."""
        # Invest $1000 total, get back cash over 5 periods
        cash_flows = [-1000.0, 0.0, 0.0, 0.0, 2000.0]
        dates = [
            date(2025, 1, 1),
            date(2025, 2, 1),
            date(2025, 3, 1),
            date(2025, 4, 1),
            date(2025, 5, 1),
        ]
        return cash_flows, dates

    def test_capital_return_first(self, simple_inputs):
        """Capital should be returned before any profit split."""
        cfs, dates = simple_inputs
        dist = calculate_waterfall_distributions(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
            lp_share=0.90,
            gp_share=0.10,
        )
        # At period 4 (big cash flow), LP should get capital back
        last = dist[4]
        assert last["lp_capital_return"] > 0
        assert last["gp_capital_return"] > 0

    def test_lp_gets_90_pct_capital(self, simple_inputs):
        """LP invested 90% → should get 90% of capital return."""
        cfs, dates = simple_inputs
        dist = calculate_waterfall_distributions(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
            lp_share=0.90,
            gp_share=0.10,
        )
        total_lp_cap = sum(d["lp_capital_return"] for d in dist)
        total_gp_cap = sum(d["gp_capital_return"] for d in dist)
        assert total_lp_cap == pytest.approx(900.0, abs=1.0)
        assert total_gp_cap == pytest.approx(100.0, abs=1.0)

    def test_total_distributions_equal_total_cf(self, simple_inputs):
        """Sum of all distributions should equal total positive cash flows."""
        cfs, dates = simple_inputs
        dist = calculate_waterfall_distributions(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
        )
        total_dist = sum(d["total_to_lp"] + d["total_to_gp"] for d in dist)
        total_positive_cf = sum(cf for cf in cfs if cf > 0)
        assert total_dist == pytest.approx(total_positive_cf, abs=1.0)

    def test_no_distributions_on_negative_cf(self, simple_inputs):
        """Negative cash flow periods should have zero distributions."""
        cfs, dates = simple_inputs
        dist = calculate_waterfall_distributions(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
        )
        assert dist[0]["total_to_lp"] == 0.0
        assert dist[0]["total_to_gp"] == 0.0

    def test_default_tiers_used(self, simple_inputs):
        """When no tiers specified, default 3-tier structure is used."""
        cfs, dates = simple_inputs
        dist = calculate_waterfall_distributions(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
        )
        # Tier distributions should include default tier names
        last = dist[4]
        assert "Hurdle I" in last["tier_distributions"]

    def test_custom_tiers(self, simple_inputs):
        """Custom tier configuration should be respected."""
        cfs, dates = simple_inputs
        custom_tier = WaterfallTier(
            name="Custom",
            pref_return=0.08,
            lp_split=0.80,
            gp_split=0.20,
            gp_promote=0.0,
        )
        dist = calculate_waterfall_distributions(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
            tiers=[custom_tier],
        )
        last = dist[4]
        assert "Custom" in last["tier_distributions"]

    def test_hurdles_alias(self, simple_inputs):
        """'hurdles' parameter should work as alias for 'tiers'."""
        cfs, dates = simple_inputs
        custom_tier = WaterfallTier(
            name="Alias",
            pref_return=0.05,
            lp_split=0.90,
            gp_split=0.10,
            gp_promote=0.0,
        )
        dist = calculate_waterfall_distributions(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
            hurdles=[custom_tier],
        )
        last = dist[4]
        assert "Alias" in last["tier_distributions"]


# ── Simple Waterfall ─────────────────────────────────────────────────────────


class TestSimpleWaterfall:
    def test_simple_waterfall_returns_distributions(self):
        cfs = [-1000.0, 500.0, 700.0]
        dates = [date(2025, 1, 1), date(2025, 2, 1), date(2025, 3, 1)]
        dist = calculate_simple_waterfall(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
        )
        assert len(dist) == 3

    def test_simple_vs_explicit_single_tier(self):
        """Simple waterfall should match explicitly setting a single tier."""
        cfs = [-1000.0, 0.0, 1500.0]
        dates = [date(2025, 1, 1), date(2025, 2, 1), date(2025, 3, 1)]
        simple = calculate_simple_waterfall(
            leveraged_cash_flows=cfs,
            dates=dates,
            total_equity=1000.0,
            pref_return=0.05,
        )
        assert len(simple) == 3
        assert simple[2]["total_to_lp"] > 0


# ── LP/GP Cash Flow Extraction ───────────────────────────────────────────────


class TestExtractCashFlows:
    def test_lp_first_period_negative(self):
        """LP period 0 should be: -lp_equity + distribution."""
        dist = [
            {"total_to_lp": 0.0, "total_to_gp": 0.0},
            {"total_to_lp": 500.0, "total_to_gp": 100.0},
        ]
        lp_cf = extract_lp_cash_flows(dist, lp_equity=900.0)
        assert lp_cf[0] == pytest.approx(-900.0)
        assert lp_cf[1] == pytest.approx(500.0)

    def test_gp_first_period_negative(self):
        dist = [
            {"total_to_lp": 0.0, "total_to_gp": 0.0},
            {"total_to_lp": 500.0, "total_to_gp": 200.0},
        ]
        gp_cf = extract_gp_cash_flows(dist, gp_equity=100.0)
        assert gp_cf[0] == pytest.approx(-100.0)
        assert gp_cf[1] == pytest.approx(200.0)


# ── Waterfall Summary ────────────────────────────────────────────────────────


class TestWaterfallSummary:
    def test_summary_totals(self):
        dist = [
            {
                "total_to_lp": 100.0,
                "total_to_gp": 20.0,
                "lp_capital_return": 90.0,
                "gp_capital_return": 10.0,
                "lp_preferred_return": 5.0,
                "gp_preferred_return": 2.0,
                "lp_profit_share": 5.0,
                "gp_profit_share": 3.0,
                "gp_promote": 5.0,
            },
            {
                "total_to_lp": 200.0,
                "total_to_gp": 50.0,
                "lp_capital_return": 0.0,
                "gp_capital_return": 0.0,
                "lp_preferred_return": 50.0,
                "gp_preferred_return": 10.0,
                "lp_profit_share": 150.0,
                "gp_profit_share": 20.0,
                "gp_promote": 20.0,
            },
        ]
        summary = calculate_waterfall_summary(dist)
        assert summary["total_to_lp"] == pytest.approx(300.0)
        assert summary["total_to_gp"] == pytest.approx(70.0)
        assert summary["total_lp_capital_return"] == pytest.approx(90.0)
        assert summary["total_gp_promote"] == pytest.approx(25.0)


# ── Default Constants ────────────────────────────────────────────────────────


class TestDefaults:
    def test_default_tiers_count(self):
        assert len(DEFAULT_WATERFALL_TIERS) == 3

    def test_default_hurdle_i_no_promote(self):
        assert DEFAULT_WATERFALL_TIERS[0].gp_promote == 0.0

    def test_default_final_split_sums_near_one(self):
        total = (
            DEFAULT_FINAL_SPLIT.lp_split
            + DEFAULT_FINAL_SPLIT.gp_split
            + DEFAULT_FINAL_SPLIT.gp_promote
        )
        assert total == pytest.approx(1.0, abs=0.001)
