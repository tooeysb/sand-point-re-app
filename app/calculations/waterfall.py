"""
Waterfall Distribution Calculations

Calculates LP/GP distributions through multi-hurdle promote structures.
Implements institutional-quality waterfall logic matching Excel pro forma models.
"""

from typing import List, Dict, Optional
from datetime import date
from dataclasses import dataclass


@dataclass
class WaterfallHurdle:
    """Configuration for a single hurdle tier in the waterfall."""

    name: str
    pref_return: float  # Annual preferred return rate (e.g., 0.05 for 5%)
    lp_split: float  # LP's share at this tier (e.g., 0.90 for 90%)
    gp_split: float  # GP's share at this tier (e.g., 0.10 for 10%)
    gp_promote: float  # GP promote percentage (e.g., 0.10 for 10% promote)


# Default 225 Worth Ave waterfall structure from Excel model
DEFAULT_HURDLES = [
    WaterfallHurdle(
        name="Hurdle I",
        pref_return=0.05,  # 5% pref
        lp_split=0.90,  # 90% to LP
        gp_split=0.10,  # 10% to GP
        gp_promote=0.0,  # No additional promote at first hurdle
    ),
    WaterfallHurdle(
        name="Hurdle II",
        pref_return=0.05,  # Additional 5% pref
        lp_split=0.75,  # 75% to LP
        gp_split=0.0833,  # 8.33% to GP equity
        gp_promote=0.1667,  # 16.67% promote to GP
    ),
    WaterfallHurdle(
        name="Hurdle III",
        pref_return=0.05,  # Additional 5% pref
        lp_split=0.75,  # 75% to LP
        gp_split=0.0833,  # 8.33% to GP equity
        gp_promote=0.1667,  # 16.67% promote to GP
    ),
]

# Default final split after all hurdles are satisfied
DEFAULT_FINAL_SPLIT = {
    "lp_split": 0.75,
    "gp_split": 0.0833,
    "gp_promote": 0.1667,
}


