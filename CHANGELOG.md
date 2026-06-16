# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[semantic versioning](https://semver.org/).

## [0.2.0] - 2026-06-16

### Added

- Signature charts for the remaining methods (need matplotlib, `revmng[plot]`):
  `emsr_curve` (expected marginal seat revenue curves and protection levels),
  `price_curve` (revenue, profit and demand against price), `newsvendor_curve`
  (expected profit against order quantity) and `bid_price_chart` (bid price per
  resource).

## [0.1.0] - 2026-06-16

First release.

### Added

- Single-leg capacity control: `littlewood` (the optimal two-class rule) and the
  `emsr_a` / `emsr_b` heuristics, returning nested protection levels and booking
  limits as an `AllocationResult`.
- Exact optimal single-leg control: `optimal_protection_levels` solves the static
  model by dynamic programming and returns the optimal protection levels and
  expected revenue; `policy_revenue` scores any policy (such as EMSR) against it.
- Group evaluation by displacement analysis: `group_displacement` (opportunity
  cost of a block across nights or legs) and `evaluate_group` (accept or reject
  and the break-even rate).
- Length-of-stay control: `evaluate_stay` accepts a multi-night request when its
  rate covers the sum of the nightly bid prices.
- Overbooking: `overbooking_limit` with a deterministic service-level mode and a
  cost-based mode that minimises expected denied-boarding and spoilage cost under
  a binomial show-up model.
- Pricing: `newsvendor` (the critical-fractile stocking quantity with expected
  sales, shortage, leftover and profit) and `optimal_price` for `LinearDemand`
  and `ConstantElasticityDemand`.
- Performance metrics: `revpar`, `adr`, `occupancy`, `yield_`, `load_factor`,
  `rasm`, `casm`, `spill`, `spoilage`, plus `nested_revenue` and
  `revenue_opportunity` (the revenue opportunity metric against
  perfect-hindsight and no-control benchmarks).
- Network bid prices: `bid_prices` solves the deterministic LP and returns the
  per-resource shadow prices and allocation; `NetworkResult.accept` applies the
  bid-price control. Optional, needs SciPy (`revmng[network]`).
- Charts: `booking_limit_chart`, `overbooking_cost_curve` and
  `revenue_opportunity_chart`. Optional, needs matplotlib (`revmng[plot]`).
- Dependency-free statistics (normal CDF, inverse CDF, loss function, binomial
  pmf), so the core library has no third-party dependencies.
- Every result carries provenance (library version, input hash, timestamp) and a
  JSON-safe `to_dict()`.
- Validated against published worked examples (Phillips 2005, Examples 9.2 and
  9.7) and the two-class EMSR-b / Littlewood identity.
