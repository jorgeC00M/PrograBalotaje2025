# -*- coding: utf-8 -*-
import argparse
import os
from .configuracion import (
    RUTA_DATOS, RUTA_RESULTADOS, RUTA_TABLAS, RUTA_GRAFICOS, RUTA_MODELOS,
    CLASES, PASOS_SIMULACION
)
from .definicion_variables import COLUMNAS_X
from .carga_limpieza import cargar_datos, codificar_variables
from .tablas_cruzadas import generar_tablas_cruzadas, exportar_tablas
from .visualizacion import guardar_barras, guardar_lineas
from .modelos.regresion_multinomial import preparar_X_y, entrenar_multinomial, exportar_coeficientes, params_a_betas_por_clase
from .simulacion.simulador import simular
# Opcional si quieres usar escenarios:
from .simulacion.escenarios import escenario_simple

def main():
    print(">>> Ejecutando pipeline Balotaje 2025...")
    parser = argparse.ArgumentParser(description="Pipeline Balotaje 2025")
    parser.add_argument("--crosstabs", action="store_true", help="Genera tablas cruzadas y gráfico de distribución")
    parser.add_argument("--multinomial", action="store_true", help="Entrena regresión logística multinomial")
    parser.add_argument("--simular", action="store_true", help="Corre simulación dinámica básica")
    args = parser.parse_args()

    # Asegura carpetas
    for d in [RUTA_RESULTADOS, RUTA_TABLAS, RUTA_GRAFICOS, RUTA_MODELOS]:
        os.makedirs(d, exist_ok=True)

    # Cargar y codificar
    df = cargar_datos(RUTA_DATOS)
    df = codificar_variables(df)

    # 1) Tablas cruzadas
    if args.crosstabs:
        tablas = generar_tablas_cruzadas(df)
        xlsx = exportar_tablas(tablas)
        if "voto" in df.columns:
            guardar_barras(df["voto"].value_counts().to_dict(), "intencion_voto.png")
        print(f"[OK] Tablas cruzadas exportadas en: {xlsx}")

    # 2) Regresión multinomial
    if args.multinomial:
        df_fit = df[df["voto"].isin(CLASES)].dropna(subset=COLUMNAS_X)
        if df_fit.empty:
            print("[AVISO] No hay filas válidas para entrenar. Revisa COLUMNAS_X y tus datos.")
        else:
            X, y = preparar_X_y(df_fit, COLUMNAS_X, "voto")
            modelo, rrr = entrenar_multinomial(X, y)
            ruta_coef = os.path.join(RUTA_MODELOS, "coeficientes_multinomial.xlsx")
            exportar_coeficientes(modelo, rrr, ruta_coef)
            print("[OK] Modelo multinomial entrenado. Coeficientes en:", ruta_coef)
            print(modelo.summary())

    # 3) Simulación (opcional, usa el modelo recién entrenado en memoria si lo tienes)
    if args.simular:
        # Si no acabas de entrenar, vuelve a entrenar rápidamente:
        df_fit = df[df["voto"].isin(CLASES)].dropna(subset=COLUMNAS_X)
        if df_fit.empty:
            print("[AVISO] No hay datos válidos para simular.")
            return
        X, y = preparar_X_y(df_fit, COLUMNAS_X, "voto")
        modelo, _ = entrenar_multinomial(X, y)
        betas_por_clase = params_a_betas_por_clase(modelo, CLASES)

        # Estado inicial y firmeza
        mapa = {cl: i for i, cl in enumerate(CLASES)}
        estados_idx = df_fit["voto"].map(mapa).to_numpy()
        firmeza = df_fit["firmeza"].fillna(0).to_numpy() if "firmeza" in df_fit.columns else (X.iloc[:, 0] * 0)

        # (Opcional) escenarios simples — puedes pasar None si no quieres shocks
        shocks = escenario_simple(CLASES, pasos=PASOS_SIMULACION, favorece="a", delta=0.4, t0=2)

        hist_df, _, hist_path = simular(
            pasos=PASOS_SIMULACION,
            X=X.to_numpy(),
            firmeza=firmeza,
            estados_idx=estados_idx,
            clases=CLASES,
            betas_por_clase=betas_por_clase,
            shocks_por_t=shocks
        )
        img_path = guardar_lineas(hist_df, "simulacion_evolucion.png")
        print("[OK] Simulación completada.")
        print("  Historial:", hist_path)
        print("  Gráfico  :", img_path)

if __name__ == "__main__":
    main()
