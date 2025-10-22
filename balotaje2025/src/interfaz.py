# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np

# IMPORTS ABSOLUTOS (sin punto)
from configuracion import AppState, DEFAULT_EXCEL
import carga_limpieza as cl
import definicion_variables as dv
import tablas_cruzadas as tc
import distribuciones as dist
from modelos.regresion_multinomial import entrenar_multinomial
from simulacion.escenarios import base_probs, efecto_shock_default
from simulacion.simulador import simular
from visualizacion import guardar_histograma, guardar_radar, guardar_lineas

class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.state = AppState()
        self.pack(fill="both", expand=True)
        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self._tab_inicio()
        self._tab_cargar()
        self._tab_definir()
        self._tab_crosstabs()
        self._tab_distribuciones()
        self._tab_poisson()
        self._tab_multinomial()
        self._tab_iteracion()
        self._tab_transiente()
        self._tab_simulacion()

    # ---- Inicio
    def _tab_inicio(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Inicio")
        self.lbl_status = ttk.Label(f, text=self._status_text(), justify="left")
        self.lbl_status.pack(padx=10, pady=10)
        ttk.Button(f, text="Ir a Cargar/Procesar datos",
                   command=lambda: self._select_tab("Cargar/Procesar datos")).pack(pady=5)

    def _status_text(self):
        d = "Cargados" if self.state.df_proc is not None else "No cargados"
        m = "Entrenado" if self.state.model is not None else "No entrenado"
        return (
            f"Datos: {d}\n"
            f"Modelo logística multinomial: {m}\n"
            f"Target: {self.state.target or '(no definido)'}\n"
            f"T={self.state.T}, R={self.state.R}, warmup={self.state.warmup}"
        )


    def _select_tab(self, name):
        for i in range(self.nb.index("end")):
            if self.nb.tab(i, "text") == name:
                self.nb.select(i); return

    # ---- Cargar/Procesar
    def _tab_cargar(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Cargar/Procesar datos")
        self.path_var = tk.StringVar(value=str(DEFAULT_EXCEL))
        top = ttk.Frame(f); top.pack(fill="x", pady=5)
        ttk.Label(top, text="Excel:").pack(side="left", padx=5)
        ttk.Entry(top, textvariable=self.path_var, width=60).pack(side="left", padx=5)
        ttk.Button(top, text="Buscar...", command=self._browse).pack(side="left")
        ttk.Button(top, text="Cargar", command=self._load).pack(side="left", padx=5)
        ttk.Button(top, text="Vista previa", command=self._preview).pack(side="left", padx=5)

        self.txt_prev = tk.Text(f, height=18); self.txt_prev.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_sum = tk.Text(f, height=8); self.txt_sum.pack(fill="x", padx=5, pady=5)

    def _browse(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if p: self.path_var.set(p)

    def _load(self):
        try:
            df = cl.cargar_excel(self.path_var.get())
            self.state.df = df
            self.state.df_proc = df.copy()
            messagebox.showinfo("OK", f"Cargado: {len(df)} filas, {df.shape[1]} columnas")
            self.lbl_status.config(text=self._status_text())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _preview(self):
        if self.state.df is None:
            messagebox.showwarning("Atención", "Carga un archivo primero."); return
        prev = cl.vista_previa(self.state.df)
        summ = cl.resumen(self.state.df)
        self.txt_prev.delete("1.0","end"); self.txt_prev.insert("1.0", str(prev))
        self.txt_sum.delete("1.0","end"); self.txt_sum.insert("1.0", f"{summ}")

    # ---- Definir variables
    def _tab_definir(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Definir variables")
        top = ttk.Frame(f); top.pack(fill="x", pady=5)
        self.target_var = tk.StringVar(value="")
        ttk.Label(top, text="Objetivo (Intención de voto):").pack(side="left", padx=5)
        self.cb_target = ttk.Combobox(top, textvariable=self.target_var, width=40, values=[])
        self.cb_target.pack(side="left", padx=5)
        ttk.Button(top, text="Guardar objetivo", command=self._save_target).pack(side="left", padx=5)

        mid = ttk.Frame(f); mid.pack(fill="both", expand=True)
        left = ttk.Frame(mid); left.pack(side="left", fill="y", padx=5)
        self.list_cols = tk.Listbox(left, selectmode="extended", height=20); self.list_cols.pack(fill="y")
        ttk.Button(left, text="Refrescar columnas", command=self._refresh_cols).pack(pady=5)

        right = ttk.Frame(mid); right.pack(side="left", fill="y", padx=10)
        ttk.Button(right, text="Marcar Demográfica", command=lambda: self._set_role("Demográfica")).pack(fill="x", pady=2)
        ttk.Button(right, text="Marcar Factor (Likert)", command=lambda: self._set_role("Likert")).pack(fill="x", pady=2)
        ttk.Button(right, text="Marcar Atributo Candidato", command=lambda: self._set_role("Atributo")).pack(fill="x", pady=2)

        self._refresh_cols()

    def _refresh_cols(self):
        self.list_cols.delete(0, "end")
        cols = dv.columnas(self.state)
        self.cb_target["values"] = cols
        for c in cols: self.list_cols.insert("end", c)

    def _save_target(self):
        col = self.target_var.get().strip()
        try:
            dv.set_target(self.state, col)
            messagebox.showinfo("OK", f"Objetivo: {col}")
            self.lbl_status.config(text=self._status_text())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _set_role(self, role):
        sel = [self.list_cols.get(i) for i in self.list_cols.curselection()]
        if not sel: 
            messagebox.showwarning("Atención","Selecciona columnas.")
            return
        dv.set_role(self.state, sel, role)
        messagebox.showinfo("OK", f"Asignadas {len(sel)} columnas como {role}")

    # ---- Tablas cruzadas
    def _tab_crosstabs(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Tablas cruzadas")
        top = ttk.Frame(f); top.pack(fill="x", pady=5)
        self.row_var = tk.StringVar(); self.col_var = tk.StringVar()
        self.cb_row = ttk.Combobox(top, textvariable=self.row_var, width=30)
        self.cb_col = ttk.Combobox(top, textvariable=self.col_var, width=30)
        ttk.Label(top, text="Fila:").pack(side="left", padx=5); self.cb_row.pack(side="left")
        ttk.Label(top, text="Columna:").pack(side="left", padx=5); self.cb_col.pack(side="left")
        ttk.Button(top, text="Calcular", command=self._calc_crosstab).pack(side="left", padx=5)
        self.txt_crosstab = tk.Text(f, height=22); self.txt_crosstab.pack(fill="both", expand=True, padx=5, pady=5)

        def refresh_cb(*_): 
            cols = dv.columnas(self.state)
            self.cb_row["values"] = cols; self.cb_col["values"] = cols
        f.bind("<Visibility>", refresh_cb)

    def _calc_crosstab(self):
        if self.state.df_proc is None: 
            messagebox.showwarning("Atención","Carga datos primero."); return
        r, c = self.row_var.get().strip(), self.col_var.get().strip()
        if not r or not c or r==c:
            messagebox.showwarning("Atención","Selecciona variables válidas y distintas."); return
        freq, por_fila = tc.crosstab(self.state.df_proc, r, c)
        v = tc.cramers_v(freq)
        path = tc.exportar_crosstab(f"crosstab_{r}_vs_{c}", freq, por_fila)
        self.txt_crosstab.delete("1.0","end")
        self.txt_crosstab.insert("1.0", f"Frecuencias:\n{freq}\n\n% Fila:\n{por_fila}\n\nV de Cramer={v:.3f}\nExportado: {path}")

    # ---- Distribuciones
    def _tab_distribuciones(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Distribuciones")
        top = ttk.Frame(f); top.pack(fill="x", pady=5)
        self.var_num = tk.StringVar(); self.var_dist = tk.StringVar(value="normal")
        self.cb_num = ttk.Combobox(top, textvariable=self.var_num, width=30)
        self.cb_num.pack(side="left", padx=5)
        self.cb_dist = ttk.Combobox(top, textvariable=self.var_dist, width=15,
                                    values=["normal","lognormal","exponencial","gamma"])
        self.cb_dist.pack(side="left", padx=5)
        ttk.Button(top, text="Ajustar", command=self._ajustar_dist).pack(side="left", padx=5)
        self.txt_dist = tk.Text(f, height=12); self.txt_dist.pack(fill="x", padx=5, pady=5)

        def refresh_cb(*_): self.cb_num["values"] = dv.numericas(self.state)
        f.bind("<Visibility>", refresh_cb)

    def _ajustar_dist(self):
        if self.state.df_proc is None: 
            messagebox.showwarning("Atención","Carga datos primero."); return
        col = self.var_num.get().strip()
        if not col: 
            messagebox.showwarning("Atención","Selecciona variable numérica."); return
        x = self.state.df_proc[col].astype(float).to_numpy()
        dist_name = self.var_dist.get()
        fitters = {
            "normal": dist.fit_normal,
            "lognormal": dist.fit_lognormal,
            "exponencial": dist.fit_exponencial,
            "gamma": dist.fit_gamma
        }
        fit = fitters.get(dist_name, dist.fit_normal)(x)
        self.state.dist_fits[col] = fit
        path = guardar_histograma(x[~np.isnan(x)], f"Ajuste {fit['dist']} - {col}", f"hist_{col}_{fit['dist']}")
        self.txt_dist.delete("1.0","end")
        self.txt_dist.insert("1.0", f"Distribución: {fit['dist']}\nParámetros: {fit['params']}\nGráfico: {path}")

    # ---- Poisson
    def _tab_poisson(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Distribución de Poisson")
        top = ttk.Frame(f); top.pack(fill="x", pady=5)
        self.var_count = tk.StringVar(); self.lambda_val = tk.DoubleVar(value=0.5)
        self.cb_count = ttk.Combobox(top, textvariable=self.var_count, width=30)
        self.cb_count.pack(side="left", padx=5)
        ttk.Button(top, text="Estimar λ", command=self._estimar_lambda).pack(side="left", padx=5)
        ttk.Label(top, text="λ:").pack(side="left"); ttk.Entry(top, textvariable=self.lambda_val, width=10).pack(side="left", padx=5)
        self.txt_poisson = tk.Text(f, height=8); self.txt_poisson.pack(fill="x", padx=5, pady=5)

        def refresh_cb(*_): self.cb_count["values"] = dv.numericas(self.state)
        f.bind("<Visibility>", refresh_cb)

    def _estimar_lambda(self):
        if self.state.df_proc is None:
            messagebox.showwarning("Atención","Carga datos primero."); return
        col = self.var_count.get().strip()
        if not col: 
            messagebox.showwarning("Atención","Selecciona variable de conteo."); return
        lam = dist.poisson_lambda(self.state.df_proc[col].to_numpy(dtype=float))
        self.lambda_val.set(lam); self.state.poisson_lambda = lam
        self.txt_poisson.delete("1.0","end")
        self.txt_poisson.insert("1.0", f"λ estimado para {col}: {lam:.4f}")

    # ---- Logística multinomial
    def _tab_multinomial(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Regresión logística multinomial")
        top = ttk.Frame(f); top.pack(fill="x", pady=5)
        ttk.Label(top, text="Objetivo:").pack(side="left", padx=5)
        self.lbl_target = ttk.Label(top, text="(definir en 'Definir variables')", foreground="blue")
        self.lbl_target.pack(side="left")
        ttk.Button(top, text="Entrenar", command=self._entrenar_modelo).pack(side="left", padx=5)

        mid = ttk.Frame(f); mid.pack(fill="both", expand=True)
        left = ttk.Frame(mid); left.pack(side="left", fill="y", padx=5)
        ttk.Label(left, text="Predictores:").pack(anchor="w")
        self.lb_feats = tk.Listbox(left, selectmode="extended", height=20); self.lb_feats.pack(fill="y")

        def refresh_cb(*_):
            self.lbl_target.config(text=self.state.target or "(definir)")
            self.lb_feats.delete(0,"end")
            if self.state.df_proc is not None:
                for c in self.state.df_proc.columns:
                    if c != self.state.target:
                        self.lb_feats.insert("end", c)
        f.bind("<Visibility>", refresh_cb)

        right = ttk.Frame(mid); right.pack(side="left", fill="both", expand=True, padx=5)
        self.txt_model = tk.Text(right); self.txt_model.pack(fill="both", expand=True)

    def _entrenar_modelo(self):
        if self.state.df_proc is None or not self.state.target:
            messagebox.showwarning("Atención","Debes cargar datos y definir objetivo."); return
        feats = [self.lb_feats.get(i) for i in self.lb_feats.curselection()]
        if not feats: 
            messagebox.showwarning("Atención","Selecciona al menos un predictor."); return
        res = entrenar_multinomial(self.state.df_proc, self.state.target, feats)
        self.state.model = res["pipeline"]
        self.state.model_report = res
        self.state.model_features = res["features"]
        self.state.model_classes = res["classes"]
        self.lbl_status.config(text=self._status_text())
        self.txt_model.delete("1.0","end")
        self.txt_model.insert("1.0", f"Accuracy: {res['accuracy']:.4f}\nClases: {res['classes']}\n\nReporte:\n{res['report']}")

    # ---- Variable de iteración
    def _tab_iteracion(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Variable de iteración")
        frm = ttk.Frame(f); frm.pack(pady=10)
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
        self.lbl_status.config(text=self._status_text())
        messagebox.showinfo("OK", f"T={self.state.T}, R={self.state.R}, seed={self.state.seed}")

    # ---- Estado transiente
    def _tab_transiente(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Estado transiente")
        frm = ttk.Frame(f); frm.pack(pady=10)
        self.warm_var = tk.IntVar(value=self.state.warmup)
        ttk.Label(frm, text="Warm-up (iteraciones a descartar):").grid(row=0, column=0, sticky="e")
        ttk.Scale(frm, variable=self.warm_var, from_=0, to=100, orient="horizontal").grid(row=0, column=1, padx=10)
        ttk.Button(frm, text="Guardar", command=self._save_warm).grid(row=1, column=0, columnspan=2, pady=10)

    def _save_warm(self):
        self.state.warmup = max(0, int(self.warm_var.get()))
        self.lbl_status.config(text=self._status_text())
        messagebox.showinfo("OK", f"Warm-up={self.state.warmup}")

    # ---- Simulación
    def _tab_simulacion(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="Simulación")
        top = ttk.Frame(f); top.pack(fill="x", pady=5)
        self.lam_var = tk.DoubleVar(value=0.5)
        ttk.Label(top, text="λ Poisson (shocks):").pack(side="left", padx=5)
        ttk.Entry(top, textvariable=self.lam_var, width=10).pack(side="left")
        self.fx_vars = {k: tk.DoubleVar(value=v) for k, v in efecto_shock_default().items()}
        fx_frame = ttk.Frame(top); fx_frame.pack(side="left", padx=15)
        for name, var in self.fx_vars.items():
            ttk.Label(fx_frame, text=f"Efecto {name}:").pack(side="left", padx=3)
            ttk.Entry(fx_frame, textvariable=var, width=7).pack(side="left")
        ttk.Button(top, text="Ejecutar", command=self._run_sim).pack(side="left", padx=10)

        self.txt_sim = tk.Text(f, height=10); self.txt_sim.pack(fill="x", padx=5, pady=5)

    def _run_sim(self):
        base = base_probs()
        fx = {k: float(v.get()) for k, v in self.fx_vars.items()}
        lam = float(self.lam_var.get() if self.state.poisson_lambda is None else self.state.poisson_lambda)
        res = simular(self.state.T, self.state.R, self.state.warmup, base, lam, fx, seed=self.state.seed)

        mean_t = res["trajectories"].mean(axis=0)  # (T, C)
        series = {res["classes"][i]: mean_t[:, i] for i in range(len(res["classes"]))}
        path = guardar_lineas(series, "sim_evolucion", f"Evolución (T={self.state.T}, R={self.state.R}, warmup={res['warmup_used']})")

        self.txt_sim.delete("1.0","end")
        self.txt_sim.insert("1.0", f"Resumen post-warmup:\n{res['summary']}\nGráfico: {path}")
