"""Deterministic financial formulas for retention campaign revenue recovery."""

from typing import List

from customer_analytics.domain.models import SimulationResult, SimulationScenario
from customer_analytics.exceptions import InvalidSimulationInputException


def compute_scenario_economics(
    scenario: SimulationScenario,
    eligible_population_size: int,
    baseline_arpu: float,
) -> SimulationResult:
    """Compute financial accounting for a retention campaign under explicit stated assumptions."""
    if eligible_population_size < 0:
        raise InvalidSimulationInputException("Eligible customer population cannot be negative.")

    warnings: List[str] = []

    # 1. Outreach bounds
    contacted = eligible_population_size
    if scenario.max_customers_to_contact is not None:
        if scenario.max_customers_to_contact < contacted:
            contacted = scenario.max_customers_to_contact
            warnings.append(
                f"Outreach capped at capacity limit of {contacted} customers "
                f"(out of {eligible_population_size} eligible)."
            )

    # 2. Conversion & Retention funnel
    expected_redeemed = int(round(contacted * scenario.expected_redemption_rate))
    expected_retained = int(round(expected_redeemed * scenario.estimated_retention_probability))

    # Revenue baseline per retained customer
    future_revenue_per_customer = (
        scenario.expected_future_revenue_per_retained
        if scenario.expected_future_revenue_per_retained > 0.0
        else baseline_arpu
    )

    if future_revenue_per_customer <= 0.0:
        future_revenue_per_customer = 100.0  # sensible default fallback
        warnings.append("Baseline revenue was non-positive; defaulted to $100.00 per customer.")

    # 3. Expenditure accounting
    discount_per_redeemed = min(
        future_revenue_per_customer * scenario.discount_percentage,
        scenario.max_discount_per_customer,
    )
    discount_expenditure = round(expected_redeemed * discount_per_redeemed, 2)
    campaign_expenditure = round(contacted * scenario.campaign_cost_per_contacted, 2)
    total_cost = round(discount_expenditure + campaign_expenditure, 2)

    # 4. Revenue & Net Value
    gross_incremental_revenue = round(expected_retained * future_revenue_per_customer, 2)
    net_incremental_value = round(gross_incremental_revenue - total_cost, 2)

    roi_pct = round((net_incremental_value / total_cost) * 100.0, 2) if total_cost > 0 else None
    net_per_contacted = round(net_incremental_value / max(1, contacted), 2)

    if net_incremental_value < 0:
        warnings.append(
            f"Campaign produces negative estimated net value (-${abs(net_incremental_value):,.2f}). "
            f"Discount expenditure and marketing costs exceed expected recovered revenue."
        )

    disclaimer = (
        "SIMULATION ESTIMATE ONLY: Results reflect mathematical extrapolation under user-specified "
        "assumptions (redemption rate, retention probability, future spend). This model does NOT prove causal lift "
        "or guarantee business outcomes. True causal effectiveness requires randomized controlled trials (A/B testing)."
    )

    return SimulationResult(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        eligible_customers=eligible_population_size,
        contacted_customers=contacted,
        expected_redeemed_customers=expected_redeemed,
        expected_retained_customers=expected_retained,
        gross_revenue_per_retained=round(future_revenue_per_customer, 2),
        estimated_discount_expenditure=discount_expenditure,
        estimated_campaign_expenditure=campaign_expenditure,
        total_cost=total_cost,
        estimated_incremental_revenue=gross_incremental_revenue,
        estimated_net_incremental_value=net_incremental_value,
        roi_percentage=roi_pct,
        net_value_per_contacted=net_per_contacted,
        warnings=warnings,
        is_causal_estimate=False,
        disclaimer=disclaimer,
    )
