"""Optional charts for revenue-management results, in a clean, neutral style.

Needs matplotlib. Install it with ``pip install revmng[plot]``. Each function
returns a matplotlib ``Figure`` so it can be shown, saved or embedded.
"""

from __future__ import annotations

INK = "#1f2d3d"
MUT = "#5b6b7b"
BAR = "#3b6ea5"
BAR2 = "#9ec2e6"
ACC = "#3a8f78"
GRID = "#dce3ea"
NEUT_E = "#9aa7b3"
CURVES = ("#2c5f8a", "#3b6ea5", "#6b9bc7", "#9ec2e6")


def _mpl():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover
        raise ImportError("charts need matplotlib; install it with "
                          "'pip install revmng[plot]'") from exc
    return plt


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(MUT)
    ax.tick_params(colors=MUT, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def booking_limit_chart(result, *, ax=None):
    """Nested booking limit per fare class from an ``AllocationResult``."""
    plt = _mpl()
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 0.6 * len(result.classes) + 1.4))
    names = [c["name"] for c in result.classes]
    limits = result.booking_limits_int
    y = range(len(names))
    ax.barh(list(y), limits, color=BAR, edgecolor=INK, linewidth=0.6, height=0.62)
    for i, v in zip(y, limits):
        ax.text(v, i, f" {v}", va="center", ha="left", fontsize=9, color=INK)
    ax.set_yticks(list(y))
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("nested booking limit (seats)")
    ax.set_title(f"{result.method} - capacity {int(result.capacity)}",
                 color=INK, fontsize=11, fontweight="bold", loc="left")
    _style(ax)
    if fig is not None:
        fig.tight_layout()
    return fig if fig is not None else ax.figure


def overbooking_cost_curve(capacity, no_show_rate, denied_cost, spoilage_cost, *,
                           ax=None):
    """Expected cost against the authorization limit, marking the optimum."""
    plt = _mpl()
    from .overbooking import _expected_over_spoil, overbooking_limit

    capacity = int(capacity)
    q = 1.0 - float(no_show_rate)
    best = overbooking_limit(capacity, no_show_rate=no_show_rate,
                             denied_cost=denied_cost, spoilage_cost=spoilage_cost)
    hi = int(capacity / q) + capacity // 2 + 5
    xs = list(range(capacity, hi + 1))
    ys = []
    for u in xs:
        over, spoil = _expected_over_spoil(u, q, capacity)
        ys.append(denied_cost * over + spoilage_cost * spoil)

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(xs, ys, color=BAR, linewidth=1.8)
    ax.axvline(best.authorization_limit, color=ACC, linewidth=1.4, linestyle="--")
    ax.text(best.authorization_limit, max(ys), f" u* = {best.authorization_limit}",
            color=ACC, fontsize=9, va="top")
    ax.set_xlabel("authorization limit (reservations)")
    ax.set_ylabel("expected cost")
    ax.set_title(f"overbooking trade-off - capacity {capacity}, "
                 f"no-show {no_show_rate:.0%}", color=INK, fontsize=11,
                 fontweight="bold", loc="left")
    _style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    if fig is not None:
        fig.tight_layout()
    return fig if fig is not None else ax.figure


def emsr_curve(result, *, ax=None):
    """Expected marginal seat revenue curves behind an ``AllocationResult``.

    For each boundary the pooled higher classes give a declining curve
    ``r_bar * P(S > x)``; where it crosses the next fare is the EMSR-b protection
    level (drawn as a vertical line). Intended for ``emsr_a`` / ``emsr_b``
    results.
    """
    plt = _mpl()
    import math

    from ._stats import norm_cdf

    classes = [(c["fare"], c["mean"], c["sd"]) for c in result.classes]
    cap = int(result.capacity)
    xs = list(range(cap + 1))
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for j in range(1, len(classes)):
        higher = classes[:j]
        mu = sum(c[1] for c in higher)
        sd = math.sqrt(sum(c[2] ** 2 for c in higher))
        wfare = sum(c[0] * c[1] for c in higher) / mu if mu > 0 else higher[0][0]
        nextfare = classes[j][0]
        colour = CURVES[(j - 1) % len(CURVES)]
        if sd > 0:
            ys = [wfare * (1.0 - norm_cdf((x - mu) / sd)) for x in xs]
        else:
            ys = [wfare if x < mu else 0.0 for x in xs]
        ax.plot(xs, ys, color=colour, linewidth=1.7,
                label=f"protect classes 1-{j}")
        ax.axhline(nextfare, color=colour, linestyle=":", linewidth=1.0)
        ax.axvline(result.protection_levels[j - 1], color=ACC, linestyle="--",
                   linewidth=1.1)
    ax.set_xlabel("seats protected")
    ax.set_ylabel("expected marginal seat revenue")
    ax.set_title(f"{result.method} - EMSR curves, capacity {cap}", color=INK,
                 fontsize=11, fontweight="bold", loc="left")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    _style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    if fig is not None:
        fig.tight_layout()
    return fig if fig is not None else ax.figure


