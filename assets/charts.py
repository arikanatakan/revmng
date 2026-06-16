"""Render the README chart gallery: a single image of the revmng charts.

Run:  python assets/charts.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import revmng

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.2))

classes = [(1000, 30, 12), (700, 40, 15), (400, 60, 20)]
alloc = revmng.emsr_b(classes, capacity=120)

revmng.emsr_curve(alloc, ax=axes[0, 0])
revmng.booking_limit_chart(alloc, ax=axes[0, 1])
revmng.overbooking_cost_curve(100, 0.12, denied_cost=400, spoilage_cost=180,
                              ax=axes[0, 2])
revmng.price_curve(revmng.LinearDemand(100, 2), unit_cost=10, ax=axes[1, 0])
revmng.newsvendor_curve(10, 4, 100, 30, ax=axes[1, 1])
revmng.revenue_opportunity_chart(
    revmng.revenue_opportunity([1000, 800, 600, 200], [25, 30, 20, 50], 100,
                               booking_limits=[100, 70, 45, 32]),
    ax=axes[1, 2])

fig.tight_layout(pad=2.0)
fig.savefig("assets/charts.png", dpi=110, bbox_inches="tight", facecolor="white")
print("wrote assets/charts.png")
