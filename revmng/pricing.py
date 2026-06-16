"""Price-based decisions: the newsvendor stocking quantity for one selling
period, and the profit-maximising price for a demand curve.

``newsvendor`` returns the order quantity that balances the cost of stocking too
much against the cost of stocking too little (the critical-fractile rule), the
same marginal logic that underlies Littlewood's rule. ``optimal_price`` returns
the price that maximises contribution for a linear or constant-elasticity demand
model; with zero unit cost the linear case gives the revenue-maximising price.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._result import Alert, make_meta, money, num
from ._stats import norm_loss, norm_ppf

SCHEMA = 1


@dataclass(frozen=True)
class NewsvendorResult:
    name: str | None
    price: float
    cost: float
    salvage: float
    demand_mean: float
    demand_sd: float
    critical_ratio: float
    z: float
    optimal_quantity: float
    expected_sales: float
    expected_shortage: float
    expected_leftover: float
    expected_profit: float
    alerts: tuple[Alert, ...]
    meta: dict

    def summary(self) -> str:
        head = "newsvendor" + (f" {self.name}" if self.name else "")
        lines = [
            f"{head}",
            f"  critical ratio       {num(self.critical_ratio, 3)}",
            f"  optimal quantity     {num(self.optimal_quantity, 1)}",
            f"  expected sales       {num(self.expected_sales, 1)}",
            f"  expected shortage    {num(self.expected_shortage, 1)}",
            f"  expected leftover    {num(self.expected_leftover, 1)}",
            f"  expected profit      {money(self.expected_profit)}",
        ]
        for a in self.alerts:
            lines.append("  " + str(a))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA, "name": self.name, "kind": "newsvendor",
            "price": self.price, "cost": self.cost, "salvage": self.salvage,
            "demand": {"mean": self.demand_mean, "sd": self.demand_sd},
            "critical_ratio": self.critical_ratio, "z": self.z,
            "optimal_quantity": self.optimal_quantity,
            "expected": {
                "sales": self.expected_sales, "shortage": self.expected_shortage,
                "leftover": self.expected_leftover, "profit": self.expected_profit,
            },
            "alerts": [
                {"indicator": a.indicator, "message": a.message, "severity": a.severity}
                for a in self.alerts
            ],
            "meta": self.meta,
        }


def newsvendor(price, cost, demand_mean, demand_sd, *, salvage: float = 0.0,
               name: str | None = None) -> NewsvendorResult:
    """Optimal single-period stocking quantity for normal demand.

    ``critical_ratio = (price - cost) / ((price - cost) + (cost - salvage))`` and
    the optimal quantity is its normal quantile, ``mean + z * sd``. Expected
    sales, shortage, leftover and profit follow from the normal loss function.
    """
    price, cost, salvage = float(price), float(cost), float(salvage)
    demand_mean, demand_sd = float(demand_mean), float(demand_sd)
    underage = price - cost
    overage = cost - salvage
    if underage <= 0:
        raise ValueError("price must exceed cost")
    if overage <= 0:
        raise ValueError("cost must exceed salvage value")
    if demand_sd < 0:
        raise ValueError("demand_sd must be non-negative")

    cr = underage / (underage + overage)
    z = norm_ppf(cr)
    q = demand_mean + z * demand_sd
    shortage = demand_sd * norm_loss(z)
    sales = demand_mean - shortage
    leftover = q - demand_mean + shortage
    profit = underage * sales - overage * leftover

    alerts: list[Alert] = []
    if q < 0:
        alerts.append(Alert("negative_quantity",
                            "optimal quantity is negative; check inputs", "warning"))
    return NewsvendorResult(
        name, price, cost, salvage, demand_mean, demand_sd, cr, z, q, sales,
        shortage, leftover, profit, tuple(alerts),
        make_meta({"price": price, "cost": cost, "salvage": salvage,
                   "mean": demand_mean, "sd": demand_sd}))


@dataclass(frozen=True)
class LinearDemand:
    """Linear demand curve ``q(p) = intercept - slope * p`` (slope > 0)."""

    intercept: float
    slope: float

    def demand(self, price: float) -> float:
        return self.intercept - self.slope * price

    def optimal_price(self, unit_cost: float) -> float:
        return self.intercept / (2.0 * self.slope) + unit_cost / 2.0

    def point_elasticity(self, price: float) -> float:
        q = self.demand(price)
        return -self.slope * price / q if q > 0 else float("nan")


@dataclass(frozen=True)
class ConstantElasticityDemand:
    """Constant-elasticity demand ``q(p) = scale * p ** (-elasticity)``."""

    scale: float
    elasticity: float

    def demand(self, price: float) -> float:
        return self.scale * price ** (-self.elasticity)

    def optimal_price(self, unit_cost: float) -> float:
        if self.elasticity <= 1.0:
            raise ValueError("constant-elasticity profit max needs elasticity > 1")
        if unit_cost <= 0.0:
            raise ValueError("constant-elasticity profit max needs unit_cost > 0")
        return unit_cost * self.elasticity / (self.elasticity - 1.0)

    def point_elasticity(self, price: float) -> float:
        return self.elasticity


@dataclass(frozen=True)
class PriceResult:
    name: str | None
    model: str
    optimal_price: float
    unit_cost: float
    quantity: float
    revenue: float
    profit: float
    margin: float
    elasticity: float
    alerts: tuple[Alert, ...]
    meta: dict

    def summary(self) -> str:
        head = f"optimal price ({self.model})" + (f" {self.name}" if self.name else "")
        lines = [
            f"{head}",
            f"  price                {money(self.optimal_price)}",
            f"  quantity             {num(self.quantity, 1)}",
            f"  revenue              {money(self.revenue)}",
            f"  profit               {money(self.profit)}",
            f"  margin               {num(100 * self.margin, 1)}%",
            f"  elasticity at price  {num(self.elasticity, 2)}",
        ]
        for a in self.alerts:
            lines.append("  " + str(a))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA, "name": self.name, "kind": "price", "model": self.model,
            "optimal_price": self.optimal_price, "unit_cost": self.unit_cost,
            "quantity": self.quantity, "revenue": self.revenue, "profit": self.profit,
            "margin": self.margin, "elasticity": self.elasticity,
            "alerts": [
                {"indicator": a.indicator, "message": a.message, "severity": a.severity}
                for a in self.alerts
            ],
            "meta": self.meta,
        }


def optimal_price(demand, unit_cost: float = 0.0,
                  name: str | None = None) -> PriceResult:
    """Profit-maximising price for a demand model.

    ``demand`` is a :class:`LinearDemand` or :class:`ConstantElasticityDemand`.
    With ``unit_cost = 0`` the linear model returns the revenue-maximising price.
    """
    unit_cost = float(unit_cost)
    if unit_cost < 0:
        raise ValueError("unit_cost must be non-negative")
    model = type(demand).__name__
    price = demand.optimal_price(unit_cost)
    if price <= unit_cost:
        raise ValueError("optimal price is not above unit cost; check the demand model")
    q = demand.demand(price)
    if q <= 0:
        raise ValueError("demand is non-positive at the optimal price; check inputs")
    revenue = price * q
    profit = (price - unit_cost) * q
    margin = (price - unit_cost) / price
    return PriceResult(
        name, model, price, unit_cost, q, revenue, profit, margin,
        demand.point_elasticity(price), (),
        make_meta({"model": model, "unit_cost": unit_cost,
                   "params": demand.__dict__}))
