"""Unit tests for deterministic retention simulation economics."""

import pytest

from customer_analytics.domain.models import SimulationScenario
from customer_analytics.exceptions import InvalidSimulationInputException
from customer_analytics.simulation.economics import compute_scenario_economics


def test_compute_scenario_economics_standard():
    """Verify accounting formulas: redemption, retention, expenditures, net value, and ROI."""
    scenario = SimulationScenario(
        scenario_id="sc_test",
        name="Test 10% Discount",
        target_population="all",
        discount_percentage=0.10,
        max_discount_per_customer=30.0,
        expected_redemption_rate=0.50,
        estimated_retention_probability=0.80,
        expected_future_revenue_per_retained=100.0,
        campaign_cost_per_contacted=2.0,
    )

    # 1,000 eligible customers
    # Contacted = 1,000
    # Redeemed = 1000 * 0.50 = 500
    # Retained = 500 * 0.80 = 400
    # Discount expenditure = 500 * min(100 * 0.10, 30) = 500 * 10 = $5,000
    # Campaign expenditure = 1,000 * 2.0 = $2,000
    # Total cost = $7,000
    # Incremental revenue = 400 * 100 = $40,000
    # Net incremental value = $40,000 - $7,000 = $33,000

    result = compute_scenario_economics(
        scenario=scenario,
        eligible_population_size=1000,
        baseline_arpu=100.0,
    )

    assert result.contacted_customers == 1000
    assert result.expected_redeemed_customers == 500
    assert result.expected_retained_customers == 400
    assert result.estimated_discount_expenditure == 5000.0
    assert result.estimated_campaign_expenditure == 2000.0
    assert result.total_cost == 7000.0
    assert result.estimated_incremental_revenue == 40000.0
    assert result.estimated_net_incremental_value == 33000.0
    assert result.roi_percentage == round((33000.0 / 7000.0) * 100.0, 2)
    assert result.is_causal_estimate is False


def test_simulation_negative_population_raises():
    """Negative eligible population must raise InvalidSimulationInputException."""
    scenario = SimulationScenario(
        scenario_id="sc_err",
        name="Invalid Scenario",
        target_population="all",
        discount_percentage=0.10,
        max_discount_per_customer=30.0,
        expected_redemption_rate=0.50,
        estimated_retention_probability=0.80,
        expected_future_revenue_per_retained=100.0,
    )
    with pytest.raises(InvalidSimulationInputException):
        compute_scenario_economics(scenario, eligible_population_size=-10, baseline_arpu=100.0)
