"""Validación del contrato HTTP y documentación OpenAPI."""

from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class Clima(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    temperatura_c: float = Field(ge=-30, le=50)
    lluvia_mm: float = Field(ge=0, le=300)
    humedad_pct: float = Field(ge=0, le=100)


class ConsultaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sucursal: Literal["Astoria", "Hell's Kitchen", "Lower Manhattan"]
    fecha: date = Field(ge=date(2023, 5, 26), le=date(2027, 12, 31))
    franja: Literal["06:00–10:59", "11:00–14:59", "15:00–20:59"] | None = None
    periodo: Literal[7, 14, 30] = 7
    clima: Clima | None = None


class Producto(BaseModel):
    producto: str
    categoria: str
    unidades: float
    nivel: Literal["Alta", "Media", "Baja"]


class Categoria(BaseModel):
    categoria: str
    unidades: float


class PuntoTendencia(BaseModel):
    fecha: date
    reales: float
    estimadas: float


class Sucursal(BaseModel):
    sucursal: str
    unidades_reales: int | None = None
    unidades_estimadas: float | None = None


class DemandaFranja(BaseModel):
    franja: str
    unidades: float


class PrediccionSalida(BaseModel):
    consulta_id: int
    sucursal: str
    fecha: date
    franja: str | None
    prediccion: float
    clase_etiqueta: str
    confianza_o_score: float | None
    menu_top5: list[Producto]
    productos: list[Producto]
    tiempo_ms: int
    modelo: str
    fuente_clima: str | None
    clima: Clima | None
    modo: Literal["historico", "escenario"] = "historico"
    base_ventas: dict[str, str] | None = None
    ventas_estimadas_usd: float
    variacion_pct: float | None
    categorias: list[Categoria]
    demanda_franjas: list[DemandaFranja]
    tendencia: list[PuntoTendencia]
    sucursales: list[Sucursal]


class ReporteEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consulta_id: int = Field(gt=0)
    comentario: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=5, max_length=2000)
    ]