def calculate_waterfall_distributions(
    leveraged_cash_flows: List[float],
    dates: List[date],
    total_equity: float,
    lp_share: float = 0.90,
    gp_share: float = 0.10,
    pref_return: float = 0.05,
    compound_monthly: bool = False,
    hurdles: Optional[List[WaterfallHurdle]] = None,
    final_split: Optional[Dict] = None,
) -> List[Dict]:
    """
    Calculate waterfall distributions for all periods using multi-hurdle structure.

    Implements a standard institutional waterfall with:
    1. Return of capital (ROC) to LP and GP based on equity shares
    2. Preferred return at each hurdle tier
    3. GP promote at each hurdle tier after pref is satisfied
    4. Final profit split after all hurdles

    Args:
        leveraged_cash_flows: Array of leveraged cash flows
        dates: Array of dates
        total_equity: Total equity invested
        lp_share: LP's share of equity (e.g., 0.90 for 90%)
        gp_share: GP's share of equity (e.g., 0.10 for 10%)
        pref_return: Base annual preferred return rate (used if no hurdles specified)
        compound_monthly: Whether to compound preferred return monthly
        hurdles: List of WaterfallHurdle objects defining the promote structure
        final_split: Dict with lp_split, gp_split, gp_promote for final tier

    Returns:
        List of distribution records with detailed breakdowns
    """
    # Use default multi-hurdle structure if not specified
    if hurdles is None:
        hurdles = DEFAULT_HURDLES
    if final_split is None:
        final_split = DEFAULT_FINAL_SPLIT

    distributions = []

    lp_equity = total_equity * lp_share
    gp_equity = total_equity * gp_share

    # Track equity balances (for ROC)
    lp_equity_balance = lp_equity
    gp_equity_balance = gp_equity

    # Track accrued preferred return at each hurdle
    # Each hurdle accrues on the ORIGINAL equity balance
    hurdle_lp_accrued = [0.0 for _ in hurdles]
    hurdle_gp_accrued = [0.0 for _ in hurdles]

    # Track which hurdles have been fully satisfied
    hurdle_lp_satisfied = [False for _ in hurdles]
    hurdle_gp_satisfied = [False for _ in hurdles]

    for i, cash_flow in enumerate(leveraged_cash_flows):
        # Accrue preferred return at each hurdle tier
        for h_idx, hurdle in enumerate(hurdles):
            monthly_rate = hurdle.pref_return / 12

            if compound_monthly:
                # Compound on balance + accrued
                hurdle_lp_accrued[h_idx] += (
                    lp_equity * lp_share + hurdle_lp_accrued[h_idx]
                ) * monthly_rate
                hurdle_gp_accrued[h_idx] += (
                    gp_equity * gp_share + hurdle_gp_accrued[h_idx]
                ) * monthly_rate
            else:
                # Simple interest on original equity
                hurdle_lp_accrued[h_idx] += lp_equity * monthly_rate
                hurdle_gp_accrued[h_idx] += gp_equity * monthly_rate

        # Initialize distribution amounts for this period
        lp_equity_paydown = 0.0
        gp_equity_paydown = 0.0
        lp_pref_paid = 0.0
        gp_pref_paid = 0.0
        gp_promote_paid = 0.0
        lp_profit = 0.0
        gp_profit = 0.0

        remaining = cash_flow

        if remaining > 0:
            # === STEP 1: Pay accrued preferred return (all hurdles) ===
            for h_idx, hurdle in enumerate(hurdles):
                if remaining <= 0:
                    break

                total_pref_owed = hurdle_lp_accrued[h_idx] + hurdle_gp_accrued[h_idx]

                if total_pref_owed > 0:
                    pref_payment = min(remaining, total_pref_owed)

                    # Split pref payment proportionally
                    if total_pref_owed > 0:
                        lp_pref_share = hurdle_lp_accrued[h_idx] / total_pref_owed
                    else:
                        lp_pref_share = lp_share

                    lp_pref_this = pref_payment * lp_pref_share
                    gp_pref_this = pref_payment * (1 - lp_pref_share)

                    lp_pref_paid += lp_pref_this
                    gp_pref_paid += gp_pref_this

                    hurdle_lp_accrued[h_idx] -= lp_pref_this
                    hurdle_gp_accrued[h_idx] -= gp_pref_this

                    remaining -= pref_payment

                    # Check if hurdle is satisfied (no more accrued pref)
                    if hurdle_lp_accrued[h_idx] <= 0.01:
                        hurdle_lp_satisfied[h_idx] = True
                    if hurdle_gp_accrued[h_idx] <= 0.01:
                        hurdle_gp_satisfied[h_idx] = True

            # === STEP 2: Return of capital ===
            total_equity_owed = lp_equity_balance + gp_equity_balance

            if remaining > 0 and total_equity_owed > 0:
                equity_payment = min(remaining, total_equity_owed)

                if total_equity_owed > 0:
                    lp_equity_share = lp_equity_balance / total_equity_owed
                else:
                    lp_equity_share = lp_share

                lp_equity_paydown = equity_payment * lp_equity_share
                gp_equity_paydown = equity_payment * (1 - lp_equity_share)

                lp_equity_balance -= lp_equity_paydown
                gp_equity_balance -= gp_equity_paydown

                remaining -= equity_payment

            # === STEP 3: Profit split with GP promote ===
            if remaining > 0:
                # Determine which hurdle tier we're in based on satisfied hurdles
                active_hurdle_idx = 0
                for h_idx, hurdle in enumerate(hurdles):
                    if all(hurdle_lp_satisfied[: h_idx + 1]) and all(
                        hurdle_gp_satisfied[: h_idx + 1]
                    ):
                        active_hurdle_idx = h_idx + 1

                # Use final split if all hurdles satisfied, otherwise use hurdle split
                if active_hurdle_idx >= len(hurdles):
                    # All hurdles satisfied - use final split
                    lp_split = final_split["lp_split"]
                    gp_split = final_split["gp_split"]
                    promote = final_split["gp_promote"]
                else:
                    # Use the active hurdle's split
                    hurdle = hurdles[active_hurdle_idx]
                    lp_split = hurdle.lp_split
                    gp_split = hurdle.gp_split
                    promote = hurdle.gp_promote

                # Calculate profit distributions
                lp_profit = remaining * lp_split
                gp_profit = remaining * gp_split
                gp_promote_paid = remaining * promote

        total_to_lp = lp_equity_paydown + lp_pref_paid + lp_profit
        total_to_gp = gp_equity_paydown + gp_pref_paid + gp_profit + gp_promote_paid

        distributions.append(
            {
                "period": i,
                "date": dates[i].isoformat() if i < len(dates) else None,
                "cash_flow": round(cash_flow, 2),
                "lp_equity_paydown": round(lp_equity_paydown, 2),
                "gp_equity_paydown": round(gp_equity_paydown, 2),
                "lp_preferred_return": round(lp_pref_paid, 2),
                "gp_preferred_return": round(gp_pref_paid, 2),
                "gp_promote": round(gp_promote_paid, 2),
                "lp_profit": round(lp_profit, 2),
                "gp_profit": round(gp_profit, 2),
                "total_to_lp": round(total_to_lp, 2),
                "total_to_gp": round(total_to_gp, 2),
                "lp_equity_balance": round(max(0, lp_equity_balance), 2),
                "gp_equity_balance": round(max(0, gp_equity_balance), 2),
            }
        )

    return distributions


