# -*- coding: utf-8 -*-
import numpy as np

def aplicar_shocks(probs: np.ndarray, n_shocks: int, effect: np.ndarray):
    """
    Aplica n_shocks veces el vector 'effect' a las probabilidades y renormaliza.
    """
    p = probs + n_shocks * effect
    p = np.clip(p, 1e-6, None)
    p = p / p.sum()
    return p
