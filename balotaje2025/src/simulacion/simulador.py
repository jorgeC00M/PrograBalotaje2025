# -*- coding: utf-8 -*-
import numpy as np
from .transiciones import aplicar_shocks
from .estado import aplicar_warmup

def simular(T: int, R: int, warmup: int, base_probs: dict, lam: float, effect_map: dict, seed=42):
    """
    - En cada t: N_t ~ Poisson(lam) shocks.
    - Cada shock añade 'effect' a las probabilidades y se normaliza.
    """
    rng = np.random.default_rng(seed)
    clases = list(base_probs.keys())
    base = np.array([base_probs[c] for c in clases], dtype=float); base = base/base.sum()
    effect = np.array([effect_map.get(c, 0.0) for c in clases], dtype=float)

    traj = np.zeros((R, T, len(clases)), dtype=float)
    for r in range(R):
        p = base.copy()
        for t in range(T):
            shocks = rng.poisson(lam)
            p = aplicar_shocks(p, shocks, effect)
            traj[r, t, :] = p

    t0, avg, sd = aplicar_warmup(traj, warmup)
    summary = {clases[i]: {"mean": float(avg[i]), "sd": float(sd[i])} for i in range(len(clases))}
    return {"classes": clases, "trajectories": traj, "warmup_used": t0, "summary": summary}
