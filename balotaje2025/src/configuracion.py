# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATOS = BASE / "datos"
RESULTADOS = BASE / "resultados"
RES_MODELOS = RESULTADOS / "modelos"
RES_GRAFICOS = RESULTADOS / "graficos"
RES_SIMULACIONES = RESULTADOS / "simulaciones"
RES_TABLAS = RESULTADOS / "tablas"

for p in [RESULTADOS, RES_MODELOS, RES_GRAFICOS, RES_SIMULACIONES, RES_TABLAS]:
    p.mkdir(parents=True, exist_ok=True)

DEFAULT_EXCEL = DATOS / "respuestas.xlsx"

@dataclass
class AppState:
    df = None                # pandas.DataFrame crudo
    df_proc = None           # DataFrame procesado
    target: str | None = None
    roles: dict = None       # {col: "Demográfica"|"Likert"|"Atributo"|...}
    dist_fits: dict = None   # {col: {"dist":..., "params":{...}}}
    poisson_lambda: float | None = None
    model = None             # sklearn pipeline
    model_report: dict | None = None
    model_features: list | None = None
    model_classes: list | None = None
    T: int = 20
    R: int = 50
    warmup: int = 0
    seed: int = 42

    def __post_init__(self):
        if self.roles is None: self.roles = {}
        if self.dist_fits is None: self.dist_fits = {}
