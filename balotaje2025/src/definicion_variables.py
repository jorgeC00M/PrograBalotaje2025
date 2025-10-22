# -*- coding: utf-8 -*-
def set_target(state, col: str):
    if state.df_proc is None or col not in state.df_proc.columns:
        raise ValueError("Columna objetivo inválida.")
    state.target = col

def set_role(state, cols: list[str], role: str):
    for c in cols:
        if c in state.df_proc.columns:
            state.roles[c] = role

def columnas(state):
    return [] if state.df_proc is None else list(state.df_proc.columns)

def numericas(state):
    if state.df_proc is None: return []
    return state.df_proc.select_dtypes(include="number").columns.tolist()

def categoricas(state):
    if state.df_proc is None: return []
    return [c for c in state.df_proc.columns if c not in numericas(state)]
