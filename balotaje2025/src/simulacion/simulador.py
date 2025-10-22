# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
from .transiciones import softmax, utilidades
from ..configuracion import RUTA_SIMULACIONES

def simular(pasos, X, firmeza, estados_idx, clases, betas_por_clase, shocks_por_t=None, rng=None):
    """
    Simulación dinámica mínima, sin necesidad de escenarios.
    - shocks_por_t: lista de dicts o None; cada dict {clase: delta_utilidad}.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    historial = []

    for t in range(pasos):
        eta = utilidades(X, betas_por_clase, clases, firmeza, estados_idx)

        # Aplica shocks opcionales
        if shocks_por_t and t < len(shocks_por_t) and shocks_por_t[t]:
            for cls, delta in shocks_por_t[t].items():
                k = clases.index(cls)
                eta[:, k] += float(delta)

        p = softmax(eta)
        cumul = p.cumsum(axis=1)
        r = rng.random((len(X), 1))
        estados_idx = (r > cumul[:, :-1]).sum(axis=1)

        conteo = {cl: int((estados_idx == i).sum()) for i, cl in enumerate(clases)}
        conteo["t"] = t
        historial.append(conteo)

    hist_df = pd.DataFrame(historial).set_index("t")
    os.makedirs(RUTA_SIMULACIONES, exist_ok=True)
    hist_path = os.path.join(RUTA_SIMULACIONES, "simulacion_historial.xlsx")
    hist_df.to_excel(hist_path)
    return hist_df, estados_idx, hist_path
