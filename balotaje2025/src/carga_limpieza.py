# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

def cargar_excel(path, sheet_name=None):
    return pd.read_excel(path, sheet_name=sheet_name)

def vista_previa(df: pd.DataFrame, n=20):
    return df.head(n)

def resumen(df: pd.DataFrame):
    return {
        "filas": len(df),
        "columnas": df.shape[1],
        "tipos": df.dtypes.astype(str).to_dict(),
        "na_%": df.isna().mean().round(3).to_dict(),
    }

def imputar_simple(df: pd.DataFrame, metodo_por_col: dict[str, str]):
    out = df.copy()
    for col, m in metodo_por_col.items():
        if m == "none" or col not in out.columns:
            continue
        if m in ("mean","median") and pd.api.types.is_numeric_dtype(out[col]):
            val = out[col].mean() if m == "mean" else out[col].median()
            out[col] = out[col].fillna(val)
        elif m == "mode":
            moda = out[col].mode(dropna=True)
            if len(moda): out[col] = out[col].fillna(moda.iloc[0])
    return out
