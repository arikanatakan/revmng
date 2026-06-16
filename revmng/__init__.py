"""revmng - revenue management for Python.

Validated, dependency-free building blocks for selling fixed, perishable
capacity well: single-leg seat protection, overbooking, pricing, the standard
performance metrics, and network bid prices.

    import revmng

    # Two-class seat protection (Littlewood's rule)
    revmng.littlewood(fare_high=1000, fare_low=400, mean_high=50, sd_high=18)

    # Multi-class nested booking limits (EMSR-b)
    a = revmng.emsr_b(
        [(1000, 30, 12), (700, 40, 15), (400, 60, 20)], capacity=120)
    a.booking_limits_int

    # Overbooking with a no-show rate and the cost trade-off
    revmng.overbooking_limit(100, no_show_rate=0.12,
                             denied_cost=400, spoilage_cost=180)

Every result carries provenance (library version, input hash, timestamp) and a
JSON-safe ``to_dict``. The methods compute decisions from the demand you supply;
forecasting demand is deliberately out of scope. Bid pricing needs SciPy
(``revmng[network]``) and the charts need matplotlib (``revmng[plot]``).
"""

from ._result import Alert
from ._version import __version__
from .group import GroupResult, evaluate_group, group_displacement
from .los import StayResult, evaluate_stay
from .metrics import (
    RevenueOpportunityResult,
    adr,
    casm,
    load_factor,
    nested_revenue,
    occupancy,
    rasm,
    revenue_opportunity,
    revpar,
    spill,
    spoilage,
    yield_,
)
from .network import NetworkResult, Product, bid_prices
from .optimal import optimal_protection_levels, policy_revenue
from .overbooking import OverbookingResult, overbooking_limit
from .plot import (
    bid_price_chart,
    booking_limit_chart,
    emsr_curve,
    newsvendor_curve,
    overbooking_cost_curve,
    price_curve,
    revenue_opportunity_chart,
)
from .pricing import (
    ConstantElasticityDemand,
    LinearDemand,
    NewsvendorResult,
    PriceResult,
    newsvendor,
    optimal_price,
)
from .singleleg import AllocationResult, FareClass, emsr_a, emsr_b, littlewood

__all__ = [
    # single-leg capacity control
    "littlewood", "emsr_a", "emsr_b", "FareClass", "AllocationResult",
    # exact optimal single-leg control
    "optimal_protection_levels", "policy_revenue",
    # group and length-of-stay (opportunity-cost acceptance)
    "evaluate_group", "group_displacement", "GroupResult",
    "evaluate_stay", "StayResult",
    # overbooking
    "overbooking_limit", "OverbookingResult",
    # pricing
    "newsvendor", "optimal_price", "LinearDemand", "ConstantElasticityDemand",
    "NewsvendorResult", "PriceResult",
    # performance metrics
    "revpar", "adr", "occupancy", "yield_", "load_factor", "rasm", "casm",
    "spill", "spoilage", "nested_revenue", "revenue_opportunity",
    "RevenueOpportunityResult",
    # network bid prices (needs scipy)
    "bid_prices", "Product", "NetworkResult",
    # charts (needs matplotlib)
    "booking_limit_chart", "emsr_curve", "overbooking_cost_curve",
    "price_curve", "newsvendor_curve", "revenue_opportunity_chart",
    "bid_price_chart",
    # shared
    "Alert", "__version__",
]
