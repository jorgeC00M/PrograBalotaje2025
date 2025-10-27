# src/analisis_encuesta.py
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# ------------ Config ----------
OUT_DIR = Path("resultados_auto")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Palabras clave para detectar target y categorías
PAZ_RE   = re.compile(r"\b(rodrigo|paz)\b", re.I)
JQR_RE   = re.compile(r"\b(jorge|quiroga)\b", re.I)
BLANCO_RE= re.compile(r"\bblanco\b", re.I)
NULO_RE  = re.compile(r"\bnulo\b", re.I)
INDEC_RE = re.compile(r"indeci|aun_no|todavia_no|no_lo_he_decid", re.I)

# Columnas sugeridas por la guía
SUGERIDAS = {
    # demografía / segmentación
    "edad": ["edad","rango_edad"],
    "genero": ["genero","sexo"],
    "departamento": ["departamento","ciudad","residencia"],
    "situacion_educativa": ["situacion_educativa","educativa","estudiante","recien_profesionalizado"],
    "estrato": ["estrato","socioeconomico","estrato_socioeconomico","estrato_percibido"],
    "estatus_laboral": ["estatus_laboral","situacion_laboral","empleo","trabajo"],

    # ideología / factores
    "firmeza_voto": ["firmeza","seguro","que_tan_seguro"],
    "tendencia_politica": ["tendencia_politica","ideologia","con_que_tendencia"],
    "influencia_corrupcion": ["corrupcion","noticias","noticias_sobre_corrupcion"],
    "fuente_confianza": ["fuente_confianza","medio_principal","medio_de_informacion"],

    # target
    "intencion_voto": [
        "si_las_elecciones_fueran_manana","intencion_de_voto","candidato_voto",
        "votaria","intencion_voto","candidato","voto"
    ],
}

def _norm(s: str) -> str:
    s = str(s).strip().lower()
    subs = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n","/":" ","-":" ","(":" ",")":" "}
    for k,v in subs.items(): s = s.replace(k,v)
    s = re.sub(r"\s+"," ", s).replace(" ","_")
    return s

def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_norm(c) for c in df.columns]
    return df

def detectar_col(df: pd.DataFrame, alias: list[str]) -> str|None:
    for kw in alias:
        for c in df.columns:
            if kw in c:
                return c
    return None

def detectar_target(df: pd.DataFrame) -> str|None:
    cand = SUGERIDAS["intencion_voto"]
    t = detectar_col(df, cand)
    if t: return t
    # fallback: busca valores con nombres de candidatos
    for c in df.columns:
        vals = df[c].dropna().astype(str).str.lower()
        if vals.str.contains("paz|quiroga|rodrigo|jorge").any():
            return c
    return None

def coerce_likert(x: pd.Series) -> pd.Series:
    # extrae número de strings "1 Nada"..."5 Mucho"
    return pd.to_numeric(x.astype(str).str.extract(r"(\d+)")[0], errors="coerce")

# -------------- 1) Descriptivos -----------------
def descriptivos_basicos(df_raw: pd.DataFrame) -> dict:
    """
    Devuelve porcentajes globales: Paz, JQR, Blanco, Nulo
    (indecisos/otros excluidos del denominador).
    Guarda un gráfico de torta 'global.png'
    """
    df = normalizar_columnas(df_raw)
    tgt = detectar_target(df)
    if not tgt:
        raise ValueError("No se detectó columna de intención de voto. Usa nombres acordes o renómbrala.")

    vals = df[tgt].astype(str).str.lower()
    mask_paz  = vals.str.contains(PAZ_RE)
    mask_jqr  = vals.str.contains(JQR_RE)
    mask_bla  = vals.str.contains(BLANCO_RE)
    mask_nul  = vals.str.contains(NULO_RE)
    mask_ind  = vals.str.contains(INDEC_RE)

    n_valid = int(mask_paz.sum() + mask_jqr.sum())
    denom = n_valid + int(mask_bla.sum()) + int(mask_nul.sum())
    if denom == 0:
        raise ValueError("No hay suficientes observaciones válidas para porcentajes (candidatos + blanco + nulo).")

    res = {
        "Rodrigo Paz": mask_paz.sum()/denom,
        "Jorge Quiroga": mask_jqr.sum()/denom,
        "Voto Blanco": mask_bla.sum()/denom,
        "Voto Nulo": mask_nul.sum()/denom,
        "Indecisos/Otros (fuera del denom)": int(mask_ind.sum())
    }

    # gráfico
    labels = ["Rodrigo Paz","Jorge Quiroga","Voto Blanco","Voto Nulo"]
    vals = [res[l] for l in labels]
    plt.figure()
    plt.pie(vals, labels=[f"{l} ({v*100:.1f}%)" for l,v in labels_and_vals(labels, vals)], autopct=None)
    plt.title("Porcentajes globales")
    out = OUT_DIR / "global.png"
    plt.savefig(out, bbox_inches="tight")
    plt.close()

    return {"porcentajes": res, "grafico": str(out), "target": tgt}

def labels_and_vals(labels, vals):
    return list(zip(labels, vals))

