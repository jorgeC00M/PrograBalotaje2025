# -*- coding: utf-8 -*-
import os

# Rutas base
RUTA_BASE = os.path.dirname(os.path.dirname(__file__))
RUTA_DATOS = os.path.join(RUTA_BASE, "datos", "respuestas.xlsx")

RUTA_RESULTADOS = os.path.join(RUTA_BASE, "resultados")
RUTA_TABLAS = os.path.join(RUTA_RESULTADOS, "tablas")
RUTA_GRAFICOS = os.path.join(RUTA_RESULTADOS, "graficos")
RUTA_MODELOS = os.path.join(RUTA_RESULTADOS, "modelos")
RUTA_SIMULACIONES = os.path.join(RUTA_RESULTADOS, "simulaciones")

# Parámetros globales
SEMILLA = 42
PASOS_SIMULACION = 6

# Clases de voto (ajusta si cambian tus etiquetas)
CLASES = ["a", "b", "blanco", "nulo", "indeciso"]
CLASE_BASE = "indeciso"
