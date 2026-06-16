import pytest

import revmng
from revmng.pricing import (
    ConstantElasticityDemand,
    LinearDemand,
    newsvendor,
    optimal_price,
)


def test_newsvendor_critical_ratio_and_quantity():
    r = newsvendor(price=10, cost=4, demand_mean=100, demand_sd=30)
    assert r.critical_ratio == pytest.approx(0.6)
    # z = Phi^-1(0.6) ~ 0.2533 -> Q ~ 100 + 0.2533 * 30
    assert r.optimal_quantity == pytest.approx(107.6, abs=0.1)
    assert r.expected_sales < r.demand_mean
    assert r.expected_profit > 0


def test_newsvendor_high_critical_ratio_overstocks():
    cheap = newsvendor(price=100, cost=10, demand_mean=50, demand_sd=20)
    assert cheap.optimal_quantity > 50          # CR > 0.5 -> stock above the mean


def test_newsvendor_errors():
    with pytest.raises(ValueError):
        newsvendor(price=4, cost=10, demand_mean=100, demand_sd=30)
    with pytest.raises(ValueError):
        newsvendor(price=10, cost=4, demand_mean=100, demand_sd=30, salvage=5)


def test_optimal_price_linear():
    r = optimal_price(LinearDemand(intercept=100, slope=2), unit_cost=10)
    assert r.optimal_price == pytest.approx(30.0)     # a/(2b) + c/2
    assert r.quantity == pytest.approx(40.0)
    assert r.revenue == pytest.approx(1200.0)
    assert r.profit == pytest.approx(800.0)
    assert r.elasticity == pytest.approx(-1.5)


def test_optimal_price_linear_zero_cost_is_revenue_max():
    r = optimal_price(LinearDemand(intercept=100, slope=2))
    assert r.optimal_price == pytest.approx(25.0)     # a/(2b)


def test_optimal_price_constant_elasticity_lerner():
    r = optimal_price(ConstantElasticityDemand(scale=10000, elasticity=2),
                      unit_cost=20)
    assert r.optimal_price == pytest.approx(40.0)     # c * e / (e - 1)
    assert r.margin == pytest.approx(0.5)
    assert r.quantity == pytest.approx(6.25)


def test_constant_elasticity_requires_elastic_demand():
    with pytest.raises(ValueError):
        optimal_price(ConstantElasticityDemand(scale=100, elasticity=0.8),
                      unit_cost=10)


def test_to_dict_json_safe():
    import json
    json.dumps(revmng.newsvendor(10, 4, 100, 30).to_dict())
    json.dumps(optimal_price(LinearDemand(100, 2), 10).to_dict())
