import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import numpy as np
import pandas as pd

# imports relativos al paquete src
from .. import carga_limpieza as cl
from ..configuracion import DEFAULT_EXCEL


def build(app):
    """
    Construye la pestaña 'Cargar/Procesar datos' dentro de app.nb.
    Usa app.state y app.actualizar_status()
    """
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Cargar/Procesar datos")

    # --- Zona superior: cargar archivo y acciones ---
    app.path_var = tk.StringVar(value=str(DEFAULT_EXCEL))
    top = ttk.Frame(f)
    top.pack(fill="x", pady=5)
    ttk.Label(top, text="Excel:").pack(side="left", padx=5)
    ttk.Entry(top, textvariable=app.path_var, width=60).pack(side="left", padx=5)
    ttk.Button(top, text="Buscar...", command=lambda: _browse(app)).pack(side="left")
    ttk.Button(top, text="Cargar", command=lambda: _load(app)).pack(side="left", padx=5)
    ttk.Button(top, text="Vista previa", command=lambda: _preview(app)).pack(side="left", padx=5)

    # --- Panel de edición (lista de columnas + tabla) ---
    panel = ttk.Frame(f)
    panel.pack(fill="both", expand=True, padx=5, pady=5)

    # Lado izquierdo: lista de columnas
    side = ttk.Frame(panel)
    side.pack(side="left", fill="y", padx=5)
    ttk.Label(side, text="Columnas (selecciona para eliminar):").pack(anchor="w")
    app._cols_list_prev = tk.Listbox(side, selectmode="extended", height=18, exportselection=False)
    app._cols_list_prev.pack(fill="y")
    ttk.Button(side, text="Refrescar columnas", command=lambda: _refresh_cols_list_prev(app)).pack(pady=4)

    # Arriba de la tabla: botones de acciones
    toolbar = ttk.Frame(panel)
    toolbar.pack(side="top", fill="x", padx=5)
    ttk.Button(toolbar, text="Eliminar filas seleccionadas", command=lambda: _del_selected_rows_prev(app)).pack(side="left", padx=3)
    ttk.Button(toolbar, text="Eliminar columnas seleccionadas", command=lambda: _del_selected_cols_prev(app)).pack(side="left", padx=3)
    ttk.Button(toolbar, text="Agregar fila", command=lambda: _add_row_prev(app)).pack(side="left", padx=3)
    ttk.Button(toolbar, text="Agregar columna", command=lambda: _add_col_prev(app)).pack(side="left", padx=3)
    ttk.Button(toolbar, text="Refrescar", command=lambda: _reload_table_prev(app)).pack(side="left", padx=3)

    # Centro: tabla con scroll
    table_frame = ttk.Frame(panel)
    table_frame.pack(side="left", fill="both", expand=True)
    app._tree_prev = ttk.Treeview(table_frame, show="headings", selectmode="extended")
    xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=app._tree_prev.xview)
    yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=app._tree_prev.yview)
    app._tree_prev.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

    app._tree_prev.pack(side="left", fill="both", expand=True)
    yscroll.pack(side="left", fill="y")
    xscroll.pack(side="bottom", fill="x")

    # Estilo zebra
    app._tree_prev.tag_configure("oddrow", background="#f7f7f7")
    app._tree_prev.tag_configure("evenrow", background="#ffffff")

    # Doble clic para editar celda
    app._cell_editor_prev = None
    app._tree_prev.bind("<Double-1>", lambda e: _on_cell_double_click_prev(app, e))
    app._tree_prev.bind("<Button-1>", lambda e: _maybe_end_edit_prev(app))

    # Inicializa listas
    _refresh_cols_list_prev(app)


# ---------- acciones superiores ----------
def _browse(app):
    p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
    if p:
        app.path_var.set(p)


