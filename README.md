# revmng

[![CI](https://github.com/arikanatakan/revmng/actions/workflows/ci.yml/badge.svg)](https://github.com/arikanatakan/revmng/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/revmng?v=2)](https://pypi.org/project/revmng/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Revenue management for Python: the building blocks for selling fixed, perishable
capacity well. Single-leg seat protection, overbooking, pricing, network bid
prices and the standard performance metrics, computed from the textbook methods
and validated against published worked examples.

The core has **no third-party dependencies**. Every result carries provenance
(library version, input hash, timestamp) and a JSON-safe `to_dict()`.

![revmng framework: inputs (fares and demand, capacity, no-shows and costs) flow through the revenue-management methods (single-leg control with Littlewood, EMSR-a/b and the exact DP, overbooking, pricing, network bid prices, group and length-of-stay) into a result with provenance, over a measurement layer of RevPAR, yield, load factor and ROM](assets/framework.png)

With `revmng[plot]` installed, each method also has a chart in a clean, neutral style:

![revmng charts: EMSR marginal seat revenue curves with protection levels, nested booking limits per fare class, the overbooking cost trade-off, price optimization with revenue and profit against price, the newsvendor expected-profit curve, and the revenue opportunity benchmark](assets/charts.png)

```bash
pip install revmng
```

## Quick start

```python
import revmng

# Two-class seat protection (Littlewood's rule)
revmng.littlewood(fare_high=1000, fare_low=400, mean_high=50, sd_high=18)
# -> protect this many seats for the high fare; sell the low fare below it

# Multi-class nested booking limits (EMSR-b, the industry-standard heuristic)
a = revmng.emsr_b(
    [(1000, 30, 12), (700, 40, 15), (400, 60, 20)],   # (fare, demand mean, sd)
    capacity=120,
)
a.booking_limits_int          # nested whole-seat booking limits
print(a.summary())

# Overbooking: balance the cost of bumping against the cost of empty seats
o = revmng.overbooking_limit(100, no_show_rate=0.12,
                             denied_cost=400, spoilage_cost=180)
o.authorization_limit         # how many reservations to accept

# Pricing: the newsvendor stocking quantity and the profit-maximising price
revmng.newsvendor(price=10, cost=4, demand_mean=100, demand_sd=30).optimal_quantity
revmng.optimal_price(revmng.LinearDemand(intercept=100, slope=2), unit_cost=10)

# Score booking limits against perfect-hindsight and no-control benchmarks
revmng.revenue_opportunity([1000, 800, 600, 200], [25, 30, 20, 50], capacity=100,
                           booking_limits=[100, 70, 45, 32]).rom

# Exact optimal protection levels (and the expected revenue EMSR leaves behind)
opt = revmng.optimal_protection_levels(
    [(1000, 30, 12), (700, 40, 15), (400, 60, 20)], capacity=120)
opt.expected_revenue

# Should we take this group? (displacement analysis)
cost = revmng.group_displacement(group_size=30, capacity=100,
                                 demand=[70, 95, 85], value_per_unit=70)
revmng.evaluate_group(group_rate=60, units=90, displacement_cost=cost,
                      variable_cost=50).accept

# Should we accept this multi-night stay? (length-of-stay bid-price control)
revmng.evaluate_stay({"Mon": 80, "Tue": 120, "Wed": 90},
                     ["Mon", "Tue", "Wed"], total_rate=320).accept
```

Network bid prices need SciPy and the charts need matplotlib:

```bash
pip install "revmng[network]"   # bid_prices via the deterministic LP
pip install "revmng[plot]"      # booking-limit, overbooking and ROM charts
```

```python
from revmng import Product
n = revmng.bid_prices(
    [Product(fare=200, uses={"AB": 1}, demand=60),
     Product(fare=300, uses={"AB": 1, "BC": 1}, demand=40)],
    capacities={"AB": 100, "BC": 100},
)
n.bid_prices                       # marginal value of each resource
n.accept(fare=250, uses={"AB": 1, "BC": 1})
```

## What it covers

| Area | Functions |
| --- | --- |
| Single-leg capacity control | `littlewood`, `emsr_a`, `emsr_b` |
| Exact optimal control | `optimal_protection_levels`, `policy_revenue` |
| Overbooking | `overbooking_limit` (service level and cost based) |
| Pricing | `newsvendor`, `optimal_price` (`LinearDemand`, `ConstantElasticityDemand`) |
| Group evaluation | `evaluate_group`, `group_displacement` |
| Length-of-stay | `evaluate_stay` |
| Performance metrics | `revpar`, `adr`, `occupancy`, `yield_`, `load_factor`, `rasm`, `casm`, `spill`, `spoilage` |
| Revenue opportunity | `revenue_opportunity`, `nested_revenue` |
| Network (needs SciPy) | `bid_prices`, `Product` |
| Charts (needs matplotlib) | `booking_limit_chart`, `emsr_curve`, `overbooking_cost_curve`, `price_curve`, `newsvendor_curve`, `revenue_opportunity_chart`, `bid_price_chart` |

`optimal_protection_levels` computes the exact optimal nested protection levels
by dynamic programming (the policy the EMSR heuristics approximate) and reports
the optimal expected revenue; `policy_revenue` scores any policy against it.
Group and length-of-stay decisions share one idea: accept a request when its
contribution covers the opportunity cost of the capacity it displaces (a
marginal seat value or a sum of nightly bid prices).

Demand for the capacity-control methods is assumed normal and independent, with
the classic low-before-high booking assumption. EMSR-a and EMSR-b are
heuristics; for two classes both reduce to Littlewood's optimal rule.

## What is out of scope

revmng computes **decisions from the demand you supply**. It does not forecast
demand, estimate willingness-to-pay, or unconstrain censored bookings, and it
does not connect to any reservation, property-management or distribution system.
Those belong upstream; keeping them out is what lets every result here be
reproduced and audited.

## Validation

The methods are checked against published and hand-derived worked examples (see
[`tests/validation_cases.json`](tests/validation_cases.json)):

| Method | Source | Result |
| --- | --- | --- |
| Littlewood booking limits | Phillips, *Pricing and Revenue Optimization* (2005), Ex. 9.2 | 25 / 50 / 76 reproduced |
| Revenue opportunity metric | Phillips (2005), Ex. 9.7 | perfect 66000, no-control 46000, realized 59200, ROM 66% |
| EMSR-b (two classes) | Belobaba (1989) | equals Littlewood's optimal rule |
| EMSR-b (three classes) | Belobaba (1989) formula, arithmetic shown | protection 23.71 / 70.83, limits 97 / 50 |
| Optimal control (DP) | Talluri and van Ryzin (2004) | matches Littlewood for two classes; expected revenue at least EMSR-b's |

A clean multi-class EMSR-b worked example with both inputs and outputs is hard to
find in the open literature, so the heuristics are also cross-checked two
independent ways (`tests/test_crosscheck.py`): their protection levels match a
separate SciPy implementation of the same formulas to 1e-9, and over many random
instances EMSR-b never exceeds revmng's exact dynamic program and stays within
about 0.5% of it, matching Belobaba's reported near-optimality.
| Group displacement | standard displacement analysis, arithmetic shown | 40 displaced room-nights, cost 2800, break-even rate 81.11 |
| Length-of-stay bid price | Talluri and van Ryzin (2004), arithmetic shown | 290 hurdle, accept at rate 320 |
| Newsvendor quantity | critical-fractile rule | reproduced |
| Overbooking (service level) | deterministic no-show formula | reproduced |

### Definitions and methods

- K. Littlewood, "Forecasting and control of passenger bookings" (1972).
- P. Belobaba, "Application of a probabilistic decision model to airline seat
  inventory control," *Operations Research* (1989). EMSR-a and EMSR-b.
- K. Talluri and G. van Ryzin, *The Theory and Practice of Revenue Management*
  (2004).
- R. Phillips, *Pricing and Revenue Optimization* (2005).

## License

MIT. Written and maintained by [Atakan Arikan](https://github.com/arikanatakan),
MSc Student at Tsinghua University and Politecnico di Milano.
