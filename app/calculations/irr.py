"""
IRR and NPV Calculations

Implements IRR using Newton-Raphson method, matching Excel's IRR/XIRR functions.
"""

from typing import List, Optional
from datetime import date
import numpy as np

MAX_ITERATIONS = 100
TOLERANCE = 1e-7
DEFAULT_GUESS = 0.1


def calculate_npv(cash_flows: List[float], discount_rate: float) -> float:
    """
    Calculate NPV (Net Present Value) of cash flows.

    Args:
        cash_flows: Array of cash flows (negative = outflow, positive = inflow)
        discount_rate: Annual discount rate (e.g., 0.10 for 10%)

    Returns:
        NPV value
    """
    npv = 0.0
    for period, cf in enumerate(cash_flows):
        npv += cf / ((1 + discount_rate) ** period)
    return npv


def _npv_derivative(cash_flows: List[float], rate: float) -> float:
    """Calculate derivative of NPV with respect to rate (for Newton-Raphson)."""
    dnpv = 0.0
    for period, cf in enumerate(cash_flows):
        dnpv -= (period * cf) / ((1 + rate) ** (period + 1))
    return dnpv


def calculate_irr(cash_flows: List[float], guess: float = DEFAULT_GUESS) -> float:
    """
    Calculate IRR (Internal Rate of Return) using Newton-Raphson method.

    Matches Excel's IRR() function behavior for periodic cash flows.

    Args:
        cash_flows: Array of periodic cash flows
        guess: Initial guess for rate (default 0.1 = 10%)

    Returns:
        Annual IRR as decimal (e.g., 0.15 for 15%)

    Raises:
        ValueError: If IRR cannot be calculated
    """
    if len(cash_flows) < 2:
        raise ValueError("At least 2 cash flows required")

    has_positive = any(cf > 0 for cf in cash_flows)
    has_negative = any(cf < 0 for cf in cash_flows)

    if not has_positive or not has_negative:
        raise ValueError("Cash flows must contain both positive and negative values")

    rate = guess

    for _ in range(MAX_ITERATIONS):
        npv = calculate_npv(cash_flows, rate)
        dnpv = _npv_derivative(cash_flows, rate)

        if abs(dnpv) < TOLERANCE:
            raise ValueError("IRR calculation failed: derivative too small")

        new_rate = rate - npv / dnpv

        if abs(new_rate - rate) < TOLERANCE:
            return new_rate

        rate = new_rate

    raise ValueError("IRR calculation did not converge")


def _days_between(date1: date, date2: date) -> int:
    """Calculate the number of days between two dates."""
    delta = date2 - date1
    return delta.days


def calculate_xnpv(
    cash_flows: List[float], dates: List[date], discount_rate: float
) -> float:
    """Calculate XNPV (NPV with specific dates)."""
    if len(cash_flows) != len(dates):
        raise ValueError("Cash flows and dates arrays must have same length")

    base_date = dates[0]
    xnpv = 0.0

    for i, cf in enumerate(cash_flows):
        days = _days_between(base_date, dates[i])
        years = days / 365.0
        xnpv += cf / ((1 + discount_rate) ** years)

    return xnpv


def _xnpv_derivative(
    cash_flows: List[float], dates: List[date], rate: float
) -> float:
    """Calculate derivative of XNPV with respect to rate."""
    base_date = dates[0]
    dxnpv = 0.0

    for i, cf in enumerate(cash_flows):
        days = _days_between(base_date, dates[i])
        years = days / 365.0
        dxnpv -= (years * cf) / ((1 + rate) ** (years + 1))

    return dxnpv


