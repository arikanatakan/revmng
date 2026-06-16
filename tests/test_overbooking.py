import pytest

import revmng
from revmng.overbooking import _expected_over_spoil, overbooking_limit


def test_service_level_limit():
    r = overbooking_limit(100, no_show_rate=0.1)
    assert r.method == "service_level"
    assert r.authorization_limit == 111          # round(100 / 0.9)
    assert r.expected_shows == pytest.approx(99.9)
    assert r.overbooking_pad == 11


def test_no_overbooking_when_no_no_shows():
    r = overbooking_limit(80, no_show_rate=0.0)
    assert r.authorization_limit == 80
    assert r.expected_oversales == pytest.approx(0.0)


def test_cost_based_limit_is_a_minimum():
    cap, q = 100, 0.88
    denied, spoil = 400.0, 120.0
    r = overbooking_limit(cap, no_show_rate=0.12, denied_cost=denied,
                          spoilage_cost=spoil)
    assert r.method == "cost"
    u = r.authorization_limit

    def cost(x):
        over, sp = _expected_over_spoil(x, q, cap)
        return denied * over + spoil * sp

    assert cost(u) <= cost(u - 1) + 1e-9
    assert cost(u) <= cost(u + 1) + 1e-9
    assert r.expected_cost == pytest.approx(cost(u))
    assert u >= cap


def test_higher_denied_cost_lowers_the_limit():
    base = overbooking_limit(150, no_show_rate=0.1, denied_cost=200,
                             spoilage_cost=150)
    pricier = overbooking_limit(150, no_show_rate=0.1, denied_cost=2000,
                                spoilage_cost=150)
    assert pricier.authorization_limit <= base.authorization_limit


def test_partial_costs_warn_and_fall_back():
    r = overbooking_limit(100, no_show_rate=0.1, denied_cost=400)
    assert r.method == "service_level"
    assert any(a.indicator == "partial_costs" for a in r.alerts)


def test_validation_errors():
    with pytest.raises(ValueError):
        overbooking_limit(100, no_show_rate=1.0)
    with pytest.raises(ValueError):
        overbooking_limit(0, no_show_rate=0.1)


def test_to_dict_json_safe():
    import json
    r = revmng.overbooking_limit(100, no_show_rate=0.1, denied_cost=400,
                                 spoilage_cost=120)
    json.dumps(r.to_dict())
