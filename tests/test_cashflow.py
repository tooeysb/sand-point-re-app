"""
Tests for cash flow calculations.

Covers tenant rent, escalation factors, NNN reimbursements,
lease commissions, TI costs, and the full cash flow generator.
"""

from datetime import date

import pytest

from app.calculations.cashflow import (
    Tenant,
    annualize_cash_flows,
    calculate_days_in_month,
    calculate_escalation_factor,
    calculate_expense_escalation,
    calculate_lease_commission,
    calculate_property_tax_escalation,
    calculate_rent_escalation,
    calculate_tenant_rent,
    calculate_tenant_rent_detailed,
    calculate_ti_cost,
    calculate_total_tenant_rent,
    generate_cash_flows,
    generate_monthly_dates,
    sum_cash_flows,
)


# ── Helper: Standard tenant fixture ──────────────────────────────────────────


def _base_tenant(**overrides) -> Tenant:
    defaults = dict(
        name="Test Tenant",
        rsf=10000.0,
        in_place_rent_psf=50.0,
        market_rent_psf=55.0,
        lease_end_month=60,
        apply_rollover_costs=True,
        free_rent_months=6,
        ti_buildout_months=6,
        lc_percent_years_1_5=0.06,
        lc_percent_years_6_plus=0.03,
        new_lease_term_years=10,
        ti_allowance_psf=25.0,
    )
    defaults.update(overrides)
    return Tenant(**defaults)


# ── Rent Escalation ──────────────────────────────────────────────────────────


class TestRentEscalation:
    def test_period_zero(self):
        assert calculate_rent_escalation(0.025, 0) == pytest.approx(1.0)

    def test_monthly_compounding(self):
        """After 12 months at 2.5%, should be ~1.02529 (monthly compounding)."""
        result = calculate_rent_escalation(0.025, 12)
        assert result == pytest.approx(1.025288, abs=1e-4)

    def test_zero_rate(self):
        assert calculate_rent_escalation(0.0, 120) == pytest.approx(1.0)


class TestExpenseEscalation:
    def test_period_zero(self):
        assert calculate_expense_escalation(0.025, 0) == pytest.approx(1.0)

    def test_after_12_months(self):
        """After 12 months at 2.5% annual, should be exactly 1.025."""
        result = calculate_expense_escalation(0.025, 12)
        assert result == pytest.approx(1.025, abs=1e-6)

    def test_after_24_months(self):
        result = calculate_expense_escalation(0.025, 24)
        assert result == pytest.approx(1.025**2, abs=1e-6)


class TestPropertyTaxEscalation:
    def test_period_zero(self):
        assert calculate_property_tax_escalation(0.025, 0) == pytest.approx(1.0)

    def test_year_1_flat(self):
        """Months 1-12 should all be 1.0 (no escalation in Year 1)."""
        for m in range(1, 13):
            assert calculate_property_tax_escalation(0.025, m) == pytest.approx(1.0)

    def test_year_2_step(self):
        """Month 13 should step up to 1.025."""
        assert calculate_property_tax_escalation(0.025, 13) == pytest.approx(1.025)

    def test_year_2_flat_through(self):
        """Months 13-24 should all be 1.025."""
        for m in range(13, 25):
            assert calculate_property_tax_escalation(0.025, m) == pytest.approx(1.025)

    def test_year_10(self):
        """Month 120 should be Year 10 = (1.025)^9."""
        result = calculate_property_tax_escalation(0.025, 120)
        assert result == pytest.approx(1.025**9, abs=1e-6)


class TestEscalationFactorLegacy:
    def test_monthly_default(self):
        result = calculate_escalation_factor(0.025, 12, "monthly")
        assert result == pytest.approx(calculate_rent_escalation(0.025, 12))

    def test_annual_step(self):
        result = calculate_escalation_factor(0.025, 12, "annual")
        assert result == pytest.approx(1.0)  # Year 0 still
        result = calculate_escalation_factor(0.025, 24, "annual")
        assert result == pytest.approx(1.025**2)


# ── Tenant Rent Calculations ─────────────────────────────────────────────────


