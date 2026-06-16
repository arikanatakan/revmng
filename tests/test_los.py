import pytest

import revmng
from revmng.los import evaluate_stay

BIDS = {"Mon": 80, "Tue": 120, "Wed": 90}


def test_stay_clears_when_rate_covers_bid_prices():
    r = evaluate_stay(BIDS, ["Mon", "Tue", "Wed"], total_rate=320)
    assert r.hurdle == pytest.approx(290)
    assert r.slack == pytest.approx(30)
    assert r.accept is True


def test_stay_rejected_below_hurdle():
    r = evaluate_stay(BIDS, ["Tue"], total_rate=100)
    assert r.hurdle == pytest.approx(120)
    assert r.accept is False


def test_unknown_night_errors():
    with pytest.raises(ValueError):
        evaluate_stay(BIDS, ["Mon", "Thu"], total_rate=300)


def test_empty_stay_errors():
    with pytest.raises(ValueError):
        evaluate_stay(BIDS, [], total_rate=100)


def test_to_dict_json_safe():
    import json
    json.dumps(revmng.evaluate_stay(BIDS, ["Mon", "Tue"], 250).to_dict())