def calculate_simple_waterfall(
    leveraged_cash_flows: List[float],
    dates: List[date],
    total_equity: float,
    lp_share: float = 0.90,
    gp_share: float = 0.10,
    pref_return: float = 0.05,
    compound_monthly: bool = False,
) -> List[Dict]:
    """
    Calculate simple single-tier waterfall (legacy compatibility).

    This is a simplified waterfall with a single preferred return hurdle
    and constant LP/GP split. Use calculate_waterfall_distributions()
    for full multi-hurdle promote structure.
    """
    # Create a single hurdle with the provided parameters
    single_hurdle = [
        WaterfallHurdle(
            name="Single Hurdle",
            pref_return=pref_return,
            lp_split=lp_share,
            gp_split=gp_share,
            gp_promote=0.0,
        )
    ]

    final_split = {
        "lp_split": lp_share,
        "gp_split": gp_share,
        "gp_promote": 0.0,
    }

    return calculate_waterfall_distributions(
        leveraged_cash_flows=leveraged_cash_flows,
        dates=dates,
        total_equity=total_equity,
        lp_share=lp_share,
        gp_share=gp_share,
        pref_return=pref_return,
        compound_monthly=compound_monthly,
        hurdles=single_hurdle,
        final_split=final_split,
    )


def extract_lp_cash_flows(
    distributions: List[Dict], lp_equity: float
) -> List[float]:
    """Extract LP cash flows from distributions for IRR calculation."""
    cash_flows = []
    for i, dist in enumerate(distributions):
        if i == 0:
            # First period: negative investment + any distribution
            cf = -lp_equity + dist["total_to_lp"]
        else:
            cf = dist["total_to_lp"]
        cash_flows.append(cf)
    return cash_flows


def extract_gp_cash_flows(
    distributions: List[Dict], gp_equity: float
) -> List[float]:
    """Extract GP cash flows from distributions for IRR calculation."""
    cash_flows = []
    for i, dist in enumerate(distributions):
        if i == 0:
            cf = -gp_equity + dist["total_to_gp"]
        else:
            cf = dist["total_to_gp"]
        cash_flows.append(cf)
    return cash_flows


def calculate_waterfall_summary(distributions: List[Dict]) -> Dict:
    """Calculate summary metrics for waterfall."""
    return {
        "total_to_lp": sum(d["total_to_lp"] for d in distributions),
        "total_to_gp": sum(d["total_to_gp"] for d in distributions),
        "total_equity_paydown": sum(
            d["lp_equity_paydown"] + d["gp_equity_paydown"] for d in distributions
        ),
        "total_preferred_return": sum(
            d["lp_preferred_return"] + d["gp_preferred_return"] for d in distributions
        ),
        "total_profit": sum(d["lp_profit"] + d["gp_profit"] for d in distributions),
    }
