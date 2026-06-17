"""Group evaluation by displacement analysis.

A group request fills capacity that could otherwise go to higher-yield
individual demand. The displaced demand has an opportunity cost: its lost
contribution, valued at the marginal worth of each seat or room it gives up (a
protection-level value or a network bid price). Accept the group when its own
contribution covers that opportunity cost.

``group_displacement`` computes the displaced units and their value for a
multi-night (or multi-leg) block from the per-period demand and capacity.
``evaluate_group`` turns a group's rate, size and displacement cost into an
accept or reject decision and the break-even rate.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ._result import Alert, make_meta, money, num

SCHEMA = 1


@dataclass(frozen=True)
class GroupResult:
    name: str | None
    units: float                 # room-nights or seats the group consumes
    group_rate: float            # revenue per unit
    variable_cost: float         # cost per unit served
    group_contribution: float
    displacement_cost: float
    net_benefit: float
    break_even_rate: float
    accept: bool
    alerts: tuple[Alert, ...]
    meta: dict

    def summary(self) -> str:
        head = "group evaluation" + (f" {self.name}" if self.name else "")
        verdict = "ACCEPT" if self.accept else "REJECT"
        lines = [
            f"{head}: {verdict}",
            f"  units                {num(self.units, 0)}",
            f"  group rate           {money(self.group_rate)}",
            f"  group contribution   {money(self.group_contribution)}",
            f"  displacement cost    {money(self.displacement_cost)}",
            f"  net benefit          {money(self.net_benefit)}",
            f"  break-even rate      {money(self.break_even_rate)}",
        ]
        for a in self.alerts:
            lines.append("  " + str(a))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA, "name": self.name, "units": self.units,
            "group_rate": self.group_rate, "variable_cost": self.variable_cost,
            "group_contribution": self.group_contribution,
            "displacement_cost": self.displacement_cost,
            "net_benefit": self.net_benefit, "break_even_rate": self.break_even_rate,
            "accept": self.accept,
            "alerts": [
                {"indicator": a.indicator, "message": a.message, "severity": a.severity}
                for a in self.alerts
            ],
            "meta": self.meta,
        }


def group_displacement(group_size: float, capacity: float, demand,
                       value_per_unit: float) -> float:
    """Opportunity cost of a block across one or more periods.

    For each period the displaced individual demand is
    ``max(demand - (capacity - group_size), 0)``; the total displacement cost is
    the displaced units times ``value_per_unit`` (the contribution lost per unit,
    or the marginal seat / bid-price value). ``demand`` is a single number or a
    sequence (one value per night or leg).
    """
    group_size = float(group_size)
    capacity = float(capacity)
    if group_size < 0 or capacity <= 0:
        raise ValueError("group_size must be non-negative and capacity positive")
    periods = demand if isinstance(demand, Sequence) and not isinstance(demand, str) \
        else [demand]
    free_for_individuals = capacity - group_size
    displaced = sum(max(0.0, float(d) - free_for_individuals) for d in periods)
    return displaced * float(value_per_unit)


def evaluate_group(group_rate: float, units: float, *,
                   displacement_cost: float | None = None,
                   marginal_value: float | None = None, variable_cost: float = 0.0,
                   name: str | None = None) -> GroupResult:
    """Accept or reject a group from its rate, size and displacement cost.

    Provide the total ``displacement_cost`` (for example from
    :func:`group_displacement`) or a per-unit ``marginal_value`` (multiplied by
    ``units``). The group is accepted when its contribution
    ``(group_rate - variable_cost) * units`` covers the displacement cost; the
    break-even rate is the lowest group rate that would still clear.
    """
    group_rate = float(group_rate)
    units = float(units)
    variable_cost = float(variable_cost)
    if units <= 0:
        raise ValueError("units must be positive")
    if (displacement_cost is None) == (marginal_value is None):
        raise ValueError("provide exactly one of displacement_cost or marginal_value")
    if displacement_cost is not None:
        disp = float(displacement_cost)
    else:
        assert marginal_value is not None  # guaranteed by the check above
        disp = float(marginal_value) * units

    contribution = (group_rate - variable_cost) * units
    net = contribution - disp
    break_even = variable_cost + disp / units

    alerts: list[Alert] = []
    if group_rate < variable_cost:
        alerts.append(Alert("below_cost",
                            "group rate is below variable cost per unit", "warning"))
    return GroupResult(
        name, units, group_rate, variable_cost, contribution, disp, net,
        break_even, net >= 0, tuple(alerts),
        make_meta({"group_rate": group_rate, "units": units,
                   "variable_cost": variable_cost, "displacement_cost": disp}))
