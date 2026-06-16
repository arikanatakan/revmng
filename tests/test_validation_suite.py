"""Check revmng against published and hand-derived worked examples.

Each case names its source. Published anchors are Phillips, Pricing and Revenue
Optimization (2005): Example 9.2 (Littlewood booking limits) and Example 9.7
(the revenue opportunity metric). The newsvendor and service-level overbooking
cases are derived by hand from the textbook formulas, with the arithmetic shown
in each case's source string.
"""

import json
import math
from pathlib import Path

import pytest

import revmng

CASES = json.loads(
    (Path(__file__).parent / "validation_cases.json").read_text())["cases"]


def _compute(case):
    kind = case["kind"]
    inp = case["inputs"]
    if kind == "littlewood_booking_limit":
        y = revmng.littlewood(inp["fare_high"], inp["fare_low"],
                              inp["mean_high"], inp["sd_high"])
        return {"booking_limit_low_int": int(inp["capacity"]) - math.floor(y)}
    if kind == "revenue_opportunity":
        r = revmng.revenue_opportunity(inp["fares"], inp["demand"], inp["capacity"],
                                       booking_limits=inp["booking_limits"])
        return {"perfect_revenue": r.perfect_revenue,
                "no_control_revenue": r.no_control_revenue,
                "realized_revenue": r.realized_revenue, "rom": r.rom}
    if kind == "emsr_b":
        r = revmng.emsr_b(inp["classes"], inp["capacity"])
        return {"protection_levels": list(r.protection_levels),
                "booking_limits_int": list(r.booking_limits_int)}
    if kind == "group_displacement":
        cost = revmng.group_displacement(inp["group_size"], inp["capacity"],
                                         inp["demand"], inp["value_per_unit"])
        return {"displacement_cost": cost}
    if kind == "group":
        r = revmng.evaluate_group(inp["group_rate"], inp["units"],
                                  displacement_cost=inp["displacement_cost"],
                                  variable_cost=inp.get("variable_cost", 0.0))
        return {"net_benefit": r.net_benefit, "break_even_rate": r.break_even_rate,
                "accept": r.accept}
    if kind == "los":
        r = revmng.evaluate_stay(inp["nightly_bid_prices"], inp["nights"],
                                 inp["total_rate"])
        return {"hurdle": r.hurdle, "slack": r.slack, "accept": r.accept}
    if kind == "newsvendor":
        r = revmng.newsvendor(inp["price"], inp["cost"], inp["demand_mean"],
                              inp["demand_sd"])
        return {"critical_ratio": r.critical_ratio,
                "optimal_quantity": r.optimal_quantity}
    if kind == "overbooking_service":
        r = revmng.overbooking_limit(inp["capacity"], no_show_rate=inp["no_show_rate"])
        return {"authorization_limit": r.authorization_limit,
                "expected_shows": r.expected_shows}
    raise ValueError(kind)


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case(case):
    got = _compute(case)
    tol = case["tol"]
    for field, expected in case["expected"].items():
        actual = got[field]
        if isinstance(expected, bool):
            assert actual is expected, f"{case['id']}.{field}"
        elif field == "rom":
            assert actual == pytest.approx(expected, abs=0.005), case["id"]
        else:
            assert actual == pytest.approx(expected, abs=tol), \
                f"{case['id']}.{field}: got {actual}, expected {expected}"