def price_curve(demand, unit_cost=0.0, *, ax=None):
    """Revenue, profit and demand against price, marking the optimal price."""
    plt = _mpl()
    from .pricing import optimal_price

    res = optimal_price(demand, unit_cost)
    lo, hi = res.optimal_price * 0.2, res.optimal_price * 2.2
    ps = [lo + (hi - lo) * i / 200 for i in range(201)]
    dem, rev, prof = [], [], []
    for p in ps:
        q = max(0.0, demand.demand(p))
        dem.append(q)
        rev.append(p * q)
        prof.append((p - unit_cost) * q)
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.plot(ps, rev, color=BAR, linewidth=1.8, label="revenue")
    ax.plot(ps, prof, color=ACC, linewidth=1.8, label="profit")
    ax.axvline(res.optimal_price, color=MUT, linestyle="--", linewidth=1.1)
    ax.text(res.optimal_price, max(rev), f" p* = {res.optimal_price:,.2f}",
            color=MUT, fontsize=8.5, va="top")
    ax.set_xlabel("price")
    ax.set_ylabel("revenue / profit")
    ax.set_title("price optimization", color=INK, fontsize=11,
                 fontweight="bold", loc="left")
    ax2 = ax.twinx()
    ax2.plot(ps, dem, color=NEUT_E, linewidth=1.1, linestyle=":", label="demand")
    ax2.set_ylabel("demand", color=MUT)
    ax2.tick_params(colors=MUT, labelsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper center")
    _style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    if fig is not None:
        fig.tight_layout()
    return fig if fig is not None else ax.figure


def newsvendor_curve(price, cost, demand_mean, demand_sd, *, salvage=0.0, ax=None):
    """Expected profit against order quantity, marking the optimal quantity."""
    plt = _mpl()
    from ._stats import norm_loss
    from .pricing import newsvendor

    res = newsvendor(price, cost, demand_mean, demand_sd, salvage=salvage)
    underage, overage = price - cost, cost - salvage
    lo = max(0.0, demand_mean - 3 * demand_sd)
    hi = demand_mean + 3 * demand_sd
    qs = [lo + (hi - lo) * i / 200 for i in range(201)]
    prof = []
    for q in qs:
        z = (q - demand_mean) / demand_sd if demand_sd > 0 else 0.0
        shortage = demand_sd * norm_loss(z)
        sales = demand_mean - shortage
        leftover = q - demand_mean + shortage
        prof.append(underage * sales - overage * leftover)
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.plot(qs, prof, color=BAR, linewidth=1.8)
    ax.axvline(res.optimal_quantity, color=ACC, linestyle="--", linewidth=1.2)
    ax.text(res.optimal_quantity, min(prof), f" Q* = {res.optimal_quantity:,.1f}",
            color=ACC, fontsize=8.5, va="bottom")
    ax.set_xlabel("order quantity")
    ax.set_ylabel("expected profit")
    ax.set_title(f"newsvendor - critical ratio {res.critical_ratio:.2f}",
                 color=INK, fontsize=11, fontweight="bold", loc="left")
    _style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    if fig is not None:
        fig.tight_layout()
    return fig if fig is not None else ax.figure


def bid_price_chart(result, *, ax=None):
    """Bid price per resource from a ``NetworkResult``."""
    plt = _mpl()
    names = list(result.resources)
    vals = [result.bid_prices[r] for r in names]
    y = range(len(names))
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.0, 0.6 * len(names) + 1.4))
    ax.barh(list(y), vals, color=BAR, edgecolor=INK, linewidth=0.6, height=0.6)
    for i, v in zip(y, vals):
        ax.text(v, i, f" {v:,.2f}", va="center", ha="left", fontsize=9, color=INK)
    ax.set_yticks(list(y))
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("bid price")
    ax.set_title("network bid prices", color=INK, fontsize=11,
                 fontweight="bold", loc="left")
    _style(ax)
    if fig is not None:
        fig.tight_layout()
    return fig if fig is not None else ax.figure


def revenue_opportunity_chart(result, *, ax=None):
    """Perfect, no-control and realised revenue from a ``RevenueOpportunityResult``."""
    plt = _mpl()
    labels = ["no controls", "realized", "perfect"]
    values = [result.no_control_revenue,
              result.realized_revenue if result.realized_revenue is not None
              else result.no_control_revenue,
              result.perfect_revenue]
    colors = [BAR2, ACC, BAR]
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(6.5, 4.2))
    bars = ax.bar(labels, values, color=colors, edgecolor=INK, linewidth=0.6)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}", ha="center",
                va="bottom", fontsize=9, color=INK)
    title = "revenue opportunity"
    if result.rom is not None:
        title += f" - ROM {result.rom:.0%}"
    ax.set_title(title, color=INK, fontsize=11, fontweight="bold", loc="left")
    ax.set_ylabel("revenue")
    _style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.grid(axis="x", visible=False)
    if fig is not None:
        fig.tight_layout()
    return fig if fig is not None else ax.figure
