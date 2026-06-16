"""Length-of-stay control for multi-night (or multi-leg) requests.

A stay that spans several nights consumes a separate, capacity-constrained
resource each night, so it cannot be judged one night at a time. Each night
carries a bid price (its marginal value, e.g. from :func:`revmng.bid_prices`);
a stay is worth accepting when its total rate covers the sum of the bid prices
of the nights it occupies. This is the bid-price control of Talluri and van
Ryzin (2004) applied to length of stay.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ._result import Alert, make_meta, money

SCHEMA = 1


@dataclass(frozen=True)
class StayResult:
    name: str | None
    nights: tuple
    total_rate: float
    hurdle: float
    slack: float
    accept: bool
    per_night: dict
    alerts: tuple[Alert, ...]
    meta: dict

    def summary(self) -> str:
        head = "length-of-stay" + (f" {self.name}" if self.name else "")
        verdict = "ACCEPT" if self.accept else "REJECT"
        lines = [
            f"{head}: {verdict}",
            f"  nights               {len(self.nights)}",
            f"  total rate           {money(self.total_rate)}",
            f"  bid-price hurdle     {money(self.hurdle)}",
            f"  slack                {money(self.slack)}",
        ]
        for a in self.alerts:
            lines.append("  " + str(a))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA, "name": self.name, "nights": list(self.nights),
            "total_rate": self.total_rate, "hurdle": self.hurdle,
            "slack": self.slack, "accept": self.accept, "per_night": self.per_night,
            "alerts": [
                {"indicator": a.indicator, "message": a.message, "severity": a.severity}
                for a in self.alerts
            ],
            "meta": self.meta,
        }


def evaluate_stay(nightly_bid_prices: Mapping, nights, total_rate: float, *,
                  name: str | None = None) -> StayResult:
    """Accept or reject a stay against the bid prices of the nights it spans.

    ``nightly_bid_prices`` maps each night (any hashable key) to its bid price;
    ``nights`` is the sequence of nights the stay occupies; ``total_rate`` is the
    revenue for the whole stay. The stay clears when ``total_rate`` is at least
    the sum of the bid prices of its nights.
    """
    if not isinstance(nightly_bid_prices, Mapping):
        raise TypeError("nightly_bid_prices must be a mapping night -> bid price")
    if isinstance(nights, str) or not isinstance(nights, Sequence):
        raise TypeError("nights must be a sequence of night keys")
    if not nights:
        raise ValueError("a stay must occupy at least one night")

    total_rate = float(total_rate)
    per_night = {}
    alerts: list[Alert] = []
    for n in nights:
        if n not in nightly_bid_prices:
            raise ValueError(f"no bid price given for night '{n}'")
        per_night[n] = float(nightly_bid_prices[n])
    hurdle = sum(per_night.values())
    slack = total_rate - hurdle
    return StayResult(
        name, tuple(nights), total_rate, hurdle, slack, slack >= 0, per_night,
        tuple(alerts), make_meta({"nights": list(nights), "total_rate": total_rate,
                                  "bid_prices": per_night}))
