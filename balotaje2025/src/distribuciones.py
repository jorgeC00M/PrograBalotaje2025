# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

def fit_normal(x: np.ndarray) -> dict:
    mu = float(np.nanmean(x)); sigma = float(np.nanstd(x, ddof=1))
    return {"dist": "normal", "params": {"mu": mu, "sigma": sigma}}

def fit_lognormal(x: np.ndarray) -> dict:
    x = x[x > 0]
    if len(x)==0: return {"dist":"lognormal","params":{"mu":np.nan,"sigma":np.nan}}
    logx = np.log(x); mu = float(np.nanmean(logx)); sigma = float(np.nanstd(logx, ddof=1))
    return {"dist":"lognormal","params":{"mu":mu,"sigma":sigma}}

def fit_exponencial(x: np.ndarray) -> dict:
    x = x[x >= 0]; m = float(np.nanmean(x))
    lam = (1.0/m) if (m and m>0) else np.nan
    return {"dist":"exponencial","params":{"lambda":lam}}

def fit_gamma(x: np.ndarray) -> dict:
    x = x[x>0]; m=float(np.nanmean(x)); v=float(np.nanvar(x, ddof=1))
    if v<=0 or m<=0: return {"dist":"gamma","params":{"k":np.nan,"theta":np.nan}}
    k = m**2 / v; theta = v / m
    return {"dist":"gamma","params":{"k":float(k),"theta":float(theta)}}

def poisson_lambda(x: np.ndarray) -> float:
    x = x[~np.isnan(x)]
    return float(np.mean(x)) if len(x) else float("nan")

def pmf_poisson(k_arr: np.ndarray, lam: float) -> np.ndarray:
    import math
    p = np.array([math.exp(-lam)*lam**k / math.factorial(k) for k in k_arr], dtype=float)
    return p / p.sum() if p.sum()>0 else p
