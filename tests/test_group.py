import pytest

import revmng
from revmng.group import evaluate_group, group_displacement


def test_group_displacement_multi_night():
    # 100 rooms, group 30/night, transient demand 70/95/85, value 70 per room.
    # displaced = max(0, demand - (100 - 30)) = 0 + 25 + 15 = 40 room-nights.
    cost = group_displacement(30, 100, [70, 95, 85], 70)
    assert cost == pytest.approx(40 * 70)


def test_group_displacement_single_period():
    assert group_displacement(30, 100, 60, 70) == pytest.approx(0.0)  # 60 < 70 free
    assert group_displacement(30, 100, 90, 70) == pytest.approx(20 * 70)


def test_evaluate_group_reject_then_break_even():
    r = evaluate_group(60, 90, displacement_cost=2800, variable_cost=50)
    assert r.group_contribution == pytest.approx(900)      # (60 - 50) * 90
    assert r.net_benefit == pytest.approx(-1900)
    assert r.accept is False
    assert r.break_even_rate == pytest.approx(50 + 2800 / 90)


def test_evaluate_group_accept():
    r = evaluate_group(90, 90, displacement_cost=2800, variable_cost=50)
    assert r.net_benefit == pytest.approx(800)
    assert r.accept is True


def test_evaluate_group_with_marginal_value():
    r = evaluate_group(100, 40, marginal_value=120)
    assert r.displacement_cost == pytest.approx(4800)
    assert r.accept is False
    assert r.break_even_rate == pytest.approx(120)


def test_evaluate_group_needs_exactly_one_cost():
    with pytest.raises(ValueError):
        evaluate_group(60, 90)
    with pytest.raises(ValueError):
        evaluate_group(60, 90, displacement_cost=100, marginal_value=10)


def test_to_dict_json_safe():
    import json
    json.dumps(revmng.evaluate_group(60, 90, displacement_cost=2800,
                                     variable_cost=50).to_dict())
