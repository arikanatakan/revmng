import pytest

import revmng
from revmng.optimal import optimal_protection_levels, policy_revenue
from revmng.singleleg import littlewood


def test_dp_two_classes_matches_littlewood():
    # Well-behaved demand so discretisation is faithful.
    classes = [(200, 50, 15), (100, 40, 12)]
    r = optimal_protection_levels(classes, capacity=100)
    assert r.protection_levels[0] == pytest.approx(littlewood(200, 100, 50, 15),
                                                   abs=1.5)


def test_dp_two_classes_lower_ratio_protects_more():
    classes = [(200, 50, 15), (80, 40, 12)]
    r = optimal_protection_levels(classes, capacity=100)
    # ratio 0.4 -> Littlewood protects ~53.8
    assert r.protection_levels[0] == pytest.approx(littlewood(200, 80, 50, 15),
                                                   abs=1.5)


def test_dp_is_at_least_as_good_as_emsr_b():
    classes = [(1000, 30, 12), (700, 40, 15), (400, 60, 20)]
    opt = optimal_protection_levels(classes, capacity=120)
    emsr = revmng.emsr_b(classes, capacity=120)
    emsr_rev = policy_revenue(classes, 120, emsr.protection_levels)
    assert opt.expected_revenue is not None
    assert opt.expected_revenue >= emsr_rev - 1e-6
    # the optimal value reproduces when its own levels are scored back
    assert opt.expected_revenue == pytest.approx(
        policy_revenue(classes, 120, opt.protection_levels), abs=1e-6)


def test_dp_protection_is_nested_and_method_labelled():
    classes = [(1000, 30, 12), (700, 40, 15), (400, 60, 20)]
    r = optimal_protection_levels(classes, capacity=120)
    assert r.method == "optimal (DP)"
    assert list(r.protection_levels) == sorted(r.protection_levels)
    assert list(r.booking_limits) == sorted(r.booking_limits, reverse=True)


def test_policy_revenue_wrong_length_errors():
    with pytest.raises(ValueError):
        policy_revenue([(200, 50, 15), (100, 40, 12)], 100, [10, 20])


def test_to_dict_json_safe():
    import json
    r = optimal_protection_levels([(1000, 30, 12), (400, 60, 20)], 100)
    d = r.to_dict()
    json.dumps(d)
    assert d["expected_revenue"] is not None
