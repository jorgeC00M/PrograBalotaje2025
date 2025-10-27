import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

from .. import definicion_variables as dv
from .. import distribuciones as dist
from ..visualizacion import guardar_histograma


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Distribuciones")

    top = ttk.Frame(f)
    top.pack(fill="x", pady=5)

    app.var_num = tk.StringVar()
    app.var_dist = tk.StringVar(value="normal")

    app.cb_num = ttk.Combobox(top, textvariable=app.var_num, width=30)
    app.cb_num.pack(side="left", padx=5)
    app.cb_dist = ttk.Combobox(
        top, textvariable=app.var_dist, width=15, values=["normal", "lognormal", "exponencial", "gamma"]
    )
    app.cb_dist.pack(side="left", padx=5)
    ttk.Button(top, text="Ajustar", command=lambda: _ajustar_dist(app)).pack(side="left", padx=5)

    app.txt_dist = tk.Text(f, height=12)
    app.txt_dist.pack(fill="x", padx=5, pady=5)

    app.img_dist_label = ttk.Label(f)
    app.img_dist_label.pack(pady=5)
    app._img_dist_ref = None

    def refresh_cb(*_):
        app.cb_num["values"] = dv.numericas(app.state)

    f.bind("<Visibility>", refresh_cb)


def _ajustar_dist(app):
    if app.state.df_proc is None:
        messagebox.showwarning("Atención", "Carga datos primero.")
        return
    col = app.var_num.get().strip()
    if not col:
        messagebox.showwarning("Atención", "Selecciona variable numérica.")
        return

    x = app.state.df_proc[col].astype(float).to_numpy()
    dist_name = app.var_dist.get()

    fitters = {
        "normal": dist.fit_normal,
        "lognormal": dist.fit_lognormal,
        "exponencial": dist.fit_exponencial,
        "gamma": dist.fit_gamma,
    }
    fit = fitters.get(dist_name, dist.fit_normal)(x)
    app.state.dist_fits[col] = fit

    path = guardar_histograma(x[~np.isnan(x)], f"Ajuste {fit['dist']} - {col}", f"hist_{col}_{fit['dist']}")

    app.txt_dist.delete("1.0", "end")
    app.txt_dist.insert("1.0", f"Distribución: {fit['dist']}\nParámetros: {fit['params']}\nGráfico: {path}")

    try:
        img = tk.PhotoImage(file=str(path))
        app.img_dist_label.configure(image=img, text="")
        app._img_dist_ref = img
    except Exception as e:
        app.img_dist_label.configure(image="", text=f"No se pudo cargar la imagen.\n{path}\n{e}")
