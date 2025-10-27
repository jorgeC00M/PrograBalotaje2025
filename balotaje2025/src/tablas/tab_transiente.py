import tkinter as tk
from tkinter import ttk, messagebox


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Estado transiente")

    frm = ttk.Frame(f)
    frm.pack(pady=10)

    app.warm_var = tk.IntVar(value=app.state.warmup)
    ttk.Label(frm, text="Warm-up (iteraciones a descartar):").grid(row=0, column=0, sticky="e")
    ttk.Scale(frm, variable=app.warm_var, from_=0, to=100, orient="horizontal").grid(row=0, column=1, padx=10)
    ttk.Button(frm, text="Guardar", command=lambda: _save_warm(app)).grid(row=1, column=0, columnspan=2, pady=10)


def _save_warm(app):
    app.state.warmup = max(0, int(app.warm_var.get()))
    app.actualizar_status()
    messagebox.showinfo("OK", f"Warm-up={app.state.warmup}")
