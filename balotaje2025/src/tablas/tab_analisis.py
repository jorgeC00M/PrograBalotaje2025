import tkinter as tk
from tkinter import ttk, messagebox

from ..analisis_encuesta import (
    descriptivos_basicos,
    crosstab_por,
    entrenar_logistica_binaria,
    normalizar_columnas,
)


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Análisis")

    # --- Descriptivos ---
    box1 = ttk.LabelFrame(f, text="Descriptivos globales"); box1.pack(fill="x", padx=6, pady=6)
    ttk.Button(box1, text="Calcular % (Paz/JQR/Blanco/Nulo)", command=lambda: _run_desc(app)).pack(side="left", padx=6, pady=6)

    # --- Crosstab ---
    box2 = ttk.LabelFrame(f, text="Crosstab"); box2.pack(fill="x", padx=6, pady=6)
    app.ct_row = tk.StringVar(); app.ct_col = tk.StringVar()
    ttk.Label(box2, text="Fila:").pack(side="left", padx=4); app.cb_ct_row = ttk.Combobox(box2, textvariable=app.ct_row, width=28); app.cb_ct_row.pack(side="left", padx=4)
    ttk.Label(box2, text="Columna:").pack(side="left", padx=4); app.cb_ct_col = ttk.Combobox(box2, textvariable=app.ct_col, width=28); app.cb_ct_col.pack(side="left", padx=4)
    ttk.Button(box2, text="Generar", command=lambda: _run_ct(app)).pack(side="left", padx=6)

    # --- Logística binaria ---
    box3 = ttk.LabelFrame(f, text="Regresión logística (Paz=1 vs JQR=0)"); box3.pack(fill="x", padx=6, pady=6)
    ttk.Button(box3, text="Entrenar (auto predictores)", command=lambda: _run_logit(app)).pack(side="left", padx=6, pady=6)

    # resultados
    app.txt_analisis = tk.Text(f, height=16)
    app.txt_analisis.pack(fill="both", expand=True, padx=6, pady=6)

    def refresh(*_):
        if app.state.df_proc is not None:
            cols = list(normalizar_columnas(app.state.df_proc).columns)
            app.cb_ct_row["values"] = cols
            app.cb_ct_col["values"] = cols
    f.bind("<Visibility>", refresh)


def _run_desc(app):
    if app.state.df_proc is None:
        messagebox.showwarning("Atención", "Carga datos primero.")
        return
    res = descriptivos_basicos(app.state.df_proc)
    app.txt_analisis.delete("1.0", "end")
    app.txt_analisis.insert("1.0", f"{res}")


def _run_ct(app):
    if app.state.df_proc is None:
        messagebox.showwarning("Atención", "Carga datos primero.")
        return
    r, c = app.ct_row.get().strip(), app.ct_col.get().strip()
    if not r or not c:
        messagebox.showwarning("Atención", "Selecciona variables.")
        return
    tabla = crosstab_por(app.state.df_proc, r, c)
    app.txt_analisis.delete("1.0", "end")
    app.txt_analisis.insert("1.0", f"{tabla}")


def _run_logit(app):
    if app.state.df_proc is None:
        messagebox.showwarning("Atención", "Carga datos primero.")
        return
    rep = entrenar_logistica_binaria(app.state.df_proc)
    app.txt_analisis.delete("1.0", "end")
    app.txt_analisis.insert("1.0", f"{rep}")
