"""Descarga el clima histórico por sucursal con Open-Meteo."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

INICIO = "2023-01-01"
FIN = "2023-06-30"
ZONA = "America/New_York"
# Puntos aproximados de los barrios. El CSV no incluye domicilios.
PUNTOS = {
    "Astoria": (40.7650, -73.9300),
    "Hell's Kitchen": (40.7635, -73.9918),
    "Lower Manhattan": (40.7128, -74.0060),
}
VARIABLES = ["temperatura_c", "lluvia_mm", "humedad_pct"]
URL = "https://archive-api.open-meteo.com/v1/archive"


def descargar(salida):
    tablas = []
    consultas = []
    for sucursal, (lat, lon) in PUNTOS.items():
        parametros = {
            "latitude": lat, "longitude": lon, "start_date": INICIO, "end_date": FIN,
            "timezone": ZONA, "models": "era5",
            "hourly": "temperature_2m,relative_humidity_2m", "daily": "rain_sum",
        }
        enlace = f"{URL}?{urlencode(parametros)}"
        with urlopen(enlace, timeout=30) as respuesta:
            datos = json.load(respuesta)
        if datos["timezone"] != ZONA:
            raise ValueError(f"Zona horaria inesperada para {sucursal}")
        horas = pd.DataFrame(datos["hourly"]).rename(columns={
            "temperature_2m": "temperatura_c", "relative_humidity_2m": "humedad_pct",
        })
        horas["fecha"] = pd.to_datetime(horas.pop("time")).dt.normalize()
        if horas.isna().any().any():
            raise ValueError(f"Faltan valores meteorológicos por hora para {sucursal}")
        medias = horas.groupby("fecha", as_index=False).mean()
        lluvia = pd.DataFrame(datos["daily"]).rename(columns={"time": "fecha", "rain_sum": "lluvia_mm"})
        lluvia["fecha"] = pd.to_datetime(lluvia["fecha"])
        dia = medias.merge(lluvia, on="fecha", how="outer", validate="one_to_one")
        esperado = pd.date_range(INICIO, FIN)
        if not pd.DatetimeIndex(dia["fecha"]).equals(esperado) or dia.isna().any().any():
            raise ValueError(f"Histórico diario incompleto para {sucursal}")
        dia["sucursal"] = sucursal
        tablas.append(dia[["fecha", "sucursal", *VARIABLES]])
        consultas.append({
            "sucursal": sucursal, "url": enlace,
            "latitud_celda": datos["latitude"], "longitud_celda": datos["longitude"],
            "unidades_horarias": datos["hourly_units"], "unidades_diarias": datos["daily_units"],
        })
        print(f"{sucursal}: {len(dia)} días, celda {datos['latitude']}, {datos['longitude']}", flush=True)
    salida.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(tablas, ignore_index=True).to_csv(salida, index=False)
    salida.with_suffix(".json").write_text(json.dumps(consultas, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/raw/clima_nyc_2023.csv"))
    descargar(parser.parse_args().output)
