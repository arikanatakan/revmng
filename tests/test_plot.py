import pytest

pytest.importorskip("matplotlib")

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import revmng  # noqa: E402


def _is_figure(obj):
    from matplotlib.figure import Figure
    return isinstance(obj, Figure)


def test_booking_limit_chart():
    r = revmng.emsr_b([(1000, 30, 12), (700, 40, 15), (400, 60, 20)], 120)
    assert _is_figure(revmng.booking_limit_chart(r))


def test_overbooking_cost_curve():
    fig = revmng.overbooking_cost_curve(100, 0.12, denied_cost=400,
                                        spoilage_cost=120)
    assert _is_figure(fig)


def test_revenue_opportunity_chart():
    r = revmng.revenue_opportunity([1000, 800, 600, 200], [25, 30, 20, 50], 100,
                                   booking_limits=[100, 70, 45, 32])
    assert _is_figure(revmng.revenue_opportunity_chart(r))


def test_emsr_curve():
    r = revmng.emsr_b([(1000, 30, 12), (700, 40, 15), (400, 60, 20)], 120)
    assert _is_figure(revmng.emsr_curve(r))


def test_price_curve():
    assert _is_figure(revmng.price_curve(revmng.LinearDemand(100, 2), unit_cost=10))
    assert _is_figure(revmng.price_curve(
        revmng.ConstantElasticityDemand(10000, 2), unit_cost=20))


def test_newsvendor_curve():
    assert _is_figure(revmng.newsvendor_curve(10, 4, 100, 30))


def test_bid_price_chart():
    pytest.importorskip("scipy")
    from revmng import Product
    r = revmng.bid_prices([Product(200, {"R": 1}, 60), Product(100, {"R": 1}, 80)],
                          {"R": 100})
    assert _is_figure(revmng.bid_price_chart(r))
