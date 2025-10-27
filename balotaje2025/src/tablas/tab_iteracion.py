import tkinter as tk
from tkinter import ttk, messagebox


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Variable de iteración")

    frm = ttk.Frame(f)
    frm.pack(pady=10)

    app.T_var = tk.IntVar(value=app.state.T)
    app.R_var = tk.IntVar(value=app.state.R)
    app.seed_var = tk.IntVar(value=app.state.seed)

    ttk.Label(frm, text="T (pasos):").grid(row=0, column=0, sticky="e")
    ttk.Entry(frm, textvariable=app.T_var, width=8).grid(row=0, column=1, padx=5)
    ttk.Label(frm, text="R (replicaciones):").grid(row=1, column=0, sticky="e")
    ttk.Entry(frm, textvariable=app.R_var, width=8).grid(row=1, column=1, padx=5)
    ttk.Label(frm, text="Semilla:").grid(row=2, column=0, sticky="e")
    ttk.Entry(frm, textvariable=app.seed_var, width=8).grid(row=2, column=1, padx=5)
    ttk.Button(frm, text="Guardar", command=lambda: _save_iter(app)).grid(row=3, column=0, columnspan=2, pady=10)


def _save_iter(app):
    app.state.T = max(1, int(app.T_var.get()))
    app.state.R = max(1, int(app.R_var.get()))
    app.state.seed = int(app.seed_var.get())
    app.actualizar_status()
    messagebox.showinfo("OK", f"T={app.state.T}, R={app.state.R}, seed={app.state.seed}")
