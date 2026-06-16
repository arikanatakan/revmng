import pytest

pytest.importorskip("scipy")

import revmng  # noqa: E402
from revmng.network import Product, bid_prices  # noqa: E402


def test_single_resource_bid_price_is_marginal_fare():
    # capacity 100: take all 60 of the $200 product, fill the rest with the $100.
    products = [
        Product(fare=200, uses={"R": 1}, demand=60, name="high"),
        Product(fare=100, uses={"R": 1}, demand=80, name="low"),
    ]
    r = bid_prices(products, {"R": 100})
    assert r.expected_revenue == pytest.approx(16000.0)
    assert r.bid_prices["R"] == pytest.approx(100.0)
    alloc = {a["name"]: a["allocation"] for a in r.allocation}
    assert alloc["high"] == pytest.approx(60.0)
    assert alloc["low"] == pytest.approx(40.0)


def test_accept_uses_bid_prices():
    r = bid_prices([Product(200, {"R": 1}, 60), Product(100, {"R": 1}, 80)],
                   {"R": 100})
    assert r.accept(150, {"R": 1}) is True
    assert r.accept(80, {"R": 1}) is False


def test_connecting_itinerary_two_legs():
    products = [
        Product(fare=120, uses={"AB": 1}, demand=70, name="A-B"),
        Product(fare=120, uses={"BC": 1}, demand=70, name="B-C"),
        Product(fare=200, uses={"AB": 1, "BC": 1}, demand=40, name="A-B-C"),
    ]
    r = bid_prices(products, {"AB": 100, "BC": 100})
    # a connecting request must cover both legs' bid prices
    assert r.accept(200, {"AB": 1, "BC": 1}) is True
    assert r.expected_revenue > 0


def test_no_binding_capacity_warns():
    r = bid_prices([Product(100, {"R": 1}, 10)], {"R": 1000})
    assert all(v == 0.0 for v in r.bid_prices.values())
    assert any(a.indicator == "slack" for a in r.alerts)


def test_unknown_resource_errors():
    with pytest.raises(ValueError):
        bid_prices([Product(100, {"X": 1}, 10)], {"R": 50})


def test_to_dict_json_safe():
    import json
    r = revmng.bid_prices([Product(200, {"R": 1}, 60), Product(100, {"R": 1}, 80)],
                          {"R": 100})
    json.dumps(r.to_dict())
