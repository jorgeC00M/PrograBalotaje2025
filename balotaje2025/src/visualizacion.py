# -*- coding: utf-8 -*-
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # sin especificar estilos ni colores
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from .configuracion import RES_GRAFICOS

def guardar_histograma(x, titulo, nombre_archivo):
    fig, ax = plt.subplots()
    ax.hist(x, bins=20, density=True, alpha=0.4)
    ax.set_title(titulo)
    fp = RES_GRAFICOS / f"{nombre_archivo}.png"
    fig.savefig(fp, bbox_inches="tight")
    plt.close(fig)
    return fp

def guardar_radar(labels, valores, nombre_archivo, titulo="Perfil"):
    import numpy as np
    vals = list(valores) + [valores[0]]
    ang = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
    ang = list(ang) + [ang[0]]

    fig = plt.figure()
    ax = fig.add_subplot(111, polar=True)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(labels, fontsize=8)
    ax.plot(ang, vals)
    ax.fill(ang, vals, alpha=0.1)
    ax.set_title(titulo)
    fp = RES_GRAFICOS / f"{nombre_archivo}.png"
    fig.savefig(fp, bbox_inches="tight")
    plt.close(fig)
    return fp

def guardar_lineas(series_dict: dict[str, np.ndarray], nombre_archivo, titulo="Serie temporal"):
    fig, ax = plt.subplots()
    for k, y in series_dict.items():
        ax.plot(y, label=k)
    ax.legend()
    ax.set_title(titulo)
    fp = RES_GRAFICOS / f"{nombre_archivo}.png"
    fig.savefig(fp, bbox_inches="tight")
    plt.close(fig)
    return fp
