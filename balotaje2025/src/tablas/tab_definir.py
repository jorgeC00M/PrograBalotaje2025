import tkinter as tk
from tkinter import ttk, messagebox

from .. import definicion_variables as dv


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Definir variables")

    top = ttk.Frame(f)
    top.pack(fill="x", pady=5)

    app.target_var = tk.StringVar(value="")
    ttk.Label(top, text="Objetivo (Intención de voto):").pack(side="left", padx=5)
    app.cb_target = ttk.Combobox(top, textvariable=app.target_var, width=40, values=[])
    app.cb_target.pack(side="left", padx=5)
    ttk.Button(top, text="Guardar objetivo", command=lambda: _save_target(app)).pack(side="left", padx=5)

    mid = ttk.Frame(f)
    mid.pack(fill="both", expand=True)

    left = ttk.Frame(mid)
    left.pack(side="left", fill="y", padx=5)
    app.list_cols = tk.Listbox(left, selectmode="extended", height=20)
    app.list_cols.pack(fill="y")
    ttk.Button(left, text="Refrescar columnas", command=lambda: _refresh_cols(app)).pack(pady=5)

    right = ttk.Frame(mid)
    right.pack(side="left", fill="y", padx=10)
    ttk.Button(right, text="Marcar Demográfica", command=lambda: _set_role(app, "Demográfica")).pack(fill="x", pady=2)
    ttk.Button(right, text="Marcar Factor (Likert)", command=lambda: _set_role(app, "Likert")).pack(fill="x", pady=2)
    ttk.Button(right, text="Marcar Atributo Candidato", command=lambda: _set_role(app, "Atributo")).pack(fill="x", pady=2)

    _refresh_cols(app)


def _refresh_cols(app):
    app.list_cols.delete(0, "end")
    cols = dv.columnas(app.state)
    app.cb_target["values"] = cols
    for c in cols:
        app.list_cols.insert("end", c)


def _save_target(app):
    col = app.target_var.get().strip()
    try:
        dv.set_target(app.state, col)
        messagebox.showinfo("OK", f"Objetivo: {col}")
        app.actualizar_status()
    except Exception as e:
        messagebox.showerror("Error", str(e))


def _set_role(app, role):
    sel = [app.list_cols.get(i) for i in app.list_cols.curselection()]
    if not sel:
        messagebox.showwarning("Atención", "Selecciona columnas.")
        return
    dv.set_role(app.state, sel, role)
    messagebox.showinfo("OK", f"Asignadas {len(sel)} columnas como {role}")
