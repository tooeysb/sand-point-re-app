"""
Tests for loan amortization calculations.

Verifies PMT, remaining balance, amortization schedules, DSCR,
and loan constants against known Excel values.
"""

from datetime import date

import pytest

from app.calculations.amortization import (
    calculate_debt_service,
    calculate_dscr,
    calculate_loan_constant,
    calculate_payment,
    calculate_remaining_balance,
    calculate_total_interest,
    generate_amortization_schedule,
)


# ── Monthly Payment (PMT) ────────────────────────────────────────────────────


class TestCalculatePayment:
    def test_standard_30yr_mortgage(self):
        """$500K at 5% for 30 years → ~$2,684.11/month (Excel PMT)."""
        result = calculate_payment(500000.0, 0.05, 360)
        assert result == pytest.approx(2684.11, abs=0.50)

    def test_zero_rate_loan(self):
        """0% interest → principal / months."""
        result = calculate_payment(120000.0, 0.0, 360)
        assert result == pytest.approx(120000.0 / 360, abs=0.01)

    def test_zero_principal(self):
        assert calculate_payment(0.0, 0.05, 360) == 0.0

    def test_zero_term(self):
        assert calculate_payment(100000.0, 0.05, 0) == 0.0

    def test_high_rate_short_term(self):
        """$100K at 12% for 12 months → ~$8,884.88."""
        result = calculate_payment(100000.0, 0.12, 12)
        assert result == pytest.approx(8884.88, abs=1.0)

    def test_commercial_loan(self):
        """$25M at 5.25% for 30 years (360 months)."""
        result = calculate_payment(25000.0, 0.0525, 360)
        # Excel PMT(0.0525/12, 360, -25000) ≈ 138.05
        assert result == pytest.approx(138.05, abs=1.0)


# ── Remaining Balance ────────────────────────────────────────────────────────


class TestCalculateRemainingBalance:
    def test_no_payments_made(self):
        result = calculate_remaining_balance(500000.0, 0.05, 360, 0)
        assert result == pytest.approx(500000.0, abs=0.01)

    def test_fully_paid(self):
        result = calculate_remaining_balance(500000.0, 0.05, 360, 360)
        assert result == pytest.approx(0.0, abs=1.0)

    def test_halfway_through(self):
        """After 180 payments on a 30yr, balance should be ~72% of original."""
        result = calculate_remaining_balance(500000.0, 0.05, 360, 180)
        assert 300000 < result < 400000

    def test_zero_rate(self):
        result = calculate_remaining_balance(120000.0, 0.0, 12, 6)
        assert result == pytest.approx(60000.0, abs=0.01)


# ── Amortization Schedule ────────────────────────────────────────────────────


class TestGenerateAmortizationSchedule:
    def test_schedule_length(self):
        """Schedule should have total_months rows (or less if paid off early)."""
        schedule = generate_amortization_schedule(
            principal=100000.0,
            annual_rate=0.05,
            amortization_months=360,
            total_months=12,
            start_date=date(2025, 1, 1),
        )
        assert len(schedule) == 12

    def test_first_period_interest(self):
        """First month interest = principal * monthly_rate."""
        schedule = generate_amortization_schedule(
            principal=100000.0,
            annual_rate=0.06,
            amortization_months=360,
            total_months=1,
            start_date=date(2025, 1, 1),
        )
        assert schedule[0]["interest"] == pytest.approx(100000.0 * 0.06 / 12, abs=0.01)

    def test_io_period(self):
        """During I/O period, principal payment should be 0."""
        schedule = generate_amortization_schedule(
            principal=100000.0,
            annual_rate=0.05,
            amortization_months=360,
            io_months=12,
            total_months=24,
            start_date=date(2025, 1, 1),
        )
        # First 12 months should be I/O
        for i in range(12):
            assert schedule[i]["principal"] == 0.0
        # Month 13 should start amortizing
        assert schedule[12]["principal"] > 0

    def test_balance_decreases(self):
        """Ending balance should decrease each period during amortization."""
        schedule = generate_amortization_schedule(
            principal=100000.0,
            annual_rate=0.05,
            amortization_months=360,
            total_months=12,
            start_date=date(2025, 1, 1),
        )
        for i in range(1, len(schedule)):
            assert schedule[i]["ending_balance"] < schedule[i - 1]["ending_balance"]

    def test_payment_equals_interest_plus_principal(self):
        """payment = interest + principal for every row."""
        schedule = generate_amortization_schedule(
            principal=100000.0,
            annual_rate=0.05,
            amortization_months=360,
            total_months=12,
            start_date=date(2025, 1, 1),
        )
        for row in schedule:
            assert row["payment"] == pytest.approx(row["interest"] + row["principal"], abs=0.02)

    def test_io_balance_stays_flat(self):
        """During I/O, ending balance should equal beginning balance."""
        schedule = generate_amortization_schedule(
            principal=100000.0,
            annual_rate=0.05,
            amortization_months=360,
            io_months=12,
            total_months=12,
            start_date=date(2025, 1, 1),
        )
        for row in schedule:
            assert row["ending_balance"] == pytest.approx(row["beginning_balance"], abs=0.01)


# ── Total Interest ───────────────────────────────────────────────────────────


class TestCalculateTotalInterest:
    def test_total_interest(self):
        schedule = generate_amortization_schedule(
            principal=100000.0,
            annual_rate=0.06,
            amortization_months=360,
            total_months=12,
            start_date=date(2025, 1, 1),
        )
        total = calculate_total_interest(schedule)
        # ~$6K for first year of $100K at 6%
        assert 5900 < total < 6100


# ── Debt Service ─────────────────────────────────────────────────────────────


class TestCalculateDebtService:
    def test_debt_service_range(self):
        schedule = generate_amortization_schedule(
            principal=100000.0,
            annual_rate=0.06,
            amortization_months=360,
            total_months=12,
            start_date=date(2025, 1, 1),
        )
        ds = calculate_debt_service(schedule, 1, 12)
        # 12 months × ~$599.55 = ~$7195
        assert ds == pytest.approx(7194.6, abs=10.0)


# ── DSCR ─────────────────────────────────────────────────────────────────────


class TestCalculateDSCR:
    def test_healthy_dscr(self):
        assert calculate_dscr(1500.0, 1000.0) == pytest.approx(1.5)

    def test_break_even_dscr(self):
        assert calculate_dscr(1000.0, 1000.0) == pytest.approx(1.0)

    def test_zero_debt_service(self):
        assert calculate_dscr(1000.0, 0.0) == float("inf")

    def test_under_coverage(self):
        assert calculate_dscr(800.0, 1000.0) == pytest.approx(0.8)


# ── Loan Constant ────────────────────────────────────────────────────────────


class TestCalculateLoanConstant:
    def test_loan_constant(self):
        """Loan constant for $500K at 5% over 30 years."""
        result = calculate_loan_constant(500000.0, 0.05, 30)
        # Annual payment / principal
        monthly = calculate_payment(500000.0, 0.05, 360)
        expected = (monthly * 12) / 500000.0
        assert result == pytest.approx(expected, abs=1e-6)

    def test_zero_principal(self):
        assert calculate_loan_constant(0.0, 0.05, 30) == 0.0
