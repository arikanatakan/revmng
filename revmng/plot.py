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
