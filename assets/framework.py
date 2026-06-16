"""Generate the revmng framework figure (academic style).

Top: inputs flow into the revenue-management methods and out to a result with
provenance. Bottom: the measurement layer.
Run:  python assets/framework.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})

INK = "#1f2d3d"
MUT = "#5b6b7b"
NEUT_F, NEUT_E = "#eef1f4", "#9aa7b3"
ANA_F, ANA_E = "#eef3f8", "#3b6ea5"
RES_F, RES_E = "#d4e4f4", "#2c5f8a"
OPT_F, OPT_E = "#e3f1ec", "#3a8f78"
CONT_F, CONT_E = "#f7f9fb", "#c9d2db"
BAN_F, BAN_E = "#f5f7f9", "#cdd6df"
ARROW = "#7c8a99"

fig, ax = plt.subplots(figsize=(12, 7.0))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, text, fill, edge, fs=8.2, bold=False, tcol=INK):
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.35,rounding_size=1.4",
        linewidth=1.25, edgecolor=edge, facecolor=fill, zorder=2))
    ax.text(x, y, text, ha="center", va="center", color=tcol, fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=5)


def arrow(x0, y0, x1, y1, color=ARROW, lw=1.15):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=1,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                shrinkA=1, shrinkB=1))


ax.text(3, 97.5, "revmng", fontsize=13.5, fontweight="bold", color=INK, ha="left")
ax.text(3, 93.5, "revenue management for Python", fontsize=9.5, color=MUT,
        ha="left", fontstyle="italic")

# ---- Top tier: inputs -> methods -> result ---------------------------------
for x, t in [(12, "Inputs"), (40, "Methods"), (76, "Result")]:
    ax.text(x, 89, t, ha="center", fontsize=9.3, color=MUT, fontstyle="italic")

box(12, 82, 18, 7.2, "Fares & demand", NEUT_F, NEUT_E, fs=8.0)
box(12, 72, 18, 7.2, "Capacity", NEUT_F, NEUT_E, fs=8.0)
box(12, 62, 18, 7.2, "No-shows & costs", NEUT_F, NEUT_E, fs=8.0)

ax.add_patch(FancyBboxPatch((23, 50), 34, 42,
             boxstyle="round,pad=0.4,rounding_size=1.6",
             linewidth=1.3, edgecolor=CONT_E, facecolor=CONT_F, zorder=0))
for y, t in [(85, "single-leg     Littlewood · EMSR-a/b · optimal DP"),
             (77, "overbooking    service level · cost"),
             (69, "pricing        newsvendor · optimal price"),
             (61, "network        bid prices  (DLP, SciPy)"),
             (53, "requests       group · length-of-stay")]:
    box(40, y, 32, 6.4, t, ANA_F, ANA_E, fs=7.1)

box(76, 71, 22, 30,
    "protection · booking limits\nexpected revenue\nauthorization limit\n"
    "price · quantity\nbid prices\naccept / reject\n\nmeta: version · hash · time",
    RES_F, RES_E, fs=7.8, bold=True)

for y in (82, 72, 62):
    arrow(20.2, y, 22.6, 71)
arrow(57.2, 71, 64.8, 71)

# ---- Bottom tier: the measurement layer ------------------------------------
ax.text(50, 44, "The measurement layer", ha="center", fontsize=11.5,
        fontweight="bold", color=INK)

band = [(11, "RevPAR"), (27, "ADR"), (43, "occupancy"), (59, "yield"),
        (75, "load factor"), (91, "ROM")]
for x, t in band:
    box(x, 32, 14, 8, t, OPT_F, OPT_E, fs=8.0)

box(50, 12, 88, 8,
    "computed from the textbook methods      ·      zero core dependencies\n"
    "validated against published worked examples (Phillips 2005)",
    BAN_F, BAN_E, fs=7.9, tcol=MUT)

fig.savefig("assets/framework.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("wrote assets/framework.png")
