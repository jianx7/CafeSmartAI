"""Contratos de la aplicación, independientes de FastAPI y pandas."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Consulta:
    sucursal: str
    fecha: str
    franja: str | None = None
    periodo: int = 7
    clima: dict[str, float] | None = None

    def entrada_modelo(self) -> dict:
        return {
            "sucursal": self.sucursal,
            "fecha": self.fecha,
            "franja": self.franja,
            "clima": self.clima,
        }


class MotorPrediccion(Protocol):
    def catalogo(self) -> dict: ...
    def calcular(self, consulta: Consulta) -> dict: ...


class RegistroConsultas(Protocol):
    def guardar_consulta(self, consulta: Consulta, resultado: dict) -> int: ...
    def listar(self) -> list[dict]: ...
    def reportar(self, consulta_id: int, comentario: str) -> int: ...
