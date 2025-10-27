# interfaz.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import numpy as np

# IMPORTS RELATIVOS (dentro del paquete src)
from .configuracion import AppState, DEFAULT_EXCEL
from . import carga_limpieza as cl
from . import definicion_variables as dv
from . import tablas_cruzadas as tc
from . import distribuciones as dist
from .modelos.regresion_multinomial import entrenar_multinomial
from .simulacion.escenarios import base_probs, efecto_shock_default
from .simulacion.simulador import simular
from .visualizacion import guardar_histograma, guardar_radar, guardar_lineas
from .analisis_encuesta import (
    descriptivos_basicos,
    crosstab_por,
    entrenar_logistica_binaria,
    normalizar_columnas,
)


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.state = AppState()
        self.pack(fill="both", expand=True)
        self._setup_style()
        self._cell_editor_prev = None  # editor flotante para pestaña Cargar/Procesar
        self._build_ui()

    # ---------------- Estilo ----------------
    def _setup_style(self):
        style = ttk.Style()
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    # ---------------- UI ----------------
    def _build_ui(self):
        # Notebook principal (pestañas)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self._tab_cargar()
        self._tab_definir()
        self._tab_crosstabs()
        self._tab_distribuciones()
        self._tab_poisson()
        self._tab_multinomial()
        self._tab_iteracion()
        self._tab_transiente()
        self._tab_simulacion()

        # Barra de estado inferior
        self.statusbar = ttk.Label(self, text=self._status_text(), anchor="w")
        self.statusbar.pack(side="bottom", fill="x")

    def _status_text(self):
        d = "Cargados" if self.state.df_proc is not None else "No cargados"
        m = "Entrenado" if self.state.model is not None else "No entrenado"
        return (
            f"Datos: {d}  |  "
            f"Modelo logística multinomial: {m}  |  "
            f"Target: {self.state.target or '(no definido)'}  |  "
            f"T={self.state.T}, R={self.state.R}, warmup={self.state.warmup}"
        )

    def _select_tab(self, name):
        for i in range(self.nb.index("end")):
            if self.nb.tab(i, "text") == name:
                self.nb.select(i)
                return

    # ========= Pestaña: Cargar/Procesar (EDITADA) =========
    def _tab_cargar(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Cargar/Procesar datos")

        # --- Zona superior: cargar archivo y acciones ---
        self.path_var = tk.StringVar(value=str(DEFAULT_EXCEL))
        top = ttk.Frame(f)
        top.pack(fill="x", pady=5)
        ttk.Label(top, text="Excel:").pack(side="left", padx=5)
        ttk.Entry(top, textvariable=self.path_var, width=60).pack(side="left", padx=5)
        ttk.Button(top, text="Buscar...", command=self._browse).pack(side="left")
        ttk.Button(top, text="Cargar", command=self._load).pack(side="left", padx=5)
        ttk.Button(top, text="Vista previa", command=self._preview).pack(side="left", padx=5)

        # --- Panel de edición (lista de columnas + tabla) ---
        panel = ttk.Frame(f)
        panel.pack(fill="both", expand=True, padx=5, pady=5)

        # Lado izquierdo: lista de columnas
        side = ttk.Frame(panel)
        side.pack(side="left", fill="y", padx=5)
        ttk.Label(side, text="Columnas (selecciona para eliminar):").pack(anchor="w")
        self._cols_list_prev = tk.Listbox(side, selectmode="extended", height=18, exportselection=False)
        self._cols_list_prev.pack(fill="y")
        ttk.Button(side, text="Refrescar columnas", command=self._refresh_cols_list_prev).pack(pady=4)

        # Arriba de la tabla: botones de acciones
        toolbar = ttk.Frame(panel)
        toolbar.pack(side="top", fill="x", padx=5)
        ttk.Button(toolbar, text="Eliminar filas seleccionadas", command=self._del_selected_rows_prev).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Eliminar columnas seleccionadas", command=self._del_selected_cols_prev).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Agregar fila", command=self._add_row_prev).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Agregar columna", command=self._add_col_prev).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Refrescar", command=self._reload_table_prev).pack(side="left", padx=3)

        # Centro: tabla con scroll
        table_frame = ttk.Frame(panel)
        table_frame.pack(side="left", fill="both", expand=True)
        self._tree_prev = ttk.Treeview(table_frame, show="headings", selectmode="extended")
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree_prev.xview)
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree_prev.yview)
        self._tree_prev.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        self._tree_prev.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="left", fill="y")
        xscroll.pack(side="bottom", fill="x")

        # Estilo zebra
        self._tree_prev.tag_configure("oddrow", background="#f7f7f7")
        self._tree_prev.tag_configure("evenrow", background="#ffffff")

        # Doble clic para editar celda
        self._tree_prev.bind("<Double-1>", self._on_cell_double_click_prev)
        self._tree_prev.bind("<Button-1>", self._maybe_end_edit_prev)

        # (Eliminados los cuadros de texto inferiores)

        # Inicializa listas
        self._refresh_cols_list_prev()

    # --- Archivo (Cargar/Procesar) ---
    def _browse(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if p:
            self.path_var.set(p)

    def _load(self):
        try:
            df = cl.cargar_excel(self.path_var.get())
            self.state.df = df
            self.state.df_proc = df.copy()
            messagebox.showinfo("OK", f"Cargado: {len(df)} filas, {df.shape[1]} columnas")
            self.statusbar.config(text=self._status_text())
            self._refresh_cols_list_prev()
            self._reload_table_prev()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _preview(self):
        if self.state.df is None:
            messagebox.showwarning("Atención", "Carga un archivo primero.")
            return
        try:
            self._refresh_cols_list_prev()
            self._reload_table_prev()
            df = self.state.df
            info = f"Filas: {len(df)} | Columnas: {df.shape[1]}\nPrimeras columnas: {list(df.columns[:6])}"
            messagebox.showinfo("Vista previa", info)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- Helpers edición en "Cargar/Procesar" ---
    def _refresh_cols_list_prev(self):
        self._cols_list_prev.delete(0, "end")
        if self.state.df_proc is None:
            return
        for c in list(self.state.df_proc.columns):
            self._cols_list_prev.insert("end", c)

    def _reload_table_prev(self):
        # cierra editor si estuviera abierto
        self._maybe_end_edit_prev()

        tree = self._tree_prev
        for col in tree["columns"]:
            tree.heading(col, text="")
        tree.delete(*tree.get_children())

        if self.state.df_proc is None or self.state.df_proc.empty:
            tree["columns"] = []
            self.statusbar.config(text=self._status_text())
            return

        cols = list(self.state.df_proc.columns)
        tree["columns"] = cols
        for c in cols:
            tree.heading(c, text=c, anchor="w")
            base = 100
            extra = min(200, 8 * len(str(c)))
            tree.column(c, width=base + extra // 2, minwidth=80, stretch=True, anchor="w")

        df_show = self.state.df_proc.fillna("").astype(str)
        for i, (_, row) in enumerate(df_show.iterrows()):
            tags = ("oddrow",) if i % 2 else ("evenrow",)
            tree.insert("", "end", values=list(row.values), tags=tags)

        self.statusbar.config(text=self._status_text())

    # --- Edición en celda (in-place) ---
    def _on_cell_double_click_prev(self, event):
        if self.state.df_proc is None or self.state.df_proc.empty:
            return
        region = self._tree_prev.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self._tree_prev.identify_row(event.y)
        col_id = self._tree_prev.identify_column(event.x)  # "#n"
        if not row_id or not col_id:
            return

        try:
            col_index = int(col_id.replace("#", "")) - 1
        except Exception:
            return

        cols = list(self._tree_prev["columns"])
        if col_index < 0 or col_index >= len(cols):
            return
        col_name = cols[col_index]

        # bbox y valor actual
        bbox = self._tree_prev.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, w, h = bbox
        cur_vals = self._tree_prev.item(row_id, "values")
        cur_val = cur_vals[col_index] if col_index < len(cur_vals) else ""

        # Cierra editor anterior
        self._maybe_end_edit_prev()

        # Crea Entry flotante
        self._cell_editor_prev = tk.Entry(self._tree_prev, borderwidth=1, font=("Segoe UI", 10))
        self._cell_editor_prev.insert(0, cur_val)
        self._cell_editor_prev.place(x=x + 1, y=y + 1, width=w - 2, height=h - 2)
        self._cell_editor_prev.focus()
        self._cell_editor_prev.select_range(0, "end")

        def _commit(_=None):
            new_val = self._cell_editor_prev.get()
            try:
                self._cell_editor_prev.destroy()
            except Exception:
                pass
            self._cell_editor_prev = None
            self._apply_cell_change_prev(row_id, col_index, col_name, new_val)

        def _cancel(_=None):
            try:
                self._cell_editor_prev.destroy()
            except Exception:
                pass
            self._cell_editor_prev = None

        self._cell_editor_prev.bind("<Return>", _commit)
        self._cell_editor_prev.bind("<Escape>", _cancel)
        self._cell_editor_prev.bind("<FocusOut>", _commit)

    def _maybe_end_edit_prev(self, event=None):
        if self._cell_editor_prev is not None:
            try:
                self._cell_editor_prev.destroy()
            except Exception:
                pass
            self._cell_editor_prev = None

    def _apply_cell_change_prev(self, row_id, col_index, col_name, new_val):
        all_items = list(self._tree_prev.get_children())
        row_pos = all_items.index(row_id) if row_id in all_items else None
        if row_pos is None:
            return

        try:
            if pd.api.types.is_numeric_dtype(self.state.df_proc[col_name]):
                cast_val = pd.to_numeric(new_val, errors="coerce")
            else:
                cast_val = new_val
            self.state.df_proc.at[self.state.df_proc.index[row_pos], col_name] = cast_val
        except Exception:
            self.state.df_proc.at[self.state.df_proc.index[row_pos], col_name] = new_val

        new_row_vals = list(self.state.df_proc.fillna("").astype(str).iloc[row_pos].values)
        self._tree_prev.item(row_id, values=new_row_vals)
        self.statusbar.config(text=self._status_text())

    # --- Operaciones filas/columnas ---
    def _del_selected_rows_prev(self):
        if self.state.df_proc is None or self.state.df_proc.empty:
            messagebox.showwarning("Atención", "No hay datos.")
            return
        selected = self._tree_prev.selection()
        if not selected:
            messagebox.showwarning("Atención", "Selecciona filas en la tabla (clic o Shift/Ctrl).")
            return
        all_items = list(self._tree_prev.get_children())
        id_to_pos = {iid: i for i, iid in enumerate(all_items)}
        pos_to_drop = sorted([id_to_pos[iid] for iid in selected], reverse=True)

        self.state.df_proc = self.state.df_proc.drop(self.state.df_proc.index[pos_to_drop]).reset_index(drop=True)
        self._reload_table_prev()
        self._refresh_cols_list_prev()
        self.statusbar.config(text=self._status_text())
        messagebox.showinfo("OK", f"Se eliminaron {len(pos_to_drop)} filas.")

    def _del_selected_cols_prev(self):
        if self.state.df_proc is None or self.state.df_proc.empty:
            messagebox.showwarning("Atención", "No hay datos.")
            return
        sel_cols = [self._cols_list_prev.get(i) for i in self._cols_list_prev.curselection()]
        if not sel_cols:
            messagebox.showwarning("Atención", "Selecciona columnas en la lista de la izquierda.")
            return
        keep = [c for c in self.state.df_proc.columns if c not in sel_cols]
        self.state.df_proc = self.state.df_proc[keep].copy()
        self._reload_table_prev()
        self._refresh_cols_list_prev()
        self.statusbar.config(text=self._status_text())
        messagebox.showinfo("OK", f"Se eliminaron {len(sel_cols)} columna(s).")

    def _add_row_prev(self):
        if self.state.df_proc is None:
            messagebox.showwarning("Atención", "Carga un archivo primero.")
            return
        empty_row = {c: np.nan for c in self.state.df_proc.columns}
        self.state.df_proc = pd.concat([self.state.df_proc, pd.DataFrame([empty_row])], ignore_index=True)
        self._reload_table_prev()
        self.statusbar.config(text=self._status_text())
        messagebox.showinfo("OK", "Se agregó una fila vacía.")

    def _add_col_prev(self):
        if self.state.df_proc is None:
            messagebox.showwarning("Atención", "Carga un archivo primero.")
            return
        name = simpledialog.askstring("Agregar columna", "Nombre de la nueva columna:")
        if not name:
            return
        if name in self.state.df_proc.columns:
            messagebox.showwarning("Atención", f"La columna '{name}' ya existe.")
            return
        self.state.df_proc[name] = np.nan
        self._reload_table_prev()
        self._refresh_cols_list_prev()
        self.statusbar.config(text=self._status_text())
        messagebox.showinfo("OK", f"Se agregó la columna '{name}'.")

    def _tab_analisis_auto(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Análisis")
        # --- Descriptivos ---
        box1 = ttk.LabelFrame(f, text="Descriptivos globales"); box1.pack(fill="x", padx=6, pady=6)
        ttk.Button(box1, text="Calcular porcentajes (Paz/JQR/Blanco/Nulo)", command=self._run_desc).pack(side="left", padx=6, pady=6)

        # --- Crosstab ---
        box2 = ttk.LabelFrame(f, text="Crosstab"); box2.pack(fill="x", padx=6, pady=6)
        self.ct_row = tk.StringVar(); self.ct_col = tk.StringVar()
        ttk.Label(box2, text="Fila:").pack(side="left", padx=4); self.cb_ct_row = ttk.Combobox(box2, textvariable=self.ct_row, width=28); self.cb_ct_row.pack(side="left", padx=4)
        ttk.Label(box2, text="Columna:").pack(side="left", padx=4); self.cb_ct_col = ttk.Combobox(box2, textvariable=self.ct_col, width=28); self.cb_ct_col.pack(side="left", padx=4)
        ttk.Button(box2, text="Generar", command=self._run_ct).pack(side="left", padx=6)

        # --- Logística binaria ---
        box3 = ttk.LabelFrame(f, text="Regresión logística (Paz=1 vs JQR=0)"); box3.pack(fill="x", padx=6, pady=6)
        ttk.Button(box3, text="Entrenar (auto-selección de predictores)", command=self._run_logit).pack(side="left", padx=6, pady=6)

        # Rellenar combos al mostrar pestaña
        def refresh(*_):
            if self.state.df_proc is not None:
                cols = list(normalizar_columnas(self.state.df_proc).columns)
                self.cb_ct_row["values"] = cols
                self.cb_ct_col["values"] = cols
        f.bind("<Visibility>", refresh)

    # ========= Pestaña: Definir variables =========
    def _tab_definir(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Definir variables")
        top = ttk.Frame(f)
        top.pack(fill="x", pady=5)
        self.target_var = tk.StringVar(value="")
        ttk.Label(top, text="Objetivo (Intención de voto):").pack(side="left", padx=5)
        self.cb_target = ttk.Combobox(top, textvariable=self.target_var, width=40, values=[])
        self.cb_target.pack(side="left", padx=5)
        ttk.Button(top, text="Guardar objetivo", command=self._save_target).pack(side="left", padx=5)

        mid = ttk.Frame(f)
        mid.pack(fill="both", expand=True)
        left = ttk.Frame(mid)
        left.pack(side="left", fill="y", padx=5)
        self.list_cols = tk.Listbox(left, selectmode="extended", height=20)
        self.list_cols.pack(fill="y")
        ttk.Button(left, text="Refrescar columnas", command=self._refresh_cols).pack(pady=5)

        right = ttk.Frame(mid)
        right.pack(side="left", fill="y", padx=10)
        ttk.Button(right, text="Marcar Demográfica", command=lambda: self._set_role("Demográfica")).pack(fill="x", pady=2)
        ttk.Button(right, text="Marcar Factor (Likert)", command=lambda: self._set_role("Likert")).pack(fill="x", pady=2)
        ttk.Button(right, text="Marcar Atributo Candidato", command=lambda: self._set_role("Atributo")).pack(fill="x", pady=2)

        self._refresh_cols()

    def _refresh_cols(self):
        self.list_cols.delete(0, "end")
        cols = dv.columnas(self.state)
        self.cb_target["values"] = cols
        for c in cols:
            self.list_cols.insert("end", c)

    def _save_target(self):
        col = self.target_var.get().strip()
        try:
            dv.set_target(self.state, col)
            messagebox.showinfo("OK", f"Objetivo: {col}")
            self.statusbar.config(text=self._status_text())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _set_role(self, role):
        sel = [self.list_cols.get(i) for i in self.list_cols.curselection()]
        if not sel:
            messagebox.showwarning("Atención", "Selecciona columnas.")
            return
        dv.set_role(self.state, sel, role)
        messagebox.showinfo("OK", f"Asignadas {len(sel)} columnas como {role}")

    # ========= Pestaña: Tablas cruzadas =========
    def _tab_crosstabs(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Tablas cruzadas")
        top = ttk.Frame(f)
        top.pack(fill="x", pady=5)
        self.row_var = tk.StringVar()
        self.col_var = tk.StringVar()
        self.cb_row = ttk.Combobox(top, textvariable=self.row_var, width=30)
        self.cb_col = ttk.Combobox(top, textvariable=self.col_var, width=30)
        ttk.Label(top, text="Fila:").pack(side="left", padx=5)
        self.cb_row.pack(side="left")
        ttk.Label(top, text="Columna:").pack(side="left", padx=5)
        self.cb_col.pack(side="left")
        ttk.Button(top, text="Calcular", command=self._calc_crosstab).pack(side="left", padx=5)
        self.txt_crosstab = tk.Text(f, height=22)
        self.txt_crosstab.pack(fill="both", expand=True, padx=5, pady=5)

        def refresh_cb(*_):
            cols = dv.columnas(self.state)
            self.cb_row["values"] = cols
            self.cb_col["values"] = cols

        f.bind("<Visibility>", refresh_cb)

    def _calc_crosstab(self):
        if self.state.df_proc is None:
            messagebox.showwarning("Atención", "Carga datos primero.")
            return
        r, c = self.row_var.get().strip(), self.col_var.get().strip()
        if not r or not c or r == c:
            messagebox.showwarning("Atención", "Selecciona variables válidas y distintas.")
            return
        freq, por_fila = tc.crosstab(self.state.df_proc, r, c)
        v = tc.cramers_v(freq)
        path = tc.exportar_crosstab(f"crosstab_{r}_vs_{c}", freq, por_fila)
        self.txt_crosstab.delete("1.0", "end")
        self.txt_crosstab.insert(
            "1.0",
            f"Frecuencias:\n{freq}\n\n% Fila:\n{por_fila}\n\nV de Cramer={v:.3f}\nExportado: {path}",
        )

    # ========= Pestaña: Distribuciones =========
    def _tab_distribuciones(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Distribuciones")
        top = ttk.Frame(f)
        top.pack(fill="x", pady=5)
        self.var_num = tk.StringVar()
        self.var_dist = tk.StringVar(value="normal")
        self.cb_num = ttk.Combobox(top, textvariable=self.var_num, width=30)
        self.cb_num.pack(side="left", padx=5)
        self.cb_dist = ttk.Combobox(
            top, textvariable=self.var_dist, width=15, values=["normal", "lognormal", "exponencial", "gamma"]
        )
        self.cb_dist.pack(side="left", padx=5)
        ttk.Button(top, text="Ajustar", command=self._ajustar_dist).pack(side="left", padx=5)
        self.txt_dist = tk.Text(f, height=12)
        self.txt_dist.pack(fill="x", padx=5, pady=5)

        self.img_dist_label = ttk.Label(f)
        self.img_dist_label.pack(pady=5)
        self._img_dist_ref = None

        def refresh_cb(*_):
            self.cb_num["values"] = dv.numericas(self.state)

        f.bind("<Visibility>", refresh_cb)

    def _ajustar_dist(self):
        if self.state.df_proc is None:
            messagebox.showwarning("Atención", "Carga datos primero.")
            return
        col = self.var_num.get().strip()
        if not col:
            messagebox.showwarning("Atención", "Selecciona variable numérica.")
            return
        x = self.state.df_proc[col].astype(float).to_numpy()
        dist_name = self.var_dist.get()
        fitters = {
            "normal": dist.fit_normal,
            "lognormal": dist.fit_lognormal,
            "exponencial": dist.fit_exponencial,
            "gamma": dist.fit_gamma,
        }
        fit = fitters.get(dist_name, dist.fit_normal)(x)
        self.state.dist_fits[col] = fit
        path = guardar_histograma(x[~np.isnan(x)], f"Ajuste {fit['dist']} - {col}", f"hist_{col}_{fit['dist']}")
        self.txt_dist.delete("1.0", "end")
        self.txt_dist.insert("1.0", f"Distribución: {fit['dist']}\nParámetros: {fit['params']}\nGráfico: {path}")

        try:
            img = tk.PhotoImage(file=str(path))
            self.img_dist_label.configure(image=img, text="")
            self._img_dist_ref = img
        except Exception as e:
            self.img_dist_label.configure(image="", text=f"No se pudo cargar la imagen.\n{path}\n{e}")

    # ========= Pestaña: Poisson =========
    def _tab_poisson(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Distribución de Poisson")
        top = ttk.Frame(f)
        top.pack(fill="x", pady=5)
        self.var_count = tk.StringVar()
        self.lambda_val = tk.DoubleVar(value=0.5)
        self.cb_count = ttk.Combobox(top, textvariable=self.var_count, width=30)
        self.cb_count.pack(side="left", padx=5)
        ttk.Button(top, text="Estimar λ", command=self._estimar_lambda).pack(side="left", padx=5)
        ttk.Label(top, text="λ:").pack(side="left")
        ttk.Entry(top, textvariable=self.lambda_val, width=10).pack(side="left", padx=5)
        self.txt_poisson = tk.Text(f, height=8)
        self.txt_poisson.pack(fill="x", padx=5, pady=5)

        def refresh_cb(*_):
            self.cb_count["values"] = dv.numericas(self.state)

        f.bind("<Visibility>", refresh_cb)

    def _estimar_lambda(self):
        if self.state.df_proc is None:
            messagebox.showwarning("Atención", "Carga datos primero.")
            return
        col = self.var_count.get().strip()
        if not col:
            messagebox.showwarning("Atención", "Selecciona variable de conteo.")
            return
        lam = dist.poisson_lambda(self.state.df_proc[col].to_numpy(dtype=float))
        self.lambda_val.set(lam)
        self.state.poisson_lambda = lam
        self.txt_poisson.delete("1.0", "end")
        self.txt_poisson.insert("1.0", f"λ estimado para {col}: {lam:.4f}")

    # ========= Pestaña: Logística multinomial =========
    def _tab_multinomial(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Regresión logística multinomial")
        top = ttk.Frame(f)
        top.pack(fill="x", pady=5)
        ttk.Label(top, text="Objetivo:").pack(side="left", padx=5)
        self.lbl_target = ttk.Label(top, text="(definir en 'Definir variables')", foreground="blue")
        self.lbl_target.pack(side="left")
        ttk.Button(top, text="Entrenar", command=self._entrenar_modelo).pack(side="left", padx=5)

        mid = ttk.Frame(f)
        mid.pack(fill="both", expand=True)
        left = ttk.Frame(mid)
        left.pack(side="left", fill="y", padx=5)
        ttk.Label(left, text="Predictores:").pack(anchor="w")
        self.lb_feats = tk.Listbox(left, selectmode="extended", height=20)
        self.lb_feats.pack(fill="y")

        def refresh_cb(*_):
            self.lbl_target.config(text=self.state.target or "(definir)")
            self.lb_feats.delete(0, "end")
            if self.state.df_proc is not None:
                for c in self.state.df_proc.columns:
                    if c != self.state.target:
                        self.lb_feats.insert("end", c)

        f.bind("<Visibility>", refresh_cb)

        right = ttk.Frame(mid)
        right.pack(side="left", fill="both", expand=True, padx=5)
        self.txt_model = tk.Text(right)
        self.txt_model.pack(fill="both", expand=True)

    def _entrenar_modelo(self):
        if self.state.df_proc is None or not self.state.target:
            messagebox.showwarning("Atención", "Debes cargar datos y definir objetivo.")
            return
        feats = [self.lb_feats.get(i) for i in self.lb_feats.curselection()]
        if not feats:
            messagebox.showwarning("Atención", "Selecciona al menos un predictor.")
            return
        res = entrenar_multinomial(self.state.df_proc, self.state.target, feats)
        self.state.model = res["pipeline"]
        self.state.model_report = res
        self.state.model_features = res["features"]
        self.state.model_classes = res["classes"]
        self.statusbar.config(text=self._status_text())
        self.txt_model.delete("1.0", "end")
        self.txt_model.insert("1.0", f"Accuracy: {res['accuracy']:.4f}\nClases: {res['classes']}\n\nReporte:\n{res['report']}")

    # ========= Pestaña: Variable de iteración =========
    def _tab_iteracion(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Variable de iteración")
        frm = ttk.Frame(f)
        frm.pack(pady=10)
        self.T_var = tk.IntVar(value=self.state.T)
        self.R_var = tk.IntVar(value=self.state.R)
        self.seed_var = tk.IntVar(value=self.state.seed)
        ttk.Label(frm, text="T (pasos):").grid(row=0, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.T_var, width=8).grid(row=0, column=1, padx=5)
        ttk.Label(frm, text="R (replicaciones):").grid(row=1, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.R_var, width=8).grid(row=1, column=1, padx=5)
        ttk.Label(frm, text="Semilla:").grid(row=2, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.seed_var, width=8).grid(row=2, column=1, padx=5)
        ttk.Button(frm, text="Guardar", command=self._save_iter).grid(row=3, column=0, columnspan=2, pady=10)

    def _save_iter(self):
        self.state.T = max(1, int(self.T_var.get()))
        self.state.R = max(1, int(self.R_var.get()))
        self.state.seed = int(self.seed_var.get())
        self.statusbar.config(text=self._status_text())
        messagebox.showinfo("OK", f"T={self.state.T}, R={self.state.R}, seed={self.state.seed}")

    # ========= Pestaña: Estado transiente =========
    def _tab_transiente(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Estado transiente")
        frm = ttk.Frame(f)
        frm.pack(pady=10)
        self.warm_var = tk.IntVar(value=self.state.warmup)
        ttk.Label(frm, text="Warm-up (iteraciones a descartar):").grid(row=0, column=0, sticky="e")
        ttk.Scale(frm, variable=self.warm_var, from_=0, to=100, orient="horizontal").grid(row=0, column=1, padx=10)
        ttk.Button(frm, text="Guardar", command=self._save_warm).grid(row=1, column=0, columnspan=2, pady=10)

    def _save_warm(self):
        self.state.warmup = max(0, int(self.warm_var.get()))
        self.statusbar.config(text=self._status_text())
        messagebox.showinfo("OK", f"Warm-up={self.state.warmup}")

    # ========= Pestaña: Simulación =========
    def _tab_simulacion(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="Simulación")
        top = ttk.Frame(f)
        top.pack(fill="x", pady=5)
        self.lam_var = tk.DoubleVar(value=0.5)
        ttk.Label(top, text="λ Poisson (shocks):").pack(side="left", padx=5)
        ttk.Entry(top, textvariable=self.lam_var, width=10).pack(side="left")
        self.fx_vars = {k: tk.DoubleVar(value=v) for k, v in efecto_shock_default().items()}
        fx_frame = ttk.Frame(top)
        fx_frame.pack(side="left", padx=15)
        for name, var in self.fx_vars.items():
            ttk.Label(fx_frame, text=f"Efecto {name}:").pack(side="left", padx=3)
            ttk.Entry(fx_frame, textvariable=var, width=7).pack(side="left")
        ttk.Button(top, text="Ejecutar", command=self._run_sim).pack(side="left", padx=10)

        self.txt_sim = tk.Text(f, height=10)
        self.txt_sim.pack(fill="x", padx=5, pady=5)

        btn_frame = ttk.Frame(f)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Abrir carpeta de gráficos", command=self._abrir_carpeta_graficos).pack(side="left", padx=5, pady=5)

        self.img_sim_label = ttk.Label(f)
        self.img_sim_label.pack(pady=5)
        self._img_sim_ref = None

    def _run_sim(self):
        base = base_probs()
        fx = {k: float(v.get()) for k, v in self.fx_vars.items()}
        lam = float(self.state.poisson_lambda if self.state.poisson_lambda is not None else self.lam_var.get())
        res = simular(self.state.T, self.state.R, self.state.warmup, base, lam, fx, seed=self.state.seed)

        mean_t = res["trajectories"].mean(axis=0)  # (T, C)
        series = {res["classes"][i]: mean_t[:, i] for i in range(len(res["classes"]))}
        path = guardar_lineas(
            series,
            "sim_evolucion",
            f"Evolución (T={self.state.T}, R={self.state.R}, warmup={res['warmup_used']})",
        )

        self.txt_sim.delete("1.0", "end")
        self.txt_sim.insert("1.0", f"Resumen post-warmup:\n{res['summary']}\nGráfico: {path}")

        try:
            img = tk.PhotoImage(file=str(path))
            self.img_sim_label.configure(image=img, text="")
            self._img_sim_ref = img
        except Exception as e:
            self.img_sim_label.configure(image="", text=f"No se pudo cargar la imagen.\n{path}\n{e}")

    def _abrir_carpeta_graficos(self):
        import os, sys, subprocess
        from .configuracion import RES_GRAFICOS
        folder = str(RES_GRAFICOS)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta.\n{folder}\n{e}")
