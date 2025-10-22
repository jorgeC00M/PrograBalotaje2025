# -*- coding: utf-8 -*-
import pandas as pd
from .definicion_variables import MAPEO_IDEOLOGIA

def cargar_datos(ruta_excel: str) -> pd.DataFrame:
    """Lee el Excel exportado de Google Forms y normaliza textos."""
    df = pd.read_excel(ruta_excel)

    # Renombrar columnas a nombres internos (AJUSTA a tu archivo real):
    ren = {
        "Intención de voto": "voto",
        "Firmeza (1-5)": "firmeza",
        "Ideología": "ideologia",
        # "Estrato": "estrato",
        # "Situación educativa": "situacion",
        # "Medio principal": "medio",
    }
    for k, v in ren.items():
        if k in df.columns:
            df.rename(columns={k: v}, inplace=True)

    # Normalizar strings
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip().str.lower()

    return df

def codificar_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte a numérico/ordinal y crea dummies donde corresponda."""
    out = df.copy()

    # Firmeza a numérico
    if "firmeza" in out:
        out["firmeza"] = pd.to_numeric(out["firmeza"], errors="coerce")

    # Ideología a ordinal
    if "ideologia" in out:
        out["ideologia_num"] = out["ideologia"].map(MAPEO_IDEOLOGIA)

    # Dummies ejemplos
    for col in ["medio", "estrato", "situacion"]:
        if col in out.columns:
            dummies = pd.get_dummies(out[col], prefix=col, dummy_na=False)
            out = pd.concat([out, dummies], axis=1)

    # Limpieza de voto
    if "voto" in out.columns:
        out["voto"] = out["voto"].str.strip().str.lower()

    return out