# -------------- 2) Crosstabs -----------------
def crosstab_por(df_raw: pd.DataFrame, fila: str, col: str) -> dict:
    """
    Crosstab de variables categóricas.
    Guarda CSV y PNG de heatmap simple.
    """
    df = normalizar_columnas(df_raw)
    if fila not in df.columns or col not in df.columns:
        raise ValueError(f"Variables '{fila}' o '{col}' no existen (usa nombres normalizados).")

    ct = pd.crosstab(df[fila], df[col], dropna=False)
    pct = ct.div(ct.sum(axis=1).replace(0, np.nan), axis=0)

    # export
    p_csv = OUT_DIR / f"crosstab_{fila}_vs_{col}.csv"
    ct.to_csv(p_csv)

    # heatmap simple con matplotlib
    plt.figure()
    plt.imshow(pct.fillna(0).to_numpy(), aspect="auto")
    plt.xticks(range(pct.shape[1]), pct.columns, rotation=45, ha="right")
    plt.yticks(range(pct.shape[0]), pct.index)
    plt.colorbar(label="% fila")
    plt.title(f"Crosstab % fila: {fila} vs {col}")
    p_png = OUT_DIR / f"crosstab_{fila}_vs_{col}.png"
    plt.tight_layout()
    plt.savefig(p_png, dpi=130)
    plt.close()

    return {"frecuencias": ct, "por_fila": pct, "csv": str(p_csv), "png": str(p_png)}

# -------------- 3) Logística binaria -----------------
def entrenar_logistica_binaria(df_raw: pd.DataFrame, predictores: list[str]|None=None) -> dict:
    """
    Entrena Regresión Logística (Paz=1 vs JQR=0).
    - Convierte Likert cuando detecta 'firmeza' o 'corrupcion'.
    - OHE para categóricas, imputación.
    Devuelve accuracy, reporte, coeficientes y exporta tabla CSV.
    """
    df = normalizar_columnas(df_raw)
    tgt = detectar_target(df)
    if not tgt:
        raise ValueError("No se detectó columna objetivo.")
    y_raw = df[tgt].astype(str).str.lower()
    y = y_raw.map(lambda s: 1 if PAZ_RE.search(s) else (0 if JQR_RE.search(s) else np.nan))
    mask = y.notna()
    if mask.sum() < 20:
        raise ValueError(f"Pocas filas válidas Paz/JQR: {int(mask.sum())}")

    # si no pasan predictores -> detecta algunos razonables
    if not predictores:
        candidatos = []
        for k, alias in SUGERIDAS.items():
            if k == "intencion_voto": continue
            c = detectar_col(df, alias)
            if c: candidatos.append(c)
        predictores = sorted(set(candidatos))

    X = df.loc[mask, predictores].copy()
    y = y.loc[mask].astype(int)

    # detectar numéricos/likert vs categóricos
    num_cols, cat_cols = [], []
    for c in X.columns:
        if any(key in c for key in ["firmeza","corrupcion","noticias"]):
            X[c] = coerce_likert(X[c])
        try_num = pd.to_numeric(X[c], errors="coerce")
        if try_num.notna().mean() > 0.8:
            X[c] = try_num
            num_cols.append(c)
        else:
            cat_cols.append(c)

    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False) if "sparse_output" in OneHotEncoder.__init__.__code__.co_varnames else OneHotEncoder(handle_unknown="ignore", sparse=False)

    pre = ColumnTransformer(
        [
            ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("ohe", ohe)]), cat_cols),
            ("num", Pipeline([("imp", SimpleImputer(strategy="median"))]), num_cols),
        ],
        remainder="drop",
    )

    pipe = Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=2000, solver="lbfgs"))])
    pipe.fit(X, y)

    # métricas
    yhat = pipe.predict(X)
    acc = accuracy_score(y, yhat)
    rep = classification_report(y, yhat, target_names=["JQR","Paz"])

    # nombres de features transformados
    Xt = pipe.named_steps["pre"].transform(X)
    cat_names = []
    if cat_cols:
        ohe_step = pipe.named_steps["pre"].named_transformers_["cat"].named_steps["ohe"]
        cat_names = list(
            ohe_step.get_feature_names_out(cat_cols) if hasattr(ohe_step, "get_feature_names_out")
            else ohe_step.get_feature_names(cat_cols)
        )
    feat_names = cat_names + num_cols

    coef = pipe.named_steps["clf"].coef_[0]
    intercept = pipe.named_steps["clf"].intercept_[0]

    coef_df = pd.DataFrame({
        "feature": feat_names,
        "coef": coef,
        "odds_ratio": np.exp(coef),
    }).sort_values("odds_ratio", ascending=False)

    p_csv = OUT_DIR / "coeficientes_logistica.csv"
    coef_df.to_csv(p_csv, index=False)

    return {
        "pipeline": pipe,
        "accuracy": acc,
        "reporte": rep,
        "coeficientes": coef_df,
        "coef_csv": str(p_csv),
        "intercepto": float(intercept),
        "predictores": predictores,
        "target": tgt,
        "n": int(mask.sum()),
    }
