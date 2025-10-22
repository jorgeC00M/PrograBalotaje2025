# -*- coding: utf-8 -*-
import os
import matplotlib.pyplot as plt
from .configuracion import RUTA_GRAFICOS

def guardar_barras(dic_conteos: dict, nombre="intencion_voto.png"):
    os.makedirs(RUTA_GRAFICOS, exist_ok=True)
    ruta = os.path.join(RUTA_GRAFICOS, nombre)
    plt.figure()
    plt.bar(list(dic_conteos.keys()), list(dic_conteos.values()))
    plt.title("Distribución de intención de voto")
    plt.ylabel("Frecuencia")
    plt.savefig(ruta, bbox_inches="tight")
    plt.close()
    return ruta

def guardar_lineas(df_hist, nombre="simulacion_evolucion.png"):
    os.makedirs(RUTA_GRAFICOS, exist_ok=True)
    ruta = os.path.join(RUTA_GRAFICOS, nombre)
    plt.figure()
    for col in df_hist.columns:
        plt.plot(df_hist.index, df_hist[col], label=col)
    plt.title("Evolución por clase (conteos)")
    plt.xlabel("t")
    plt.ylabel("Conteos")
    plt.legend()
    plt.savefig(ruta, bbox_inches="tight")
    plt.close()
    return ruta
