import pytest

import revmng
from revmng.singleleg import FareClass, emsr_a, emsr_b, littlewood


def test_littlewood_fare_ratio_only():
    # Equal fares: nothing to protect, the low class may sell freely.
    assert littlewood(100, 100, 50, 20) == pytest.approx(0.0)
    # At a 0.5 fare ratio, protect exactly the high-class mean.
    assert littlewood(100, 50, 50, 20) == pytest.approx(50.0)
    # A cheaper low fare protects more of the high class.
    assert littlewood(100, 40, 50, 100) > littlewood(100, 60, 50, 100)


def test_littlewood_validation_errors():
    with pytest.raises(ValueError):
        littlewood(100, 200, 50, 10)   # low > high
    with pytest.raises(ValueError):
        littlewood(-1, 40, 50, 10)


def test_emsr_b_two_classes_equals_littlewood():
    classes = [(1000, 50, 100), (400, 30, 10)]
    r = emsr_b(classes, capacity=200)
    assert r.protection_levels[0] == pytest.approx(littlewood(1000, 400, 50, 100))


def test_emsr_b_nested_limits_and_ordering():
    classes = [(1000, 30, 12), (700, 40, 15), (400, 60, 20)]
    r = emsr_b(classes, capacity=120)
    # classes are sorted high -> low by fare
    assert [c["fare"] for c in r.classes] == [1000, 700, 400]
    # nested booking limits: highest class gets full capacity, then non-increasing
    assert r.booking_limits[0] == 120
    assert list(r.booking_limits) == sorted(r.booking_limits, reverse=True)
    # protection levels accumulate
    assert list(r.protection_levels) == sorted(r.protection_levels)
    assert r.booking_limits_int[0] == 120


def test_emsr_a_and_b_agree_on_first_boundary():
    # With a single higher class, both heuristics reduce to Littlewood, so the
    # first protection level is identical; later boundaries can differ.
    classes = [(1000, 30, 12), (700, 40, 15), (400, 60, 20)]
    a = emsr_a(classes, capacity=120)
    b = emsr_b(classes, capacity=120)
    assert a.protection_levels[0] == pytest.approx(b.protection_levels[0])
    assert all(0 <= y <= 120 for y in a.protection_levels)
    assert all(0 <= y <= 120 for y in b.protection_levels)


def test_fareclass_and_mapping_inputs_match():
    tuples = [(500, 20, 8), (300, 25, 10)]
    objs = [FareClass(500, 20, 8), FareClass(300, 25, 10)]
    maps = [{"fare": 500, "mean": 20, "sd": 8}, {"fare": 300, "mean": 25, "sd": 10}]
    rt = emsr_b(tuples, 60)
    ro = emsr_b(objs, 60)
    rm = emsr_b(maps, 60)
    assert rt.protection_levels == ro.protection_levels == rm.protection_levels


def test_to_dict_is_json_safe_and_has_provenance():
    import json
    r = emsr_b([(1000, 30, 12), (400, 60, 20)], capacity=100)
    d = r.to_dict()
    json.dumps(d)
    assert d["meta"]["library"] == "revmng"
    assert d["meta"]["input_hash"].startswith("sha256:")


def test_needs_two_classes():
    with pytest.raises(ValueError):
        emsr_b([(100, 10, 5)], capacity=50)


def test_summary_runs():
    r = revmng.emsr_b([(1000, 30, 12), (700, 40, 15), (400, 60, 20)], 120)
    assert "EMSR-b" in r.summary()
