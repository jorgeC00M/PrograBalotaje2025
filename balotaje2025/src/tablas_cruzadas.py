# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from .configuracion import RES_TABLAS

def crosstab(df: pd.DataFrame, fila: str, col: str):
    freq = pd.crosstab(df[fila], df[col], dropna=True)
    por_fila = pd.crosstab(df[fila], df[col], normalize="index", dropna=True).round(3)
    return freq, por_fila

def cramers_v(tabla: pd.DataFrame) -> float:
    chi2 = _chi2_stat(tabla.values)
    n = tabla.values.sum()
    r, k = tabla.shape
    return float(np.sqrt(chi2 / (n * (min(r-1, k-1))))) if min(r,k) > 1 else float("nan")

def _chi2_stat(obs):
    row_sums = obs.sum(axis=1, keepdims=True)
    col_sums = obs.sum(axis=0, keepdims=True)
    total = obs.sum()
    expected = row_sums @ col_sums / total
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((obs-expected)**2 / expected)
    return float(chi2)

def exportar_crosstab(nombre_base: str, freq: pd.DataFrame, por_fila: pd.DataFrame):
    xlsx = RES_TABLAS / f"{nombre_base}.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
        freq.to_excel(w, sheet_name="Frecuencias")
        por_fila.to_excel(w, sheet_name="%Fila")
    return xlsx