class TestTenantRent:
    def test_in_place_rent_period_1(self):
        """Month 1 in-place rent = RSF * in_place_psf * escalation / 12 / 1000."""
        tenant = _base_tenant()
        result = calculate_tenant_rent(tenant, 1, 0.025)
        # 10000 * 50 * (1+0.025/12)^1 / 12 / 1000
        esc = (1 + 0.025 / 12) ** 1
        expected = 10000 * 50 * esc / 12 / 1000
        assert result == pytest.approx(expected, abs=0.01)

    def test_rent_after_rollover_during_ti_buildout(self):
        """During TI buildout after lease expiry, rent should be 0."""
        tenant = _base_tenant(lease_end_month=10, ti_buildout_months=6)
        # Month 11 = rollover, TI buildout months 11-16
        result = calculate_tenant_rent(tenant, 11, 0.025)
        assert result == pytest.approx(0.0)

    def test_rent_after_rollover_during_free_rent(self):
        """During free rent after TI buildout, net rent = 0 (gross - deduction)."""
        tenant = _base_tenant(lease_end_month=10, ti_buildout_months=3, free_rent_months=3)
        # Rollover at 11, TI buildout 11-13, free rent 14-16
        gross, deduction = calculate_tenant_rent_detailed(tenant, 14, 0.025)
        assert deduction == pytest.approx(-gross, abs=0.01)

    def test_rent_after_rollover_paying(self):
        """After TI + free rent, tenant pays at market rate."""
        tenant = _base_tenant(
            lease_end_month=10,
            ti_buildout_months=3,
            free_rent_months=3,
        )
        # Rollover at 11, TI 11-13, free 14-16, paying from 17+
        result = calculate_tenant_rent(tenant, 17, 0.025)
        assert result > 0

    def test_no_rollover_costs_flag(self):
        """With apply_rollover_costs=False, immediate transition to market rent."""
        tenant = _base_tenant(
            lease_end_month=10,
            apply_rollover_costs=False,
        )
        result = calculate_tenant_rent(tenant, 11, 0.025)
        assert result > 0  # Immediate market rent, no TI gap

    def test_in_place_free_rent(self):
        """Free rent during in-place lease."""
        tenant = _base_tenant(free_rent_start_month=5, free_rent_months=3)
        # Months 5, 6, 7 should have net rent = 0
        result = calculate_tenant_rent(tenant, 5, 0.025)
        assert result == pytest.approx(0.0, abs=0.01)


class TestTotalTenantRent:
    def test_sum_of_tenants(self):
        t1 = _base_tenant(name="A", rsf=5000, in_place_rent_psf=40, lease_end_month=120)
        t2 = _base_tenant(name="B", rsf=5000, in_place_rent_psf=50, lease_end_month=120)
        total = calculate_total_tenant_rent([t1, t2], 1, 0.025)
        assert total == pytest.approx(
            calculate_tenant_rent(t1, 1, 0.025) + calculate_tenant_rent(t2, 1, 0.025),
            abs=0.01,
        )


# ── Lease Commission ─────────────────────────────────────────────────────────


class TestLeaseCommission:
    def test_no_rollover_costs(self):
        tenant = _base_tenant(apply_rollover_costs=False)
        assert calculate_lease_commission(tenant, 0.025, 61) == pytest.approx(0.0)

    def test_lc_positive(self):
        tenant = _base_tenant()
        result = calculate_lease_commission(tenant, 0.025, 61)
        assert result > 0

    def test_lc_uses_market_rent(self):
        """LC should be based on market rent, not in-place."""
        t_low = _base_tenant(market_rent_psf=40.0)
        t_high = _base_tenant(market_rent_psf=80.0)
        lc_low = calculate_lease_commission(t_low, 0.025, 61)
        lc_high = calculate_lease_commission(t_high, 0.025, 61)
        assert lc_high > lc_low


# ── TI Cost ──────────────────────────────────────────────────────────────────


class TestTICost:
    def test_no_rollover_costs(self):
        tenant = _base_tenant(apply_rollover_costs=False)
        assert calculate_ti_cost(tenant, 0.025, 61) == pytest.approx(0.0)

    def test_ti_cost_positive(self):
        tenant = _base_tenant(ti_allowance_psf=25.0)
        result = calculate_ti_cost(tenant, 0.025, 61)
        assert result > 0

    def test_ti_scales_with_rsf(self):
        t_small = _base_tenant(rsf=5000, ti_allowance_psf=25.0)
        t_large = _base_tenant(rsf=10000, ti_allowance_psf=25.0)
        assert calculate_ti_cost(t_large, 0.025, 61) == pytest.approx(
            2 * calculate_ti_cost(t_small, 0.025, 61), abs=0.1
        )


# ── Date Helpers ─────────────────────────────────────────────────────────────


class TestDateHelpers:
    def test_generate_monthly_dates(self):
        dates = generate_monthly_dates(date(2025, 1, 1), 3)
        assert len(dates) == 4  # 0,1,2,3
        assert dates[0] == date(2025, 1, 1)
        assert dates[3] == date(2025, 4, 1)

    def test_days_in_february(self):
        assert calculate_days_in_month(date(2025, 2, 1)) == 28

    def test_days_in_leap_february(self):
        assert calculate_days_in_month(date(2024, 2, 1)) == 29

    def test_days_in_january(self):
        assert calculate_days_in_month(date(2025, 1, 1)) == 31


