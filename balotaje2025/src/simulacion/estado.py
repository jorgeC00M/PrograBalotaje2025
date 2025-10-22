# -*- coding: utf-8 -*-
def aplicar_warmup(trajectories, warmup: int):
    """
    trajectories: ndarray (R, T, C)
    warmup: iteraciones a descartar del inicio (0..T-1)
    """
    import numpy as np
    R, T, C = trajectories.shape
    t0 = min(max(int(warmup), 0), T-1)
    post = trajectories[:, t0:, :].mean(axis=1)   # promedio por réplica en tiempo post-warmup
    avg = post.mean(axis=0); sd = post.std(axis=0, ddof=1) if R>1 else post.std(axis=0)
    return t0, avg, sd
