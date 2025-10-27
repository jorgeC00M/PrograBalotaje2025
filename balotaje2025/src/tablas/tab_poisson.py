import tkinter as tk
from tkinter import ttk, messagebox

from .. import definicion_variables as dv
from .. import distribuciones as dist


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Distribución de Poisson")

    top = ttk.Frame(f)
    top.pack(fill="x", pady=5)

    app.var_count = tk.StringVar()
    app.lambda_val = tk.DoubleVar(value=0.5)

    app.cb_count = ttk.Combobox(top, textvariable=app.var_count, width=30)
    app.cb_count.pack(side="left", padx=5)
    ttk.Button(top, text="Estimar λ", command=lambda: _estimar_lambda(app)).pack(side="left", padx=5)
    ttk.Label(top, text="λ:").pack(side="left")
    ttk.Entry(top, textvariable=app.lambda_val, width=10).pack(side="left", padx=5)

    app.txt_poisson = tk.Text(f, height=8)
    app.txt_poisson.pack(fill="x", padx=5, pady=5)

    def refresh_cb(*_):
        app.cb_count["values"] = dv.numericas(app.state)

    f.bind("<Visibility>", refresh_cb)


def _estimar_lambda(app):
    if app.state.df_proc is None:
        messagebox.showwarning("Atención", "Carga datos primero.")
        return
    col = app.var_count.get().strip()
    if not col:
        messagebox.showwarning("Atención", "Selecciona variable de conteo.")
        return
    lam = dist.poisson_lambda(app.state.df_proc[col].to_numpy(dtype=float))
    app.lambda_val.set(lam)
    app.state.poisson_lambda = lam
    app.txt_poisson.delete("1.0", "end")
    app.txt_poisson.insert("1.0", f"λ estimado para {col}: {lam:.4f}")
