"""Exact optimal single-leg capacity control.

For the static single-resource model with independent demand and the classic
low-before-high booking order, the optimal control is a set of nested protection
levels (Brumelle and McGill, 1993; Talluri and van Ryzin, 2004). This module
computes them exactly by dynamic programming over discrete remaining capacity,
discretising each class's normal demand. The EMSR heuristics in
:mod:`revmng.singleleg` approximate exactly this policy.

``optimal_protection_levels`` returns the optimal protection levels, booking
limits and the optimal expected revenue (as an ``AllocationResult``).
``policy_revenue`` evaluates the expected revenue of any protection-level
policy under the same demand model, so a heuristic can be scored against the
optimum.
"""

from __future__ import annotations

from ._stats import norm_cdf
from .singleleg import AllocationResult, _build, _normalize


def _demand_pmf(mean: float, sd: float, cap: int) -> list[float]:
    """Probability that rounded demand equals d, for d in 0..cap (tail at cap)."""
    p = [0.0] * (cap + 1)
    if sd <= 0:
        p[max(0, min(cap, round(mean)))] = 1.0
        return p
    p[0] = norm_cdf((0.5 - mean) / sd)
    for d in range(1, cap):
        p[d] = (norm_cdf((d + 0.5 - mean) / sd)
                - norm_cdf((d - 0.5 - mean) / sd))
    p[cap] = 1.0 - norm_cdf((cap - 0.5 - mean) / sd)
    return p


def _run_dp(cls, cap: int, pmfs, fixed=None):
    """Backward DP over remaining capacity.

    Classes book lowest fare first; the value function ``W`` is the expected
    revenue from the higher classes still to come. When ``fixed`` is given the
    protection levels are taken as-is; otherwise the optimal protection at each
    boundary is found from the (concave) marginal value of ``W``.
    """
    n = len(cls)
    w = [0.0] * (cap + 1)
    used: list[float] = []
    for m in range(1, n + 1):
        fare = cls[m - 1].fare
        pmf = pmfs[m - 1]
        if m == 1:
            b = 0
        elif fixed is not None:
            b = max(0, min(cap, int(round(fixed[m - 2]))))
            used.append(float(b))
        else:
            b = 0
            for x in range(1, cap + 1):
                if w[x] - w[x - 1] > fare:   # marginal seat worth more than this fare
                    b = x
                else:
                    break                    # W is concave: marginals only fall
            used.append(float(b))
        new_w = [0.0] * (cap + 1)
        for x in range(cap + 1):
            avail = x - b if x > b else 0
            ev = 0.0
            for d, prob in enumerate(pmf):
                if prob == 0.0:
                    continue
                sell = d if d < avail else avail
                ev += prob * (fare * sell + w[x - sell])
            new_w[x] = ev
        w = new_w
    return w[cap], used


def optimal_protection_levels(classes, capacity, *,
                              name: str | None = None) -> AllocationResult:
    """Exact optimal nested protection levels for one resource.

    ``classes`` are ``(fare, demand mean, demand sd)`` (or :class:`FareClass`),
    as for the EMSR functions. Demand is discretised to whole units up to
    ``capacity``. The returned ``AllocationResult`` carries the optimal expected
    revenue in ``expected_revenue``.
    """
    cls = _normalize(classes)
    cap = int(capacity)
    if cap <= 0:
        raise ValueError("capacity must be positive")
    pmfs = [_demand_pmf(c.mean, c.sd, cap) for c in cls]
    revenue, protection = _run_dp(cls, cap, pmfs)
    return _build(cls, cap, protection, "optimal (DP)", name, revenue)


def policy_revenue(classes, capacity, protection_levels) -> float:
    """Expected revenue of a given protection-level policy under the DP model.

    ``protection_levels`` is one cumulative level per class boundary (length
    ``len(classes) - 1``), as returned by the EMSR functions. Useful for scoring
    a heuristic against :func:`optimal_protection_levels`.
    """
    cls = _normalize(classes)
    cap = int(capacity)
    if len(protection_levels) != len(cls) - 1:
        raise ValueError("need one protection level per class boundary")
    pmfs = [_demand_pmf(c.mean, c.sd, cap) for c in cls]
    revenue, _ = _run_dp(cls, cap, pmfs, fixed=list(protection_levels))
    return revenue
