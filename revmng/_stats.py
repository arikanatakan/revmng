"""Small, dependency-free statistics: the normal distribution, its inverse and
loss function, and the binomial pmf. These are all the probability tools the
revenue-management methods need, so the core library has no third-party
dependencies.

The inverse normal CDF uses Acklam's rational approximation refined by one
Halley step, which is accurate to roughly machine precision.
"""

from __future__ import annotations

import math

_A = (-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
      1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00)
_B = (-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
      6.680131188771972e01, -1.328068155288572e01)
_C = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
      -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00)
_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
      3.754408661907416e00)
_P_LOW = 0.02425
_P_HIGH = 1.0 - _P_LOW
_SQRT_2PI = math.sqrt(2.0 * math.pi)


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * math.erfc(-float(x) / math.sqrt(2.0))


def norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    x = float(x)
    return math.exp(-0.5 * x * x) / _SQRT_2PI


def norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (the quantile function).

    ``norm_ppf(0.975) == 1.959963...``. Returns -inf at 0 and +inf at 1.
    """
    p = float(p)
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must be in [0, 1]")
    if p == 0.0:
        return -math.inf
    if p == 1.0:
        return math.inf
    if p < _P_LOW:
        q = math.sqrt(-2.0 * math.log(p))
        x = ((((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q
              + _C[5]) / ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0))
    elif p <= _P_HIGH:
        q = p - 0.5
        r = q * q
        x = ((((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r
              + _A[5]) * q / (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r
                               + _B[4]) * r + 1.0))
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = (-(((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q
               + _C[5]) / ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0))
    # One Halley step to polish the approximation to full precision.
    e = norm_cdf(x) - p
    u = e * _SQRT_2PI * math.exp(0.5 * x * x)
    return x - u / (1.0 + 0.5 * x * u)


def norm_loss(z: float) -> float:
    """Standard normal loss function L(z) = phi(z) - z * (1 - Phi(z)).

    For demand ``D ~ N(mu, sigma)`` and a stock of ``Q = mu + z * sigma``, the
    expected shortage E[(D - Q)+] equals ``sigma * norm_loss(z)``.
    """
    z = float(z)
    return norm_pdf(z) - z * (1.0 - norm_cdf(z))


def binom_pmf(k: int, n: int, p: float) -> float:
    """Binomial probability mass P(X = k) for X ~ Binomial(n, p)."""
    if k < 0 or k > n:
        return 0.0
    if p <= 0.0:
        return 1.0 if k == 0 else 0.0
    if p >= 1.0:
        return 1.0 if k == n else 0.0
    log_coef = math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    return math.exp(log_coef + k * math.log(p) + (n - k) * math.log1p(-p))
