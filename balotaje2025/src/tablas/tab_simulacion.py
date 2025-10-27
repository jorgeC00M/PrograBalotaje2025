import tkinter as tk
from tkinter import ttk, messagebox

from ..simulacion.escenarios import base_probs, efecto_shock_default
from ..simulacion.simulador import simular
from ..visualizacion import guardar_lineas
from ..configuracion import RES_GRAFICOS


def build(app):
    f = ttk.Frame(app.nb)
    app.nb.add(f, text="Simulación")

    top = ttk.Frame(f)
    top.pack(fill="x", pady=5)

    app.lam_var = tk.DoubleVar(value=0.5)
    ttk.Label(top, text="λ Poisson (shocks):").pack(side="left", padx=5)
    ttk.Entry(top, textvariable=app.lam_var, width=10).pack(side="left")

    app.fx_vars = {k: tk.DoubleVar(value=v) for k, v in efecto_shock_default().items()}
    fx_frame = ttk.Frame(top)
    fx_frame.pack(side="left", padx=15)
    for name, var in app.fx_vars.items():
        ttk.Label(fx_frame, text=f"Efecto {name}:").pack(side="left", padx=3)
        ttk.Entry(fx_frame, textvariable=var, width=7).pack(side="left")

    ttk.Button(top, text="Ejecutar", command=lambda: _run_sim(app)).pack(side="left", padx=10)

    app.txt_sim = tk.Text(f, height=10)
    app.txt_sim.pack(fill="x", padx=5, pady=5)

    btn_frame = ttk.Frame(f)
    btn_frame.pack(fill="x")
    ttk.Button(btn_frame, text="Abrir carpeta de gráficos", command=lambda: _abrir_carpeta_graficos(app)).pack(side="left", padx=5, pady=5)

    app.img_sim_label = ttk.Label(f)
    app.img_sim_label.pack(pady=5)
    app._img_sim_ref = None


def _run_sim(app):
    base = base_probs()
    fx = {k: float(v.get()) for k, v in app.fx_vars.items()}
    lam = float(app.state.poisson_lambda if app.state.poisson_lambda is not None else app.lam_var.get())

    res = simular(app.state.T, app.state.R, app.state.warmup, base, lam, fx, seed=app.state.seed)

    mean_t = res["trajectories"].mean(axis=0)  # (T, C)
    series = {res["classes"][i]: mean_t[:, i] for i in range(len(res["classes"]))}
    path = guardar_lineas(
        series,
        "sim_evolucion",
        f"Evolución (T={app.state.T}, R={app.state.R}, warmup={res['warmup_used']})",
    )

    app.txt_sim.delete("1.0", "end")
    app.txt_sim.insert("1.0", f"Resumen post-warmup:\n{res['summary']}\nGráfico: {path}")

    try:
        img = tk.PhotoImage(file=str(path))
        app.img_sim_label.configure(image=img, text="")
        app._img_sim_ref = img
    except Exception as e:
        app.img_sim_label.configure(image="", text=f"No se pudo cargar la imagen.\n{path}\n{e}")


def _abrir_carpeta_graficos(app):
    import os, sys, subprocess
    folder = str(RES_GRAFICOS)
    try:
        if sys.platform.startswith("win"):
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir la carpeta.\n{folder}\n{e}")
