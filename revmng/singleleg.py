"""Single-resource (single-leg) capacity control: how to split one pool of
fixed, perishable capacity across nested fare classes so the cheaper classes do
not crowd out later, more valuable demand.

Three standard methods are provided:

* ``littlewood`` - the optimal two-class rule (Littlewood, 1972).
* ``emsr_a`` and ``emsr_b`` - Belobaba's Expected Marginal Seat Revenue
  heuristics for more than two classes. EMSR-b (the industry default) collapses
  the higher classes into one with a demand-weighted fare; EMSR-a sums the
  pairwise protection levels and is more conservative.

Demand for each class is assumed normal and independent, with the classic
low-before-high booking assumption. Both heuristics return *nested* protection
levels and booking limits: the booking limit for a class is the capacity left
after protecting everything more valuable than it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ._result import Alert, make_meta, num
from ._stats import norm_ppf

SCHEMA = 1


@dataclass(frozen=True)
class FareClass:
    """One fare class: its fare and its (normal) demand mean and std dev."""

    fare: float
    mean: float
    sd: float = 0.0
    name: str | None = None


def _as_class(item, index: int) -> FareClass:
    if isinstance(item, FareClass):
        c = item
    elif isinstance(item, Mapping):
        c = FareClass(fare=float(item["fare"]), mean=float(item["mean"]),
                      sd=float(item.get("sd", 0.0)), name=item.get("name"))
    elif isinstance(item, Sequence) and not isinstance(item, str):
        fare, mean = float(item[0]), float(item[1])
        sd = float(item[2]) if len(item) > 2 else 0.0
        name = item[3] if len(item) > 3 else None
        c = FareClass(fare=fare, mean=mean, sd=sd, name=name)
    else:
        raise TypeError("each class must be a FareClass, mapping or (fare, mean, sd)")
    if c.fare <= 0:
        raise ValueError("fare must be positive")
    if c.mean < 0 or c.sd < 0:
        raise ValueError("demand mean and sd must be non-negative")
    return FareClass(c.fare, c.mean, c.sd, c.name or f"class {index + 1}")


def _normalize(classes) -> list[FareClass]:
    items = [_as_class(c, i) for i, c in enumerate(classes)]
    if len(items) < 2:
        raise ValueError("need at least two fare classes")
    ordered = sorted(items, key=lambda c: c.fare, reverse=True)
    return ordered


@dataclass(frozen=True)
class AllocationResult:
    """Nested protection levels and booking limits for a single resource."""

    name: str | None
    method: str
    capacity: float
    classes: tuple[dict, ...]
    protection_levels: tuple[float, ...]   # cumulative; one per class boundary
    booking_limits: tuple[float, ...]      # nested; first class gets capacity
    alerts: tuple[Alert, ...]
    meta: dict
    expected_revenue: float | None = None  # set by the optimal (DP) policy

    @property
    def booking_limits_int(self) -> tuple[int, ...]:
        """Whole-seat booking limits: capacity minus the floored protection."""
        out = [int(self.capacity)]
        for y in self.protection_levels:
            out.append(max(0, int(self.capacity) - math.floor(y)))
        return tuple(out)

    @property
    def protection_levels_int(self) -> tuple[int, ...]:
        return tuple(math.floor(y) for y in self.protection_levels)

    def summary(self) -> str:
        head = f"{self.method}" + (f" {self.name}" if self.name else "")
        lines = [f"{head} - capacity {num(self.capacity, 0)}",
                 "  class        fare   protect  booking limit"]
        limits = self.booking_limits_int
        prot = (0, *self.protection_levels_int)
        for i, c in enumerate(self.classes):
            lines.append(
                f"  {c['name']:<10} {num(c['fare'], 0):>6}   {prot[i]:>6}   "
                f"{limits[i]:>11}")
        if self.expected_revenue is not None:
            lines.append(f"  expected revenue {num(self.expected_revenue, 2)}")
        for a in self.alerts:
            lines.append("  " + str(a))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "name": self.name,
            "method": self.method,
            "capacity": self.capacity,
            "classes": list(self.classes),
            "protection_levels": list(self.protection_levels),
            "protection_levels_int": list(self.protection_levels_int),
            "booking_limits": list(self.booking_limits),
            "booking_limits_int": list(self.booking_limits_int),
            "expected_revenue": self.expected_revenue,
            "alerts": [
                {"indicator": a.indicator, "message": a.message, "severity": a.severity}
                for a in self.alerts
            ],
            "meta": self.meta,
        }


def littlewood(fare_high: float, fare_low: float, mean_high: float,
               sd_high: float) -> float:
    """Protection level for the high fare class in the two-class problem.

    Returns the number of seats to reserve for the high class; sell the low
    class while remaining capacity exceeds this level. The rule is
    ``y = mu + z * sigma`` with ``z = Phi^-1(1 - fare_low / fare_high)``, so the
    low-class demand never enters - only the fare ratio and high-class demand.
    """
    fare_high = float(fare_high)
    fare_low = float(fare_low)
    if fare_high <= 0 or fare_low <= 0:
        raise ValueError("fares must be positive")
    if fare_low > fare_high:
        raise ValueError("fare_low must not exceed fare_high")
    z = norm_ppf(1.0 - fare_low / fare_high)
    return max(0.0, float(mean_high) + z * float(sd_high))


def _build(classes, capacity, protection, method, name,
           expected_revenue=None) -> AllocationResult:
    capacity = float(capacity)
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    protection = tuple(max(0.0, min(y, capacity)) for y in protection)
    limits = (capacity, *(max(0.0, capacity - y) for y in protection))
    alerts: list[Alert] = []
    total_mean = sum(c.mean for c in classes)
    if total_mean < capacity:
        alerts.append(Alert(
            "low_demand",
            f"total mean demand {total_mean:g} is below capacity {capacity:g}; "
            "protection may not bind",
            "info"))
    cls = tuple({"name": c.name, "fare": c.fare, "mean": c.mean, "sd": c.sd}
                for c in classes)
    meta = make_meta({"method": method, "capacity": capacity, "classes": cls})
    return AllocationResult(name, method, capacity, cls, protection, limits,
                            tuple(alerts), meta, expected_revenue)


def emsr_b(classes, capacity, *, name: str | None = None) -> AllocationResult:
    """EMSR-b nested protection levels and booking limits.

    For the boundary above class ``j`` the higher classes are pooled: their
    means add, their variances add (independence), and they share one
    demand-weighted fare ``r_bar``. Littlewood's rule is then applied once with
    the next fare against ``r_bar``.
    """
    cls = _normalize(classes)
    protection = []
    for j in range(1, len(cls)):
        higher = cls[:j]
        agg_mean = sum(c.mean for c in higher)
        agg_sd = math.sqrt(sum(c.sd ** 2 for c in higher))
        weighted_fare = (sum(c.fare * c.mean for c in higher) / agg_mean
                         if agg_mean > 0 else higher[0].fare)
        ratio = min(1.0, cls[j].fare / weighted_fare)
        z = norm_ppf(1.0 - ratio)
        protection.append(agg_mean + z * agg_sd)
    return _build(cls, capacity, protection, "EMSR-b", name)


def emsr_a(classes, capacity, *, name: str | None = None) -> AllocationResult:
    """EMSR-a nested protection levels and booking limits.

    The protection above class ``j`` is the sum of the pairwise Littlewood
    protection levels of each higher class against class ``j``'s fare. This adds
    the safety stocks rather than pooling demand, so it protects more (and is
    more conservative) than EMSR-b.
    """
    cls = _normalize(classes)
    protection = []
    for j in range(1, len(cls)):
        y = 0.0
        for c in cls[:j]:
            ratio = min(1.0, cls[j].fare / c.fare)
            z = norm_ppf(1.0 - ratio)
            y += max(0.0, c.mean + z * c.sd)
        protection.append(y)
    return _build(cls, capacity, protection, "EMSR-a", name)
