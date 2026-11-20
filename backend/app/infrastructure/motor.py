"""Adaptador que reutiliza el motor entrenado y aporta los datos del dashboard."""

import json
import sys
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.domain.contracts import Consulta

MOTOR = Path(__file__).resolve().parents[2] / "motor"
sys.path.insert(0, str(MOTOR))
from src.models.predict import cargar_modelo, predecir  # noqa: E402

INICIO = "2023-05-26"
FIN = "2023-06-30"
LIMITE = "2027-12-31"
FRANJAS = ["06:00–10:59", "11:00–14:59", "15:00–20:59"]


class MotorLocal:
    def __init__(self):
        self.panel = pd.read_csv(
            MOTOR / "data/processed/ventas_diarias_por_producto.csv", parse_dates=["fecha"]
        )
        self.panel_franjas = pd.read_csv(
            MOTOR / "data/processed/ventas_por_franja.csv", parse_dates=["fecha"]
        )
        self.clima = pd.read_csv(MOTOR / "data/raw/clima_nyc_2023.csv")
        self.predicciones = {
            False: pd.read_csv(MOTOR / "evidencias/predicciones_test.csv", parse_dates=["fecha"]),
            True: pd.read_csv(
                MOTOR / "evidencias/franjas/predicciones_test.csv", parse_dates=["fecha"]
            ),
        }
        self.selecciones = {}
        for por_franja in [False, True]:
            carpeta = MOTOR / ("models/franjas" if por_franja else "models")
            seleccion = json.loads((carpeta / "seleccion.json").read_text())
            self.selecciones[por_franja] = seleccion
            for nombre in [seleccion["seleccionado"], seleccion["respaldo_sin_clima"]]:
                cargar_modelo(carpeta / f"{nombre}.joblib")
        ventas = pd.read_csv(MOTOR / "data/raw/Coffee_Shop_Sales.csv")
        fechas = pd.to_datetime(ventas["transaction_date"], format="%m/%d/%y")
        ventas = ventas.loc[fechas.le("2023-05-25")].copy()
        ventas["importe"] = ventas["transaction_qty"] * ventas["unit_price"]
        precios = ventas.groupby(["store_location", "product_type"])[
            ["importe", "transaction_qty"]
        ].sum()
        self.precios = (precios.importe / precios.transaction_qty).to_dict()

    def catalogo(self) -> dict:
        return {
            "sucursales": sorted(self.panel.sucursal.unique()),
            "franjas": FRANJAS,
            "fecha_min": INICIO,
            "fecha_max": FIN,
            "escenario_hasta": LIMITE,
            "moneda": "USD",
            "ejemplo": {
                "sucursal": "Hell's Kitchen",
                "fecha": "2023-06-15",
                "franja": None,
                "periodo": 7,
                "clima": None,
            },
        }

    @lru_cache(maxsize=256)
    def tendencia(self, sucursal: str, fecha: str, franja: str | None, periodo: int) -> list[dict]:
        tabla = self.predicciones[franja is not None]
        seleccionado = self.selecciones[franja is not None]["seleccionado"]
        fin = pd.Timestamp(fecha)
        inicio = max(pd.Timestamp(INICIO), fin - pd.Timedelta(days=periodo - 1))
        mask = tabla.sucursal.eq(sucursal) & tabla.fecha.between(inicio, fin)
        if franja is not None:
            mask &= tabla.franja.eq(franja)
        grupos = tabla.loc[mask].groupby("fecha")[["unidades", seleccionado]].sum()
        return [
            {
                "fecha": f.strftime("%Y-%m-%d"),
                "reales": round(float(r.unidades), 2),
                "estimadas": round(float(r[seleccionado]), 2),
            }
            for f, r in grupos.iterrows()
        ]

    def calcular(self, consulta: Consulta) -> dict:
        if consulta.sucursal not in self.catalogo()["sucursales"]:
            raise ValueError("La sucursal no pertenece al dataset.")
        if not INICIO <= consulta.fecha <= LIMITE:
            raise ValueError(f"Selecciona una fecha entre {INICIO} y {LIMITE}.")
        date.fromisoformat(consulta.fecha)
        escenario = consulta.fecha > FIN
        if consulta.franja is not None and consulta.franja not in FRANJAS:
            raise ValueError("Selecciona una franja válida.")
        resultado = predecir(consulta.entrada_modelo())
        productos = resultado["productos"]
        # Precios ponderados por unidades usando exclusivamente entrenamiento.
        importe = sum(
            p["unidades"] * self.precios[(consulta.sucursal, p["producto"])] for p in productos
        )
        demanda_franjas = [
            {
                "franja": horario,
                "unidades": predecir(
                    {
                        **consulta.entrada_modelo(),
                        "franja": horario,
                    }
                )["prediccion"],
            }
            for horario in FRANJAS
        ]
        categorias = {}
        for producto in productos:
            categoria = producto["categoria"]
            categorias[categoria] = categorias.get(categoria, 0) + producto["unidades"]
        clima = consulta.clima
        if clima is None and not escenario:
            fila = self.clima.loc[
                self.clima.sucursal.eq(consulta.sucursal) & self.clima.fecha.eq(consulta.fecha)
            ].iloc[0]
            clima = {k: float(fila[k]) for k in ("temperatura_c", "lluvia_mm", "humedad_pct")}
        tabla = self.panel_franjas if consulta.franja is not None else self.panel
        if escenario:
            # Base del escenario: promedio diario de los últimos siete días del dataset.
            mask = tabla.sucursal.eq(consulta.sucursal) & tabla.fecha.isin(
                pd.date_range(end=FIN, periods=7)
            )
            if consulta.franja is not None:
                mask &= tabla.franja.eq(consulta.franja)
            previo = float(tabla.loc[mask, "unidades"].sum()) / 7
            sucursales = [
                {
                    "sucursal": nombre,
                    "unidades_reales": None,
                    "unidades_estimadas": predecir(
                        {**consulta.entrada_modelo(), "sucursal": nombre, "franja": None}
                    )["prediccion"],
                }
                for nombre in self.catalogo()["sucursales"]
            ]
            tendencia = []
        else:
            mask = tabla.sucursal.eq(consulta.sucursal) & tabla.fecha.eq(consulta.fecha)
            if consulta.franja is not None:
                mask &= tabla.franja.eq(consulta.franja)
            previo = float(tabla.loc[mask, "unidades_prom7"].sum())
            comparativo = (
                self.panel.loc[self.panel.fecha.eq(consulta.fecha)]
                .groupby("sucursal")
                .unidades.sum()
            )
            sucursales = [
                {"sucursal": k, "unidades_reales": int(v), "unidades_estimadas": None}
                for k, v in comparativo.items()
            ]
            tendencia = self.tendencia(
                consulta.sucursal, consulta.fecha, consulta.franja, consulta.periodo
            )
        return {
            **resultado,
            "sucursal": consulta.sucursal,
            "fecha": consulta.fecha,
            "ventas_estimadas_usd": round(importe, 2),
            "variacion_pct": (
                round((resultado["prediccion"] / previo - 1) * 100, 2) if previo else None
            ),
            "categorias": [
                {"categoria": k, "unidades": round(v, 2)} for k, v in categorias.items()
            ],
            "demanda_franjas": demanda_franjas,
            "clima": clima,
            "tendencia": tendencia,
            "sucursales": sucursales,
        }
