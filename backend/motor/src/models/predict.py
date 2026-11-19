"""Interfaz de inferencia independiente de la API y el dashboard."""
import argparse
import json
from datetime import date
from functools import lru_cache
from math import isfinite
from pathlib import Path
from time import perf_counter

import joblib
import pandas as pd

from src.data.clima import VARIABLES

RAIZ = Path(__file__).resolve().parents[2]
DATOS_DIARIOS = RAIZ / "data/processed/ventas_diarias_por_producto.csv"
DATOS_FRANJA = RAIZ / "data/processed/ventas_por_franja.csv"
RANGOS = {"temperatura_c": (-30, 50), "lluvia_mm": (0, 300), "humedad_pct": (0, 100)}


@lru_cache(maxsize=4)
def cargar_modelo(path):
    return joblib.load(path)


@lru_cache(maxsize=2)
def cargar_panel(path):
    return pd.read_csv(path, parse_dates=["fecha"])


def validar_clima(clima):
    if not isinstance(clima, dict) or any(k not in clima for k in VARIABLES):
        raise ValueError("El clima requiere temperatura_c, lluvia_mm y humedad_pct.")
    resultado = {}
    for campo, (minimo, maximo) in RANGOS.items():
        valor = clima[campo]
        if (isinstance(valor, bool) or not isinstance(valor, (float, int))
                or not isfinite(valor) or not minimo <= valor <= maximo):
            raise ValueError(f"{campo} debe estar entre {minimo} y {maximo}.")
        resultado[campo] = float(valor)
    return resultado


def etiqueta(prediccion, referencia):
    if referencia == 0:
        return "Alta" if prediccion > 0 else "Media"
    if prediccion >= 1.10 * referencia:
        return "Alta"
    if prediccion <= 0.90 * referencia:
        return "Baja"
    return "Media"


def predecir(entrada: dict) -> dict:
    """Predice para una sucursal y fecha. La franja y el clima son opcionales."""
    inicio = perf_counter()
    if not isinstance(entrada, dict):
        raise ValueError("Se espera un diccionario.")
    fecha_texto = entrada.get("fecha")
    try:
        fecha_iso = date.fromisoformat(fecha_texto)
        if fecha_iso.isoformat() != fecha_texto:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("La fecha debe tener formato AAAA-MM-DD.") from None
    fecha = pd.Timestamp(fecha_iso)
    clima = entrada.get("clima")
    if clima is not None:
        clima = validar_clima(clima)

    franja = entrada.get("franja")
    directorio = RAIZ / ("models/franjas" if franja is not None else "models")
    panel = cargar_panel(DATOS_FRANJA if franja is not None else DATOS_DIARIOS)
    sucursal = entrada.get("sucursal")
    if not isinstance(sucursal, str) or sucursal not in set(panel.sucursal):
        raise ValueError("Sucursal desconocida. Usa Astoria, Hell's Kitchen o Lower Manhattan.")
    panel = panel[panel.sucursal == sucursal]
    if franja is not None:
        if not isinstance(franja, str) or franja not in set(panel.franja):
            raise ValueError("Franja inválida. Consulta las franjas del README.")
        panel = panel[panel.franja == franja]
    if fecha < panel.fecha.min() or fecha > panel.fecha.max():
        raise ValueError("Fecha fuera del periodo histórico del prototipo.")

    dias_previos = pd.date_range(end=fecha - pd.Timedelta(days=1), periods=7)
    historico = panel[panel.fecha.isin(dias_previos)]
    if len(historico) != panel.producto.nunique() * len(dias_previos):
        raise ValueError("Se requieren siete días previos de ventas para esa sucursal.")
    filas = (historico.sort_values("fecha").groupby(["sucursal", "producto", "categoria"], as_index=False)
             .agg(unidades_lag7=("unidades", "first"), unidades_prom7=("unidades", "mean")))
    filas["dia_semana"] = fecha.dayofweek
    filas["mes"] = fecha.month
    filas["fin_de_semana"] = int(fecha.dayofweek >= 5)
    if franja is not None:
        filas["franja"] = franja

    seleccion = json.loads((directorio / "seleccion.json").read_text(encoding="utf-8"))
    nombre = seleccion["seleccionado"]
    fuente_clima = None
    if seleccion["usa_clima"]:
        if clima is None and set(VARIABLES).issubset(panel.columns):
            valores = panel.loc[panel.fecha.eq(fecha), VARIABLES].dropna().drop_duplicates()
            if len(valores) == 1:
                clima = valores.iloc[0].to_dict()
                fuente_clima = "historico"
        elif clima is not None:
            fuente_clima = "entrada"
        if clima is None:
            nombre = seleccion["respaldo_sin_clima"]
        else:
            for campo, valor in clima.items():
                filas[campo] = valor

    pipeline = cargar_modelo(directorio / f"{nombre}.joblib")
    filas["prediccion"] = pipeline.predict(filas).clip(min=0)
    total = float(filas.prediccion.sum())
    ranking = filas.sort_values(["prediccion", "producto"], ascending=[False, True])
    menu = [{"producto": f.producto, "categoria": f.categoria,
             "unidades": round(float(f.prediccion), 2),
             "nivel": etiqueta(f.prediccion, f.unidades_prom7)}
            for f in ranking.itertuples(index=False)]
    return {
        "prediccion": round(total, 2),
        "clase_etiqueta": f"Demanda {etiqueta(total, filas.unidades_prom7.sum())}",
        "confianza_o_score": None,
        "menu_top5": menu[:5],
        "productos": menu,
        "tiempo_ms": round((perf_counter() - inicio) * 1000),
        "modelo": nombre,
        "fuente_clima": fuente_clima,
        "franja": franja,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sucursal", default="Hell's Kitchen")
    parser.add_argument("--fecha", default="2023-06-15")
    parser.add_argument("--franja")
    args = parser.parse_args()
    entrada = vars(args)
    print(json.dumps({"entrada": entrada, "salida": predecir(entrada)}, indent=2, ensure_ascii=False))
