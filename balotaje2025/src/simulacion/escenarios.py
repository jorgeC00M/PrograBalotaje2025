# -*- coding: utf-8 -*-
def base_probs():
    # Puedes ajustar esto o calcularlo desde tus datos reales (p.ej., promedios observados)
    return {"A": 0.30, "B": 0.40, "Blanco": 0.20, "Nulo": 0.05, "Indeciso": 0.05}

def efecto_shock_default():
    # Efectos por shock sobre probabilidades (se renormalizan en la simulación)
    return {"A": +0.01, "B": -0.01, "Blanco": 0.0, "Nulo": 0.0, "Indeciso": 0.0}