def _try_xirr_with_guess(
    cash_flows: List[float], dates: List[date], guess: float
) -> Optional[float]:
    """
    Try to calculate XIRR with a specific initial guess.

    Returns the rate if successful, None if it fails.
    """
    rate = guess

    for _ in range(MAX_ITERATIONS):
        try:
            xnpv = calculate_xnpv(cash_flows, dates, rate)
            dxnpv = _xnpv_derivative(cash_flows, dates, rate)

            # Skip if derivative is too small
            if abs(dxnpv) < TOLERANCE:
                return None

            new_rate = rate - xnpv / dxnpv

            # Check for convergence
            if abs(new_rate - rate) < TOLERANCE:
                # Validate the result is reasonable (-100% to 1000%)
                if -1.0 < new_rate < 10.0:
                    return new_rate
                return None

            # Prevent rate from going too extreme
            if new_rate < -0.99:
                new_rate = -0.99
            elif new_rate > 10.0:
                new_rate = 10.0

            rate = new_rate
        except (ZeroDivisionError, OverflowError):
            return None

    return None


def calculate_xirr(
    cash_flows: List[float], dates: List[date], guess: float = DEFAULT_GUESS
) -> float:
    """
    Calculate XIRR (IRR with specific dates).

    Matches Excel's XIRR() function behavior for irregular cash flows.
    Uses multiple initial guesses to improve robustness.

    Args:
        cash_flows: Array of cash flows
        dates: Array of dates corresponding to each cash flow
        guess: Initial guess for rate (default 0.1 = 10%)

    Returns:
        Annual IRR as decimal

    Raises:
        ValueError: If XIRR cannot be calculated
    """
    if len(cash_flows) != len(dates):
        raise ValueError("Cash flows and dates arrays must have same length")

    if len(cash_flows) < 2:
        raise ValueError("At least 2 cash flows required")

    has_positive = any(cf > 0 for cf in cash_flows)
    has_negative = any(cf < 0 for cf in cash_flows)

    if not has_positive or not has_negative:
        raise ValueError("Cash flows must contain both positive and negative values")

    # Try multiple guesses to find a solution
    guesses = [guess, 0.05, 0.1, 0.15, 0.2, 0.01, -0.05, 0.3, 0.5]

    for g in guesses:
        result = _try_xirr_with_guess(cash_flows, dates, g)
        if result is not None:
            return result

    # If all guesses failed, try a bisection approach
    # Find a bracket where XNPV changes sign
    low, high = -0.99, 1.0
    xnpv_low = calculate_xnpv(cash_flows, dates, low)
    xnpv_high = calculate_xnpv(cash_flows, dates, high)

    if xnpv_low * xnpv_high > 0:
        # Try expanding the bracket
        for h in [2.0, 5.0, 10.0]:
            xnpv_high = calculate_xnpv(cash_flows, dates, h)
            if xnpv_low * xnpv_high < 0:
                high = h
                break

    if xnpv_low * xnpv_high < 0:
        # Bisection method
        for _ in range(100):
            mid = (low + high) / 2
            xnpv_mid = calculate_xnpv(cash_flows, dates, mid)
            if abs(xnpv_mid) < TOLERANCE:
                return mid
            if xnpv_low * xnpv_mid < 0:
                high = mid
                xnpv_high = xnpv_mid
            else:
                low = mid
                xnpv_low = xnpv_mid
        return (low + high) / 2

    raise ValueError("XIRR calculation did not converge")


def calculate_multiple(cash_flows: List[float]) -> float:
    """
    Calculate equity multiple.

    Args:
        cash_flows: Array of cash flows (investments are negative)

    Returns:
        Multiple (e.g., 2.0 = 2.0x return)
    """
    total_inflows = sum(cf for cf in cash_flows if cf > 0)
    total_outflows = abs(sum(cf for cf in cash_flows if cf < 0))

    if total_outflows == 0:
        raise ValueError("No investment (outflows) found")

    return total_inflows / total_outflows


def calculate_profit(cash_flows: List[float]) -> float:
    """Calculate profit (total inflows minus total outflows)."""
    return sum(cash_flows)


def monthly_to_annual_irr(monthly_irr: float) -> float:
    """Convert monthly IRR to annual IRR."""
    return ((1 + monthly_irr) ** 12) - 1


def annual_to_monthly_irr(annual_irr: float) -> float:
    """Convert annual IRR to monthly IRR."""
    return ((1 + annual_irr) ** (1 / 12)) - 1
