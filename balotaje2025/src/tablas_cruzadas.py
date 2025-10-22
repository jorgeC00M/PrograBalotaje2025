# -*- coding: utf-8 -*-
import os
import pandas as pd
from .configuracion import RUTA_TABLAS

def generar_tablas_cruzadas(df: pd.DataFrame) -> dict:
    """Crea crosstabs normalizadas por fila (porcentaje dentro de cada grupo)."""
    tablas = {}
    if "estrato" in df.columns and "voto" in df.columns:
        tablas["estrato_voto"] = pd.crosstab(df["estrato"], df["voto"], normalize="index").round(3)
    if "situacion" in df.columns and "voto" in df.columns:
        tablas["situacion_voto"] = pd.crosstab(df["situacion"], df["voto"], normalize="index").round(3)
    if "ideologia" in df.columns and "voto" in df.columns:
        tablas["ideologia_voto"] = pd.crosstab(df["ideologia"], df["voto"], normalize="index").round(3)
    return tablas

def exportar_tablas(tablas: dict, nombre="tablas_cruzadas.xlsx"):
    os.makedirs(RUTA_TABLAS, exist_ok=True)
    ruta = os.path.join(RUTA_TABLAS, nombre)
    with pd.ExcelWriter(ruta) as w:
        for hoja, t in tablas.items():
            t.to_excel(w, sheet_name=hoja[:31])
    return ruta
