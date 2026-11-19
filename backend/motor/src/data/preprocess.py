"""Agrega ventas y construye variables que solo usan historial previo."""
import argparse
from pathlib import Path

import pandas as pd

from src.data.clima import VARIABLES

CATEGORIAS = ["Coffee", "Tea", "Drinking Chocolate", "Bakery"]
FRANJAS = ["06:00–10:59", "11:00–14:59", "15:00–20:59"]
CLAVE = ["fecha", "sucursal", "producto"]


def agregar_variables(tabla, grupos):
    tabla = tabla.sort_values([*grupos, "fecha"]).copy()
    historial = tabla.groupby(grupos, sort=False)["unidades"]
    tabla["unidades_lag7"] = historial.shift(7)
    tabla["unidades_prom7"] = historial.transform(lambda s: s.shift(1).rolling(7).mean())
    tabla["dia_semana"] = tabla["fecha"].dt.dayofweek
    tabla["mes"] = tabla["fecha"].dt.month
    tabla["fin_de_semana"] = (tabla["dia_semana"] >= 5).astype(int)
    return tabla


def preparar(archivo, clima=None, por_franja=False):
    ventas = pd.read_csv(archivo)
    print(f"CSV original: {len(ventas):,} filas, {len(ventas.columns)} columnas")
    necesarias = ["transaction_id", "transaction_date", "transaction_time", "transaction_qty",
                  "store_location", "product_type", "product_category"]
    if ventas[necesarias].isna().any().any() or ventas["transaction_id"].duplicated().any():
        raise ValueError("Revisa nulos y transacciones duplicadas antes de agregar.")
    ventas["fecha"] = pd.to_datetime(ventas["transaction_date"], format="%m/%d/%y")
    ventas = ventas.rename(columns={"store_location": "sucursal", "product_type": "producto",
                                    "product_category": "categoria", "transaction_qty": "unidades"})
    calendario = pd.date_range(ventas["fecha"].min(), ventas["fecha"].max())
    actividad = ventas.groupby("sucursal")["fecha"].nunique()
    if not actividad.eq(len(calendario)).all():
        raise ValueError("Faltan días completos de alguna sucursal. Revisa cierres o datos faltantes.")
    ventas = ventas[ventas["categoria"].isin(CATEGORIAS)].copy()
    catalogo = ventas[["sucursal", "producto", "categoria"]].drop_duplicates()
    if catalogo.duplicated(["sucursal", "producto"]).any():
        raise ValueError("Un tipo de producto tiene varias categorías dentro de una sucursal.")
    tabla = catalogo.merge(pd.DataFrame({"fecha": calendario}), how="cross")
    grupos = ["sucursal", "producto"]
    if por_franja:
        horas = pd.to_datetime(ventas["transaction_time"], format="%H:%M:%S").dt.hour
        ventas["franja"] = pd.cut(horas, [6, 11, 15, 21], right=False, labels=FRANJAS).astype("object")
        if ventas["franja"].isna().any():
            raise ValueError("Hay transacciones fuera de las franjas definidas.")
        tabla = tabla.merge(pd.DataFrame({"franja": FRANJAS}), how="cross")
        grupos.append("franja")
    clave = ["fecha", *grupos]
    totales = ventas.groupby(clave, as_index=False)["unidades"].sum()
    tabla = tabla.merge(totales, how="left", on=clave, validate="one_to_one")
    ceros = int(tabla["unidades"].isna().sum())
    tabla["unidades"] = tabla["unidades"].fillna(0).astype(int)
    if tabla["unidades"].sum() != ventas["unidades"].sum():
        raise ValueError("Las unidades agregadas no coinciden con el CSV filtrado.")
    print(f"Catálogo: {catalogo.producto.nunique()} tipos, {len(catalogo)} pares sucursal-tipo")
    print(f"Combinaciones sin ventas completadas con cero: {ceros:,}")
    tabla = agregar_variables(tabla, grupos)
    if clima:
        meteorologia = pd.read_csv(clima, parse_dates=["fecha"])
        tabla = tabla.merge(meteorologia[["fecha", "sucursal", *VARIABLES]], how="left",
                            on=["fecha", "sucursal"], validate="many_to_one")
        faltantes = tabla[VARIABLES].isna().any(axis=1).sum()
        if faltantes:
            raise ValueError(f"Clima incompleto para {faltantes} filas. Revisa fechas y sucursales.")
    listas = tabla["unidades_lag7"].notna() & tabla["unidades_prom7"].notna()
    print(f"Panel: {len(tabla):,} filas. Listas para entrenar: {listas.sum():,}")
    return tabla.sort_values(clave)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ventas", type=Path, default=Path("data/raw/Coffee_Shop_Sales.csv"))
    parser.add_argument("--clima", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/processed/ventas_diarias_por_producto.csv"))
    parser.add_argument("--por-franja", action="store_true")
    args = parser.parse_args()
    tabla = preparar(args.ventas, args.clima, args.por_franja)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(args.output, index=False)
    print(f"Guardado: {args.output}")
