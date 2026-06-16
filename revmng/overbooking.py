"""Overbooking: how many reservations to accept above physical capacity so that
no-shows do not leave the resource under-used, without bumping too many
customers who do show up.

Two methods:

* service level (deterministic) - authorize ``capacity / (1 - no_show_rate)``
  so the expected number of show-ups equals capacity.
* cost based - choose the authorization limit that minimises expected
  ``denied_cost * oversales + spoilage_cost * empty_seats`` under a binomial
  show-up model. This is a newsvendor trade-off: the optimal limit is where the
  marginal cost of one more denied boarding balances the marginal saving from
  one fewer empty seat.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._result import Alert, make_meta, money, num
from ._stats import binom_pmf

SCHEMA = 1


@dataclass(frozen=True)
class OverbookingResult:
    """An authorization (overbooking) limit and its expected consequences."""

    name: str | None
    method: str
    capacity: int
    no_show_rate: float
    authorization_limit: int
    overbooking_pad: int
    expected_shows: float
    expected_oversales: float
    expected_spoilage: float
    expected_cost: float | None
    denied_cost: float | None
    spoilage_cost: float | None
    alerts: tuple[Alert, ...]
    meta: dict

    @property
    def virtual_capacity(self) -> int:
        return self.authorization_limit

    def summary(self) -> str:
        head = f"overbooking ({self.method})" + (f" {self.name}" if self.name else "")
        lines = [
            f"{head}",
            f"  capacity              {self.capacity}",
            f"  no-show rate          {num(100 * self.no_show_rate, 1)}%",
            f"  authorize up to       {self.authorization_limit}  "
            f"(+{self.overbooking_pad} over capacity)",
            f"  expected show-ups     {num(self.expected_shows, 1)}",
            f"  expected oversales    {num(self.expected_oversales, 2)}",
            f"  expected empty seats  {num(self.expected_spoilage, 2)}",
        ]
        if self.expected_cost is not None:
            lines.append(f"  expected cost         {money(self.expected_cost)}")
        for a in self.alerts:
            lines.append("  " + str(a))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "name": self.name,
            "method": self.method,
            "capacity": self.capacity,
            "no_show_rate": self.no_show_rate,
            "authorization_limit": self.authorization_limit,
            "overbooking_pad": self.overbooking_pad,
            "expected": {
                "shows": self.expected_shows,
                "oversales": self.expected_oversales,
                "spoilage": self.expected_spoilage,
                "cost": self.expected_cost,
            },
            "costs": {"denied": self.denied_cost, "spoilage": self.spoilage_cost},
            "alerts": [
                {"indicator": a.indicator, "message": a.message, "severity": a.severity}
                for a in self.alerts
            ],
            "meta": self.meta,
        }


def _expected_over_spoil(u: int, q: float, capacity: int) -> tuple[float, float]:
    """Expected oversales and empty seats when authorizing ``u`` reservations
    with show probability ``q`` against ``capacity`` seats."""
    over = 0.0
    spoil = 0.0
    for s in range(u + 1):
        p = binom_pmf(s, u, q)
        if p == 0.0:
            continue
        if s > capacity:
            over += (s - capacity) * p
        elif s < capacity:
            spoil += (capacity - s) * p
    return over, spoil


def overbooking_limit(capacity, *, no_show_rate: float, denied_cost=None,
                      spoilage_cost=None, name: str | None = None) -> OverbookingResult:
    """Authorization limit for one resource given a no-show rate.

    With both ``denied_cost`` (per bumped customer) and ``spoilage_cost`` (per
    empty seat) the cost-minimising limit is returned; otherwise the
    service-level limit ``round(capacity / (1 - no_show_rate))`` is used. The
    expected show-ups, oversales and empty seats are computed from a binomial
    show-up model either way.
    """
    capacity = int(capacity)
    if capacity <= 0:
        raise ValueError("capacity must be a positive number of seats")
    no_show_rate = float(no_show_rate)
    if not 0.0 <= no_show_rate < 1.0:
        raise ValueError("no_show_rate must be in [0, 1)")
    q = 1.0 - no_show_rate

    cost_mode = denied_cost is not None and spoilage_cost is not None
    alerts: list[Alert] = []

    if cost_mode:
        denied_cost = float(denied_cost)
        spoilage_cost = float(spoilage_cost)
        if denied_cost < 0 or spoilage_cost < 0:
            raise ValueError("costs must be non-negative")
        max_u = int(capacity / q) + capacity + 10
        best_u, best_cost, best_over, best_spoil = capacity, None, 0.0, 0.0
        misses = 0
        u = capacity
        while u <= max_u:
            over, spoil = _expected_over_spoil(u, q, capacity)
            cost = denied_cost * over + spoilage_cost * spoil
            if best_cost is None or cost < best_cost - 1e-12:
                best_u, best_cost, best_over, best_spoil = u, cost, over, spoil
                misses = 0
            else:
                misses += 1
                if misses >= 5:
                    break
            u += 1
        method = "cost"
        limit, exp_cost = best_u, best_cost
        over, spoil = best_over, best_spoil
    else:
        if denied_cost is not None or spoilage_cost is not None:
            alerts.append(Alert(
                "partial_costs",
                "give both denied_cost and spoilage_cost for the cost-based "
                "limit; using the service-level limit instead", "warning"))
        method = "service_level"
        limit = round(capacity / q)
        over, spoil = _expected_over_spoil(limit, q, capacity)
        exp_cost = None

    return OverbookingResult(
        name, method, capacity, no_show_rate, int(limit), int(limit) - capacity,
        limit * q, over, spoil, exp_cost,
        denied_cost if cost_mode else None,
        spoilage_cost if cost_mode else None,
        tuple(alerts), make_meta({"method": method, "capacity": capacity,
                                  "no_show_rate": no_show_rate,
                                  "denied_cost": denied_cost,
                                  "spoilage_cost": spoilage_cost}))
