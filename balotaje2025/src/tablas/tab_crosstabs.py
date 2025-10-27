import tkinter as tk
from tkinter import ttk, messagebox

from .. import definicion_variables as dv
from .. import tablas_cruzadas as tc


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Tablas cruzadas")

    top = ttk.Frame(f)
    top.pack(fill="x", pady=5)

    app.row_var = tk.StringVar()
    app.col_var = tk.StringVar()
    app.cb_row = ttk.Combobox(top, textvariable=app.row_var, width=30)
    app.cb_col = ttk.Combobox(top, textvariable=app.col_var, width=30)
    ttk.Label(top, text="Fila:").pack(side="left", padx=5)
    app.cb_row.pack(side="left")
    ttk.Label(top, text="Columna:").pack(side="left", padx=5)
    app.cb_col.pack(side="left")
    ttk.Button(top, text="Calcular", command=lambda: _calc_crosstab(app)).pack(side="left", padx=5)

    app.txt_crosstab = tk.Text(f, height=22)
    app.txt_crosstab.pack(fill="both", expand=True, padx=5, pady=5)

    def refresh_cb(*_):
        cols = dv.columnas(app.state)
        app.cb_row["values"] = cols
        app.cb_col["values"] = cols

    f.bind("<Visibility>", refresh_cb)


def _calc_crosstab(app):
    if app.state.df_proc is None:
        messagebox.showwarning("Atención", "Carga datos primero.")
        return
    r, c = app.row_var.get().strip(), app.col_var.get().strip()
    if not r or not c or r == c:
        messagebox.showwarning("Atención", "Selecciona variables válidas y distintas.")
        return

    freq, por_fila = tc.crosstab(app.state.df_proc, r, c)
    v = tc.cramers_v(freq)
    path = tc.exportar_crosstab(f"crosstab_{r}_vs_{c}", freq, por_fila)

    app.txt_crosstab.delete("1.0", "end")
    app.txt_crosstab.insert(
        "1.0",
        f"Frecuencias:\n{freq}\n\n% Fila:\n{por_fila}\n\nV de Cramer={v:.3f}\nExportado: {path}",
    )
