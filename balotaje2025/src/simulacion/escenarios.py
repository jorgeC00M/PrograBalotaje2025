# -*- coding: utf-8 -*-
"""
Escenarios (opcional). Genera una lista de shocks simples por paso.
Cada shock es un dict {clase: delta_utilidad}.
Si no quieres escenarios, no lo uses (pasa None en el simulador).
"""

def escenario_simple(clases, pasos=6, favorece="a", delta=0.4, t0=2):
    shocks = [None] * pasos
    if favorece in clases and 0 <= t0 < pasos:
        shocks[t0] = {favorece: float(delta)}
    return shocks
