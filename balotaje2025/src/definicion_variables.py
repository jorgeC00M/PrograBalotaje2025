# -*- coding: utf-8 -*-
"""
Define mapeos y el listado de predictores que entran al modelo.
Ajusta los nombres a los encabezados reales de tu Excel.
"""

MAPEO_IDEOLOGIA = {
    "izquierda": -2,
    "centro-izquierda": -1,
    "centro": 0,
    "centro-derecha": 1,
    "derecha": 2
}

# Variables atributo (Likert 1–5) — AJUSTA a tus columnas reales:
ATRIBUTOS = [
    "honestidad_a", "liderazgo_a", "conexion_a", "propuestas_a",
    "honestidad_b", "liderazgo_b", "conexion_b", "propuestas_b"
]

# Lista de features del modelo — AJUSTA a tus columnas reales:
COLUMNAS_X = [
    "firmeza",
    "ideologia_num",
] + ATRIBUTOS
