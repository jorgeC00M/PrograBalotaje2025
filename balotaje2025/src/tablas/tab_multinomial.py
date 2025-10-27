import tkinter as tk
from tkinter import ttk, messagebox

from ..modelos.regresion_multinomial import entrenar_multinomial


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Regresión logística multinomial")

    top = ttk.Frame(f)
    top.pack(fill="x", pady=5)

    ttk.Label(top, text="Objetivo:").pack(side="left", padx=5)
    app.lbl_target = ttk.Label(top, text="(definir en 'Definir variables')", foreground="blue")
    app.lbl_target.pack(side="left")
    ttk.Button(top, text="Entrenar", command=lambda: _entrenar_modelo(app)).pack(side="left", padx=5)

    mid = ttk.Frame(f)
    mid.pack(fill="both", expand=True)

    left = ttk.Frame(mid)
    left.pack(side="left", fill="y", padx=5)
    ttk.Label(left, text="Predictores:").pack(anchor="w")
    app.lb_feats = tk.Listbox(left, selectmode="extended", height=20)
    app.lb_feats.pack(fill="y")

    def refresh_cb(*_):
        app.lbl_target.config(text=app.state.target or "(definir)")
        app.lb_feats.delete(0, "end")
        if app.state.df_proc is not None:
            for c in app.state.df_proc.columns:
                if c != app.state.target:
                    app.lb_feats.insert("end", c)

    f.bind("<Visibility>", refresh_cb)

    right = ttk.Frame(mid)
    right.pack(side="left", fill="both", expand=True, padx=5)
    app.txt_model = tk.Text(right)
    app.txt_model.pack(fill="both", expand=True)


def _entrenar_modelo(app):
    if app.state.df_proc is None or not app.state.target:
        messagebox.showwarning("Atención", "Debes cargar datos y definir objetivo.")
        return
    feats = [app.lb_feats.get(i) for i in app.lb_feats.curselection()]
    if not feats:
        messagebox.showwarning("Atención", "Selecciona al menos un predictor.")
        return
    res = entrenar_multinomial(app.state.df_proc, app.state.target, feats)
    app.state.model = res["pipeline"]
    app.state.model_report = res
    app.state.model_features = res["features"]
    app.state.model_classes = res["classes"]
    app.actualizar_status()
    app.txt_model.delete("1.0", "end")
    app.txt_model.insert("1.0", f"Accuracy: {res['accuracy']:.4f}\nClases: {res['classes']}\n\nReporte:\n{res['report']}")
