"""The measurement layer: the standard, vendor-neutral performance ratios used
to judge revenue management, plus the revenue opportunity metric.

The ratios (RevPAR, ADR, occupancy, yield, load factor, RASM/CASM, spill and
spoilage) are simple functions that return a number. ``revenue_opportunity``
scores a set of booking limits against two benchmarks - perfect hindsight and no
controls at all - and returns how much of the available revenue gap the controls
captured.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ._result import Alert, make_meta, money, num

SCHEMA = 1


def _safe_div(numerator: float, denominator: float, what: str) -> float:
    denominator = float(denominator)
    if denominator <= 0:
        raise ValueError(f"{what} must be positive")
    return float(numerator) / denominator


def revpar(room_revenue: float, available_rooms: float) -> float:
    """Revenue per available room = room revenue / available rooms (= ADR x occupancy)."""
    return _safe_div(room_revenue, available_rooms, "available_rooms")


def adr(room_revenue: float, rooms_sold: float) -> float:
    """Average daily rate = room revenue / rooms sold."""
    return _safe_div(room_revenue, rooms_sold, "rooms_sold")


def occupancy(rooms_sold: float, available_rooms: float) -> float:
    """Occupancy = rooms sold / available rooms."""
    return _safe_div(rooms_sold, available_rooms, "available_rooms")


def yield_(passenger_revenue: float, revenue_passenger_units: float) -> float:
    """Yield = passenger revenue / revenue passenger miles (or kilometres)."""
    return _safe_div(passenger_revenue, revenue_passenger_units,
                     "revenue_passenger_units")


def load_factor(traffic: float, capacity: float) -> float:
    """Load factor = traffic / capacity (e.g. RPK / ASK, or seats sold / seats)."""
    return _safe_div(traffic, capacity, "capacity")


def rasm(revenue: float, available_seat_units: float) -> float:
    """Revenue per available seat mile (or kilometre)."""
    return _safe_div(revenue, available_seat_units, "available_seat_units")


def casm(cost: float, available_seat_units: float) -> float:
    """Cost per available seat mile (or kilometre)."""
    return _safe_div(cost, available_seat_units, "available_seat_units")


def spill(demand: float, capacity: float) -> float:
    """Demand turned away for lack of capacity = max(demand - capacity, 0)."""
    return max(0.0, float(demand) - float(capacity))


def spoilage(capacity: float, sold: float) -> float:
    """Perishable capacity left unsold = max(capacity - sold, 0)."""
    return max(0.0, float(capacity) - float(sold))


def _columns(classes, demand, booking_limits):
    """Normalise parallel inputs into (fares, demand, limits) sorted high->low."""
    if isinstance(classes, Mapping):
        raise TypeError("classes must be a sequence of fares or class mappings")
    fares, names = [], []
    for i, c in enumerate(classes):
        if isinstance(c, Mapping):
            fares.append(float(c["fare"]))
            names.append(c.get("name", f"class {i + 1}"))
        elif isinstance(c, Sequence) and not isinstance(c, str):
            fares.append(float(c[0]))
            names.append(c[1] if len(c) > 1 else f"class {i + 1}")
        else:
            fares.append(float(c))
            names.append(f"class {i + 1}")
    n = len(fares)
    if n < 1:
        raise ValueError("need at least one class")
    demand = [float(d) for d in demand]
    if len(demand) != n:
        raise ValueError("demand must have one value per class")
    limits = None if booking_limits is None else [float(b) for b in booking_limits]
    if limits is not None and len(limits) != n:
        raise ValueError("booking_limits must have one value per class")
    order = sorted(range(n), key=lambda i: fares[i], reverse=True)
    fares = [fares[i] for i in order]
    names = [names[i] for i in order]
    demand = [demand[i] for i in order]
    limits = None if limits is None else [limits[i] for i in order]
    return fares, names, demand, limits


def nested_revenue(fares, booking_limits, demand, capacity) -> float:
    """Revenue realised under nested booking limits with low-before-high arrival.

    ``fares``, ``booking_limits`` and ``demand`` are parallel, ordered from the
    highest fare to the lowest; ``booking_limits[i]`` is the most seats that may
    go to class ``i`` and every lower class together. Lower classes book first;
    each class sells up to its remaining nested room and the remaining capacity.
    """
    capacity = float(capacity)
    n = len(fares)
    sold = [0.0] * n
    total = 0.0
    for i in range(n - 1, -1, -1):
        below = sum(sold[i + 1:])
        room_class = max(0.0, min(booking_limits[i], capacity) - below)
        room_cap = capacity - total
        s = max(0.0, min(demand[i], room_class, room_cap))
        sold[i] = s
        total += s
    return sum(f * s for f, s in zip(fares, sold))


@dataclass(frozen=True)
class RevenueOpportunityResult:
    name: str | None
    capacity: float
    classes: tuple[dict, ...]
    perfect_revenue: float
    no_control_revenue: float
    realized_revenue: float | None
    rom: float | None
    alerts: tuple[Alert, ...]
    meta: dict

    def summary(self) -> str:
        head = "revenue opportunity" + (f" {self.name}" if self.name else "")
        lines = [
            f"{head} - capacity {num(self.capacity, 0)}",
            f"  perfect (hindsight)  {money(self.perfect_revenue)}",
            f"  no controls          {money(self.no_control_revenue)}",
        ]
        if self.realized_revenue is not None:
            lines.append(f"  realized             {money(self.realized_revenue)}")
        if self.rom is not None:
            lines.append(f"  ROM                  {num(100 * self.rom, 1)}%")
        for a in self.alerts:
            lines.append("  " + str(a))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA, "name": self.name, "capacity": self.capacity,
            "classes": list(self.classes),
            "perfect_revenue": self.perfect_revenue,
            "no_control_revenue": self.no_control_revenue,
            "realized_revenue": self.realized_revenue,
            "rom": self.rom,
            "alerts": [
                {"indicator": a.indicator, "message": a.message, "severity": a.severity}
                for a in self.alerts
            ],
            "meta": self.meta,
        }


def revenue_opportunity(classes, demand, capacity, *, booking_limits=None,
                        name: str | None = None) -> RevenueOpportunityResult:
    """Score booking limits against perfect-hindsight and no-control benchmarks.

    ``classes`` are the fares (or class mappings) and ``demand`` the realised
    demand per class. Perfect revenue fills capacity with the highest fares
    first; no-control revenue lets the lowest fares book first with no
    protection. When ``booking_limits`` are given, the realised revenue under
    those nested limits and the revenue opportunity metric
    ``ROM = (realised - no_control) / (perfect - no_control)`` are returned.
    """
    fares, names, demand, limits = _columns(classes, demand, booking_limits)
    capacity = float(capacity)
    if capacity <= 0:
        raise ValueError("capacity must be positive")

    perfect = 0.0
    used = 0.0
    for f, d in zip(fares, demand):  # already high -> low
        take = max(0.0, min(d, capacity - used))
        perfect += f * take
        used += take

    no_control = nested_revenue(fares, [capacity] * len(fares), demand, capacity)

    realized = rom = None
    alerts: list[Alert] = []
    if limits is not None:
        realized = nested_revenue(fares, limits, demand, capacity)
        gap = perfect - no_control
        if gap <= 0:
            alerts.append(Alert("no_gap",
                                "perfect and no-control revenue are equal; ROM "
                                "is undefined", "info"))
        else:
            rom = (realized - no_control) / gap

    cls = tuple({"name": nm, "fare": f} for nm, f in zip(names, fares))
    return RevenueOpportunityResult(
        name, capacity, cls, perfect, no_control, realized, rom, tuple(alerts),
        make_meta({"capacity": capacity, "fares": fares, "demand": demand,
                   "booking_limits": limits}))
