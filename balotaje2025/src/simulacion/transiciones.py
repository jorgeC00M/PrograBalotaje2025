# -*- coding: utf-8 -*-
import numpy as np

def softmax(eta):
    e = np.exp(eta - eta.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)

def utilidades(X, betas_por_clase: dict, clases: list, firmeza, estado_idx, lambda_firmeza=0.4):
    """
    η_k = β0_k + X @ β_k + λ * firmeza (solo para la clase actual)
    - X: matriz [n, p-1] si p incluye constante aparte.
    - betas_por_clase[clase]: vector [const, β1, β2, ...]
    """
    n = X.shape[0]; K = len(clases)
    eta = np.zeros((n, K))
    for k, cls in enumerate(clases):
        beta = betas_por_clase[cls]
        eta[:, k] = beta[0] + X @ beta[1:]
    # inercia hacia la clase actual
    for k in range(K):
        mask = (estado_idx == k)
        eta[mask, k] += lambda_firmeza * firmeza[mask]
    return eta
