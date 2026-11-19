"""Entrena y evalúa modelos de ventas con cortes cronológicos."""
import argparse
import json
from pathlib import Path
from time import perf_counter

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.data.clima import VARIABLES

CORTE = pd.Timestamp("2023-05-25")
FIN = pd.Timestamp("2023-06-30")
NUMERICAS = ["dia_semana", "mes", "fin_de_semana", "unidades_lag7", "unidades_prom7"]
RF = "random_forest"
GB = "gradient_boosting"
CONFIGURACIONES = {
    RF: [
        {"n_estimators": 200, "min_samples_leaf": 1},
        {"n_estimators": 200, "max_depth": 12, "min_samples_leaf": 5},
    ],
    GB: [
        {"n_estimators": 200, "max_depth": 2, "learning_rate": 0.05, "min_samples_leaf": 5},
        {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05, "min_samples_leaf": 10},
    ],
}


def crear_pipeline(algoritmo, parametros, categoricas, clima):
    codificador = ColumnTransformer([
        ("categorias", OneHotEncoder(handle_unknown="error", sparse_output=False), categoricas),
        ("numericas", "passthrough", [*NUMERICAS, *(VARIABLES if clima else [])]),
    ])
    clase = RandomForestRegressor if algoritmo == RF else GradientBoostingRegressor
    return Pipeline([("datos", codificador), ("modelo", clase(random_state=42, **parametros))])


def cortes(train):
    fechas = train["fecha"].sort_values().unique()
    for anteriores, siguientes in TimeSeriesSplit(n_splits=3, test_size=21).split(fechas):
        yield train[train.fecha.isin(fechas[anteriores])], train[train.fecha.isin(fechas[siguientes])]


def validar(algoritmo, parametros, categoricas, con_clima, folds):
    errores = []
    for ajuste, validacion in folds:
        modelo = crear_pipeline(algoritmo, parametros, categoricas, con_clima)
        modelo.fit(ajuste, ajuste.unidades)
        errores.append(mean_absolute_error(validacion.unidades, modelo.predict(validacion)))
    return float(np.mean(errores))


def acierto_top5(tabla, predicciones, grupos):
    ranking = tabla.assign(estimadas=predicciones)
    aciertos = []
    for _, grupo in ranking.groupby(grupos, sort=False):
        real = set(grupo.sort_values(["unidades", "producto"], ascending=[False, True]).head(5).producto)
        estimado = set(grupo.sort_values(["estimadas", "producto"], ascending=[False, True]).head(5).producto)
        aciertos.append(len(real & estimado))
    return float(np.mean(aciertos))


def curva_boosting(parametros, categoricas, con_clima, fold, destino):
    ajuste, validacion = fold
    pipeline = crear_pipeline(GB, parametros, categoricas, con_clima)
    pipeline.fit(ajuste, ajuste.unidades)
    transformar = pipeline.named_steps["datos"].transform
    boosting = pipeline.named_steps["modelo"]
    fig, ax = plt.subplots(figsize=(8.4, 4.5), layout="constrained")
    for etiqueta, datos, color in [("Entrenamiento", ajuste, "#426a9a"), ("Validación", validacion, "#a64c32")]:
        valores = [mean_absolute_error(datos.unidades, p.clip(min=0))
                   for p in boosting.staged_predict(transformar(datos))]
        ax.plot(range(1, len(valores) + 1), valores, label=etiqueta, color=color, linewidth=2)
    ax.set(title="Error de Gradient Boosting según el número de árboles",
           xlabel="Número de árboles", ylabel="MAE (unidades)")
    ax.legend()
    ax.grid(alpha=0.22)
    fig.savefig(destino, dpi=150)
    plt.close(fig)


