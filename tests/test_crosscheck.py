"""Independent cross-checks for the single-leg methods.

Two ways to gain confidence without a published multi-class worked example:

1. Re-implement the EMSR / Littlewood formulas with SciPy's inverse normal
   (independent of revmng's own ``norm_ppf``) and confirm an exact match. This
   isolates "is the formula coded correctly" from "is the formula right".
2. Score the EMSR heuristics against revmng's exact dynamic program (a wholly
   different algorithm) over many random instances. The optimal value is an
   upper bound, so a correct heuristic can never beat it, and EMSR-b should sit
   within a small gap of it (Belobaba reports EMSR-b within about 0.5% of the
   optimum for realistic demand).
"""

import math
import random

import pytest

pytest.importorskip("scipy")

from scipy.stats import norm  # noqa: E402

import revmng  # noqa: E402
from revmng.optimal import optimal_protection_levels, policy_revenue  # noqa: E402


def _emsr_b_ref(classes, cap):
    """EMSR-b protection levels computed independently with scipy."""
    prot = []
    for j in range(1, len(classes)):
        higher = classes[:j]
        mu = sum(c[1] for c in higher)
        sd = math.sqrt(sum(c[2] ** 2 for c in higher))
        wfare = sum(c[0] * c[1] for c in higher) / mu if mu > 0 else higher[0][0]
        ratio = min(1.0, classes[j][0] / wfare)
        y = mu + float(norm.ppf(1.0 - ratio)) * sd
        prot.append(max(0.0, min(float(cap), y)))
    return prot


def _emsr_a_ref(classes, cap):
    prot = []
    for j in range(1, len(classes)):
        y = 0.0
        for c in classes[:j]:
            ratio = min(1.0, classes[j][0] / c[0])
            y += max(0.0, c[1] + float(norm.ppf(1.0 - ratio)) * c[2])
        prot.append(max(0.0, min(float(cap), y)))
    return prot


def test_emsr_b_matches_independent_scipy_implementation():
    classes = [(1000, 30, 12), (700, 40, 15), (400, 60, 20), (250, 80, 25)]
    got = revmng.emsr_b(classes, 150).protection_levels
    ref = _emsr_b_ref(classes, 150)
    assert list(got) == pytest.approx(ref, abs=1e-9)


def test_emsr_a_matches_independent_scipy_implementation():
    classes = [(1000, 30, 12), (700, 40, 15), (400, 60, 20), (250, 80, 25)]
    got = revmng.emsr_a(classes, 150).protection_levels
    ref = _emsr_a_ref(classes, 150)
    assert list(got) == pytest.approx(ref, abs=1e-9)


def test_littlewood_matches_scipy():
    got = revmng.littlewood(1000, 400, 50, 18)
    ref = max(0.0, 50 + float(norm.ppf(1.0 - 400 / 1000)) * 18)
    assert got == pytest.approx(ref, abs=1e-9)


def test_emsr_never_beats_the_optimal_dp():
    """Over random instances, no heuristic may exceed the DP optimum."""
    rng = random.Random(20260616)
    ratios_b = []
    worst_b = 1.0
    for _ in range(60):
        n = rng.randint(2, 4)
        cap = rng.randint(40, 140)
        fares = sorted((rng.uniform(120, 1000) for _ in range(n)), reverse=True)
        classes = [(fares[i], rng.uniform(8, 45), rng.uniform(3, 18))
                   for i in range(n)]
        opt = optimal_protection_levels(classes, cap).expected_revenue
        rev_b = policy_revenue(classes, cap, revmng.emsr_b(classes, cap).protection_levels)
        rev_a = policy_revenue(classes, cap, revmng.emsr_a(classes, cap).protection_levels)
        # the optimum is an upper bound for any policy
        assert rev_b <= opt + 1e-6
        assert rev_a <= opt + 1e-6
        if opt > 0:
            ratios_b.append(rev_b / opt)
            worst_b = min(worst_b, rev_b / opt)
    mean_ratio = sum(ratios_b) / len(ratios_b)
    # EMSR-b lands close to the optimum (Belobaba: within ~0.5% for realistic
    # demand); across these instances the worst gap is under 1% and the mean
    # gap is a few hundredths of a percent.
    assert mean_ratio >= 0.999, mean_ratio
    assert worst_b >= 0.99, worst_b
