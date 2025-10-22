# -*- coding: utf-8 -*-
from math import comb, exp, factorial, erf, sqrt

# === Normal (CDF) ===
def normal_cdf(x, mu=0.0, sigma=1.0):
    z = (x - mu) / (sigma * sqrt(2))
    return 0.5 * (1 + erf(z))

# === Binomial (PMF) ===
def binomial_pmf(k, n, p):
    if k < 0 or k > n:
        return 0.0
    return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

# === Poisson (PMF, CDF, Muestra) ===
def poisson_pmf(k, lam):
    if k < 0:
        return 0.0
    return (exp(-lam) * (lam ** k)) / factorial(k)

def poisson_cdf(k, lam):
    return sum(poisson_pmf(i, lam) for i in range(k + 1))

def poisson_muestra(lam, n=1, rng=None):
    import numpy as np
    if rng is None:
        rng = np.random.default_rng(42)
    return rng.poisson(lam, size=n)
