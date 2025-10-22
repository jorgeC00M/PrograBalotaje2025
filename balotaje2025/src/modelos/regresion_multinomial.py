# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import statsmodels.api as sm

def preparar_X_y(df: pd.DataFrame, columnas_X: list, col_y: str = "voto"):
    X = sm.add_constant(df[columnas_X], has_constant="add")
    y = df[col_y]
    return X, y

def entrenar_multinomial(X: pd.DataFrame, y: pd.Series):
    modelo = sm.MNLogit(y, X).fit(method="newton", maxiter=200, disp=False)
    rrr = np.exp(modelo.params)  # Razones de riesgo relativas
    return modelo, rrr

def exportar_coeficientes(modelo, rrr, ruta_excel: str):
    with pd.ExcelWriter(ruta_excel) as w:
        modelo.params.to_excel(w, sheet_name="coeficientes")
        rrr.to_excel(w, sheet_name="RRR_exp_beta")

def params_a_betas_por_clase(modelo, clases: list):
    """
    Convierte modelo.params (clases vs coef) a dict {clase: vector_beta},
    asignando vector 0 a la clase base que no aparece en las filas de params.
    """
    cols = list(modelo.params.columns)  # ['const', features...]
    p = len(cols)
    betas = {}
    clases_en_params = set(modelo.params.index)
    clase_base = list(set(clases) - clases_en_params)
    base = clase_base[0] if clase_base else clases[-1]
    for cl in clases:
        if cl in clases_en_params:
            v = modelo.params.loc[cl, :].to_numpy()
        else:
            v = np.zeros(p)
        betas[cl] = v
    return betas