def _load(app):
    try:
        df = cl.cargar_excel(app.path_var.get())
        app.state.df = df
        app.state.df_proc = df.copy()
        messagebox.showinfo("OK", f"Cargado: {len(df)} filas, {df.shape[1]} columnas")
        app.actualizar_status()
        _refresh_cols_list_prev(app)
        _reload_table_prev(app)
    except Exception as e:
        messagebox.showerror("Error", str(e))


def _preview(app):
    if app.state.df is None:
        messagebox.showwarning("Atención", "Carga un archivo primero.")
        return
    try:
        _refresh_cols_list_prev(app)
        _reload_table_prev(app)
        df = app.state.df
        info = f"Filas: {len(df)} | Columnas: {df.shape[1]}\nPrimeras columnas: {list(df.columns[:6])}"
        messagebox.showinfo("Vista previa", info)
    except Exception as e:
        messagebox.showerror("Error", str(e))


# ---------- helpers lista/tabla ----------
def _refresh_cols_list_prev(app):
    app._cols_list_prev.delete(0, "end")
    if app.state.df_proc is None:
        return
    for c in list(app.state.df_proc.columns):
        app._cols_list_prev.insert("end", c)


def _reload_table_prev(app):
    _maybe_end_edit_prev(app)

    tree = app._tree_prev
    for col in tree["columns"]:
        tree.heading(col, text="")
    tree.delete(*tree.get_children())

    if app.state.df_proc is None or app.state.df_proc.empty:
        tree["columns"] = []
        app.actualizar_status()
        return

    cols = list(app.state.df_proc.columns)
    tree["columns"] = cols
    for c in cols:
        tree.heading(c, text=c, anchor="w")
        base = 100
        extra = min(200, 8 * len(str(c)))
        tree.column(c, width=base + extra // 2, minwidth=80, stretch=True, anchor="w")

    df_show = app.state.df_proc.fillna("").astype(str)
    for i, (_, row) in enumerate(df_show.iterrows()):
        tags = ("oddrow",) if i % 2 else ("evenrow",)
        tree.insert("", "end", values=list(row.values), tags=tags)

    app.actualizar_status()


# ---------- edición in-place ----------
def _on_cell_double_click_prev(app, event):
    if app.state.df_proc is None or app.state.df_proc.empty:
        return
    region = app._tree_prev.identify("region", event.x, event.y)
    if region != "cell":
        return

    row_id = app._tree_prev.identify_row(event.y)
    col_id = app._tree_prev.identify_column(event.x)
    if not row_id or not col_id:
        return

    try:
        col_index = int(col_id.replace("#", "")) - 1
    except Exception:
        return

    cols = list(app._tree_prev["columns"])
    if col_index < 0 or col_index >= len(cols):
        return
    col_name = cols[col_index]

    bbox = app._tree_prev.bbox(row_id, col_id)
    if not bbox:
        return
    x, y, w, h = bbox
    cur_vals = app._tree_prev.item(row_id, "values")
    cur_val = cur_vals[col_index] if col_index < len(cur_vals) else ""

    _maybe_end_edit_prev(app)
    app._cell_editor_prev = tk.Entry(app._tree_prev, borderwidth=1, font=("Segoe UI", 10))
    app._cell_editor_prev.insert(0, cur_val)
    app._cell_editor_prev.place(x=x + 1, y=y + 1, width=w - 2, height=h - 2)
    app._cell_editor_prev.focus()
    app._cell_editor_prev.select_range(0, "end")

    def _commit(_=None):
        new_val = app._cell_editor_prev.get()
        try:
            app._cell_editor_prev.destroy()
        except Exception:
            pass
        app._cell_editor_prev = None
        _apply_cell_change_prev(app, row_id, col_index, col_name, new_val)

    def _cancel(_=None):
        try:
            app._cell_editor_prev.destroy()
        except Exception:
            pass
        app._cell_editor_prev = None

    app._cell_editor_prev.bind("<Return>", _commit)
    app._cell_editor_prev.bind("<Escape>", _cancel)
    app._cell_editor_prev.bind("<FocusOut>", _commit)


def _maybe_end_edit_prev(app, event=None):
    if getattr(app, "_cell_editor_prev", None) is not None:
        try:
            app._cell_editor_prev.destroy()
        except Exception:
            pass
        app._cell_editor_prev = None


def _apply_cell_change_prev(app, row_id, col_index, col_name, new_val):
    all_items = list(app._tree_prev.get_children())
    row_pos = all_items.index(row_id) if row_id in all_items else None
    if row_pos is None:
        return

    try:
        if pd.api.types.is_numeric_dtype(app.state.df_proc[col_name]):
            cast_val = pd.to_numeric(new_val, errors="coerce")
        else:
            cast_val = new_val
        app.state.df_proc.at[app.state.df_proc.index[row_pos], col_name] = cast_val
    except Exception:
        app.state.df_proc.at[app.state.df_proc.index[row_pos], col_name] = new_val

    new_row_vals = list(app.state.df_proc.fillna("").astype(str).iloc[row_pos].values)
    app._tree_prev.item(row_id, values=new_row_vals)
    app.actualizar_status()


# ---------- operaciones filas/columnas ----------
def _del_selected_rows_prev(app):
    if app.state.df_proc is None or app.state.df_proc.empty:
        messagebox.showwarning("Atención", "No hay datos.")
        return
    selected = app._tree_prev.selection()
    if not selected:
        messagebox.showwarning("Atención", "Selecciona filas en la tabla (clic o Shift/Ctrl).")
        return
    all_items = list(app._tree_prev.get_children())
    id_to_pos = {iid: i for i, iid in enumerate(all_items)}
    pos_to_drop = sorted([id_to_pos[iid] for iid in selected], reverse=True)

    app.state.df_proc = app.state.df_proc.drop(app.state.df_proc.index[pos_to_drop]).reset_index(drop=True)
    _reload_table_prev(app)
    _refresh_cols_list_prev(app)
    app.actualizar_status()
    messagebox.showinfo("OK", f"Se eliminaron {len(pos_to_drop)} filas.")


def _del_selected_cols_prev(app):
    if app.state.df_proc is None or app.state.df_proc.empty:
        messagebox.showwarning("Atención", "No hay datos.")
        return
    sel_cols = [app._cols_list_prev.get(i) for i in app._cols_list_prev.curselection()]
    if not sel_cols:
        messagebox.showwarning("Atención", "Selecciona columnas en la lista de la izquierda.")
        return
    keep = [c for c in app.state.df_proc.columns if c not in sel_cols]
    app.state.df_proc = app.state.df_proc[keep].copy()
    _reload_table_prev(app)
    _refresh_cols_list_prev(app)
    app.actualizar_status()
    messagebox.showinfo("OK", f"Se eliminaron {len(sel_cols)} columna(s).")


def _add_row_prev(app):
    if app.state.df_proc is None:
        messagebox.showwarning("Atención", "Carga un archivo primero.")
        return
    empty_row = {c: np.nan for c in app.state.df_proc.columns}
    app.state.df_proc = pd.concat([app.state.df_proc, pd.DataFrame([empty_row])], ignore_index=True)
    _reload_table_prev(app)
    app.actualizar_status()
    messagebox.showinfo("OK", "Se agregó una fila vacía.")


def _add_col_prev(app):
    if app.state.df_proc is None:
        messagebox.showwarning("Atención", "Carga un archivo primero.")
        return
    name = simpledialog.askstring("Agregar columna", "Nombre de la nueva columna:")
    if not name:
        return
    if name in app.state.df_proc.columns:
        messagebox.showwarning("Atención", f"La columna '{name}' ya existe.")
        return
    app.state.df_proc[name] = np.nan
    _reload_table_prev(app)
    _refresh_cols_list_prev(app)
    app.actualizar_status()
    messagebox.showinfo("OK", f"Se agregó la columna '{name}'.")