def entrenar(archivo, output, evidencias):
    tabla = pd.read_csv(archivo, parse_dates=["fecha"]).dropna(subset=["unidades_lag7", "unidades_prom7"])
    train = tabla[tabla.fecha <= CORTE].copy()
    test = tabla[(tabla.fecha > CORTE) & (tabla.fecha <= FIN)].copy()
    for nombre, conjunto in [("Train", train), ("Test", test)]:
        print(f"{nombre}: {len(conjunto):,} filas, {conjunto.fecha.min():%Y-%m-%d} a {conjunto.fecha.max():%Y-%m-%d}", flush=True)
    categoricas = ["sucursal", "producto"] + (["franja"] if "franja" in tabla else [])
    grupos_top = ["fecha", "sucursal"] + (["franja"] if "franja" in tabla else [])
    usar_clima = all(col in tabla for col in VARIABLES)
    folds = list(cortes(train))
    tuning = []
    candidatos = []
    for algoritmo, opciones in CONFIGURACIONES.items():
        for parametros in opciones:
            mae = validar(algoritmo, parametros, categoricas, False, folds)
            tuning.append({"algoritmo": algoritmo, "hiperparametros": parametros, "mae_validacion": mae})
            print(f"Ajuste {algoritmo} {parametros}: MAE validación {mae:.3f}", flush=True)
        elegido = min((fila for fila in tuning if fila["algoritmo"] == algoritmo),
                      key=lambda fila: fila["mae_validacion"])
        candidatos.append((algoritmo, False, elegido["hiperparametros"], elegido["mae_validacion"]))
        if usar_clima:
            mae = validar(algoritmo, elegido["hiperparametros"], categoricas, True, folds)
            candidatos.append((algoritmo, True, elegido["hiperparametros"], mae))

    output.mkdir(parents=True, exist_ok=True)
    evidencias.mkdir(parents=True, exist_ok=True)
    resultados = []
    salida_test = test[[*grupos_top, "producto", "unidades"]].copy()
    promedios = train.groupby(categoricas)["unidades"].mean()

    def registrar(nombre, pred_train, pred_test, **detalles):
        fila = dict(modelo=nombre, mae_train=mean_absolute_error(train.unidades, pred_train),
                    mae_test=mean_absolute_error(test.unidades, pred_test),
                    top5_test=acierto_top5(test, pred_test, grupos_top), **detalles)
        resultados.append(fila)
        salida_test[nombre] = pred_test
        print(f"{nombre}: MAE Train {fila['mae_train']:.3f} | MAE Test {fila['mae_test']:.3f} "
              f"| acierto top 5 {fila['top5_test']:.3f}/5", flush=True)

    registrar("promedio_historico",
              promedios.reindex(pd.MultiIndex.from_frame(train[categoricas])).to_numpy(),
              promedios.reindex(pd.MultiIndex.from_frame(test[categoricas])).to_numpy())
    registrar("promedio_7d", train.unidades_prom7.to_numpy(), test.unidades_prom7.to_numpy())
    for algoritmo, clima, parametros, mae_cv in candidatos:
        nombre = algoritmo + ("_con_clima" if clima else "_sin_clima")
        print(f"Entrenando {nombre} con {parametros}", flush=True)
        pipeline = crear_pipeline(algoritmo, parametros, categoricas, clima)
        inicio = perf_counter()
        pipeline.fit(train, train.unidades)
        segundos = perf_counter() - inicio
        pred_train = pipeline.predict(train).clip(min=0)
        pred_test = pipeline.predict(test).clip(min=0)
        muestra = next(iter(test.groupby(grupos_top)))[1]
        inicio = perf_counter()
        for _ in range(10):
            pipeline.predict(muestra)
        milisegundos = (perf_counter() - inicio) * 100
        registrar(nombre, pred_train, pred_test, mae_validacion=mae_cv, entrenamiento_s=segundos,
                  inferencia_ms=milisegundos, hiperparametros=json.dumps(parametros))
        destino = output / f"{nombre}.joblib"
        joblib.dump(pipeline, destino, compress=3)
        print(f"Guardado: {destino}", flush=True)

    def nombre_candidato(candidato):
        return candidato[0] + ("_con_clima" if candidato[1] else "_sin_clima")

    seleccionado = min(candidatos, key=lambda candidato: candidato[3])
    respaldo = min((c for c in candidatos if not c[1]), key=lambda candidato: candidato[3])
    metadata = {"seleccionado": nombre_candidato(seleccionado), "usa_clima": seleccionado[1],
                "respaldo_sin_clima": nombre_candidato(respaldo), "por_franja": "franja" in tabla}
    (output / "seleccion.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Seleccionado por validación: {metadata['seleccionado']}", flush=True)
    pd.DataFrame(resultados).to_csv(evidencias / "metricas.csv", index=False)
    pd.DataFrame(tuning).to_csv(evidencias / "ajuste.csv", index=False)
    salida_test.to_csv(evidencias / "predicciones_test.csv", index=False)
    gb = min((c for c in candidatos if c[0] == GB), key=lambda c: c[3])
    curva_boosting(gb[2], categoricas, gb[1], folds[-1], evidencias / "curva_mae.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("models"))
    parser.add_argument("--evidencias", type=Path, default=Path("evidencias"))
    args = parser.parse_args()
    entrenar(args.data, args.output, args.evidencias)
