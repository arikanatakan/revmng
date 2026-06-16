"""Network (multi-resource) revenue management by bid prices.

When a product consumes several resources at once - a connecting itinerary that
uses two flight legs, or a multi-night stay - a seat or room cannot be valued in
isolation. The deterministic linear program (DLP) allocates expected demand to
products to maximise revenue subject to each resource's capacity; the shadow
price of each capacity constraint is its bid price. A request is then worth
accepting when its fare covers the sum of the bid prices of the resources it
uses.

This module needs SciPy. Install it with ``pip install revmng[network]``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ._result import Alert, make_meta, money, num

SCHEMA = 1


@dataclass(frozen=True)
class Product:
    """A sellable product: its fare, the resources it uses, and its demand."""

    fare: float
    uses: dict          # resource -> units consumed
    demand: float
    name: str | None = None


def _as_product(item, index: int) -> Product:
    if isinstance(item, Product):
        p = item
    elif isinstance(item, Mapping):
        uses = item["uses"]
        if isinstance(uses, str) or not isinstance(uses, Mapping):
            raise TypeError("product 'uses' must be a mapping resource -> units")
        p = Product(float(item["fare"]), dict(uses), float(item["demand"]),
                    item.get("name"))
    else:
        raise TypeError("each product must be a Product or a mapping")
    if p.fare < 0 or p.demand < 0:
        raise ValueError("fare and demand must be non-negative")
    return Product(p.fare, {str(k): float(v) for k, v in p.uses.items()},
                   p.demand, p.name or f"product {index + 1}")


@dataclass(frozen=True)
class NetworkResult:
    name: str | None
    resources: tuple[str, ...]
    capacities: dict
    bid_prices: dict
    allocation: tuple[dict, ...]
    expected_revenue: float
    alerts: tuple[Alert, ...]
    meta: dict

    def accept(self, fare: float, uses: Mapping) -> bool:
        """True when ``fare`` covers the bid prices of the resources it uses."""
        threshold = sum(self.bid_prices.get(str(r), 0.0) * float(u)
                        for r, u in uses.items())
        return float(fare) >= threshold

    def summary(self) -> str:
        head = "network bid prices" + (f" {self.name}" if self.name else "")
        lines = [head, "  resource        capacity   bid price"]
        for r in self.resources:
            lines.append(f"  {r:<14} {num(self.capacities[r], 0):>8}   "
                         f"{money(self.bid_prices[r])}")
        lines.append(f"  expected revenue {money(self.expected_revenue)}")
        for a in self.alerts:
            lines.append("  " + str(a))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA, "name": self.name,
            "resources": list(self.resources), "capacities": self.capacities,
            "bid_prices": self.bid_prices, "allocation": list(self.allocation),
            "expected_revenue": self.expected_revenue,
            "alerts": [
                {"indicator": a.indicator, "message": a.message, "severity": a.severity}
                for a in self.alerts
            ],
            "meta": self.meta,
        }


def bid_prices(products, capacities: Mapping, *,
               name: str | None = None) -> NetworkResult:
    """Bid prices and the DLP allocation for a resource network.

    ``products`` is a sequence of :class:`Product` (or mappings with ``fare``,
    ``uses`` and ``demand``); ``capacities`` maps each resource to its capacity.
    Returns the per-resource bid prices (the capacity shadow prices), the
    expected revenue and the allocation of demand to each product.
    """
    try:
        from scipy.optimize import linprog
    except ImportError as exc:  # pragma: no cover - exercised only without scipy
        raise ImportError(
            "network bid pricing needs SciPy; install it with "
            "'pip install revmng[network]'") from exc

    if isinstance(products, (str, Mapping)) or not isinstance(products, Sequence):
        raise TypeError("products must be a sequence of products")
    prods = [_as_product(p, i) for i, p in enumerate(products)]
    if not prods:
        raise ValueError("need at least one product")
    caps = {str(k): float(v) for k, v in capacities.items()}
    if not caps:
        raise ValueError("need at least one resource capacity")
    for p in prods:
        for r in p.uses:
            if r not in caps:
                raise ValueError(f"product '{p.name}' uses unknown resource '{r}'")

    resources = tuple(caps.keys())
    cost = [-p.fare for p in prods]                      # maximise revenue
    a_ub = [[p.uses.get(r, 0.0) for p in prods] for r in resources]
    b_ub = [caps[r] for r in resources]
    bounds = [(0.0, p.demand) for p in prods]

    res = linprog(cost, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
    if not res.success:  # pragma: no cover - degenerate inputs
        raise ValueError(f"the linear program did not solve: {res.message}")

    marginals = res.ineqlin.marginals
    bids = {r: max(0.0, -float(m)) for r, m in zip(resources, marginals)}
    alloc = tuple({"name": p.name, "fare": p.fare, "allocation": float(x)}
                  for p, x in zip(prods, res.x))
    revenue = float(-res.fun)

    alerts: list[Alert] = []
    if all(v == 0.0 for v in bids.values()):
        alerts.append(Alert("slack",
                            "no resource is binding; every request clears at its "
                            "own fare", "info"))
    return NetworkResult(
        name, resources, caps, bids, alloc, revenue, tuple(alerts),
        make_meta({"products": [{"fare": p.fare, "uses": p.uses,
                                 "demand": p.demand} for p in prods],
                   "capacities": caps}))
