import pytest

import revmng
from revmng.metrics import nested_revenue, revenue_opportunity


def test_revpar_identity():
    # RevPAR = ADR * occupancy
    rev, sold, avail = 18000.0, 75.0, 100.0
    assert revmng.revpar(rev, avail) == pytest.approx(
        revmng.adr(rev, sold) * revmng.occupancy(sold, avail))


def test_simple_ratios():
    assert revmng.load_factor(8000, 10000) == pytest.approx(0.8)
    assert revmng.yield_(50000, 250000) == pytest.approx(0.2)
    assert revmng.spill(120, 100) == 20
    assert revmng.spoilage(100, 80) == 20
    assert revmng.spill(80, 100) == 0


def test_ratio_guards():
    with pytest.raises(ValueError):
        revmng.occupancy(10, 0)


def test_nested_revenue_low_before_high():
    # No controls (all limits = capacity): lowest fares fill first.
    fares = [1000, 800, 600, 200]
    demand = [25, 30, 20, 50]
    rev = nested_revenue(fares, [100] * 4, demand, 100)
    assert rev == pytest.approx(46000.0)


def test_revenue_opportunity_benchmarks():
    r = revenue_opportunity([1000, 800, 600, 200], [25, 30, 20, 50], 100)
    assert r.perfect_revenue == pytest.approx(66000.0)
    assert r.no_control_revenue == pytest.approx(46000.0)
    assert r.realized_revenue is None
    assert r.rom is None


def test_revenue_opportunity_with_limits():
    r = revenue_opportunity([1000, 800, 600, 200], [25, 30, 20, 50], 100,
                            booking_limits=[100, 70, 45, 32])
    assert r.realized_revenue == pytest.approx(59200.0)
    assert r.rom == pytest.approx(0.66, abs=0.005)


def test_to_dict_json_safe():
    import json
    r = revenue_opportunity([500, 300], [40, 80], 100, booking_limits=[100, 70])
    json.dumps(r.to_dict())