# ── Full Cash Flow Generator ─────────────────────────────────────────────────


class TestGenerateCashFlows:
    @pytest.fixture
    def base_params(self):
        return dict(
            acquisition_date=date(2025, 1, 1),
            hold_period_months=12,
            purchase_price=10000.0,  # $10M (in $000s)
            closing_costs=200.0,
            total_sf=10000.0,
            in_place_rent_psf=50.0,
            market_rent_psf=55.0,
            rent_growth=0.025,
            vacancy_rate=0.05,
            fixed_opex_psf=10.0,
            management_fee_percent=0.04,
            property_tax_amount=100.0,
            capex_reserve_psf=2.0,
            expense_growth=0.025,
            exit_cap_rate=0.05,
            sales_cost_percent=0.01,
        )

    def test_output_length(self, base_params):
        cfs = generate_cash_flows(**base_params)
        assert len(cfs) == 13  # 0 through 12

    def test_month_zero_acquisition(self, base_params):
        cfs = generate_cash_flows(**base_params)
        assert cfs[0]["acquisition_costs"] == 10200.0  # purchase + closing

    def test_month_zero_no_revenue(self, base_params):
        cfs = generate_cash_flows(**base_params)
        assert cfs[0]["base_rent"] == 0.0

    def test_exit_period_has_proceeds(self, base_params):
        cfs = generate_cash_flows(**base_params)
        assert cfs[-1]["exit_proceeds"] > 0

    def test_no_loan_no_debt_service(self, base_params):
        cfs = generate_cash_flows(**base_params)
        for cf in cfs:
            assert cf["debt_service"] == 0.0

    def test_with_loan(self, base_params):
        base_params["loan_amount"] = 7000.0
        base_params["interest_rate"] = 0.05
        cfs = generate_cash_flows(**base_params)
        assert cfs[1]["debt_service"] > 0
        assert cfs[-1]["loan_payoff"] > 0

    def test_unleveraged_cf_month0(self, base_params):
        """Month 0 unleveraged CF = -acquisition_costs + noi(0) + exit_proceeds(0)."""
        cfs = generate_cash_flows(**base_params)
        assert cfs[0]["unleveraged_cash_flow"] == pytest.approx(-10200.0, abs=1.0)

    def test_noi_positive_during_hold(self, base_params):
        """NOI should be positive during operating months."""
        cfs = generate_cash_flows(**base_params)
        for cf in cfs[1:-1]:
            assert cf["noi"] > 0

    def test_nnn_reimbursement(self, base_params):
        """NNN lease should include reimbursement revenue."""
        base_params["nnn_lease"] = True
        cfs = generate_cash_flows(**base_params)
        assert cfs[1]["reimbursement_revenue"] > 0

    def test_no_nnn(self, base_params):
        """Non-NNN lease should have zero reimbursements."""
        base_params["nnn_lease"] = False
        cfs = generate_cash_flows(**base_params)
        assert cfs[1]["reimbursement_revenue"] == 0.0


# ── Annualize Cash Flows ─────────────────────────────────────────────────────


class TestAnnualizeCashFlows:
    def test_annualize_basic(self):
        monthly = [
            {"period": i, "potential_revenue": 100.0, "effective_revenue": 95.0,
             "total_expenses": 50.0, "noi": 45.0, "debt_service": 10.0,
             "unleveraged_cash_flow": 35.0, "leveraged_cash_flow": 25.0}
            for i in range(13)
        ]
        annual = annualize_cash_flows(monthly)
        assert len(annual) >= 1
        # Year 1 = periods 0-11
        assert annual[0]["year"] == 1


# ── Sum Cash Flows ───────────────────────────────────────────────────────────


class TestSumCashFlows:
    def test_sum_field(self):
        cfs = [
            {"period": 0, "noi": 10.0},
            {"period": 1, "noi": 20.0},
            {"period": 2, "noi": 30.0},
        ]
        assert sum_cash_flows(cfs, "noi") == pytest.approx(60.0)

    def test_sum_range(self):
        cfs = [
            {"period": 0, "noi": 10.0},
            {"period": 1, "noi": 20.0},
            {"period": 2, "noi": 30.0},
        ]
        assert sum_cash_flows(cfs, "noi", 1, 2) == pytest.approx(50.0)

    def test_sum_missing_field(self):
        cfs = [{"period": 0}, {"period": 1}]
        assert sum_cash_flows(cfs, "noi") == pytest.approx(0.0)
