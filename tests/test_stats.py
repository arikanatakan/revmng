import math

import pytest

from revmng._stats import binom_pmf, norm_cdf, norm_loss, norm_pdf, norm_ppf


def test_norm_cdf_known_points():
    assert norm_cdf(0.0) == pytest.approx(0.5)
    assert norm_cdf(1.96) == pytest.approx(0.9750021, abs=1e-6)
    assert norm_cdf(-1.96) == pytest.approx(0.0249979, abs=1e-6)


def test_norm_ppf_inverts_cdf():
    for p in (0.01, 0.1, 0.25, 0.5, 0.6, 0.9, 0.975, 0.999):
        assert norm_cdf(norm_ppf(p)) == pytest.approx(p, abs=1e-9)


def test_norm_ppf_known_quantiles():
    assert norm_ppf(0.975) == pytest.approx(1.959963985, abs=1e-7)
    assert norm_ppf(0.5) == pytest.approx(0.0, abs=1e-12)
    assert norm_ppf(0.0) == -math.inf
    assert norm_ppf(1.0) == math.inf


def test_norm_pdf_and_loss():
    assert norm_pdf(0.0) == pytest.approx(1.0 / math.sqrt(2 * math.pi))
    assert norm_loss(0.0) == pytest.approx(norm_pdf(0.0))
    # loss is decreasing in z
    assert norm_loss(0.0) > norm_loss(1.0) > norm_loss(2.0) > 0


def test_binom_pmf():
    assert sum(binom_pmf(k, 10, 0.3) for k in range(11)) == pytest.approx(1.0)
    assert binom_pmf(0, 5, 0.0) == 1.0
    assert binom_pmf(5, 5, 1.0) == 1.0
    assert binom_pmf(2, 4, 0.5) == pytest.approx(6 / 16)
